from typing import Any, Dict, List, Union

JSON = Dict[str, Any]
ELEMENT = Union[str, int, float, bool, bytes]
SUB_JSON = Union[ELEMENT, JSON, List, None]
