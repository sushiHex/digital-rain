from cleanup.types import CellVerdict, Provenance, expected_chars

def test_cellverdict_fields():
    v = CellVerdict(index=5, expected="F", ocr_text="E", ocr_pass=False, style_z=3.1, flagged=True)
    assert v.index == 5 and v.expected == "F" and not v.ocr_pass and v.flagged

def test_provenance_values():
    assert {Provenance.ORIGINAL, Provenance.ENSEMBLE, Provenance.INPAINTED, Provenance.UNRESOLVED} \
        == {"original", "ensemble", "inpainted", "unresolved"}

def test_expected_chars_maps_drawn_indices_to_charset():
    from atlas_constants import CHARSET, DRAWN_INDICES
    exp = expected_chars()
    assert set(exp) == set(DRAWN_INDICES)
    assert exp[DRAWN_INDICES[0]] == CHARSET[DRAWN_INDICES[0]]
