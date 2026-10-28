from dataclasses import replace

import pytest

from app.domain.comparison import PreparedOption, display_order
from tests.support.synthetic import EXAMPLE, create_service
from app.application.comparisons import Submission


def test_display_order_is_normalized_alphabetical_with_stable_identity_ties():
    options = [
        PreparedOption("00000000-0000-0000-0000-000000000003", "Zeta", {}, ()),
        PreparedOption("00000000-0000-0000-0000-000000000002", "Ａlpha", {}, ()),
        PreparedOption("00000000-0000-0000-0000-000000000001", "alpha", {}, ()),
    ]
    ordered = display_order(options)
    assert [option.alternative_id[-1] for option in ordered] == ["1", "2", "3"]
    assert ordered[1].display_name == "Ａlpha"


def test_rendering_failure_never_enters_the_save_boundary(tmp_path):
    service = create_service(tmp_path / "comparison.sqlite3")
    saved = []

    class BrokenRenderer:
        def prepare(self, interpretation, candidates):
            raise RuntimeError("synthetic rendering failure")

    class NeverSave:
        def find(self, key):
            return None

        def save(self, prepared):
            saved.append(prepared)

    engine = service.store.engine
    service = replace(service, renderer=BrokenRenderer(), store=NeverSave())
    with pytest.raises(RuntimeError, match="rendering failure"):
        service.execute(Submission("00000000-0000-0000-0000-000000000001", "a" * 64, EXAMPLE, {"country_code": "CH"}, "provided", {}))
    assert saved == []
    engine.dispose()
