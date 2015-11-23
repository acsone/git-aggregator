# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License LGPLv3 (http://www.gnu.org/licenses/lgpl-3.0-standalone.html)
# Parts of the code comes from ANYBOX
# https://github.com/anybox/anybox.recipe.odoo

import os
import logging
import subprocess

from .utils import working_directory_keeper

logger = logging.getLogger(__name__)


class Repo(object):
    def __init__(self, cwd, remotes, merges, target):
        self.cwd = cwd
        self.remotes = remotes
        self.merges = merges
        self.target = target

    def log_call(self, cmd, callwith=subprocess.check_call,
                 log_level=logging.INFO, **kw):
            """Wrap a subprocess call with logging
            :param meth: the calling method to use.
            """
            logger.log(log_level, "%s> call %r", self.cwd, cmd)
            return callwith(cmd, **kw)

    def aggregate(self):
        """ Aggregate all merges into the target branch
        If the target_dir doesn't exist, create an empty git repo otherwise
        clean it, add all remotes , and merge all merges.
        """
        target_dir = self.cwd

        with working_directory_keeper:
            is_new = not os.path.exists(target_dir)
            if is_new:
                self.log_call(['git', 'init', target_dir])

            os.chdir(target_dir)
            if not is_new:
                self.log_call(['git', 'reset', '--hard', 'ORIG_HEAD'])
            else:
                self.log_call(['git', 'checkout', '-b', self.target['branch']])

            for r in self.remotes:
                self._set_remote(**r)
            self.log_call(['git', 'fetch',  '--all'])
            for merge in self.merges:
                self._merge(**merge)

    def push(self):
        with working_directory_keeper:
            os.chdir(self.cwd)
            self.log_call(
                ['git', 'push', '-f', self.target['remote']])

    def _merge(self, remote, ref):
        self.log_call(
            ['git', 'pull', remote, ref, '--no-edit'])

    def _get_remotes(self):
        lines = self.log_call(
            ['git', 'remote', '-v'],
            callwith=subprocess.check_output).splitlines()
        remotes = {}
        for line in lines:
            name, url = line.split('\t')
            url = url.split(' ')[0]
            v = remotes.setdefault(name, url)
            if v != url:
                raise NotImplemented(
                    'Different urls gor push and fetch for remote %s\n'
                    '%s != %s' % (name, url, v))
        return remotes

    def _set_remote(self, name, url):
        """Add remote to the repository. It's equivalent to the command
        git remote add <name> <url>

        If the remote already exists with an other url, it's removed
        and added aggain
        """
        remotes = self._get_remotes()
        exising_url = remotes.get(name)
        if exising_url == url:
            logger.info('Remote already exists %s <%s>', name, url)
            return
        if not exising_url:
            logger.info('Adding remote %s <%s>', name, url)
            self.log_call(['git', 'remote', 'add', name, url])
        else:
            logger.info('Remote remote %s <%s> -> <%s>',
                        name, exising_url, url)
            self.log_call(['git', 'remote', 'rm', name])
            self.log_call(['git', 'remote', 'add', name, url])
