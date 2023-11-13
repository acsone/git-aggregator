# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
import logging
import subprocess
from pathlib import Path

from .command import CommandExecutor

logger = logging.getLogger(__name__)


class Patch(CommandExecutor):
    is_local = False

    def __init__(self, path, cwd):
        super().__init__(cwd)
        self.path = path
        path = Path(path)
        if path.exists():
            self.is_local = True

    def retrive_data(self):
        path = self.path
        if self.is_local:
            patch_path = Path(path).absolute()
            path = f"FILE:{str(patch_path)}"
        cmd = [
            "curl",
            path,
        ]
        if logger.getEffectiveLevel() != logging.DEBUG:
            cmd.append('-s')
        return self.log_call(
            cmd,
            callwith=subprocess.Popen,
            stdout=subprocess.PIPE
        )

    def apply(self):
        res = self.retrive_data()
        cmd = [
            "git",
            "am",
        ]
        if logger.getEffectiveLevel() != logging.DEBUG:
            cmd.append('--quiet')
        self.log_call(cmd, cwd=self.cwd, stdin=res.stdout)


class Patches(list):
    """List of patches"""
    @staticmethod
    def prepare_patches(path, cwd):
        _path = Path(path)
        patches = Patches()
        if not _path.exists() or _path.is_file():
            patches.append(Patch(path, cwd))
        elif _path.is_dir():
            for fpath in _path.iterdir():
                if fpath.is_file():
                    patches.append(Patch(str(fpath), cwd))
        return patches

    def apply(self):
        for patch in self:
            patch.apply()
