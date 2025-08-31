# -*- coding: utf-8 -*-

"""
Initialize PyWf object from a ``pyproject.toml`` file.
"""

import dataclasses
from pathlib import Path
from pywf_open_source.api import PyWf

@dataclasses.dataclass
class MyPyWf(PyWf):
    def _poetry_export_logic(
        self: "PyWf",
        current_poetry_lock_hash: str,
        with_hash: bool = False,
        real_run: bool = True,
    ):
        super()._poetry_export_logic(
            current_poetry_lock_hash=current_poetry_lock_hash,
            with_hash=with_hash,
            real_run=real_run,
        )

        for group, path in [
            ("aws", self.dir_project_root / "requirements-aws.txt"),
            ("publish", self.dir_project_root / "requirements-publish.txt"),
        ]:
            self._poetry_export_group(
                group=group,
                path=path,
                with_hash=with_hash,
                real_run=real_run,
            )


dir_here = Path(__file__).absolute().parent
path_pyproject_toml = dir_here.parent.joinpath("pyproject.toml")
pywf = MyPyWf.from_pyproject_toml(path_pyproject_toml)
