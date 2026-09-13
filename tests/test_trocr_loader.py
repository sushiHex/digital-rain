"""The TrOCR loader must not depend on AutoTokenizer's ability to convert a
sentencepiece checkpoint, because transformers 5 lost that path for this
model and an upgrade of the shared site-packages killed an eval mid-run
(2026-09-13). Runs only where the snapshot is already cached; CI skips it."""
import glob
import os

import pytest

SNAP = glob.glob(os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub",
                              "models--microsoft--trocr-small-printed", "snapshots", "*"))


@pytest.mark.skipif(not SNAP or os.environ.get("FONTGEN_NO_MODEL_DOWNLOADS"),
                    reason="needs the cached TrOCR snapshot")
def test_trocr_loads_from_explicit_classes_and_decodes():
    from eval_checkpoint import load_trocr
    processor, model = load_trocr()
    ids = processor.tokenizer("Hamburg").input_ids
    assert processor.tokenizer.decode(ids, skip_special_tokens=True) == "Hamburg"
    assert processor.tokenizer.vocab_size == 64002
    assert not model.training


def test_no_module_loads_trocr_through_the_auto_processor():
    """Every TrOCR user goes through load_trocr; the fragile path is not used."""
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    offenders = []
    for path in glob.glob(os.path.join(repo, "**", "*.py"), recursive=True):
        if any(part in path for part in (".venv", "node_modules", os.sep + "tests" + os.sep)):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            if "TrOCRProcessor.from_pretrained(" in fh.read():
                offenders.append(os.path.relpath(path, repo))
    assert offenders == [], offenders
