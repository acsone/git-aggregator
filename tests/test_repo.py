# © 2015 ACSONE SA/NV
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Parts of the code comes from ANYBOX
# https://github.com/anybox/anybox.recipe.odoo
import argparse
import os
import shutil
import subprocess
import unittest

try:
    # Py 2
    from urllib import pathname2url

    from urlparse import urljoin
except ImportError:
    # PY  3
    from urllib.parse import urljoin
    from urllib.request import pathname2url
import logging
from tempfile import mkdtemp
from textwrap import dedent

from git_aggregator import exception, main
from git_aggregator.patch import Patches
from git_aggregator.repo import Repo
from git_aggregator.utils import (
    WorkingDirectoryKeeper,
    working_directory_keeper,
)


def git_get_last_rev(repo_dir):
    """Return full hash of parent nodes.
    """
    with working_directory_keeper:
        os.chdir(repo_dir)
        p = subprocess.check_output(['git', 'rev-parse', '--verify', 'HEAD'])
        return p.strip()


def git_write_commit(repo_dir, filepath, contents, msg="Unit test commit"):
    """Write specified file with contents, commit and return commit SHA.
    :param filepath: path of file to write to, relative to repository
    """
    with WorkingDirectoryKeeper():  # independent from the main instance
        os.chdir(repo_dir)
        # needs to be done just once, but I prefer to do it a few useless
        # times than to forget it, since it's easy to turn into a sporadic
        # test breakage on continuous integration builds.

        with open(filepath, 'w') as f:
            f.write(contents)
        subprocess.call(['git', 'add', filepath])
        # Ignore local hooks with '-n'
        subprocess.call(['git', 'commit', '-n', '-m', msg])
        return subprocess.check_output(
            ['git', 'rev-parse', '--verify', 'HEAD']).strip()


def path2url(path):
    return urljoin(
        'file:', pathname2url(os.path.abspath(path)))


class TestRepo(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        main.setup_logger(level=logging.DEBUG)
        super().setUpClass()

    def setUp(self):
        """ Setup
        * remote1
             commit 1 -> fork after -> remote 2
             tag1
             commit 2
             annotated tag2
        *remote2 (clone remote 1)
             commit 1
             commit 3
             branch b2
        """
        super().setUp()
        sandbox = self.sandbox = mkdtemp('test_repo')
        with working_directory_keeper:
            os.chdir(sandbox)
            subprocess.call(['git', 'init', 'remote1'])
            self.cwd = os.path.join(sandbox, 'dst')
            self.remote1 = os.path.join(sandbox, 'remote1')
            self.url_remote1 = path2url(self.remote1)
            self.commit_1_sha = git_write_commit(
                self.remote1, 'tracked', "first", msg="initial commit")
            self.remote2 = os.path.join(sandbox, 'remote2')
            subprocess.call(['git', 'clone', self.url_remote1, 'remote2'])
            self.url_remote2 = path2url(self.remote2)
            subprocess.check_call(['git', 'tag', 'tag1'], cwd=self.remote1)
            self.commit_2_sha = git_write_commit(
                self.remote1, 'tracked', "last", msg="last commit")
            subprocess.check_call(['git', 'tag', '-am', 'foo', 'tag2'],
                                  cwd=self.remote1)
            self.commit_3_sha = git_write_commit(
                self.remote2, 'tracked2', "remote2", msg="new commit")
            subprocess.check_call(['git', 'checkout', '-b', 'b2'],
                                  cwd=self.remote2)
        self.maxDiff = None

    def tearDown(self):
        shutil.rmtree(self.sandbox)

    def test_minimal(self):
        remotes = [{
            'name': 'r1',
            'url': self.url_remote1
        }]
        merges = [{
            'remote': 'r1',
            'ref': 'tag1'
        }]
        target = {
            'remote': 'r1',
            'branch': 'agg1'
        }
        repo = Repo(self.cwd, remotes, merges, target)
        repo.aggregate()
        last_rev = git_get_last_rev(self.cwd)
        self.assertEqual(last_rev, self.commit_1_sha)

    def _make_patches(self, count):
        """Commit ``count`` changes on top of remote1 master in a scratch
        clone and export them with git format-patch.
        Return the directory holding the patch files."""
        scratch = os.path.join(self.sandbox, 'scratch')
        patch_dir = os.path.join(self.sandbox, 'patches')
        subprocess.check_call(['git', 'clone', self.url_remote1, scratch])
        for i in range(1, count + 1):
            git_write_commit(
                scratch, 'patched', f"patch {i}", msg=f"patch commit {i}")
        subprocess.check_call(
            ['git', 'format-patch', f'-{count}', '-o', patch_dir],
            cwd=scratch)
        return patch_dir

    def _aggregate_with_patches(self, patch_path):
        remotes = [{
            'name': 'r1',
            'url': self.url_remote1
        }]
        merges = [{
            'remote': 'r1',
            'ref': 'master'
        }]
        target = {
            'remote': 'r1',
            'branch': 'agg'
        }
        patches = Patches.prepare_patches(patch_path, self.cwd)
        repo = Repo(self.cwd, remotes, merges, target, patches=patches)
        repo.aggregate()

    def _git_log_subjects(self, count):
        return subprocess.check_output(
            ['git', 'log', f'-{count}', '--format=%s'],
            cwd=self.cwd, universal_newlines=True).splitlines()

    def test_patch_file(self):
        patch_dir = self._make_patches(1)
        patch_file = os.path.join(patch_dir, os.listdir(patch_dir)[0])
        self._aggregate_with_patches(patch_file)
        self.assertEqual(
            self._git_log_subjects(2), ["patch commit 1", "last commit"])
        with open(os.path.join(self.cwd, 'patched')) as f:
            self.assertEqual(f.read(), "patch 1")

    def test_patch_dir(self):
        patch_dir = self._make_patches(2)
        self._aggregate_with_patches(patch_dir)
        self.assertEqual(
            self._git_log_subjects(3),
            ["patch commit 2", "patch commit 1", "last commit"])
        with open(os.path.join(self.cwd, 'patched')) as f:
            self.assertEqual(f.read(), "patch 2")

    def test_patch_url(self):
        patch_dir = self._make_patches(1)
        patch_file = os.path.join(patch_dir, os.listdir(patch_dir)[0])
        self._aggregate_with_patches(path2url(patch_file))
        self.assertEqual(
            self._git_log_subjects(2), ["patch commit 1", "last commit"])

    def test_patch_missing_file(self):
        with self.assertRaises(exception.ConfigException):
            Patches.prepare_patches(
                os.path.join(self.sandbox, 'missing.patch'), self.cwd)

    def test_patch_unreachable_url(self):
        url = path2url(os.path.join(self.sandbox, 'missing.patch'))
        with self.assertRaises(subprocess.CalledProcessError):
            self._aggregate_with_patches(url)

    def test_patch_empty(self):
        patch_file = os.path.join(self.sandbox, 'empty.patch')
        open(patch_file, 'w').close()
        with self.assertRaises(exception.GitAggregatorException):
            self._aggregate_with_patches(patch_file)

    def test_empty_dir(self):
        # ensure git clone in empty directory works
        remotes = [{
            'name': 'r1',
            'url': self.url_remote1
        }]
        merges = [{
            'remote': 'r1',
            'ref': 'tag1'
        }]
        target = {
            'remote': 'r1',
            'branch': 'agg1'
        }
        # self.cwd should not exist yet
        self.assertFalse(os.path.exists(self.cwd))
        os.mkdir(self.cwd)
        repo = Repo(self.cwd, remotes, merges, target)
        repo.aggregate()
        last_rev = git_get_last_rev(self.cwd)
        self.assertEqual(last_rev, self.commit_1_sha)

    def test_annotated_tag(self):
        remotes = [{
            'name': 'r1',
            'url': self.url_remote1
        }]
        merges = [{
            'remote': 'r1',
            'ref': 'tag2'
        }]
        target = {
            'remote': 'r1',
            'branch': 'agg1'
        }
        repo = Repo(self.cwd, remotes, merges, target)
        repo.aggregate()
        last_rev = git_get_last_rev(self.cwd)
        self.assertEqual(last_rev, self.commit_2_sha)

    def test_simple_merge(self):
        remotes = [{
            'name': 'r1',
            'url': self.url_remote1
        }, {
            'name': 'r2',
            'url': self.url_remote2
        }]
        merges = [{
            'remote': 'r1',
            'ref': 'tag1'
        }, {
            'remote': 'r2',
            'ref': self.commit_3_sha
        }]
        target = {
            'remote': 'r1',
            'branch': 'agg'
        }
        repo = Repo(self.cwd, remotes, merges, target, fetch_all=True)
        repo.aggregate()
        last_rev = git_get_last_rev(self.cwd)
        self.assertEqual(last_rev, self.commit_3_sha)
        # push
        repo.push()
        rtype, sha = repo.query_remote_ref('r1', 'agg')
        self.assertEqual(rtype, 'branch')
        self.assertTrue(sha)

    def test_push_missing_remote(self):
        remotes = [{
            'name': 'r1',
            'url': self.url_remote1
        }, {
            'name': 'r2',
            'url': self.url_remote2
        }]
        merges = [{
            'remote': 'r1',
            'ref': 'tag1'
        }, {
            'remote': 'r2',
            'ref': self.commit_3_sha
        }]
        target = {
            'remote': None,
            'branch': 'agg'
        }
        repo = Repo(self.cwd, remotes, merges, target, fetch_all=True)
        repo.aggregate()
        with self.assertRaises(exception.GitAggregatorException) as ex:
            repo.push()
        self.assertEqual(
            ex.exception.args[0],
            "Cannot push agg, no target remote configured"
        )

    def test_update_aggregate(self):
        # in this test
        # * we'll aggregate a first time r1 master with r2
        #   at commit 3
        # * create a new commit on r1
        # aggregate again
        # the last change of r1 must be in the aggregated branch
        remotes = [{
            'name': 'r1',
            'url': self.url_remote1
        }, {
            'name': 'r2',
            'url': self.url_remote2
        }]
        merges = [{
            'remote': 'r1',
            'ref': 'master'
        }, {
            'remote': 'r2',
            'ref': self.commit_3_sha
        }]
        target = {
            'remote': 'r1',
            'branch': 'agg'
        }
        repo = Repo(self.cwd, remotes, merges, target, fetch_all=True)
        repo.aggregate()
        self.assertTrue(os.path.isfile(os.path.join(self.cwd, 'tracked')))
        self.assertTrue(os.path.isfile(os.path.join(self.cwd, 'tracked2')))
        git_write_commit(
            self.remote1, 'tracked_new', "last", msg="new file on remote1")
        repo.aggregate()
        self.assertTrue(os.path.isfile(os.path.join(self.cwd, 'tracked_new')))

    def test_update_aggregate_2(self):
        # in this test
        # * we'll aggregate a first time r1 commit1 with r2
        #   at commit 3
        # * create a new commit on r1
        # aggregate again
        # the last change of r1 must not be in the aggregated branch
        remotes = [{
            'name': 'r1',
            'url': self.url_remote1
        }, {
            'name': 'r2',
            'url': self.url_remote2
        }]
        merges = [{
            'remote': 'r1',
            'ref': self.commit_1_sha
        }, {
            'remote': 'r2',
            'ref': self.commit_3_sha
        }]
        target = {
            'remote': 'r1',
            'branch': 'agg'
        }
        repo = Repo(self.cwd, remotes, merges, target, fetch_all=True)
        repo.aggregate()
        self.assertTrue(os.path.isfile(os.path.join(self.cwd, 'tracked')))
        self.assertTrue(os.path.isfile(os.path.join(self.cwd, 'tracked2')))
        git_write_commit(
            self.remote1, 'tracked_new', "last", msg="new file on remote1")
        repo.aggregate()
        self.assertFalse(os.path.isfile(os.path.join(self.cwd, 'tracked_new')))

    def test_depth_1(self):
        """Ensure a simple shallow clone with 1 commit works."""
        remotes = [{
            'name': 'shallow',
            'url': self.url_remote1
        }]
        merges = [{
            'remote': 'shallow',
            "ref": "master",
        }]
        target = {
            'remote': 'shallow',
            'branch': 'master'
        }
        defaults = {
            "depth": 1,
        }
        repo = Repo(self.cwd, remotes, merges, target, defaults=defaults)
        repo.aggregate()
        self.assertTrue(os.path.isfile(os.path.join(self.cwd, 'tracked')))

        with working_directory_keeper:
            os.chdir(self.cwd)
            log_shallow = subprocess.check_output(
                ("git", "rev-list", "shallow/master"))
        # Shallow fetch: just 1 commmit
        self.assertEqual(len(log_shallow.splitlines()), 1)

    def test_force(self):
        """Ensure --force works fine."""
        remotes = [{
            'name': 'r1',
            'url': self.url_remote1
        }]
        merges = [{
            'remote': 'r1',
            'ref': 'tag1'
        }]
        target = {
            'remote': 'r1',
            'branch': 'agg1'
        }
        # Aggregate 1st time
        repo_noforce = Repo(self.cwd, remotes, merges, target)
        repo_noforce.aggregate()
        # Create a dummy file to set the repo dirty
        dummy_file = os.path.join(self.cwd, "dummy")
        with open(dummy_file, "a"):
            pass
        # Aggregate 2nd time, dirty, which should fail
        with self.assertRaises(exception.DirtyException):
            repo_noforce.aggregate()
        # Aggregate 3rd time, forcing, so it should work and remove that file
        repo_force = Repo(self.cwd, remotes, merges, target, force=True)
        repo_force.aggregate()
        self.assertFalse(os.path.exists(dummy_file))

    def test_depth(self):
        """Ensure `depth` is used correctly."""
        remotes = [{
            'name': 'r1',
            'url': self.url_remote1
        }, {
            'name': 'r2',
            'url': self.url_remote2
        }]
        merges = [{
            'remote': 'r1',
            "ref": "master",
        }, {
            "remote": "r2",
            'ref': "b2",
        }]
        target = {
            'remote': 'r1',
            'branch': 'agg'
        }
        defaults = {
            "depth": 2,
        }
        repo = Repo(self.cwd, remotes, merges, target, defaults=defaults)
        repo.aggregate()
        self.assertTrue(os.path.isfile(os.path.join(self.cwd, 'tracked')))
        self.assertTrue(os.path.isfile(os.path.join(self.cwd, 'tracked2')))

        with working_directory_keeper:
            os.chdir(self.cwd)
            log_r1 = subprocess.check_output(
                ("git", "rev-list", "r1/master"))
            log_r2 = subprocess.check_output(
                ("git", "rev-list", "r2/b2"))
        # Shallow fetch: just 1 commmit
        self.assertEqual(len(log_r1.splitlines()), 2)
        # Full fetch: all 3 commits
        self.assertEqual(len(log_r2.splitlines()), 2)

    def test_multithreading(self):
        """Clone two repos and do a merge in a third one, simultaneously."""
        config_yaml = os.path.join(self.sandbox, 'config.yaml')
        with open(config_yaml, 'w') as f:
            f.write(dedent("""
            ./repo1:
                remotes:
                    r1: %(r1_remote_url)s
                merges:
                    - r1 tag1
                target: r1 agg
            ./repo2:
                remotes:
                    r2: %(r2_remote_url)s
                merges:
                    - r2 b2
                target: r2 agg
            ./repo3:
                remotes:
                    r1: %(r1_remote_url)s
                    r2: %(r2_remote_url)s
                merges:
                    - r1 tag1
                    - r2 b2
                target: r1 agg
            """ % {
                'r1_remote_url': self.url_remote1,
                'r2_remote_url': self.url_remote2,
            }))

        args = argparse.Namespace(
            command='aggregate',
            config=config_yaml,
            jobs=3,
            dirmatch=None,
            do_push=False,
            expand_env=False,
            env_file=None,
            force=False,
        )

        with working_directory_keeper:
            os.chdir(self.sandbox)
            main.run(args)

        repo1_dir = os.path.join(self.sandbox, 'repo1')
        repo2_dir = os.path.join(self.sandbox, 'repo2')
        repo3_dir = os.path.join(self.sandbox, 'repo3')

        self.assertTrue(os.path.isfile(os.path.join(repo1_dir, 'tracked')))
        self.assertFalse(os.path.isfile(os.path.join(repo1_dir, 'tracked2')))

        self.assertTrue(os.path.isfile(os.path.join(repo2_dir, 'tracked')))
        self.assertTrue(os.path.isfile(os.path.join(repo2_dir, 'tracked2')))

        self.assertTrue(os.path.isfile(os.path.join(repo3_dir, 'tracked')))
        self.assertTrue(os.path.isfile(os.path.join(repo3_dir, 'tracked2')))
