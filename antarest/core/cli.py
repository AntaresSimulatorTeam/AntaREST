# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import argparse
from pathlib import Path


class PathType:
    """file or directory path type for `argparse` parser

    The `PathType` class represents a type of argument that can be used
    with the `argparse` library.
    This class takes three boolean arguments, `exists`, `file_ok`, and `dir_ok`,
    which specify whether the path argument must exist, whether it can be a file,
    and whether it can be a directory, respectively.

    Example Usage::

        import argparse
        from antarest.main import PathType

        parser = argparse.ArgumentParser()
        parser.add_argument("--input", type=PathType(file_ok=True, exists=True))
        args = parser.parse_args()

        print(args.input)

    In the above example, `PathType` is used to specify the type of the `--input`
    argument for the `argparse` parser. The argument must be an existing file path.
    If the given path is not an existing file, the argparse library raises an error.
    The Path object representing the given path is then printed to the console.
    """

    def __init__(
        self,
        exists: bool = False,
        file_ok: bool = False,
        dir_ok: bool = False,
    ) -> None:
        if not (file_ok or dir_ok):
            msg = "Either `file_ok` or `dir_ok` must be set at a minimum."
            raise ValueError(msg)
        self.exists = exists
        self.file_ok = file_ok
        self.dir_ok = dir_ok

    def __call__(self, string: str) -> Path:
        """
        Check whether the given string represents a valid path.

        If `exists` is `False`, the method simply returns the given path.
        If `exists` is True, it checks whether the path exists and whether it is
        a file or a directory, depending on the values of `file_ok` and `dir_ok`.
        If the path exists and is of the correct type, the method returns the path;
        otherwise, it raises an :class:`argparse.ArgumentTypeError` with an
        appropriate error message.

        Args:
            string: file or directory path

        Returns:
            the file or directory path

        Raises
            argparse.ArgumentTypeError: if the path is invalid
        """
        file_path = Path(string).expanduser()
        if not self.exists:
            return file_path
        if self.file_ok and self.dir_ok:
            if file_path.exists():
                return file_path
            msg = f"The file or directory path does not exist: '{file_path}'"
            raise argparse.ArgumentTypeError(msg)
        elif self.file_ok:
            if file_path.is_file():
                return file_path
            elif file_path.exists():
                msg = f"The path is not a regular file: '{file_path}'"
            else:
                msg = f"The file path does not exist: '{file_path}'"
            raise argparse.ArgumentTypeError(msg)
        elif self.dir_ok:
            if file_path.is_dir():
                return file_path
            elif file_path.exists():
                msg = f"The path is not a directory: '{file_path}'"
            else:
                msg = f"The directory path does not exist: '{file_path}'"
            raise argparse.ArgumentTypeError(msg)
        else:  # pragma: no cover
            raise NotImplementedError((self.file_ok, self.dir_ok))
