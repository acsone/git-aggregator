# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)

import logging
import os
from string import Template

import kaptan
from .exception import ConfigException
from ._compat import string_types


log = logging.getLogger(__name__)


def get_repos(config, force=False):
    """Return a :py:obj:`list` list of repos from config file.
    :param config: the repos config in :py:class:`dict` format.
    :param bool force: Force aggregate dirty repos or not.
    :type config: dict
    :rtype: list
    """
    repo_list = []
    for directory, repo_data in config.items():
        if not os.path.isabs(directory):
            directory = os.path.abspath(directory)
        repo_dict = {
            'cwd': directory,
            'force': force,
            'defaults': dict(),
            'fetch_all': False,
            'shell_command_after': [],
        }
        remote_names = set()
        # Handle DRY format
        if isinstance(repo_data, string_types):
            parts = repo_data.split(' ')
            if len(parts) != 2:
                raise ConfigException(
                    '%s: Repository must be formatted as '
                    '"url ref".' % directory)
            repo_dict['remotes'] = [{'name': 'origin', 'url': parts[0]}]
            repo_dict['merges'] = [{'remote': 'origin', 'ref': parts[1]}]
            repo_dict['target'] = {'remote': 'origin', 'branch': parts[1]}
            repo_list.append(repo_dict)
            continue
        # full format
        if 'defaults' in repo_data:
            repo_dict['defaults'] = repo_data.get('defaults', dict())
        if 'remotes' in repo_data:
            repo_dict['remotes'] = []
            remotes_data = repo_data['remotes'] or {}
            for remote_name, url in remotes_data.items():
                if not url:
                    raise ConfigException(
                        '%s: No url defined for remote %s.' %
                        (directory, remote_name))
                remote_dict = {
                    'name': remote_name,
                    'url': url
                }
                repo_dict['remotes'].append(remote_dict)
                remote_names.add(remote_name)
            if not remote_names:
                raise ConfigException(
                    '%s: You should at least define one remote.' % directory)
        else:
            raise ConfigException('%s: remotes is not defined.' % directory)
        if 'merges' in repo_data:
            merges = []
            merge_data = repo_data.get('merges') or []
            for merge in merge_data:
                try:
                    # Assume parts is a str
                    parts = merge.split(' ')
                    if len(parts) != 2:
                        raise ConfigException(
                            '%s: Merge must be formatted as '
                            '"remote_name ref".' % directory)
                    merge = {
                        "remote": parts[0],
                        "ref": parts[1],
                    }
                except AttributeError:
                    # Parts is a dict
                    try:
                        merge["remote"] = str(merge["remote"])
                        merge["ref"] = str(merge["ref"])
                    except KeyError:
                        raise ConfigException(
                            '%s: Merge lacks mandatory '
                            '`remote` or `ref` keys.' % directory)
                # Check remote is available
                if merge["remote"] not in remote_names:
                    raise ConfigException(
                        '%s: Merge remote %s not defined in remotes.' %
                        (directory, merge["remote"]))
                merges.append(merge)
            repo_dict['merges'] = merges
            if not merges:
                raise ConfigException(
                    '%s: You should at least define one merge.' % directory)
        else:
            raise ConfigException(
                '%s: merges is not defined.' % directory)
        # Only fetch required remotes by default
        repo_dict["fetch_all"] = repo_data.get("fetch_all", False)
        if isinstance(repo_dict["fetch_all"], string_types):
            repo_dict["fetch_all"] = frozenset((repo_dict["fetch_all"],))
        elif isinstance(repo_dict["fetch_all"], list):
            repo_dict["fetch_all"] = frozenset(repo_dict["fetch_all"])
        if 'target' not in repo_data:
            raise ConfigException('%s: No target defined.' % directory)
        parts = (repo_data.get('target') or "") .split(' ')
        if len(parts) != 2:
            raise ConfigException(
                '%s: Target must be formatted as '
                '"remote_name branch_name"' % directory)

        remote_name, branch = repo_data.get('target').split(' ')
        if remote_name not in remote_names:
            raise ConfigException(
                '%s: Target remote %s not defined in remotes.' %
                (directory, remote_name))
        repo_dict['target'] = {
            'remote': remote_name,
            'branch': branch,
        }
        commands = []
        if 'shell_command_after' in repo_data:
            cmds = repo_data['shell_command_after']
            # if str: turn to list
            if cmds:
                if isinstance(cmds, string_types):
                    cmds = [cmds]
                commands = cmds
        repo_dict['shell_command_after'] = commands
        repo_list.append(repo_dict)
    return repo_list


def load_config(config, expand_env=False, force=False):
    """Return repos from a directory and fnmatch. Not recursive.

    :param config: paths to config file
    :type config: str
    :param expand_env: True to expand environment varialbes in the config.
    :type expand_env: bool
    :param bool force: True to aggregate even if repo is dirty.
    :returns: expanded config dict item
    :rtype: iter(dict)
    """
    if not os.path.exists(config):
        raise ConfigException('Unable to find configuration file: %s' % config)

    file_extension = os.path.splitext(config)[1][1:]
    conf = kaptan.Kaptan(handler=kaptan.HANDLER_EXT.get(file_extension))

    if expand_env:
        with open(config, 'r') as file_handler:
            config = Template(file_handler.read())
            config = config.substitute(os.environ)

    conf.import_config(config)
    return get_repos(conf.export('dict') or {}, force)
