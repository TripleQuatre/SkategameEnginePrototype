from dictionary.inline_primary_grind import InlinePrimaryGrindDictionary


_RUNTIME_DICTIONARY = InlinePrimaryGrindDictionary()


def get_runtime_dictionary() -> InlinePrimaryGrindDictionary:
    return _RUNTIME_DICTIONARY


def resolve_runtime_trick_record(
    raw_value: str | None,
) -> tuple[str | None, dict[str, object] | None]:
    if raw_value is None:
        return None, None

    resolution = _RUNTIME_DICTIONARY.resolve(raw_value)
    if resolution is None:
        return raw_value, None

    return resolution.label, resolution.to_dict()


def build_runtime_trick_payload(
    raw_value: str | None,
    trick_data: dict[str, object] | None = None,
) -> dict[str, object]:
    if raw_value is None:
        return {"trick": None}

    resolved_data = trick_data
    if resolved_data is None:
        _, resolved_data = resolve_runtime_trick_record(raw_value)

    payload: dict[str, object] = {
        "trick": raw_value,
    }
    if resolved_data is not None:
        payload["trick_label"] = resolved_data["label"]
        payload["trick_key"] = resolved_data["canonical_key"]
        payload["trick_data"] = resolved_data

    return payload
