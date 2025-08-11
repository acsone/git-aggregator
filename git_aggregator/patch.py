# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
import logging
import subprocess
from pathlib import Path

from .command import CommandExecutor
from .exception import ConfigException, GitAggregatorException

logger = logging.getLogger(__name__)


class Patch(CommandExecutor):
    is_local = False

    def __init__(self, path, cwd):
        super().__init__(cwd)
        self.path = path
        if "://" not in path:
            if not Path(path).is_file():
                raise ConfigException(f"Patch file not found: {path}")
            self.is_local = True

    def retrive_data(self):
        if self.is_local:
            data = Path(self.path).read_bytes()
        else:
            cmd = [
                "curl",
                "--fail",
                "--location",
                self.path,
            ]
            if logger.getEffectiveLevel() != logging.DEBUG:
                cmd.append('--silent')
                cmd.append('--show-error')
            data = self.log_call(
                cmd,
                callwith=subprocess.run,
                check=True,
                stdout=subprocess.PIPE,
            ).stdout
        if not data.strip():
            raise GitAggregatorException(f"Patch is empty: {self.path}")
        return data

    def apply(self):
        data = self.retrive_data()
        cmd = [
            "git",
            "am",
        ]
        if logger.getEffectiveLevel() != logging.DEBUG:
            cmd.append('--quiet')
        self.log_call(cmd, callwith=subprocess.run, check=True,
                      cwd=self.cwd, input=data)


class Patches(list):
    """List of patches"""
    @staticmethod
    def prepare_patches(path, cwd):
        _path = Path(path)
        patches = Patches()
        if not _path.exists() or _path.is_file():
            patches.append(Patch(path, cwd))
        elif _path.is_dir():
            for fpath in sorted(_path.iterdir()):
                if fpath.is_file():
                    patches.append(Patch(str(fpath), cwd))
        return patches

    def apply(self):
        for patch in self:
            patch.apply()
