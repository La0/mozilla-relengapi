# -*- coding: utf-8 -*-
import asyncio

import structlog

from pulselistener import taskcluster
from pulselistener.code_coverage import CodeCoverage
from pulselistener.code_review import CodeReview
from pulselistener.config import QUEUE_MERCURIAL
from pulselistener.config import QUEUE_MONITORING
from pulselistener.config import QUEUE_PHABRICATOR_RESULTS
from pulselistener.config import QUEUE_PULSE_CODECOV
from pulselistener.config import QUEUE_WEB_BUILDS
from pulselistener.lib.bus import MessageBus
from pulselistener.lib.mercurial import MercurialWorker
from pulselistener.lib.monitoring import Monitoring
from pulselistener.lib.pulse import PulseListener
from pulselistener.lib.pulse import run_consumer
from pulselistener.lib.web import WebServer

logger = structlog.get_logger(__name__)


class EventListener(object):
    '''
    Listen to external events and trigger new tasks
    '''
    def __init__(self, cache_root):
        # Create message bus shared amongst process
        self.bus = MessageBus()

        # Build client applications configuration
        # TODO: use simpler secret structure per client
        clients_conf = {
            h['type']: h
            for h in taskcluster.secrets['HOOKS']
        }
        code_review_conf = clients_conf.get('static-analysis-phabricator')
        code_coverage_conf = clients_conf.get('code-coverage')

        # Code Review Workflow
        if code_review_conf:
            self.code_review = CodeReview(
                api_key=taskcluster.secrets['PHABRICATOR']['token'],
                url=taskcluster.secrets['PHABRICATOR']['url'],
                publish=taskcluster.secrets['PHABRICATOR'].get('publish', False),
                risk_analysis_reviewers=code_review_conf.get('risk_analysis_reviewers', [])
            )
            self.code_review.register(self.bus)

            # Build mercurial worker & queue
            self.mercurial = MercurialWorker(
                QUEUE_MERCURIAL,
                QUEUE_PHABRICATOR_RESULTS,
                repositories=self.code_review.get_repositories(taskcluster.secrets['repositories'], cache_root),
            )
            self.mercurial.register(self.bus)

            # Create web server
            self.webserver = WebServer(QUEUE_WEB_BUILDS)
            self.webserver.register(self.bus)
        else:
            self.code_review = None
            self.mercurial = None
            self.webserver = None

        # Code Coverage Workflow
        if code_coverage_conf:
            self.code_coverage = CodeCoverage(code_coverage_conf, self.bus)

            # Setup monitoring for newly created tasks
            self.monitoring = Monitoring(QUEUE_MONITORING, taskcluster.secrets['ADMINS'], 7 * 3600)
            self.monitoring.register(self.bus)

            # Create pulse listener for code coverage
            self.pulse = PulseListener(
                QUEUE_PULSE_CODECOV,
                'exchange/taskcluster-queue/v1/task-group-resolved',
                '#',
                taskcluster.secrets['PULSE_USER'],
                taskcluster.secrets['PULSE_PASSWORD'],
            )
            self.pulse.register(self.bus)

        else:
            self.code_coverage = None
            self.monitoring = None
            self.pulse = None

        assert self.code_review or self.code_coverage, 'No client applications to run !'

    def run(self):
        consumers = []

        if self.code_review:
            consumers += [
                # Code review main workflow
                self.code_review.run(),

                # Add mercurial task
                self.mercurial.run(),
            ]

            # Publish results on Phabricator
            if self.code_review.publish:
                consumers.append(
                    self.bus.run(self.code_review.publish_results, QUEUE_PHABRICATOR_RESULTS)
                )

            # Start the web server in its own process
            web_process = self.webserver.start()

        if self.code_coverage:
            consumers += [
                # Code coverage main workflow
                self.code_coverage.run(),

                # Add monitoring task
                self.monitoring.run(),

                # Add pulse task
                self.pulse.run(),
            ]

        # Run all tasks concurrently
        run_consumer(asyncio.gather(*consumers))

        if self.code_review:
            web_process.join()
