from pydantic import BaseModel


def missing_fields(value, path: str = "$") -> list[str]:
    if value is None:
        return [path]
    if isinstance(value, BaseModel):
        return [
            missing
            for name in type(value).model_fields
            for missing in missing_fields(getattr(value, name), f"{path}.{name}")
        ]
    if isinstance(value, list):
        return [
            missing
            for i, item in enumerate(value)
            for missing in missing_fields(item, f"{path}[{i}]")
        ]
    return []
