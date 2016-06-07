# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)

import logging
import os

import kaptan
from .exception import ConfigException
from ._compat import string_types


log = logging.getLogger(__name__)


def get_repos(config):
    """Return a :py:obj:`list` list of repos from config file.
    :param config: the repos config in :py:class:`dict` format.
    :type config: dict
    :rtype: list
    """
    repo_list = []
    for directory, repo_data in config.items():
        if not os.path.isabs(directory):
            directory = os.path.abspath(directory)
        repo_dict = {
            'cwd': directory,
        }
        remote_names = set()
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
                parts = merge.split(' ')
                if len(parts) != 2:
                    raise ConfigException(
                        '%s: Merge must be formatted as '
                        '"remote_name ref".' % directory)

                remote_name, ref = merge.split(' ')
                if remote_name not in remote_names:
                    raise ConfigException(
                        '%s: Merge remote %s not defined in remotes.' %
                        (directory, remote_name))
                merges.append({
                    'remote': remote_name,
                    'ref': ref,
                })
            repo_dict['merges'] = merges
            if not merges:
                raise ConfigException(
                    '%s: You should at least define one merge.' % directory)
        else:
            raise ConfigException(
                '%s: merges is not defined.' % directory)
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


def load_config(config):
    """Return repos from a directory and fnmatch. Not recursive.

    :param config: paths to config file
    :type config: str
    :returns: expanded config dict item
    :rtype: iter(dict)
    """
    if not os.path.exists(config):
        raise ConfigException('Unable to find configuration file: %s' % config)

    fExt = os.path.splitext(config)[-1]
    conf = kaptan.Kaptan(handler=fExt.lstrip('.'))
    conf.import_config(config)
    return get_repos(conf.export('dict'))
