# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Parts of the code comes from ANYBOX
# https://github.com/anybox/anybox.recipe.odoo
from __future__ import unicode_literals
import os
import logging
import re
import subprocess

import requests

from .exception import DirtyException, GitAggregatorException
from ._compat import console_to_str

FETCH_DEFAULTS = ("depth", "shallow-since", "shallow-exclude")
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

    _git_version = None

    def __init__(self, cwd, remotes, merges, target,
                 shell_command_after=None, fetch_all=False, defaults=None,
                 force=False):
        """Initialize a git repository aggregator

        :param cwd: path to the directory where to initialize the repository
        :param remotes: list of remote linked to the repository. A remote is
        a dict {'name': '', 'url': ''}
        :param: merges list of merge to apply to build the aggregated
        repository. A merge is a dict {'remote': '', 'ref': ''}
        :param target:
        :param shell_command_after: an optional list of shell command to
        execute after the aggregation
        :param fetch_all:
            Can be an iterable (recommended: ``frozenset``) that yields names
            of remotes where all refs should be fetched, or ``True`` to do it
            for every configured remote.
        :param defaults:
            Collection of default parameters to be passed to git.
        :param bool force:
            When ``False``, it will stop if repo is dirty.
        """
        self.cwd = cwd
        self.remotes = remotes
        if fetch_all is True:
            self.fetch_all = frozenset(r["name"] for r in remotes)
        else:
            self.fetch_all = fetch_all or frozenset()
        self.merges = merges
        self.target = target
        self.shell_command_after = shell_command_after or []
        self.defaults = defaults or dict()
        self.force = force

    @property
    def git_version(self):
        cls = self.__class__
        version = cls._git_version
        if version is not None:
            return version

        return cls.init_git_version(
            console_to_str(subprocess.check_output(
                ['git', '--version'])))

    @classmethod
    def init_git_version(cls, v_str):
        r"""Parse git version string and store the resulting tuple on self.
        :returns: the parsed version tuple
        Only the first 3 digits are kept. This is good enough for the few
        version dependent cases we need, and coarse enough to avoid
        more complicated parsing.
        Some real-life examples::
          >>> GitRepo.init_git_version('git version 1.8.5.3')
          (1, 8, 5)
          >>> GitRepo.init_git_version('git version 1.7.2.5')
          (1, 7, 2)
        Seen on MacOSX (not on MacPorts)::
          >>> GitRepo.init_git_version('git version 1.8.5.2 (Apple Git-48)')
          (1, 8, 5)
        Seen on Windows (Tortoise Git)::
          >>> GitRepo.init_git_version('git version 1.8.4.msysgit.0')
          (1, 8, 4)
        A compiled version::
          >>> GitRepo.init_git_version('git version 2.0.3.2.g996b0fd')
          (2, 0, 3)
        Rewrapped by `hub <https://hub.github.com/>`_, it has two lines:
          >>> GitRepo.init_git_version('git version 1.7.9\nhub version 1.11.0')
          (1, 7, 9)
        This one does not exist, allowing us to prove that this method
        actually governs the :attr:`git_version` property
          >>> GitRepo.init_git_version('git version 0.0.666')
          (0, 0, 666)
          >>> GitRepo('', '').git_version
          (0, 0, 666)
        Expected exceptions::
          >>> try: GitRepo.init_git_version('invalid')
          ... except ValueError: pass
        After playing with it, we must reset it so that tests can run with
        the proper detected one, if needed::
          >>> GitRepo.init_git_version(None)
        """
        if v_str is None:
            cls._git_version = None
            return

        v_str = v_str.strip()
        try:
            version = cls._git_version = tuple(
                int(x) for x in v_str.split()[2].split('.')[:3])
        except Exception:
            raise ValueError("Could not parse git version output %r. Please "
                             "report this" % v_str)
        return version

    def query_remote_ref(self, remote, ref):
        """Query remote repo about given ref.
        :return: ``('tag', sha)`` if ref is a tag in remote
                 ``('branch', sha)`` if ref is branch (aka "head") in remote
                 ``(None, ref)`` if ref does not exist in remote. This happens
                 notably if ref if a commit sha (they can't be queried)
        """
        out = self.log_call(['git', 'ls-remote', remote, ref],
                            cwd=self.cwd if os.path.exists(self.cwd) else None,
                            callwith=subprocess.check_output).strip()
        for sha, fullref in (line.split() for line in out.splitlines()):
            if fullref == 'refs/heads/' + ref:
                return 'branch', sha
            elif fullref == 'refs/tags/' + ref:
                return 'tag', sha
            elif fullref == ref and ref == 'HEAD':
                return 'HEAD', sha
        return None, ref

    def log_call(self, cmd, callwith=subprocess.check_call,
                 log_level=logging.DEBUG, **kw):
        """Wrap a subprocess call with logging
        :param meth: the calling method to use.
        """
        logger.log(log_level, "%s> call %r", self.cwd, cmd)
        try:
            ret = callwith(cmd, **kw)
        except Exception:
            logger.error("%s> error calling %r", self.cwd, cmd)
            raise
        if callwith == subprocess.check_output:
            ret = console_to_str(ret)
        return ret

    def aggregate(self):
        """ Aggregate all merges into the target branch
        If the target_dir doesn't exist, create an empty git repo otherwise
        clean it, add all remotes , and merge all merges.
        """
        logger.info('Start aggregation of %s', self.cwd)
        target_dir = self.cwd

        is_new = not os.path.exists(target_dir)
        if is_new:
            cloned = self.init_repository(target_dir)

        self._switch_to_branch(self.target['branch'])
        for r in self.remotes:
            self._set_remote(**r)
        self.fetch()
        merges = self.merges
        if not is_new or cloned:
            # reset to the first merge
            origin = merges[0]
            merges = merges[1:]
            self._reset_to(origin["remote"], origin["ref"])
        for merge in merges:
            self._merge(merge)
        self._execute_shell_command_after()
        logger.info('End aggregation of %s', self.cwd)

    def init_repository(self, target_dir):
        """Inits the local repository

        If a remote is specified as a target, it will be cloned.
        If the target has an associated branch, and that branch exists in the
        remote repository, the clone will be limited to that branch.
        If there is not a valid specified target, an empty repository will be
        initialized.

        :return: True if the repository was cloned
                 False otherwise
        """
        repository = None
        for remote in self.remotes:
            if remote["name"] == self.target["remote"]:
                repository = remote["url"]
                break
        branch = self.target["branch"]
        # If no target is defined, init an empty repository
        if not repository:
            logger.info('Init empty git repository in %s', target_dir)
            self.log_call(['git', 'init', target_dir])
            return False
        # If a target is defined, use it as the base repository
        logger.info(
            'Cloning git repository %s in %s',
            repository,
            target_dir,
        )
        cmd = ('git', 'clone')
        if self.git_version >= (2, 17):
            # Git added support for partial clone in 2.17
            # https://git-scm.com/docs/partial-clone
            # Speeds up cloning by functioning without a complete copy of
            # repository
            cmd += ('--filter=blob:none',)
        # Try to clone target branch, if it exists
        rtype, _sha = self.query_remote_ref(repository, branch)
        if rtype in {'branch', 'tag'}:
            cmd += ('-b', branch)
        # Emtpy fetch options to use global default for 1st clone
        cmd += self._fetch_options({})
        cmd += (repository, target_dir)
        self.log_call(cmd)
        return True

    def fetch(self):
        basecmd = ("git", "fetch")
        logger.info("Fetching required remotes")
        for merge in self.merges:
            cmd = basecmd + self._fetch_options(merge) + (merge["remote"],)
            if merge["remote"] not in self.fetch_all:
                cmd += (merge["ref"],)
            self.log_call(cmd, cwd=self.cwd)

    def push(self):
        remote = self.target['remote']
        branch = self.target['branch']
        if remote is None:
            raise GitAggregatorException(
                "Cannot push %s, no target remote configured" % branch
            )
        logger.info("Push %s to %s", branch, remote)
        self.log_call(['git', 'push', '-f', remote, branch], cwd=self.cwd)

    def _check_status(self):
        """Check repo status and except if dirty."""
        logger.info('Checking repo status')
        status = self.log_call(
            ['git', 'status', '--porcelain'],
            callwith=subprocess.check_output,
            cwd=self.cwd,
        )
        if status:
            raise DirtyException(status)

    def _fetch_options(self, merge):
        """Get the fetch options from the given merge dict."""
        cmd = tuple()
        for option in FETCH_DEFAULTS:
            value = merge.get(option, self.defaults.get(option))
            if value:
                cmd += ("--%s" % option, str(value))
        return cmd

    def _reset_to(self, remote, ref):
        if not self.force:
            self._check_status()
        logger.info('Reset branch to %s %s', remote, ref)
        rtype, sha = self.query_remote_ref(remote, ref)
        if rtype is None and not ishex(ref):
            raise GitAggregatorException(
                'Could not reset %s to %s. No commit found for %s '
                % (remote, ref, ref))
        cmd = ['git', 'reset', '--hard', sha]
        if logger.getEffectiveLevel() != logging.DEBUG:
            cmd.insert(2, '--quiet')
        self.log_call(cmd, cwd=self.cwd)
        self.log_call(['git', 'clean', '-ffd'], cwd=self.cwd)

    def _switch_to_branch(self, branch_name):
        # check if the branch already exists
        logger.info("Switch to branch %s", branch_name)
        self.log_call(['git', 'checkout', '-B', branch_name], cwd=self.cwd)

    def _execute_shell_command_after(self):
        logger.info('Execute shell after commands')
        for cmd in self.shell_command_after:
            self.log_call(cmd, shell=True, cwd=self.cwd)

    def _merge(self, merge):
        logger.info("Pull %s, %s", merge["remote"], merge["ref"])
        cmd = ("git", "pull", "--ff", "--no-rebase")
        if self.git_version >= (1, 7, 10):
            # --edit and --no-edit appear with Git 1.7.10
            # see Documentation/RelNotes/1.7.10.txt of Git
            # (https://git.kernel.org/cgit/git/git.git/tree)
            cmd += ('--no-edit',)
        if logger.getEffectiveLevel() != logging.DEBUG:
            cmd += ('--quiet',)
        cmd += self._fetch_options(merge) + (merge["remote"], merge["ref"])
        self.log_call(cmd, cwd=self.cwd)

    def _get_remotes(self):
        lines = self.log_call(
            ['git', 'remote', '-v'],
            callwith=subprocess.check_output,
            cwd=self.cwd).splitlines()
        remotes = {}
        for line in lines:
            name, url = line.split('\t')
            url = url.split(' ')[0]
            v = remotes.setdefault(name, url)
            if v != url:
                raise NotImplementedError(
                    'Different urls gor push and fetch for remote %s\n'
                    '%s != %s' % (name, url, v)
                )
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
            self.log_call(['git', 'remote', 'add', name, url], cwd=self.cwd)
        else:
            logger.info('Updating remote %s <%s> -> <%s>',
                        name, exising_url, url)
            self.log_call(['git', 'remote', 'rm', name], cwd=self.cwd)
            self.log_call(['git', 'remote', 'add', name, url], cwd=self.cwd)

    def _github_api_get(self, path):
        url = 'https://api.github.com' + path
        token = os.environ.get('GITHUB_TOKEN')
        headers = None
        if token:
            headers = {'Authorization': 'token %s' % token}
        return requests.get(url, headers=headers)

    def collect_prs_info(self):
        """Collect all pending merge PRs info.

        :returns: mapping of PRs by state
        """
        REPO_RE = re.compile(
            '^(https://github.com/|git@github.com:)'
            '(?P<owner>.*?)/(?P<repo>.*?)(.git)?$')
        PULL_RE = re.compile(
            '^(refs/)?pull/(?P<pr>[0-9]+)/head$')
        remotes = {r['name']: r['url'] for r in self.remotes}
        all_prs = {}
        for merge in self.merges:
            remote = merge['remote']
            ref = merge['ref']
            repo_url = remotes[remote]
            repo_mo = REPO_RE.match(repo_url)
            if not repo_mo:
                logger.debug('%s is not a github repo', repo_url)
                continue
            pull_mo = PULL_RE.match(ref)
            if not pull_mo:
                logger.debug('%s is not a github pull reqeust', ref)
                continue
            pr_info = {
                'owner': repo_mo.group('owner'),
                'repo': repo_mo.group('repo'),
                'pr': pull_mo.group('pr'),
            }
            pr_info['path'] = '{owner}/{repo}/pulls/{pr}'.format(**pr_info)
            pr_info['shortcut'] = '{owner}/{repo}#{pr}'.format(**pr_info)
            r = self._github_api_get('/repos/{path}'.format(**pr_info))
            if r.status_code != 200:
                logger.warning(
                    'Could not get status of {path}. '
                    'Reason: {r.status_code} {r.reason}'.format(r=r, **pr_info)
                )
                continue
            rj = r.json()
            pr_info['raw'] = rj
            pr_info['state'] = rj.get('state')
            pr_info['url'] = rj.get('html_url')
            pr_info['labels'] = ", ".join(
                label['name'] for label in rj.get('labels')
            )
            pr_info['merged'] = (
                not rj.get('merged') and 'not ' or ''
            ) + 'merged'
            all_prs.setdefault(pr_info['state'], []).append(pr_info)
        return all_prs

    def show_closed_prs(self):
        """Log only closed PRs."""
        all_prs = self.collect_prs_info()
        for pr_info in all_prs.get('closed', []):
            logger.info(
                '{url} in state {state} ({merged}; labels: {labels})'
                .format(**pr_info)
            )

    def show_all_prs(self):
        """Log all PRs grouped by state."""
        for __, prs in self.collect_prs_info().items():
            for pr_info in prs:
                logger.info(
                    '{url} in state {state} ({merged})'.format(**pr_info)
                )
