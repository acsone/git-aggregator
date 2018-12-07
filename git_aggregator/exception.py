# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)


class GitAggregatorException(Exception):
    """Base Exception
    """
    pass


class ConfigException(GitAggregatorException):
    """Malformed config definition
    """
    pass


class DirtyException(GitAggregatorException):
    """Repo directory is dirty"""
