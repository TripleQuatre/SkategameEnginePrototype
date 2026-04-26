def is_attack_repetition_synergy_active(
    attack_attempts: int,
    repetition_mode: str,
    *,
    multiple_attack_enabled: bool = False,
    no_repetition: bool = False,
) -> bool:
    return (
        attack_attempts > 1
        and repetition_mode != "disabled"
        and not multiple_attack_enabled
        and not no_repetition
    )


def is_attack_repetition_synergy_compatible(
    attack_attempts: int,
    repetition_mode: str,
    repetition_limit: int,
    *,
    multiple_attack_enabled: bool = False,
    no_repetition: bool = False,
) -> bool:
    if not is_attack_repetition_synergy_active(
        attack_attempts,
        repetition_mode,
        multiple_attack_enabled=multiple_attack_enabled,
        no_repetition=no_repetition,
    ):
        return True

    return (
        repetition_limit >= attack_attempts
        and repetition_limit % attack_attempts == 0
    )


def suggest_attack_repetition_limits(
    attack_attempts: int,
    repetition_mode: str,
    current_limit: int | None = None,
    *,
    multiple_attack_enabled: bool = False,
    no_repetition: bool = False,
    max_limit: int | None = None,
    count: int = 3,
) -> tuple[int, ...]:
    if not is_attack_repetition_synergy_active(
        attack_attempts,
        repetition_mode,
        multiple_attack_enabled=multiple_attack_enabled,
        no_repetition=no_repetition,
    ):
        return ()

    anchor = current_limit if current_limit is not None and current_limit > 0 else attack_attempts
    lower_multiple = max(attack_attempts, (anchor // attack_attempts) * attack_attempts)

    suggestions: list[int] = []
    candidate = lower_multiple
    while len(suggestions) < count:
        if candidate >= attack_attempts and (
            max_limit is None or candidate <= max_limit
        ):
            suggestions.append(candidate)
        candidate += attack_attempts
        if max_limit is not None and candidate > max_limit and suggestions:
            break

    return tuple(dict.fromkeys(suggestions))
