# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)

import logging
import os
import sys
import threading
import traceback
try:
    from Queue import Queue, Empty as EmptyQueue
except ImportError:
    from queue import Queue, Empty as EmptyQueue

import argparse
import argcomplete
import fnmatch

from .utils import ThreadNameKeeper
from .log import DebugLogFormatter
from .log import LogFormatter
from .config import load_config
from .repo import Repo


logger = logging.getLogger(__name__)

_LOG_LEVEL_STRINGS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']


def _log_level_string_to_int(log_level_string):
    if log_level_string not in _LOG_LEVEL_STRINGS:
        message = 'invalid choice: {0} (choose from {1})'.format(
            log_level_string, _LOG_LEVEL_STRINGS)
        raise argparse.ArgumentTypeError(message)

    log_level_int = getattr(logging, log_level_string, logging.INFO)
    # check the logging log_level_choices have not changed from our expected
    # values
    assert isinstance(log_level_int, int)

    return log_level_int


def setup_logger(log=None, level=logging.INFO):
    """Setup logging for CLI use.
    :param log: instance of logger
    :type log: :py:class:`Logger`
    """
    if not log:
        log = logging.getLogger()
    if not log.handlers:
        channel = logging.StreamHandler()
        if level == logging.DEBUG:
            channel.setFormatter(DebugLogFormatter())
        else:
            channel.setFormatter(LogFormatter())

        log.setLevel(level)
        log.addHandler(channel)


def get_parser():
    """Return :py:class:`argparse.ArgumentParser` instance for CLI."""

    main_parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)

    main_parser.add_argument(
        '-c', '--config',
        dest='config',
        type=str,
        nargs='?',
        help='Pull the latest repositories from config(s)'
    ).completer = argcomplete.completers.FilesCompleter(
        allowednames=('.yaml', '.yml', '.json'), directories=False
    )

    main_parser.add_argument(
        '-p', '--push',
        dest='do_push',
        action='store_true', default=False,
        help='Push result to target',
    )

    main_parser.add_argument(
        '-d', '--dirmatch',
        dest='dirmatch',
        type=str,
        nargs='?',
        help='Pull only from the directories. Accepts fnmatch(1)'
             'by commands'
    )
    main_parser.add_argument(
        '--log-level',
        default='INFO',
        dest='log_level',
        type=_log_level_string_to_int,
        nargs='?',
        help='Set the logging output level. {0}'.format(_LOG_LEVEL_STRINGS))

    main_parser.add_argument(
        '-e', '--expand-env',
        dest='expand_env',
        default=False,
        action='store_true',
        help='Expand environment variables in configuration file',
    )
    main_parser.add_argument(
        '-f', '--force',
        dest='force',
        default=False,
        action='store_true',
        help='Force cleanup and aggregation on dirty repositories.',
    )

    main_parser.add_argument(
        '-j', '--jobs',
        dest='jobs',
        default=1,
        type=int,
        help='Amount of processes to use when aggregating repos. '
             'This is useful when there are a lot of large repos. '
             'Set `1` or less to disable multiprocessing (default).',
    )

    main_parser.add_argument(
        'command',
        nargs='?',
        default='aggregate',
        help='aggregate (default): run the aggregation process.\n'
             'show-closed-prs: show pull requests that are not open anymore\n'
             '                 such pull requests are indentified as having\n'
             '                 a github.com remote and a\n'
             '                 refs/pull/NNN/head ref in the merge section.')

    return main_parser


def main():
    """Main CLI application."""

    parser = get_parser()

    argcomplete.autocomplete(parser, always_complete_options=False)

    args = parser.parse_args()

    setup_logger(
        level=args.log_level
    )

    try:
        if args.config and \
                args.command in ('aggregate', 'show-closed-prs'):
            run(args)
        else:
            parser.print_help()
    except KeyboardInterrupt:
        pass


def match_dir(cwd, dirmatch=None):
    if not dirmatch:
        return True
    return (fnmatch.fnmatch(cwd, dirmatch) or
            fnmatch.fnmatch(os.path.relpath(cwd), dirmatch) or
            os.path.relpath(cwd) == os.path.relpath(dirmatch))


def load_aggregate(args):
    """Load YAML and JSON configs and begin creating / updating , aggregating
    and pushing the repos (deprecated in favor or run())"""
    repos = load_config(args.config, args.expand_env)
    dirmatch = args.dirmatch
    for repo_dict in repos:
        r = Repo(**repo_dict)
        logger.debug('%s' % r)
        if not match_dir(r.cwd, dirmatch):
            logger.info("Skip %s", r.cwd)
            continue
        r.aggregate()
        if args.do_push:
            r.push()


def aggregate_repo(repo, args, sem, err_queue):
    """Aggregate one repo according to the args.

    Args:
         repo (Repo): The repository to aggregate.
         args (argparse.Namespace): CLI arguments.
    """
    try:
        logger.debug('%s' % repo)
        dirmatch = args.dirmatch
        if not match_dir(repo.cwd, dirmatch):
            logger.info("Skip %s", repo.cwd)
            return
        if args.command == 'aggregate':
            repo.aggregate()
            if args.do_push:
                repo.push()
        elif args.command == 'show-closed-prs':
            repo.show_closed_prs()
    except Exception:
        err_queue.put_nowait(sys.exc_info())
    finally:
        sem.release()


def run(args):
    """Load YAML and JSON configs and run the command specified
    in args.command"""

    repos = load_config(args.config, args.expand_env, args.force)

    jobs = max(args.jobs, 1)
    threads = []
    sem = threading.Semaphore(jobs)
    err_queue = Queue()

    for repo_dict in repos:
        if not err_queue.empty():
            break

        sem.acquire()
        r = Repo(**repo_dict)
        tname = os.path.basename(repo_dict['cwd'])

        if jobs > 1:
            t = threading.Thread(
                target=aggregate_repo, args=(r, args, sem, err_queue))
            t.daemon = True
            t.name = tname
            threads.append(t)
            t.start()
        else:
            with ThreadNameKeeper():
                threading.current_thread().name = tname
                aggregate_repo(r, args, sem, err_queue)

    for t in threads:
        t.join()

    if not err_queue.empty():
        while True:
            try:
                exc_type, exc_obj, exc_trace = err_queue.get_nowait()
            except EmptyQueue:
                break
            traceback.print_exception(exc_type, exc_obj, exc_trace)
        sys.exit(1)
