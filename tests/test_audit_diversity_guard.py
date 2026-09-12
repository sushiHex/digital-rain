def test_guard_exposed():
    import audit_diversity as a
    assert hasattr(a, "guard")
    import inspect
    assert "gen_dir" in inspect.signature(a.guard).parameters
