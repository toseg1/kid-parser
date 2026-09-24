"""Regex-only PRIIPs KID PDF parser (no LLM, no API keys).

    from kid_parser import parse_kid, parse_kids, KidDocument

    # Parse one PDF -> a dataclass, entirely in memory, no disk writes
    kid = parse_kid("IE00BL6K8D99.pdf")
    kid.isin                              # "IE00BL6K8D99"
    kid.share_class                       # "EUR Accu"
    kid.cost_section.total_cost_1y.value  # 18.0

    # Parse a whole directory (or a list of paths)
    kids = parse_kids("path/to/kids_dir")   # -> list[KidDocument]

    # JSON is opt-in (de)serialization, not a mandatory side effect:
    json_str = kid.to_json()
    kid2 = KidDocument.from_json(json_str)            # round-trip from a string
    kid3 = KidDocument.from_json("saved.json")        # or from a file, no PDF needed

CLI mirrors this: JSON writing only happens if you ask for it.

    kid-parser some/*.pdf                   # prints one-line summaries only
    kid-parser some_dir/ --json-dir out/    # also writes <isin>.kid.json + kids_parsed.json
    kid-parser some_dir/ --json             # prints the combined JSON array to stdout
"""

from .models import (
    CostBreakdown,
    CostLineItem,
    CostSection,
    KidDocument,
    Money,
    Scenario,
    ScenarioPoint,
    ScenarioTimeFrame,
)
from .parser import parse_kid, parse_kids

__all__ = [
    "parse_kid",
    "parse_kids",
    "KidDocument",
    "Money",
    "Scenario",
    "ScenarioPoint",
    "CostSection",
    "CostBreakdown",
    "CostLineItem",
    "ScenarioTimeFrame",
]
