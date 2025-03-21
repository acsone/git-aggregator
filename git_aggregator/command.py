# © 2015 ACSONE SA/NV
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Parts of the code comes from ANYBOX
# https://github.com/anybox/anybox.recipe.odoo
import logging
import subprocess

from ._compat import console_to_str

logger = logging.getLogger(__name__)


class CommandExecutor:
    def __init__(self, cwd):
        self.cwd = cwd

    def log_call(self, cmd, callwith=subprocess.check_call,
                 log_level=logging.DEBUG, **kw):
        """Wrap a subprocess call with logging
        :param meth: the calling method to use.
        """
        logger.log(log_level, "%s> call %r", self.cwd, cmd)
        try:
            ret = callwith(cmd, **kw)
        except Exception:
            logger.error("%s> error calling %r", self.cwd, cmd)
            raise
        if callwith == subprocess.check_output:
            ret = console_to_str(ret)
        return ret
