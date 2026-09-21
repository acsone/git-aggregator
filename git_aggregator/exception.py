# © 2015 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)


class GitAggregatorException(Exception):
    """Base Exception
    """


class ConfigException(GitAggregatorException):
    """Malformed config definition
    """


class DirtyException(GitAggregatorException):
    """Repo directory is dirty"""
