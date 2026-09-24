"""Top-level parse_kid / parse_kids entry points."""

import os
from pathlib import Path

from . import fields
from .models import CostBreakdown, CostLineItem, CostSection, KidDocument, Money, Scenario, ScenarioPoint, ScenarioTimeFrame
from .text import extract_pdf_text, normalize_flat


def _money(data):
    return Money(**data) if data else None


def _cost_line_item(data):
    return CostLineItem(
        description=data["description"],
        pct=data["pct"],
        amount=_money(data["amount"]),
    )


def _scenario(data):
    if data is None:
        return None
    one_year = data["1y"]
    rhp = data["rhp"]
    return Scenario(
        one_year=ScenarioPoint(**one_year) if one_year else None,
        rhp=ScenarioPoint(**rhp) if rhp else None,
    )


def parse_kid(pdf_path) -> KidDocument:
    pdf_path = str(pdf_path)
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    raw_text = extract_pdf_text(pdf_path)
    flat = normalize_flat(raw_text)

    filename_fields = fields.parse_filename(stem)
    isin = fields.extract_isin(flat, filename_fields.get("isin"))
    product_section = fields.extract_product_section(flat)
    product_name, share_class = fields.extract_product_and_class(product_section)
    rhp_years = fields.extract_rhp_years(flat)

    total_1y, total_rhp, impact_1y, impact_rhp = fields.extract_total_costs(flat)
    breakdown, performance_fees_yn = fields.extract_cost_breakdown(flat)

    cost_breakdown = CostBreakdown(
        entry_costs=_cost_line_item(breakdown["entry_costs"]),
        exit_costs=_cost_line_item(breakdown["exit_costs"]),
        management_fees=_cost_line_item(breakdown["management_fees"]),
        transaction_costs=_cost_line_item(breakdown["transaction_costs"]),
        performance_fees=_cost_line_item(breakdown["performance_fees"]),
    )

    scenarios_raw = fields.extract_scenarios(flat)
    scenario_time_frame_raw = fields.extract_scenario_time_frame(rhp_years)

    return KidDocument(
        source_file=pdf_path,
        isin=isin,
        product_name=product_name,
        share_class=share_class,
        issuer=fields.extract_issuer(flat),
        website=fields.extract_website(flat),
        phone=fields.extract_phone(flat),
        email=fields.extract_email(flat),
        type=fields.extract_type(flat),
        term=fields.extract_term(flat),
        objective=fields.extract_objective(flat),
        custodian=fields.extract_custodian(flat),
        index=fields.extract_index(flat),
        currency=fields.extract_currency(flat),
        sfdr_article=fields.extract_sfdr_article(flat),
        distribution_policy=fields.extract_distribution_policy(flat),
        intended_for=fields.extract_intended_for(flat),
        sri=fields.extract_sri(flat),
        rhp_years=rhp_years,
        example_investment_amount=_money(fields.extract_example_investment(flat)),
        scenario_time_frame=ScenarioTimeFrame(**scenario_time_frame_raw),
        scenarios={name: _scenario(value) for name, value in scenarios_raw.items()},
        cost_section=CostSection(
            example_cost_amount=_money(fields.extract_cost_example_investment(flat)),
            total_cost_1y=_money(total_1y),
            total_cost_rhp=_money(total_rhp),
            cost_impact_pct_1y=impact_1y,
            cost_impact_pct_rhp=impact_rhp,
            breakdown=cost_breakdown,
            performance_fees_yn=performance_fees_yn,
        ),
    )


def _iter_pdf_paths(paths):
    if isinstance(paths, (str, Path)):
        path = Path(paths)
        if path.is_dir():
            yield from sorted(path.glob("*.pdf"))
        else:
            yield path
        return
    for item in paths:
        yield from _iter_pdf_paths(item)


def parse_kids(paths) -> list:
    """Parse a directory of PDFs, a single PDF, or an iterable of either."""
    return [parse_kid(p) for p in _iter_pdf_paths(paths)]
