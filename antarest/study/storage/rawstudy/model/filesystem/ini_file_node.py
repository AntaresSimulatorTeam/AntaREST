from functools import reduce
from typing import List, Optional, cast, Dict, Any, Union

from jsonschema import Validator, Draft6Validator

from antarest.core.model import JSON, SUB_JSON
from antarest.core.utils.utils import assert_this
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
    TREE,
)


DEFAULT_INI_VALIDATOR = Draft6Validator(
    {
        "type": "object",
    }
)


class IniReaderError(Exception):
    """
    Left node to handle .ini file behavior
    """

    def __init__(self, name: str, mes: str):
        super(IniReaderError, self).__init__(f"Error read node {name} = {mes}")


LAZY_PREFIX = "json://"


class IniFileNode(INode[SUB_JSON, SUB_JSON, JSON]):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        validator: Validator = DEFAULT_INI_VALIDATOR,
        reader: Optional[IReader] = None,
        writer: Optional[IniWriter] = None,
    ):
        super().__init__(config)
        self.context = context
        self.path = config.path
        self.validator = validator
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
            return f"{LAZY_PREFIX}{self.config.path.name}"

        if depth == 0:
            return {}
        url = url or []
        try:
            json = self.reader.read(self.path)
        except Exception as e:
            raise IniReaderError(self.__class__.__name__, str(e))
        if len(url) == 2:
            json = json[url[0]][url[1]]
        elif len(url) == 1:
            json = json[url[0]]
        else:
            json = {k: {} for k in json} if depth == 1 else json
        return cast(SUB_JSON, json)

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
        url = url or []
        json = self.reader.read(self.path) if self.path.exists() else {}
        if len(url) == 2:
            if url[0] not in json:
                json[url[0]] = {}
            json[url[0]][url[1]] = data
        elif len(url) == 1:
            json[url[0]] = data
        else:
            json = cast(JSON, data)
        self.writer.write(json, self.path)

    def delete(self, url: Optional[List[str]] = None) -> None:
        url = url or []
        if len(url) == 0:
            if self.config.path.exists():
                self.config.path.unlink()
        elif len(url) > 0:
            json = self.reader.read(self.path) if self.path.exists() else {}
            section_name = url[0]
            if len(url) == 1:
                try:
                    del json[section_name]
                except KeyError:
                    pass
            elif len(url) == 2:
                # remove dict key
                key_name = url[1]
                try:
                    del json[section_name][key_name]
                except KeyError:
                    pass
            else:
                raise ValueError(
                    f"url should be fully resolved when arrives on {self.__class__.__name__}"
                )
            self.writer.write(json, self.path)

    def check_errors(
        self,
        data: JSON,
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        data_to_validate = data
        if isinstance(data, str) and data.startswith(LAZY_PREFIX):
            data_to_validate = self._get([], -1, expanded=False)
        errors = [
            error.message
            for error in self.validator.iter_errors(data_to_validate)
        ]
        if raising and errors:
            raise ValueError("\n".join(errors))
        return errors

    def get_validator(self) -> Validator:
        return self.validator

    def normalize(self) -> None:
        pass  # no external store in this node

    def denormalize(self) -> None:
        pass  # no external store in this node
