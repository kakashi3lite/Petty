def test_powertools_import():
    from common.observability import powertools as pt
    assert hasattr(pt, "logger")
    assert hasattr(pt, "tracer")
    assert hasattr(pt, "metrics")
