import contextlib
import io
import os
import json
import tempfile
import zipfile
from json import JSONDecodeError
from pathlib import Path
from typing import List, Optional, cast, Dict, Any, Union

from filelock import FileLock

from antarest.core.model import JSON, SUB_JSON
from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.io.reader.ini_reader import IReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import (
    IniWriter,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import (
    INode,
)


class IniReaderError(Exception):
    """
    Left node to handle .ini file behavior
    """

    def __init__(self, name: str, mes: str):
        super(IniReaderError, self).__init__(f"Error read node {name} = {mes}")


class IniFileNode(INode[SUB_JSON, SUB_JSON, JSON]):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        types: Optional[Dict[str, Any]] = None,
        reader: Optional[IReader] = None,
        writer: Optional[IniWriter] = None,
    ):
        super().__init__(config)
        self.context = context
        self.path = config.path
        self.types = types or {}
        self.reader = reader or IniReader()
        self.writer = writer or IniWriter()

    def _get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        get_node: bool = False,
    ) -> Union[SUB_JSON, INode[SUB_JSON, SUB_JSON, JSON]]:
        if get_node:
            return self

        if depth <= -1 and expanded:
            return f"json://{self.config.path.name}"

        if depth == 0:
            return {}
        url = url or []

        if self.config.zip_path:
            with zipfile.ZipFile(
                self.config.zip_path, mode="r"
            ) as zipped_folder:
                inside_zip_path = str(self.config.path)[
                    len(str(self.config.zip_path)[:-4]) + 1 :
                ].replace("\\", "/")
                with io.TextIOWrapper(
                    zipped_folder.open(inside_zip_path)
                ) as f:
                    try:
                        data = self.reader.read(f)
                    except Exception as e:
                        raise IniReaderError(
                            self.__class__.__name__, str(e)
                        ) from e
        else:
            try:
                data = self.reader.read(self.path)
            except Exception as e:
                raise IniReaderError(self.__class__.__name__, str(e)) from e

        if len(url) == 2:
            data = data[url[0]][url[1]]
        elif len(url) == 1:
            data = data[url[0]]
        else:
            data = {k: {} for k in data} if depth == 1 else data
        return cast(SUB_JSON, data)

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> SUB_JSON:
        output = self._get(url, depth, expanded, get_node=False)
        assert not isinstance(output, INode)
        return output

    def get_node(
        self,
        url: Optional[List[str]] = None,
    ) -> INode[SUB_JSON, SUB_JSON, JSON]:
        output = self._get(url, get_node=True)
        assert isinstance(output, INode)
        return output

    def save(self, data: SUB_JSON, url: Optional[List[str]] = None) -> None:
        self._assert_not_in_zipped_file()
        url = url or []
        with FileLock(
            str(
                Path(tempfile.gettempdir())
                / f"{self.config.study_id}-{self.path.relative_to(self.config.study_path).name.replace(os.sep, '.')}.lock"
            )
        ):
            info = self.reader.read(self.path) if self.path.exists() else {}
            obj = data
            if isinstance(data, str):
                with contextlib.suppress(JSONDecodeError):
                    obj = json.loads(data)
            if len(url) == 2:
                if url[0] not in info:
                    info[url[0]] = {}
                info[url[0]][url[1]] = obj
            elif len(url) == 1:
                info[url[0]] = obj
            else:
                info = cast(JSON, obj)
            self.writer.write(info, self.path)

    def delete(self, url: Optional[List[str]] = None) -> None:
        url = url or []
        if len(url) == 0:
            if self.config.path.exists():
                self.config.path.unlink()
        elif len(url) > 0:
            data = self.reader.read(self.path) if self.path.exists() else {}
            section_name = url[0]
            if len(url) == 1:
                with contextlib.suppress(KeyError):
                    del data[section_name]
            elif len(url) == 2:
                # remove dict key
                key_name = url[1]
                with contextlib.suppress(KeyError):
                    del data[section_name][key_name]
            else:
                raise ValueError(
                    f"url should be fully resolved when arrives on {self.__class__.__name__}"
                )
            self.writer.write(data, self.path)

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        errors = []
        for section, params in self.types.items():
            if section not in data:
                msg = f"section {section} not in {self.__class__.__name__}"
                if raising:
                    raise ValueError(msg)
                errors.append(msg)
            else:
                self._validate_param(
                    section, params, data[section], errors, raising
                )

        return errors

    def normalize(self) -> None:
        pass  # no external store in this node

    def denormalize(self) -> None:
        pass  # no external store in this node

    def _validate_param(
        self,
        section: str,
        params: Any,
        data: JSON,
        errors: List[str],
        raising: bool,
    ) -> None:
        for param, typing in params.items():
            if param not in data:
                msg = f"param {param} of section {section} not in {self.__class__.__name__}"
                if raising:
                    raise ValueError(msg)
                errors.append(msg)
            else:
                if not isinstance(data[param], typing):
                    msg = f"param {param} of section {section} in {self.__class__.__name__} bad type"
                    if raising:
                        raise ValueError(msg)
                    errors.append(msg)
