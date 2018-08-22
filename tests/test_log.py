# -*- coding: utf-8 -*-
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)

import logging
import threading
import unittest

from git_aggregator import main
from git_aggregator.utils import ThreadNameKeeper

logger = logging.getLogger(__name__)


def reset_logger():
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)


class TestLog(unittest.TestCase):

    def setUp(self):
        """ Setup """
        super(TestLog, self).setUp()
        reset_logger()

    def test_info(self):
        """ Test log.LogFormatter. """
        main.setup_logger(logger, level=logging.INFO)
        # self._suite = unittest.TestLoader().loadTestsFromName(
        #     'tests.test_repo.TestRepo.test_multithreading')
        # unittest.TextTestRunner(verbosity=0).run(self._suite)
        logger.debug('This message SHOULD NOT be visible.')
        logger.info('Message from MainThread.')
        with ThreadNameKeeper():
            name = threading.current_thread().name = 'repo_name'
            logger.info('Message from %s.', name)
        logger.info('Hello again from MainThread.')

    def test_debug(self):
        """ Test log.DebugLogFormatter. """
        main.setup_logger(logger, level=logging.DEBUG)
        logger.debug('This message SHOULD be visible.')
        logger.info('Message from MainThread.')
        with ThreadNameKeeper():
            name = threading.current_thread().name = 'repo_name'
            logger.info('Message from %s.', name)
        logger.info('Hello again from MainThread.')

    def test_colors(self):
        """ Test log.LEVEL_COLORS. """
        main.setup_logger(logger, level=logging.DEBUG)
        logger.debug('Color: Fore.BLUE')
        logger.info('Color: Fore.GREEN')
        logger.warning('Color: Fore.YELLOW')
        logger.error('Color: Fore.RED')
        logger.critical('Color: Fore.RED')
