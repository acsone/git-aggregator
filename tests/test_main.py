# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)

import argparse
import queue
import threading
import unittest

from git_aggregator import exception, main


class FakeRepo:
    """Minimal Repo stand-in whose aggregation always fails."""

    cwd = "/tmp/some/dirty-repo"

    def aggregate(self):
        raise exception.DirtyException("?? untracked-dir/")


class TestAggregateRepo(unittest.TestCase):
    """The failing repository must be identifiable from the output."""

    def setUp(self):
        self.args = argparse.Namespace(
            command="aggregate", dirmatch=None, do_push=False
        )
        self.sem = threading.Semaphore(1)
        self.err_queue = queue.Queue()

    def test_error_keeps_repo_path(self):
        """The queued error carries the path of the failing repository."""
        main.aggregate_repo(FakeRepo(), self.args, self.sem, self.err_queue)
        cwd, (exc_type, exc_obj, _exc_trace) = self.err_queue.get_nowait()
        self.assertEqual(cwd, FakeRepo.cwd)
        self.assertIs(exc_type, exception.DirtyException)
        self.assertEqual(str(exc_obj), "?? untracked-dir/")

    def test_error_is_logged_with_repo_path(self):
        """The failure is logged together with its repository path."""
        with self.assertLogs(main.logger, level="ERROR") as logs:
            main.aggregate_repo(
                FakeRepo(), self.args, self.sem, self.err_queue
            )
        self.assertIn(FakeRepo.cwd, "\n".join(logs.output))
