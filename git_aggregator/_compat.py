# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
import sys

PY2 = sys.version_info[0] == 2

if PY2:
    string_types = (str, unicode)  # noqa

    def console_to_str(s):
        return s.decode('utf_8')
else:
    string_types = (str,)
    console_encoding = sys.__stdout__.encoding

    def console_to_str(s):
        """ From pypa/pip project, pip.backwardwardcompat. License MIT. """
        try:
            return s.decode(console_encoding)
        except UnicodeDecodeError:
            return s.decode('utf_8')
        except AttributeError:  # for tests, #13
            return s
