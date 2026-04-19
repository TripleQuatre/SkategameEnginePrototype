from config.match_policies import InitialTurnOrderPolicy, MatchPolicies


def build_default_policies_for_structure(structure_name: str) -> MatchPolicies:
    if structure_name == "battle":
        return MatchPolicies(
            initial_turn_order=InitialTurnOrderPolicy.RANDOMIZED,
        )

    return MatchPolicies()


def build_default_policies_for_mode(mode_name: str) -> MatchPolicies:
    """Compatibility alias kept during the V7 migration."""

    return build_default_policies_for_structure(mode_name)
