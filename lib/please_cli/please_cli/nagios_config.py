# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click
import please_cli.config
import please_cli.projects

NAGIOS_TEMPLATE = ''''%s' => {
    parents        => 'fw1.private.releng.scl3.mozilla.net',
    check_command  => 'check_tcp2!443!2!4',
    ping_check_command => 'check_tcp2!443!2!4',
    contact_groups => '%s',
    hostgroups => [
        'releng-apps'
    ]
},'''


@click.command()
@click.option(
    '--channel',
    type=click.Choice(please_cli.config.CHANNELS),
    default=None,
    )
def cmd(channel):

    if channel is None:
        channels = please_cli.config.CHANNELS
    else:
        channels = [channel]


    for project in please_cli.projects.ALL.list_deployable():
        project_deploy_options = project.get('deploy_options')

        if project_deploy_options:
            for channel in sorted(channels):

                if channel not in project_deploy_options or 'url' not in project_deploy_options[channel]:
                    continue

                project_url = project_deploy_options[channel]['url']
                project_url = project_url.lstrip('https')
                project_url = project_url.lstrip('http')
                project_url = project_url.lstrip('://')

                contact_groups = 'shipitalerts'
                if channel == 'production':
                    contact_groups = 'build'


                click.echo(NAGIOS_TEMPLATE % (project_url, contact_groups))
