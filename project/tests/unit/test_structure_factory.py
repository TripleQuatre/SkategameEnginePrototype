from match.structure.structure_factory import StructureFactory


def test_structure_factory_creates_one_vs_one_structure() -> None:
    structure = StructureFactory().create("one_vs_one")

    assert structure.__class__.__name__ == "OneVsOneStructure"
    assert structure.structure_name == "one_vs_one"


def test_structure_factory_creates_battle_structure() -> None:
    structure = StructureFactory().create("battle")

    assert structure.__class__.__name__ == "BattleStructure"
    assert structure.structure_name == "battle"
