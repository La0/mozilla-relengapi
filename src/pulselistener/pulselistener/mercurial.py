# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import atexit
import io
import os
import tempfile

import hglib

from cli_common.log import get_logger
from cli_common.mercurial import robust_checkout
from pulselistener.config import REPO_TRY

logger = get_logger(__name__)


class MercurialWorker(object):
    '''
    Mercurial worker maintaining a local clone of mozilla-unified
    '''
    def __init__(self, phabricator_api, ssh_user, ssh_key, repo_url, repo_dir):
        self.repo_url = repo_url
        self.repo_dir = repo_dir
        self.phabricator_api = phabricator_api

        # Build asyncio shared queue
        self.queue = asyncio.Queue()

        # Write ssh key from secret
        _, self.ssh_key_path = tempfile.mkstemp(suffix='.key')
        with open(self.ssh_key_path, 'w') as f:
            f.write(ssh_key)

        # Build ssh conf
        conf = {
            'StrictHostKeyChecking': 'no',
            'User': ssh_user,
            'IdentityFile': self.ssh_key_path,
        }
        self.ssh_conf = 'ssh {}'.format(' '.join('-o {}="{}"'.format(k, v) for k, v in conf.items())).encode('utf-8')

        # Remove key when finished
        atexit.register(self.cleanup)

    def cleanup(self):
        os.unlink(self.ssh_key_path)
        logger.info('Removed ssh key')

    async def run(self):
        # Start by updating the repo
        logger.info('Checking out tip', repo=self.repo_url)
        self.repo = robust_checkout(self.repo_url, self.repo_dir)
        self.repo.setcbout(lambda msg: logger.info('Mercurial', stdout=msg))
        self.repo.setcberr(lambda msg: logger.info('Mercurial', stderr=msg))
        logger.info('Initial clone finished')

        # Wait for phabricator diffs to apply
        while True:
            diff = await self.queue.get()
            assert isinstance(diff, dict)
            assert 'phid' in diff

            try:
                await self.handle_diff(diff)

            except hglib.error.CommandError as e:
                logger.warn('Mercurial error on diff', error=e.err, args=e.args, phid=diff['phid'])

                # Remove uncommited changes
                self.repo.revert(self.repo_dir.encode('utf-8'), all=True)

            except Exception as e:
                logger.warn('Failed to process diff', error=e, phid=diff['phid'])

                # Remove uncommited changes
                self.repo.revert(self.repo_dir.encode('utf-8'), all=True)

            # Notify the queue that the message has been processed
            self.queue.task_done()

    def clean(self):
        '''
        Steps to clean the mercurial repo
        '''
        logger.info('Remove all mercurial drafts')
        try:
            cmd = hglib.util.cmdbuilder(b'strip', rev=b'roots(outgoing())', force=True)
            self.repo.rawcommand(cmd)
        except hglib.error.CommandError as e:
            if b'abort: empty revision set' not in e.err:
                raise

        logger.info('Pull updates from remote repo')
        self.repo.pull()

    async def handle_diff(self, diff):
        '''
        Handle a new diff received from Phabricator:
        - apply revision to mercurial repo
        - trigger push-to-try
        '''
        logger.info('Received diff {phid}'.format(**diff))

        # Start by cleaning the repo
        self.clean()

        # Get the stack of patches
        patches = self.phabricator_api.load_patches_stack(self.repo, diff, default_revision='central')
        assert len(patches) > 0, 'No patches to apply'

        # Get current revision
        base = self.repo.tip()

        # Apply the patches and commit them one by one
        for diff_phid, patch in patches:
            logger.info('Applying patch', phid=diff_phid)
            self.repo.import_(
                patches=io.BytesIO(patch.encode('utf-8')),
                message='Patch {}'.format(diff_phid),
                user='pulselistener',
            )

        # Rebase multiple patches into a single commit
        if len(patches) > 1:
            rebase_msg = '"Patches {}"'.format(', '.join(p[0] for p in patches)).encode('utf-8')
            cmd = hglib.util.cmdbuilder(
                b'rebase',
                dest=base.node,
                collapse=True,
                message=rebase_msg
            )

            logger.info('Rebasing multiple patches into a single commit', msg=rebase_msg)
            self.repo.rawcommand(cmd)

        # Push the commit on try
        commit = self.repo.tip()
        assert commit.node != base.node, 'Commit is the same as base ({}), nothing changed !'.format(commit.node)
        logger.info('Pushing patches to try', rev=commit.node)
        self.repo.push(
            dest=REPO_TRY,
            rev=commit.node,
            ssh=self.ssh_conf,
            force=True,
        )

        logger.info('Diff has been pushed !')
