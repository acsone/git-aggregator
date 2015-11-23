# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License LGPLv3 (http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

import logging
import os

import kaptan

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
        if 'remotes' in repo_data:
            repo_dict['remotes'] = []
            for remote_name, url in repo_data['remotes'].items():
                remote_dict = {
                    'name': remote_name,
                    'url': url
                }
                repo_dict['remotes'].append(remote_dict)
        merges = []
        for merge in repo_data.get('merges', []):
            remote, ref = merge.split(' ')
            merges.append({
                'remote': remote,
                'ref': ref,
            })
        repo_dict['merges'] = merges
        remote, branch = repo_data.get('target').split(' ')
        repo_dict['target'] = {
                'remote': remote,
                'branch': branch,
            }
        repo_list.append(repo_dict)
    return repo_list


def load_config(config):
    """Return repos from a directory and fnmatch. Not recursive.
    :param configs: paths to config file
    :type path: list
    :returns: expanded config dict item
    :rtype: iter(dict)
    """
    fExt = os.path.splitext(config)[-1]
    conf = kaptan.Kaptan(handler=fExt.lstrip('.'))
    conf.import_config(config)
    return get_repos(conf.export('dict'))
