# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# © ANYBOX https://github.com/anybox/anybox.recipe.odoo
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
import os
import threading
import logging
logger = logging.getLogger(__name__)


class WorkingDirectoryKeeper(object):  # DEPRECATED
    """A context manager to get back the working directory as it was before.
    If you want to stack working directory keepers, you need a new instance
    for each stage.
    """

    active = False

    def __enter__(self):
        if self.active:
            raise RuntimeError("Already in a working directory keeper !")
        self.wd = os.getcwd()
        self.active = True

    def __exit__(self, *exc_args):
        os.chdir(self.wd)
        self.active = False


working_directory_keeper = WorkingDirectoryKeeper()


class ThreadNameKeeper(object):
    """A contect manager to get back the thread name as it was before. It
    is meant to be used when modifying the 'MainThread' tread.
    """

    def __enter__(self):
        self._name = threading.current_thread().name

    def __exit__(self, *exc_args):
        threading.current_thread().name = self._name
