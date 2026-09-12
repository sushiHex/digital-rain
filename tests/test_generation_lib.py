import inspect


def test_generation_lib_exposes_loader_and_generator():
    import generation_lib as g
    assert hasattr(g, "load_generation_pipe")
    assert hasattr(g, "generate_one_atlas")
    ld = inspect.signature(g.load_generation_pipe)
    assert "use_template" in ld.parameters
    assert "template_pt" in ld.parameters
    assert "checkpoint" in ld.parameters
    gen = inspect.signature(g.generate_one_atlas)
    for p in ("ref_path", "out_path", "steps", "seed"):
        assert p in gen.parameters


def test_eval_checkpoint_uses_generation_lib():
    src = open("eval_checkpoint.py", encoding="utf-8").read()
    assert "generation_lib" in src, "generate_phase_inprocess must call the factored functions"
