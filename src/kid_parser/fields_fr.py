"""Regex field extractors for French-language PRIIPs KIDs ("Document
d'informations clés").

Same contract as kid_parser.fields: every function takes the normalized
("flat") text and returns plain values. Anchored on the headings the French
translation of the PRIIPs RTS mandates ("Nous avons classé ce produit dans
la classe de risque N sur 7", "Coûts totaux", "Incidence des coûts", ...).
Verified against 6 templates: Crédit Mutuel AM (OPCVM and FIA), Robeco,
FFG/Waystone, La Française, Eiffel IG.

French KIDs mix three number formats depending on the issuer -- "10 000 €",
"10.000 EUR" (dot thousands, comma decimals) and "10,000 EUR" / "6.9%"
(English-style, Robeco) -- so amounts and percentages have their own
parsers below rather than the English MONEY pattern.
"""

import re
from datetime import date

from .text import clean, find

CURRENCY = r"(€|EUR|USD|GBP|CHF)"
# A thousands group is exactly 3 digits after a space/dot/comma separator;
# anything else after a separator is a decimal part.
AMOUNT = r"(-?\d{1,3}(?:[ .,]\d{3})*(?:[.,]\d{1,2})?|-?\d+(?:[.,]\d+)?)"
MONEY_FR = AMOUNT + r"\s?" + CURRENCY
PCT_FR = r"(-?\s?\d+(?:[.,]\d+)?)\s?%"

# Scenario rows are labelled "Tensions" / "Scénario de tensions" etc. and
# are always followed by the table's own "Si vous sortez"/"Ce que vous
# pourriez obtenir" text -- that lookahead keeps prose mentions ("Le
# scénario de tensions montre ...") from matching. \b keeps "favorable"
# from matching inside "défavorable" ("é" is a word character).
SCENARIO_LABELS = [
    ("stress", r"(?:Sc[ée]nario de )?\b[Tt]ensions"),
    ("unfavourable", r"(?:Sc[ée]nario )?\b[Dd]éfavorable"),
    ("moderate", r"(?:Sc[ée]nario )?\b[Ii]ntermédiaire"),
    ("favourable", r"(?:Sc[ée]nario )?\b[Ff]avorable"),
]
SCENARIO_ROW_START = r"\s*:?\s*(?=Si vous sortez|Ce que vous pourriez)"
SCENARIO_END = r"Ce type de sc[ée]nario|Sc[ée]nario défavorable :|Que se passe|QUE SE PASSE|Ce tableau"

BOILERPLATE = [
    r"Co[ûu]ts (?:ponctuels|uniques) à l'entrée ou à la sortie\s*",
    r"Co[ûu]ts récurrents\s*\[?prélevés chaque année\]?\s*",
    r"Co[ûu]ts (?:accessoires|récurrents) prélevés sous certaines conditions\s*",
    r"Si vous sortez après 1 [Aa]n\s*",
]

# Case-sensitive: the table labels are capitalized, the surrounding prose
# ("Aucun coût d'entrée n'est appliqué") is not.
COST_CATEGORIES = [
    ("entry_costs", r"Co[ûu]ts? d'entrée"),
    ("exit_costs", r"(?:Co[ûu]ts?|Frais) de sortie"),
    ("management_fees", r"Frais de gestion et autres frais administratifs?\s*et d'exploitation"),
    ("transaction_costs", r"(?:Co[ûu]ts|Frais) de transaction"),
    ("performance_fees", r"Commissions liées aux (?:résultats|performances)(?: et commission d'intéressement)?"),
]


def parse_amount(token):
    """French/English-agnostic amount: "2 030", "10.000", "3,100" are
    thousands-grouped integers; "1,90" / "6.9" are decimals."""
    s = token.replace(" ", "")
    negative = s.startswith("-")
    s = s.lstrip("-")
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", s):
        s = s.replace(".", "").replace(",", "")
    else:
        s = s.replace(",", ".")
    value = float(s)
    return -value if negative else value


def parse_pct(token):
    return float(token.replace(" ", "").replace(",", "."))


def _currency(symbol):
    return "EUR" if symbol == "€" else symbol


def _money(amount, symbol):
    return {"value": parse_amount(amount), "currency": _currency(symbol)}


def extract_isin(flat, filename_isin):
    if filename_isin:
        return filename_isin
    m = re.search(r"ISIN[^:A-Z]{0,20}:?\s*([A-Z]{2}[A-Z0-9]{9}\d)", flat)
    if m:
        return m.group(1)
    m = re.search(r"\b([A-Z]{2}[A-Z0-9]{9}\d)\b", flat)
    return m.group(1) if m else None


def extract_production_date(flat):
    m = re.search(r"Date de (?:production|publication)[^\d]{0,60}?(\d{1,2})/(\d{1,2})/(\d{4})", flat)
    if not m:
        return None
    day, month, year = (int(g) for g in m.groups())
    return date(year, month, day).isoformat()


def extract_product_and_class(flat):
    # Eiffel-style labelled field
    m = re.search(r"Nom du [Pp]roduit\s*:\s*(.+?)\s*(?:Initiateur|Code ISIN)", flat)
    if m:
        name = clean(m.group(1))
        pm = re.match(r"(.+?)\s*-\s*(Part\s+\S+)$", name)
        return (clean(pm.group(1)), clean(pm.group(2))) if pm else (name, None)
    # FFG-style: "Produit <name> un compartiment de <umbrella> classe <class> - <ISIN>"
    m = re.search(r"Produit\s+(.+?)\s+un compartiment de .+? classe (.+?)\s*-\s*[A-Z]{2}[A-Z0-9]{9}\d", flat)
    if m:
        return clean(m.group(1)), clean(m.group(2))
    # Robeco / La Française: "Produit : <name> (<ISIN>)" or "Produit : <name> Code ISIN"
    m = re.search(r"Produit\s*:\s*(.+?)\s*(?:\([A-Z]{2}[A-Z0-9]{9}\d\)|Code ISIN)", flat)
    if m:
        return clean(m.group(1)), None
    # Crédit Mutuel AM: the title directly follows the document heading
    m = re.search(r"Document d'informations clés\s+(.+?)\s+OBJECTIF\b", flat)
    if m:
        cm = re.search(r"Code ISIN (Part \S+)\s*:", flat)
        return clean(m.group(1)), clean(cm.group(1)) if cm else None
    return None, None


def extract_issuer(flat):
    m = re.search(
        r"Initiateur\s*(?:/ Société de gestion)?\s*(?:Nom)?\s*:\s*(.+?)"
        r"(?:\.\s|\s+(?:Code ISIN|Coordonnées|En quoi|L'autorité|Site internet))",
        flat,
    )
    if m:
        return clean(m.group(1))
    m = re.search(r"chargée du contrôle de (.+?) en ce qui concerne", flat)
    return clean(m.group(1)) if m else None


def extract_website(flat):
    m = re.search(r"\b(?:https?://)?www\.[^\s,;)]+", flat)
    return clean(m.group(0).rstrip(".")) if m else None


def extract_phone(flat):
    m = re.search(
        r"(?:Appelez le(?: n°)?|Téléphonez au|appelez le|par téléphone au)\s*([+0-9][0-9 ()]{6,}\d)",
        flat,
    )
    return clean(m.group(1)) if m else None


def extract_email(flat):
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", flat)
    return clean(m.group(0).rstrip(".")) if m else None


def extract_type(flat):
    return find(
        r"(?:TYPE DE PRODUIT D'INVESTISSEMENT|Type(?: de produit)?\s*:?)\s+(.{5,400}?)\s*"
        r"(?=DUREE DE VIE|Durée|OBJECTIFS|Objectifs|Ce document d'informations|Échéance)",
        flat,
        flags=0,
    )


def extract_term(flat):
    return find(r"(?:DUREE DE VIE DE L'OPC|Durée\s*:?)\s+(.{5,400}?)\s*(?=OBJECTIFS|Objectifs)", flat, flags=0)


def extract_objective(flat):
    return find(
        r"(?:OBJECTIFS|Objectifs\s*:?)\s+(.*?)\s*(?=INVESTISSEURS DE DETAIL VISES|Investisseurs de détail visés)",
        flat,
        flags=0,
    )


def extract_custodian(flat):
    m = re.search(
        r"(?:Nom du dépositaire|[Dd]épositaire(?: de la SICAV| du [Ff]onds| du compartiment)?)"
        r"\s*(?:est|:)\s*(.+?)\s*(?=\s(?:Le|La|Les|Revenus|Autres|Pour|Ce|Cette|Des)\s)",
        flat,
    )
    return clean(m.group(1)) if m else None


def extract_index(flat):
    m = re.search(r"indice de référence\s*(?:est\s*)?:?\s*(?:l[ea]\s+)?([A-Z][^.(,;]+?)\s*(?:\(|\.|,|;)", flat)
    return clean(m.group(1)) if m else None


def extract_currency(flat):
    m = re.search(r"devise de (?:la classe d'actions|la part|référence)[^.]{0,30}?\b([A-Z]{3})\b", flat)
    if m:
        return m.group(1)
    example = extract_example_investment(flat)
    return example["currency"] if example else None


def extract_sfdr_article(flat):
    m = re.search(r"[Aa]rticle\s*(6|8|9)\b\s*(?:du|de la)\s*(?:[Rr]èglement|SFDR)(?!\s*ELTIF)", flat)
    return f"Article {m.group(1)}" if m else None


def extract_distribution_policy(flat):
    if re.search(
        r"(?:distribuables|dividendes|résultats)\s*:\s*Distribution|(?:parts?|classe|actions?) de distribution",
        flat,
    ):
        return "Distributing"
    if re.search(r"capitalis", flat, re.I):
        return "Accumulating"
    return None


def extract_is_ucits(flat):
    head = flat[:4000]
    if re.search(r"\bFIA\b|FIVG|ELTIF|Fonds Commun de Placement à Risques|\bFCPR\b|\bFCPI\b", head):
        return False
    if re.search(r"OPCVM|UCITS|valeurs mobilières|Partie I de la loi", head):
        return True
    return None


def extract_intended_for(flat):
    body = find(
        r"(?:INVESTISSEURS DE DETAIL VISES|Investisseurs de détail visés)\s*:?\s*(.*?)"
        r"(?=INFORMATIONS PRATIQUES|Informations pratiques|Autres informations|Quels sont les risques|QUELS SONT)",
        flat,
        flags=0,
    ) or ""
    is_retail = bool(re.search(r"investisseurs de détail|particuliers|tous (?:les )?(?:types d')?investisseurs|connaissance", body, re.I))
    is_professional = bool(re.search(r"professionnels|institutionnels|contreparties éligibles", body, re.I))
    if is_retail and is_professional:
        return "Retail/Professional"
    if is_retail:
        return "Retail"
    if is_professional:
        return "Professional"
    return None


def extract_sri(flat):
    m = re.search(r"(?:classe de risque|niveau|catégorie)\s*(\d)\s*sur\s*7", flat)
    return int(m.group(1)) if m else None


def extract_rhp_years(flat):
    m = re.search(
        r"(?:[Pp]ériode (?:de détention|d'investissement)|[Dd]urée de placement) recommandée"
        r"\s*(?:\(RHP\))?\s*:?\s*(?:supérieure? à\s*)?(\d+)\s*[Aa]ns?\b",
        flat,
    )
    return int(m.group(1)) if m else None


def extract_example_investment(flat):
    m = re.search(r"(?:Exemple d'investissement|Investissement)\s*:?\s*" + MONEY_FR, flat)
    return _money(m.group(1), m.group(2)) if m else None


def extract_scenarios(flat):
    starts = []
    for key, label in SCENARIO_LABELS:
        m = re.search(label + SCENARIO_ROW_START, flat)
        starts.append((m.start(), m.end(), key) if m else None)
    found = sorted(s for s in starts if s)

    scenarios = {key: None for key, _ in SCENARIO_LABELS}
    for i, (_, end, key) in enumerate(found):
        stop = found[i + 1][0] if i + 1 < len(found) else len(flat)
        chunk = flat[end:stop]
        em = re.search(SCENARIO_END, chunk)
        if em:
            chunk = chunk[:em.start()]
        # drop the "Si vous sortez après N an(s)" headers, whose year
        # counts would otherwise read as amounts
        chunk = re.sub(r"Si vous sortez après \d+ [Aa]ns?(?: \(période de détention recommandée\))?", "", chunk)
        amounts = re.findall(MONEY_FR, chunk)
        pcts = re.findall(PCT_FR, chunk)
        if not amounts:
            continue

        def point(amount, pct):
            return {**_money(*amount), "return_pct": parse_pct(pct) if pct is not None else None}

        scenarios[key] = {
            "1y": point(amounts[0], pcts[0] if pcts else None),
            "rhp": point(amounts[-1], pcts[-1] if pcts else None),
        }
    return scenarios


def extract_total_costs(flat):
    m = re.search(
        r"Co[ûu]ts? totaux?\s+(.*?)Incidence des co[ûu]ts(?: annuels)?\s*\(?\*?\)?\s*(.*?)(?=\(?\*|Elle montre|Cela illustre|Ceci illustre)",
        flat,
    ) or re.search(r"Co[ûu]t total\s+(.*?)Incidence des co[ûu]ts(?: annuels)?\s*\(?\*?\)?\s*(.*?)(?=\(?\*|Elle montre|Cela illustre|Ceci illustre)", flat)
    if not m:
        return None, None, None, None
    amounts = re.findall(MONEY_FR, m.group(1))
    pcts = re.findall(PCT_FR, m.group(2))
    if not amounts or not pcts:
        return None, None, None, None
    return (
        _money(*amounts[0]),
        _money(*amounts[-1]),
        parse_pct(pcts[0]),
        parse_pct(pcts[-1]),
    )


def extract_cost_example_investment(flat):
    m = re.search(r"(?:Investissement|Exemple d'investissement)\s*:?\s*" + MONEY_FR + r"\s*Si vous sortez", flat)
    if m:
        return _money(m.group(1), m.group(2))
    m = re.search(AMOUNT + r"\s*(euros|EUR|€)\s*(?:sont|est)\s*investis?", flat)
    if m:
        return {"value": parse_amount(m.group(1)), "currency": "EUR"}
    # Robeco: currency code before the amount ("EUR 10,000 est investi")
    m = re.search(r"\b(EUR|USD|GBP|CHF)\s" + AMOUNT + r"\s*(?:sont|est)\s*investis?", flat)
    if m:
        return {"value": parse_amount(m.group(2)), "currency": m.group(1)}
    return None


def extract_cost_breakdown(flat):
    m = re.search(r"COMPOSITION DES CO[UÛ]TS|Composition des co[ûu]ts", flat)
    section = flat[m.end():] if m else flat
    em = re.search(r"COMBIEN DE TEMPS|Combien de temps", section)
    if em:
        section = section[:em.start()]

    boundaries = []
    for key, label in COST_CATEGORIES:
        bm = re.search(label, section)
        if bm:
            boundaries.append((bm.start(), bm.end(), key))
    boundaries.sort()

    breakdown = {key: {"description": None, "pct": None, "amount": None} for key, _ in COST_CATEGORIES}
    for i, (_, end, key) in enumerate(boundaries):
        chunk_end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(section)
        chunk = section[end:chunk_end]
        for boilerplate in BOILERPLATE:
            chunk = re.sub(boilerplate, "", chunk)
        chunk = re.sub(r"\s+", " ", chunk).strip()

        pct_m = re.search(PCT_FR, chunk)
        amount_ms = list(re.finditer(MONEY_FR, chunk))
        amount = _money(amount_ms[-1].group(1), amount_ms[-1].group(2)) if amount_ms else None
        description = chunk[:amount_ms[-1].start()] if amount_ms else chunk
        description = re.sub(r"\b[Jj]usqu'à\s*$", "", description.strip())

        breakdown[key] = {
            "description": clean(description),
            "pct": parse_pct(pct_m.group(1)) if pct_m else None,
            "amount": amount,
        }

    performance_desc = breakdown["performance_fees"]["description"] or ""
    performance_fees_yn = (
        not bool(re.search(r"\bAucune commission|ne comporte pas de commission|pas de commission", performance_desc, re.I))
        if performance_desc
        else None
    )
    return breakdown, performance_fees_yn
