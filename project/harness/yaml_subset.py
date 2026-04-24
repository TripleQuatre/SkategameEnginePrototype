import ast
import re
from dataclasses import dataclass


_INT_PATTERN = re.compile(r"^-?\d+$")
_FLOAT_PATTERN = re.compile(r"^-?\d+\.\d+$")
_LIST_ITEM_MAPPING_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_ -]*:")


@dataclass(frozen=True)
class _YAMLLine:
    indent: int
    content: str
    line_number: int


class YAMLSubsetError(ValueError):
    pass


def load_yaml_subset(text: str):
    lines = _prepare_lines(text)
    if not lines:
        return {}

    node, index = _parse_node(lines, 0, lines[0].indent)
    if index != len(lines):
        line = lines[index]
        raise YAMLSubsetError(
            f"Unexpected trailing content at line {line.line_number}: {line.content}"
        )
    return node


def _prepare_lines(text: str) -> list[_YAMLLine]:
    prepared: list[_YAMLLine] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent % 2 != 0:
            raise YAMLSubsetError(
                f"Invalid indentation at line {line_number}: use multiples of two spaces."
            )

        prepared.append(
            _YAMLLine(
                indent=indent,
                content=raw_line[indent:],
                line_number=line_number,
            )
        )
    return prepared


def _parse_node(lines: list[_YAMLLine], index: int, indent: int):
    if lines[index].content.startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_dict(lines, index, indent)


def _parse_dict(lines: list[_YAMLLine], index: int, indent: int):
    data: dict[str, object] = {}

    while index < len(lines):
        line = lines[index]
        if line.indent < indent:
            break
        if line.indent != indent:
            raise YAMLSubsetError(
                f"Unexpected indentation at line {line.line_number}: {line.content}"
            )
        if line.content.startswith("- "):
            break
        if ":" not in line.content:
            raise YAMLSubsetError(
                f"Expected mapping entry at line {line.line_number}: {line.content}"
            )

        key, tail = line.content.split(":", 1)
        key = key.strip()
        tail = tail.strip()
        if not key:
            raise YAMLSubsetError(f"Empty key at line {line.line_number}.")

        index += 1
        if tail:
            data[key] = _parse_scalar(tail)
            continue

        if index < len(lines) and lines[index].indent > indent:
            child, index = _parse_node(lines, index, lines[index].indent)
            data[key] = child
        else:
            data[key] = {}

    return data, index


def _parse_list(lines: list[_YAMLLine], index: int, indent: int):
    items: list[object] = []

    while index < len(lines):
        line = lines[index]
        if line.indent < indent:
            break
        if line.indent != indent or not line.content.startswith("- "):
            break

        rest = line.content[2:].strip()
        if not rest:
            index += 1
            if index < len(lines) and lines[index].indent > indent:
                child, index = _parse_node(lines, index, lines[index].indent)
                items.append(child)
            else:
                items.append(None)
            continue

        if _LIST_ITEM_MAPPING_PATTERN.match(rest):
            key, tail = rest.split(":", 1)
            key = key.strip()
            tail = tail.strip()
            item: dict[str, object] = {}
            index += 1

            if tail:
                item[key] = _parse_scalar(tail)
            elif index < len(lines) and lines[index].indent > indent:
                child, index = _parse_node(lines, index, lines[index].indent)
                item[key] = child
            else:
                item[key] = {}

            if index < len(lines) and lines[index].indent > indent:
                extra, index = _parse_dict(lines, index, lines[index].indent)
                item.update(extra)

            items.append(item)
            continue

        items.append(_parse_scalar(rest))
        index += 1

    return items, index


def _parse_scalar(value: str):
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~", "none"}:
        return None

    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return ast.literal_eval(value)

    if _INT_PATTERN.match(value):
        return int(value)
    if _FLOAT_PATTERN.match(value):
        return float(value)

    return value
