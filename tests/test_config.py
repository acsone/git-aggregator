# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
import os
import tempfile
import unittest
import kaptan

from git_aggregator import config
from git_aggregator.exception import ConfigException
from git_aggregator._compat import PY2


class TestConfig(unittest.TestCase):

    def _parse_config(self, config_str):
        conf = kaptan.Kaptan(handler='yaml')
        conf.import_config(config_str)
        return conf.export('dict')

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
        self.assertEquals(len(repos), 1)
        # remotes are configured as dict therefore the order is not preserved
        # when parsed
        remotes = repos[0]['remotes']
        repos[0]['remotes'] = []
        self.assertDictEqual(
            repos[0],
            {'cwd': '/product_attribute',
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
        self.assertEquals(repos[0]['shell_command_after'], ['ls'])
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
        self.assertEquals(repos[0]['shell_command_after'], ['ls', 'echo'])

    def test_load_remotes_exception(self):
        config_yaml = """
/product_attribute:
    merges:
        - oca 8.0
    target: oca aggregated_branch
"""
        with self.assertRaises(ConfigException) as ex:
            config.get_repos(self._parse_config(config_yaml))
        self.assertEquals(
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
        self.assertEquals(
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
        self.assertEquals(
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
        self.assertEquals(
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
        self.assertEquals(
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
        self.assertEquals(
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
        self.assertEquals(
            ex.exception.args[0],
            '/product_attribute: Merge remote oba not defined in remotes.')

    def test_load_target_exception(self):
        config_yaml = """
/product_attribute:
    remotes:
        oca: https://github.com/OCA/product-attribute.git
    merges:
        - oca 8.0
"""
        with self.assertRaises(ConfigException) as ex:
            config.get_repos(self._parse_config(config_yaml))
        self.assertEquals(ex.exception.args[0],
                          '/product_attribute: No target defined.')

        config_yaml = """
/product_attribute:
    remotes:
        oca: https://github.com/OCA/product-attribute.git
    merges:
        - oca 8.0
    target:
"""
        with self.assertRaises(ConfigException) as ex:
            config.get_repos(self._parse_config(config_yaml))
        self.assertEquals(
            ex.exception.args[0],
            '/product_attribute: Target must be formatted as '
            '"remote_name branch_name"')

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
        self.assertEquals(
            ex.exception.args[0],
            '/product_attribute: Target remote oba not defined in remotes.')

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
            self.assertEquals(len(repos), 1)
        finally:
            if os.path.exists(config_path):
                os.remove(config_path)
