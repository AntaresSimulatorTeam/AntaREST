def to_pascal_case(value: str) -> str:
    return "".join(word.capitalize() for word in value.split("_"))


def to_camel_case(value: str) -> str:
    v = to_pascal_case(value)
    return v[0].lower() + v[1:] if len(v) > 0 else ""
