# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
import os
import tempfile
import unittest
from textwrap import dedent

import yaml

from git_aggregator import config
from git_aggregator.exception import ConfigException
from git_aggregator._compat import PY2


class TestConfig(unittest.TestCase):

    def _parse_config(self, config_str):
        return yaml.load(config_str, Loader=yaml.SafeLoader)

    def test_load(self):
        config_yaml = """
/product_attribute:
    remotes:
        oca: https://github.com/OCA/product-attribute.git
        acsone: git+ssh://git@github.com/acsone/product-attribute.git
    merges:
        - oca 8.0
        - oca refs/pull/105/head
        - oca refs/pull/106/head
    target: acsone aggregated_branch_name
        """
        repos = config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(len(repos), 1)
        # remotes are configured as dict therefore the order is not preserved
        # when parsed
        remotes = repos[0]['remotes']
        repos[0]['remotes'] = []
        self.assertDictEqual(
            repos[0],
            {'cwd': '/product_attribute',
             'fetch_all': False,
             'force': False,
             'defaults': {},
             'merges': [{'ref': '8.0', 'remote': 'oca'},
                        {'ref': 'refs/pull/105/head', 'remote': 'oca'},
                        {'ref': 'refs/pull/106/head', 'remote': 'oca'}],
             'remotes': [],
             'shell_command_after': [],
             'target': {'branch': 'aggregated_branch_name',
                        'remote': 'acsone'}})
        assertfn = self.assertItemsEqual if PY2 else self.assertCountEqual
        assertfn(
            remotes,
            [{'name': 'oca',
              'url': 'https://github.com/OCA/product-attribute.git'},
             {'name': 'acsone',
              'url':
              'git+ssh://git@github.com/acsone/product-attribute.git'}])

    def test_load_defaults(self):
        config_yaml = dedent("""
            /web:
                defaults:
                    depth: 1
                remotes:
                    oca: https://github.com/OCA/web.git
                    acsone: git+ssh://git@github.com/acsone/web.git
                merges:
                    -
                        remote: oca
                        ref: 8.0
                        depth: 1000
                    - oca refs/pull/105/head
                    -
                        remote: oca
                        ref: refs/pull/106/head
                target: acsone aggregated_branch_name
        """)
        repos = config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(len(repos), 1)
        # remotes are configured as dict therefore the order is not preserved
        # when parsed
        remotes = repos[0]['remotes']
        repos[0]['remotes'] = []
        self.assertDictEqual(
            repos[0],
            {'cwd': '/web',
             'fetch_all': False,
             'force': False,
             'defaults': {'depth': 1},
             'merges': [{'ref': '8.0', 'remote': 'oca', 'depth': 1000},
                        {'ref': 'refs/pull/105/head', 'remote': 'oca'},
                        {'ref': 'refs/pull/106/head', 'remote': 'oca'}],
             'remotes': [],
             'shell_command_after': [],
             'target': {'branch': 'aggregated_branch_name',
                        'remote': 'acsone'}})
        assertfn = self.assertItemsEqual if PY2 else self.assertCountEqual
        assertfn(
            remotes,
            [{'name': 'oca',
              'url': 'https://github.com/OCA/web.git'},
             {'name': 'acsone',
              'url':
              'git+ssh://git@github.com/acsone/web.git'}])

    def test_load_shell_command_after(self):
        """Shell command after are alway parser as a list
        """
        config_yaml = """
/product_attribute:
    remotes:
        oca: https://github.com/OCA/product-attribute.git
        acsone: git+ssh://git@github.com/acsone/product-attribute.git
    merges:
        - oca 8.0
    target: acsone aggregated_branch_name
    shell_command_after: ls
        """
        repos = config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(repos[0]['shell_command_after'], ['ls'])
        config_yaml = """
/product_attribute:
    remotes:
        oca: https://github.com/OCA/product-attribute.git
        acsone: git+ssh://git@github.com/acsone/product-attribute.git
    merges:
        - oca 8.0
    target: acsone aggregated_branch_name
    shell_command_after:
        - ls
        - echo
        """
        repos = config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(repos[0]['shell_command_after'], ['ls', 'echo'])

    def test_load_remotes_exception(self):
        config_yaml = """
/product_attribute:
    merges:
        - oca 8.0
    target: oca aggregated_branch
"""
        with self.assertRaises(ConfigException) as ex:
            config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(
            ex.exception.args[0],
            '/product_attribute: remotes is not defined.')

        config_yaml = """
/product_attribute:
    remotes:
    merges:
        - oca 8.0
    target: oca aggregated_branch
"""
        with self.assertRaises(ConfigException) as ex:
            config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(
            ex.exception.args[0],
            '/product_attribute: You should at least define one remote.')

        config_yaml = """
/product_attribute:
    remotes:
        oca:
    merges:
        - oca 8.0
    target: oca aggregated_branch
"""
        with self.assertRaises(ConfigException) as ex:
            config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(
            ex.exception.args[0],
            '/product_attribute: No url defined for remote oca.')

    def test_load_merges_exception(self):
        config_yaml = """
/product_attribute:
    remotes:
        oca: https://github.com/OCA/product-attribute.git
    target: oca aggregated_branch
"""
        with self.assertRaises(ConfigException) as ex:
            config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(
            ex.exception.args[0],
            '/product_attribute: merges is not defined.')

        config_yaml = """
/product_attribute:
    remotes:
        oca: https://github.com/OCA/product-attribute.git
    merges:
        - oca
    target: oca aggregated_branch
"""
        with self.assertRaises(ConfigException) as ex:
            config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(
            ex.exception.args[0],
            '/product_attribute: Merge must be formatted as '
            '"remote_name ref".')
        config_yaml = """
/product_attribute:
    remotes:
        oca: https://github.com/OCA/product-attribute.git
    merges:
    target: oca aggregated_branch
"""
        with self.assertRaises(ConfigException) as ex:
            config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(
            ex.exception.args[0],
            '/product_attribute: You should at least define one merge.')

        config_yaml = """
/product_attribute:
    remotes:
        oca: https://github.com/OCA/product-attribute.git
    merges:
        - oba 8.0
    target: oca aggregated_branch
"""
        with self.assertRaises(ConfigException) as ex:
            config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(
            ex.exception.args[0],
            '/product_attribute: Merge remote oba not defined in remotes.')

        config_yaml = dedent("""
            /web:
                remotes:
                    oca: https://github.com/OCA/web.git
                merges:
                    -
                        depth: 1
                target: oca aggregated_branch
        """)
        with self.assertRaises(ConfigException) as ex:
            config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(
            ex.exception.args[0],
            '/web: Merge lacks mandatory `remote` or `ref` keys.')

    def test_load_target_exception(self):
        config_yaml = """
/product_attribute:
    remotes:
        oca: https://github.com/OCA/product-attribute.git
    merges:
        - oca 8.0
    target: oca 8.0 extra_arg
"""
        with self.assertRaises(ConfigException) as ex:
            config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(
            ex.exception.args[0],
            '/product_attribute: Target must be formatted as '
            '"[remote_name] branch_name"')

        config_yaml = """
/product_attribute:
    remotes:
        oca: https://github.com/OCA/product-attribute.git
    merges:
        - oca 8.0
    target: oba aggregated_branch
"""
        with self.assertRaises(ConfigException) as ex:
            config.get_repos(self._parse_config(config_yaml))
        self.assertEqual(
            ex.exception.args[0],
            '/product_attribute: Target remote oba not defined in remotes.')

    def test_target_defaults(self):
        config_yaml = """
/product_attribute:
    remotes:
        oca: https://github.com/OCA/product-attribute.git
    merges:
        - oca 8.0
    target: 8.0
"""
        repos = config.get_repos(self._parse_config(config_yaml))
        self.assertDictEqual(
            repos[0]["target"], {"branch": "8.0", "remote": None}
        )

        config_yaml = """
/product_attribute:
    remotes:
        oca: https://github.com/OCA/product-attribute.git
    merges:
        - oca 8.0
"""
        repos = config.get_repos(self._parse_config(config_yaml))
        self.assertDictEqual(
            repos[0]["target"], {"branch": "_git_aggregated", "remote": None}
        )

    def test_import_config__not_found(self):
        with self.assertRaises(ConfigException) as exc:
            config.load_config("not_found.yaml")
        self.assertEqual(
            "Unable to find configuration file: not_found.yaml",
            str(exc.exception)
        )

    def test_import_config(self):
        data_yaml = """
/test:
    remotes:
        oca: https://github.com/test/test.git
    merges:
        - oca 8.0
    target: oca aggregated_branch_name
"""

        _, config_path = tempfile.mkstemp(suffix='.yaml')
        try:
            with open(config_path, 'w') as config_file:
                config_file.write(data_yaml)

            repos = config.load_config(config_file.name)
            self.assertEqual(len(repos), 1)
        finally:
            if os.path.exists(config_path):
                os.remove(config_path)

    def test_import_config_expand_env(self):
        """ It should expand environment variables in the config. """
        os.environ['TEST_REPO'] = 'https://github.com/test/test.git'
        data_yaml = """
/test:
    remotes:
        oca: $TEST_REPO
    merges:
        - oca 8.0
    target: oca aggregated_branch_name
"""

        _, config_path = tempfile.mkstemp(suffix='.yaml')
        try:
            with open(config_path, 'w') as config_file:
                config_file.write(data_yaml)

            repos = config.load_config(config_file.name, True)
        finally:
            if os.path.exists(config_path):
                os.remove(config_path)

        remotes = repos[0]['remotes']
        self.assertEqual(
            remotes[0]['url'], os.environ['TEST_REPO']
        )

    def test_import_config_expand_env_from_file(self):
        """ It should expand the config with variables form file. """
        os.environ['TEST_REPO'] = 'https://github.com/test/test.git'
        data_yaml = """
            ${TEST_FOLDER}:
                remotes:
                    oca: $TEST_REPO
                merges:
                    - oca 8.0
                target: oca aggregated_branch_name
            """
        vars_env = """
            # comment

            TEST_REPO=to be overridden by environ
            TEST_FOLDER = /test
            """

        _, env_path = tempfile.mkstemp(suffix='.env')
        try:
            with open(env_path, 'w') as env_file:
                env_file.write(vars_env)
                _, config_path = tempfile.mkstemp(suffix='.yaml')
            with open(config_path, 'w') as config_file:
                config_file.write(data_yaml)
            repos = config.load_config(config_file.name, True, env_file.name)
        finally:
            if os.path.exists(env_path):
                os.remove(env_path)
            if os.path.exists(config_path):
                os.remove(config_path)

        self.assertEqual(repos[0]['cwd'], '/test')
        remotes = repos[0]['remotes']
        self.assertEqual(
            remotes[0]['url'], os.environ['TEST_REPO']
        )

    def test_fetch_all_string(self):
        config_yaml = """
            ./test:
                remotes:
                    oca: https://github.com/test/test.git
                merges:
                    - oca 8.0
                target: oca aggregated_branch_name
                fetch_all: oca
            """
        config_yaml = dedent(config_yaml)
        repos = config.get_repos(self._parse_config(config_yaml))
        self.assertSetEqual(repos[0]["fetch_all"], {"oca"})

    def test_fetch_all_list(self):
        config_yaml = """
            ./test:
                remotes:
                    oca: https://github.com/test/test.git
                merges:
                    - oca 8.0
                target: oca aggregated_branch_name
                fetch_all:
                    - oca
            """
        config_yaml = dedent(config_yaml)
        repos = config.get_repos(self._parse_config(config_yaml))
        self.assertSetEqual(repos[0]["fetch_all"], {"oca"})

    def test_fetch_all_true(self):
        config_yaml = """
            ./test:
                remotes:
                    oca: https://github.com/test/test.git
                merges:
                    - oca 8.0
                target: oca aggregated_branch_name
                fetch_all: yes
            """
        config_yaml = dedent(config_yaml)
        repos = config.get_repos(self._parse_config(config_yaml))
        self.assertIs(repos[0]["fetch_all"], True)
