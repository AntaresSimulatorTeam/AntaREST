import copy
from typing import Dict, Any


def merge_deep(a: Dict[Any, Any], b: Dict[Any, Any]) -> Dict[Any, Any]:
    result = copy.deepcopy(a)
    for key, value in b.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = merge_deep(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result
