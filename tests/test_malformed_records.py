"""Malformed-record safety checks for public service functions."""

import pytest

from models import new_order, new_partner
from service import estimate_eta


@pytest.mark.parametrize(
    "order,partner,travel",
    [
        (None, new_partner("P", "Z"), {("Z", "R"): 1, ("R", "D"): 1}),
        (new_order("O", "R", "D"), None, {("Z", "R"): 1, ("R", "D"): 1}),
        (new_order("O", "R", "D"), new_partner("P", "Z"), None),
        (new_order("O", "R", "D"), new_partner("P", "Z"), []),
    ],
)
def test_eta_rejects_malformed_top_level_records(order, partner, travel):
    result = estimate_eta(order, partner, travel)
    assert result["eligible"] is False
    assert result["eta_minutes"] is None


def test_eta_rejects_missing_partner_identifier():
    partner = new_partner("P", "Z")
    partner["partner_id"] = ""

    result = estimate_eta(
        new_order("O", "R", "D"),
        partner,
        {("Z", "R"): 1, ("R", "D"): 1},
    )

    assert result["eligible"] is False
    assert result["eta_minutes"] is None
