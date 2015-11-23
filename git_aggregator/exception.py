# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License LGPLv3 (http://www.gnu.org/licenses/lgpl-3.0-standalone.html)


class GitAggregatorException(Exception):
    """Base Exception
    """
    pass


class ConfigException(GitAggregatorException):
    """Malformed config definition
    """
    pass
