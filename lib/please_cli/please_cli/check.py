# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import cli_common.cli
import click
import click_spinner
import please_cli.projects
import please_cli.config
import please_cli.shell
import please_cli.utils

CMD_HELP = '''
Run tests, linters, etc.. for an PROJECT.

\b
PROJECTS:
{projects}

'''.format(
    projects=please_cli.projects.ALL,
)


@click.command(
    cls=please_cli.utils.ClickCustomCommand,
    short_help="Run tests, linters, etc.. for an PROJECT.",
    epilog="Happy hacking!",
    help=CMD_HELP,
    )
@click.argument(
    'project',
    required=True,
    type=click.Choice(please_cli.projects.ALL.names()),
    )
@click.option(
    '--nix-shell',
    required=True,
    default=please_cli.config.NIX_BIN_DIR + 'nix-shell',
    help='Path to nix-shell command (default: {}).'.format(
        please_cli.config.NIX_BIN_DIR + 'nix-shell',
        ),
    )
@cli_common.cli.taskcluster_options
@click.pass_context
def cmd(ctx, project_name, nix_shell,
        taskcluster_secret,
        taskcluster_client_id,
        taskcluster_access_token,
    ):
    project = please_cli.projects.ALL.get(project_name)
    if not project:
        raise click.ClickException('Missing project {}'.format(project_name))

    checks = project.get('checks')
    if not checks:
        raise click.ClickException('No checks found for `{}` project.'.format(project_name))

    for check_title, check_command in checks:
        click.echo(' => {}: '.format(check_title), nl=False)
        with click_spinner.spinner():
            returncode, output, error = ctx.invoke(please_cli.shell.cmd,
                                                   project=project.name,
                                                   quiet=True,
                                                   command=check_command,
                                                   nix_shell=nix_shell,
                                                   taskcluster_secret=taskcluster_secret,
                                                   taskcluster_client_id=taskcluster_client_id,
                                                   taskcluster_access_token=taskcluster_access_token,
                                                   )
        please_cli.utils.check_result(returncode, output, raise_exception=False)


if __name__ == "__main__":
    cmd()
