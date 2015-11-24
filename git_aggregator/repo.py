# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License LGPLv3 (http://www.gnu.org/licenses/lgpl-3.0-standalone.html)
# Parts of the code comes from ANYBOX
# https://github.com/anybox/anybox.recipe.odoo

import os
import logging
import subprocess

from .utils import working_directory_keeper
from exception import GitAggregatorException
from colorama.initialise import orig_stderr

logger = logging.getLogger(__name__)


def ishex(s):
    """True iff given string is a valid hexadecimal number.
    >>> ishex('deadbeef')
    True
    >>> ishex('01bn78')
    False
    """
    try:
        int(s, 16)
    except ValueError:
        return False
    return True


class Repo(object):
    def __init__(self, cwd, remotes, merges, target,
                 shell_command_after=None):
        """Initialize a git repository aggregator

        :param cwd: path to the directory where to initialize the repository
        :param remotes: list of remote linked to the repository. A remote is
        a dict {'name': '', 'url': ''}
        :param: merges list of merge to apply to build the aggregated
        repository. A merge is a dict {'remote': '', 'ref': ''}
        :param target:
        :patam shell_command_after: an optional list of shell command to
        execute after the aggregation
        """
        self.cwd = cwd
        self.remotes = remotes
        self.merges = merges
        self.target = target
        self.shell_command_after = shell_command_after or []

    def query_remote_ref(self, remote, ref):
        """Query remote repo about given ref.
        :return: ``('tag', sha)`` if ref is a tag in remote
                 ``('branch', sha)`` if ref is branch (aka "head") in remote
                 ``(None, ref)`` if ref does not exist in remote. This happens
                 notably if ref if a commit sha (they can't be queried)
        """
        out = self.log_call(['git', 'ls-remote', remote, ref],
                            cwd=self.cwd,
                            callwith=subprocess.check_output,
                            log_level=logging.DEBUG).strip()
        for sha, fullref in (l.split() for l in out.splitlines()):
            if fullref == 'refs/heads/' + ref:
                return 'branch', sha
            elif fullref == 'refs/tags/' + ref:
                return 'tag', sha
            elif fullref == ref and ref == 'HEAD':
                return 'HEAD', sha
        return None, ref

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
        logger.info('Start aggregation of %s', self.cwd)
        target_dir = self.cwd

        with working_directory_keeper:
            is_new = not os.path.exists(target_dir)
            if is_new:
                self.log_call(['git', 'init', target_dir])

            os.chdir(target_dir)
            self._switch_to_branch(self.target['branch'])
            for r in self.remotes:
                self._set_remote(**r)
            self.log_call(['git', 'fetch',  '--all'])
            merges = self.merges
            if not is_new:
                # reset to the first merge
                origin = merges[0]
                merges = merges[1:]
                self._reset_to(**origin)
            for merge in merges:
                self._merge(**merge)
            self._execute_shell_command_after()
        logger.info('End aggregation of %s', self.cwd)

    def push(self):
        with working_directory_keeper:
            os.chdir(self.cwd)
            self.log_call(
                ['git', 'push', '-f', self.target['remote']])

    def _reset_to(self, remote, ref):
        logger.info('Reset branch to %s %s', remote, ref)
        rtype, sha = self.query_remote_ref(remote, ref)
        if rtype is None and not ishex(ref):
            raise GitAggregatorException(
                'Could not reset %s to %s. No commit found for %s '
                % (remote, ref, ref))
        self.log_call(['git', 'reset', '--hard', sha],
                      log_level=logging.DEBUG)

    def _switch_to_branch(self, branch_name):
        # check if the branch already exists
        logger.info("Switch to branch %s", branch_name)
        self.log_call(['git', 'checkout', '-B', branch_name],
                      log_level=logging.DEBUG)

    def _execute_shell_command_after(self):
        logger.info('Execute shell after commands')
        for cmd in self.shell_command_after:
            self.log_call(cmd.split(' '))

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
