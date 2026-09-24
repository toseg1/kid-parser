"""Regression tests against 4 real-world PRIIPs KID templates.

Every value asserted here was hand-verified against the raw PDF text during
development (see project history) -- these guard against regressions when a
5th issuer's template needs new fallback patterns added to kid_parser.fields.
"""

from pathlib import Path

from kid_parser import KidDocument, parse_kid, parse_kids

FIXTURES = Path(__file__).parent / "fixtures"


def _scenario_point(scenario, key):
    point = getattr(scenario, key)
    return (point.value, point.currency, point.return_pct)


def test_ishares_core_msci_world():
    kid = parse_kid(FIXTURES / "PRP_DE_en_IE00B4L5Y983_YES_2026-09-03.pdf")

    assert kid.isin == "IE00B4L5Y983"
    assert kid.product_name == "iShares Core MSCI World UCITS ETF"
    assert kid.share_class == "USD Accu"
    assert kid.issuer == "BlackRock Asset Management Ireland Limited"
    assert kid.website == "www.blackrock.com"
    assert kid.phone == "+49 89427295800"
    assert kid.email == "info@ishares.co.uk"
    assert kid.currency == "USD"
    assert kid.sfdr_article is None
    assert kid.distribution_policy == "Accumulating"
    assert kid.intended_for == "Retail"
    assert kid.sri == 4
    assert kid.rhp_years == 5
    assert kid.example_investment_amount.value == 10000.0
    assert kid.example_investment_amount.currency == "USD"
    assert kid.scenario_time_frame.short == "1 year"
    assert kid.scenario_time_frame.recommended == "5 years"

    assert _scenario_point(kid.scenarios["stress"], "one_year") == (7490.0, "USD", -25.1)
    assert _scenario_point(kid.scenarios["stress"], "rhp") == (3850.0, "USD", -17.4)
    assert _scenario_point(kid.scenarios["unfavourable"], "one_year") == (8050.0, "USD", -19.5)
    assert _scenario_point(kid.scenarios["unfavourable"], "rhp") == (11960.0, "USD", 3.7)
    assert _scenario_point(kid.scenarios["moderate"], "one_year") == (11550.0, "USD", 15.5)
    assert _scenario_point(kid.scenarios["moderate"], "rhp") == (17800.0, "USD", 12.2)
    assert _scenario_point(kid.scenarios["favourable"], "one_year") == (15420.0, "USD", 54.2)
    assert _scenario_point(kid.scenarios["favourable"], "rhp") == (21200.0, "USD", 16.2)

    cost = kid.cost_section
    assert (cost.total_cost_1y.value, cost.total_cost_1y.currency) == (20.0, "USD")
    assert (cost.total_cost_rhp.value, cost.total_cost_rhp.currency) == (180.0, "USD")
    assert (cost.cost_impact_pct_1y, cost.cost_impact_pct_rhp) == (0.2, 0.2)
    assert cost.breakdown.entry_costs.amount is None
    assert cost.breakdown.exit_costs.amount is None
    assert cost.breakdown.management_fees.pct == 0.2
    assert (cost.breakdown.management_fees.amount.value, cost.breakdown.management_fees.amount.currency) == (20.0, "USD")
    assert cost.breakdown.transaction_costs.pct == 0.0
    assert (cost.breakdown.transaction_costs.amount.value, cost.breakdown.transaction_costs.amount.currency) == (0.0, "USD")
    assert cost.performance_fees_yn is False


def test_ishares_msci_emu_paris_aligned():
    kid = parse_kid(FIXTURES / "PRP_DE_en_IE00BL6K8D99_YES_2026-04-09.pdf")

    assert kid.isin == "IE00BL6K8D99"
    assert kid.product_name == "iShares MSCI EMU Paris-Aligned Climate UCITS ETF"
    assert kid.share_class == "EUR Accu"
    assert kid.currency == "EUR"
    assert kid.sfdr_article is None
    assert kid.sri == 4
    assert kid.rhp_years == 5

    assert _scenario_point(kid.scenarios["stress"], "one_year") == (7890.0, "EUR", -21.1)
    assert _scenario_point(kid.scenarios["stress"], "rhp") == (4090.0, "EUR", -16.4)
    assert _scenario_point(kid.scenarios["unfavourable"], "one_year") == (8100.0, "EUR", -19.0)
    assert _scenario_point(kid.scenarios["unfavourable"], "rhp") == (9780.0, "EUR", -0.5)
    assert _scenario_point(kid.scenarios["moderate"], "one_year") == (10980.0, "EUR", 9.8)
    assert _scenario_point(kid.scenarios["moderate"], "rhp") == (13940.0, "EUR", 6.9)
    assert _scenario_point(kid.scenarios["favourable"], "one_year") == (14240.0, "EUR", 42.4)
    assert _scenario_point(kid.scenarios["favourable"], "rhp") == (18170.0, "EUR", 12.7)

    cost = kid.cost_section
    assert (cost.total_cost_1y.value, cost.total_cost_rhp.value) == (18.0, 123.0)
    assert cost.breakdown.management_fees.pct == 0.15
    assert cost.breakdown.transaction_costs.pct == 0.03
    assert cost.performance_fees_yn is False


def test_amundi_emerging_markets_esg():
    kid = parse_kid(FIXTURES / "PRP_DE_en_LU2109787049_YES_2026-06-15.pdf")

    assert kid.isin == "LU2109787049"
    assert kid.product_name == "Amundi MSCI Emerging Markets ESG Broad Transition UCITS ETF Acc"
    assert kid.share_class is None  # no quoted "Share Class" in this template
    assert kid.issuer == "Amundi Luxembourg S.A"
    assert kid.currency == "USD"
    assert kid.sfdr_article == "Article 8"
    assert kid.distribution_policy == "Accumulating"
    # "Intended retail investor" is mandatory boilerplate; this template's
    # body text never actually names an audience.
    assert kid.intended_for is None
    assert kid.sri == 4
    assert kid.rhp_years == 5

    assert _scenario_point(kid.scenarios["stress"], "one_year") == (4030.0, "USD", -59.7)
    assert _scenario_point(kid.scenarios["stress"], "rhp") == (3340.0, "USD", -19.7)
    assert _scenario_point(kid.scenarios["favourable"], "one_year") == (15720.0, "USD", 57.2)
    assert _scenario_point(kid.scenarios["favourable"], "rhp") == (18030.0, "USD", 12.5)

    cost = kid.cost_section
    assert (cost.total_cost_1y.value, cost.total_cost_rhp.value) == (38.0, 223.0)
    assert (cost.cost_impact_pct_1y, cost.cost_impact_pct_rhp) == (0.4, 0.4)
    assert cost.breakdown.entry_costs.amount.value == 0.0
    assert cost.breakdown.management_fees.pct == 0.18
    assert cost.breakdown.transaction_costs.amount.value == 20.33
    assert cost.performance_fees_yn is False


def test_lg_clean_water():
    kid = parse_kid(FIXTURES / "PRP_DE_en_IE00BK5BC891_YES_2025-05-19_ADCX.pdf")

    assert kid.isin == "IE00BK5BC891"
    assert kid.product_name == "L&G Clean Water UCITS ETF"
    assert kid.share_class == "USD Accumulating ETF"
    assert kid.issuer == "LGIM Managers (Europe) Limited"
    assert kid.phone == "+44 (0) 203 124 3180"
    assert kid.currency == "USD"
    assert kid.distribution_policy == "Accumulating"
    assert kid.intended_for is None  # body text names no audience, only the mandatory heading does
    assert kid.sri == 5
    assert kid.rhp_years == 5  # from "recommended holding period of 5 years", not the usual phrasing
    assert kid.example_investment_amount.value == 10000.0  # decimal "10,000.00" handled

    # "Stress scenario*" ordering (word before asterisk), unlike the other 3 templates
    assert _scenario_point(kid.scenarios["stress"], "one_year") == (4570.0, "USD", -54.3)
    assert _scenario_point(kid.scenarios["favourable"], "rhp") == (25300.0, "USD", 20.4)

    cost = kid.cost_section
    # "Impact on return (RIY) per year" wording, not "Annual cost Impact"
    assert (cost.total_cost_1y.value, cost.total_cost_rhp.value) == (58.0, 533.0)
    assert (cost.cost_impact_pct_1y, cost.cost_impact_pct_rhp) == (0.6, 0.7)
    assert cost.breakdown.management_fees.pct == 0.49
    assert cost.breakdown.transaction_costs.pct == 0.09
    # "Performance fees and carried interest" label - suffix must not leak into description
    assert cost.breakdown.performance_fees.description == "0.00% There is no performance fee for this product"
    assert cost.performance_fees_yn is False


def test_parse_kids_over_fixtures_dir():
    kids = parse_kids(FIXTURES)
    assert len(kids) == 4
    assert {kid.isin for kid in kids} == {
        "IE00B4L5Y983", "IE00BL6K8D99", "LU2109787049", "IE00BK5BC891",
    }


def test_json_round_trip():
    kid = parse_kid(FIXTURES / "PRP_DE_en_IE00BL6K8D99_YES_2026-04-09.pdf")
    reloaded = KidDocument.from_json(kid.to_json())
    assert reloaded.to_dict() == kid.to_dict()
