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


# --- French-language KIDs --------------------------------------------------
# One golden test per distinct French template (Crédit Mutuel AM OPCVM and
# FIA, Robeco, FFG/Waystone, La Française, Eiffel IG), plus a sweep over
# every fixture for the fields a portfolio tracker actually consumes.

FR_FIXTURES = FIXTURES / "fr"


def _fr(isin_and_date):
    return parse_kid(FR_FIXTURES / f"KID_fr_{isin_and_date}.pdf")


def _scenario(kid, name):
    s = kid.scenarios[name]
    return (s.one_year.value, s.one_year.return_pct, s.rhp.value, s.rhp.return_pct)


def test_fr_cm_am_opcvm_human_care():
    kid = _fr("FR0013041654_2026-03-02")

    assert kid.language == "fr"
    assert kid.isin == "FR0013041654"
    assert kid.production_date == "2026-03-02"
    assert kid.product_name == "CM-AM HUMAN CARE"  # soft hyphen "CM ­AM" repaired
    assert kid.share_class == "Part RC"
    assert kid.issuer == "CREDIT MUTUEL ASSET MANAGEMENT"
    assert kid.custodian == "BANQUE FEDERATIVE DU CREDIT MUTUEL"
    assert kid.type == "OPCVM sous forme de fonds commun de placement (FCP)"
    assert kid.is_ucits is True
    assert kid.distribution_policy == "Accumulating"
    assert kid.currency == "EUR"
    assert kid.sri == 4
    assert kid.rhp_years == 5
    assert kid.sfdr_article is None  # not stated in this KID
    assert (kid.example_investment_amount.value, kid.example_investment_amount.currency) == (10000.0, "EUR")

    # "­79,7 %": soft-hyphen minus, comma decimal, space-grouped "2 030 €"
    assert _scenario(kid, "stress") == (2030.0, -79.7, 2270.0, -25.7)
    assert _scenario(kid, "unfavourable") == (7050.0, -29.5, 7390.0, -5.9)
    assert _scenario(kid, "moderate") == (9940.0, -0.6, 10070.0, 1.0)
    assert _scenario(kid, "favourable") == (13520.0, 35.2, 13610.0, 6.4)

    cost = kid.cost_section
    assert (cost.total_cost_1y.value, cost.total_cost_rhp.value) == (411.0, 1336.0)
    assert (cost.cost_impact_pct_1y, cost.cost_impact_pct_rhp) == (4.2, 2.6)
    b = cost.breakdown
    assert (b.entry_costs.pct, b.entry_costs.amount.value) == (2.0, 200.0)
    assert b.exit_costs.amount.value == 0.0
    assert (b.management_fees.pct, b.management_fees.amount.value) == (1.9, 186.0)
    assert (b.transaction_costs.pct, b.transaction_costs.amount.value) == (0.31, 25.0)
    assert cost.performance_fees_yn is False


def test_fr_cm_am_fia_is_not_ucits():
    kid = _fr("FR0014001TX4_2026-09-01")

    assert kid.product_name == "CM-AM SOLIDAIRE TEMPERE ISR"
    assert kid.is_ucits is False  # "Ce FIA", FIVG
    assert kid.sri == 2
    assert (kid.cost_section.breakdown.management_fees.pct, kid.cost_section.breakdown.transaction_costs.pct) == (0.78, 0.03)


def test_fr_robeco_english_style_numbers():
    kid = _fr("LU2145461757_2026-07-16")

    assert kid.production_date == "2026-07-16"  # "Date de publication 16/7/2026"
    assert kid.product_name == "Robeco Smart Energy D EUR"
    assert kid.issuer == "Robeco Institutional Asset Management B.V"
    assert kid.custodian == "J.P. Morgan SE"
    assert kid.sfdr_article == "Article 9"
    assert kid.sri == 5
    assert kid.rhp_years == 5  # "5 Ans"
    # "3,100 EUR" is three thousand one hundred, "-69.0%" a dot decimal
    assert _scenario(kid, "stress") == (3100.0, -69.0, 2370.0, -25.0)
    cost = kid.cost_section
    assert (cost.example_cost_amount.value, cost.example_cost_amount.currency) == (10000.0, "EUR")
    assert (cost.total_cost_1y.value, cost.total_cost_rhp.value) == (692.0, 3111.0)
    assert (cost.cost_impact_pct_1y, cost.cost_impact_pct_rhp) == (6.9, 3.4)
    assert (cost.breakdown.entry_costs.pct, cost.breakdown.entry_costs.amount.value) == (5.0, 500.0)
    assert cost.breakdown.management_fees.pct == 1.72
    assert cost.breakdown.transaction_costs.pct == 0.2


def test_fr_ffg_three_holding_periods():
    kid = _fr("LU2612532759_2026-07-11")

    assert kid.product_name == "FFG - BLI Global Impact Equities"
    assert kid.share_class == "R Acc"
    assert kid.issuer == "Waystone Management Company (Lux) S.A"
    assert kid.custodian == "Banque de Luxembourg"
    assert kid.rhp_years == 10
    # 1 / 5 / 10-year columns: rhp is the last one, "5.410 EUR" dot-grouped
    assert _scenario(kid, "stress") == (5410.0, -45.9, 3610.0, -9.7)
    cost = kid.cost_section
    assert (cost.total_cost_1y.value, cost.total_cost_rhp.value) == (511.0, 4554.0)
    assert (cost.cost_impact_pct_1y, cost.cost_impact_pct_rhp) == (5.1, 2.4)
    assert (cost.breakdown.management_fees.pct, cost.breakdown.transaction_costs.pct) == (1.8, 0.3)


def test_fr_la_francaise_alternate_labels():
    kid = _fr("LU1744646933_2025-08-06")

    assert kid.sri == 4  # "catégorisé ce produit au niveau 4 sur 7"
    assert kid.rhp_years == 5
    assert kid.sfdr_article == "Article 9"
    assert kid.index == "MSCI All Country World Index"
    # "Scénario de tensions" row label, "Coût total", "Frais de transaction"
    assert _scenario(kid, "stress") == (4660.0, -53.4, 3530.0, -18.8)
    assert _scenario(kid, "favourable") == (14510.0, 45.1, 17050.0, 11.3)
    cost = kid.cost_section
    assert (cost.total_cost_1y.value, cost.total_cost_rhp.value) == (544.0, 2178.0)
    assert (cost.breakdown.management_fees.pct, cost.breakdown.transaction_costs.pct) == (2.03, 0.49)
    assert cost.performance_fees_yn is False


def test_fr_eiffel_eltif_with_performance_fee():
    kid = _fr("FR001400OLI0_2026-06-05")

    assert (kid.product_name, kid.share_class) == ("EIFFEL INFRASTRUCTURES VERTES", "Part A")
    assert kid.issuer == "EIFFEL INVESTMENT GROUP"
    assert kid.custodian == "Société Générale"
    assert kid.is_ucits is False  # ELTIF / FCPR
    assert kid.sri == 3
    # amounts and returns interleaved per column ("8 586 EUR -14,14 % 8 117 EUR -4,09 %")
    assert _scenario(kid, "moderate") == (10767.0, 7.67, 14712.0, 8.03)
    cost = kid.cost_section
    assert (cost.cost_impact_pct_1y, cost.cost_impact_pct_rhp) == (2.02, 2.18)
    assert cost.breakdown.performance_fees.pct == 15.0
    assert cost.performance_fees_yn is True


def test_fr_every_fixture_has_the_core_fields():
    kids = parse_kids(FR_FIXTURES)
    assert len(kids) == 11
    for kid in kids:
        assert kid.language == "fr", kid.source_file
        for field in ("isin", "product_name", "issuer", "production_date", "sri", "rhp_years", "currency", "distribution_policy"):
            assert getattr(kid, field) is not None, (kid.source_file, field)
        assert kid.cost_section.total_cost_1y is not None, kid.source_file
        assert kid.cost_section.breakdown.management_fees.pct is not None, kid.source_file
        assert all(kid.scenarios[name] is not None for name in ("stress", "unfavourable", "moderate", "favourable")), kid.source_file


def test_english_kids_carry_language_and_production_date():
    kid = parse_kid(FIXTURES / "PRP_DE_en_IE00B4L5Y983_YES_2026-09-03.pdf")
    assert kid.language == "en"
    assert kid.production_date == "2026-09-03"
    assert kid.is_ucits is True
