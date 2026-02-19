"""
Deterministic Auto-Tagger for VidhimurAI.

Analyses `title` and `headline` from kanoon_raw.json to automatically
generate enrichment tags (keywords, legal_issues, statutes_referenced,
outcome) — no LLM required.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.config import ISSUE_KEYWORDS, STOPWORDS

# ---------------------------------------------------------------------------
# Statute extraction patterns
# ---------------------------------------------------------------------------

# Matches: "Article 21", "Articles 14, 19, and 21", "Article 19(1)(g)"
_ARTICLE_RE = re.compile(
    r"Articles?\s+([\d]+(?:\s*\(\d+\)\s*(?:\([a-z]\))?)?(?:\s*,\s*\d+(?:\s*\(\d+\)\s*(?:\([a-z]\))?)?)*(?:\s*,?\s*and\s+\d+(?:\s*\(\d+\)\s*(?:\([a-z]\))?)?)?)",
    re.IGNORECASE,
)

# Matches: "Section 377", "Section 498A", "Sections 43 and 66"
_SECTION_RE = re.compile(
    r"Sections?\s+([\d]+[A-Z]?(?:\s*,\s*\d+[A-Z]?)*(?:\s*,?\s*and\s+\d+[A-Z]?)?)",
    re.IGNORECASE,
)

# Matches: "XXXXX Act, YYYY" or "XXXXX Act YYYY" — limited to reasonable length
_ACT_RE = re.compile(
    r"\b((?:(?:the|of|for)\s+)?[A-Z][a-zA-Z\s&()]{3,55}?(?:Act|Code|Rules|Procedure|Regulation)\s*,?\s*\d{4})",
)

# Known statute shorthands that the regex might miss
_STATUTE_KEYWORDS: dict[str, str] = {
    "ipc": "Indian Penal Code, 1860",
    "indian penal code": "Indian Penal Code, 1860",
    "crpc": "Code of Criminal Procedure, 1973",
    "cpc": "Code of Civil Procedure, 1908",
    "sarfaesi": "SARFAESI Act, 2002",
    "it act": "Information Technology Act, 2000",
    "posh": "Sexual Harassment of Women at Workplace Act, 2013",
    "consumer protection": "Consumer Protection Act, 2019",
    "consumer complaint": "Consumer Protection Act, 2019",
    "rera": "Real Estate (Regulation and Development) Act, 2016",
    "real estate developer": "Real Estate (Regulation and Development) Act, 2016",
    "ngt": "National Green Tribunal Act, 2010",
    "green tribunal": "National Green Tribunal Act, 2010",
    "passport": "Passport Act, 1967",
}

# Context-based statute inference: if the text mentions these topics,
# infer the relevant statutes even if they aren't explicitly named
_CONTEXT_STATUTES: dict[str, list[str]] = {
    "basic structure": [
        "Constitution of India, Article 368",
        "Constitution of India, Article 14",
        "Constitution of India, Article 19",
    ],
    "right to life": ["Constitution of India, Article 21"],
    "personal liberty": ["Constitution of India, Article 21"],
    "right to privacy": [
        "Constitution of India, Article 21",
        "Constitution of India, Article 14",
    ],
    "sexual harassment": [
        "Sexual Harassment of Women at Workplace Act, 2013",
        "Constitution of India, Article 14",
        "Constitution of India, Article 19(1)(g)",
        "Constitution of India, Article 21",
    ],
    "domestic violence": [
        "Protection of Women from Domestic Violence Act, 2005",
        "Indian Penal Code, Section 498A",
    ],
    "eviction": [
        "Transfer of Property Act, 1882",
    ],
    "rent control": [
        "Transfer of Property Act, 1882",
    ],
    "retrenchment": [
        "Industrial Disputes Act, 1947",
    ],
    "wrongful termination": [
        "Industrial Disputes Act, 1947",
    ],
    "industrial dispute": [
        "Industrial Disputes Act, 1947",
    ],
    "cheating": ["Indian Penal Code, Section 420"],
    "forgery": ["Indian Penal Code, Section 468"],
    "bail": ["Code of Criminal Procedure, Section 439"],
    "customs duty": [
        "Customs Act, 1962",
        "Customs Tariff Act, 1975",
    ],
    "customs assessment": [
        "Customs Act, 1962",
        "Customs Tariff Act, 1975",
    ],
    "imported goods": [
        "Customs Act, 1962",
        "Customs Tariff Act, 1975",
    ],
    "environmental": [
        "Environment Protection Act, 1986",
    ],
    "protected forest": [
        "Forest Conservation Act, 1980",
        "Environment Protection Act, 1986",
    ],
    "pollution clearance": [
        "Environment Protection Act, 1986",
    ],
    "factory operating": [
        "Environment Protection Act, 1986",
    ],
    "defective": [
        "Consumer Protection Act, 2019",
    ],
    "deferred possession": [
        "Consumer Protection Act, 2019",
        "Real Estate (Regulation and Development) Act, 2016",
    ],
    "delayed possession": [
        "Consumer Protection Act, 2019",
        "Real Estate (Regulation and Development) Act, 2016",
    ],
    "medical negligence": [
        "Consumer Protection Act, 2019",
    ],
    "data localization": [
        "Information Technology Act, 2000",
        "Digital Personal Data Protection Act, 2023",
    ],
    "habeas corpus": [
        "Constitution of India, Article 21",
        "Constitution of India, Article 22",
    ],
    "preventive detention": [
        "Constitution of India, Article 22",
        "Constitution of India, Article 21",
    ],
    "public safety act": [
        "Jammu & Kashmir Public Safety Act, 1978",
    ],
    "terrorism": [
        "Indian Penal Code, Section 120B",
        "Prevention of Terrorism Act, 2002",
        "Evidence Act, 1872",
    ],
    "conspiracy": [
        "Indian Penal Code, Section 120B",
    ],
    "homosexual": [
        "Indian Penal Code, Section 377",
        "Constitution of India, Article 14",
        "Constitution of India, Article 15",
        "Constitution of India, Article 21",
    ],
    "decriminalized": [
        "Indian Penal Code, Section 377",
    ],
    "widow pension": [
        "Constitution of India, Article 21",
        "Constitution of India, Article 226",
    ],
    "writ petition": [
        "Constitution of India, Article 226",
    ],
    "demolition": [
        "Constitution of India, Article 300A",
    ],
    "unauthorized construction": [
        "Constitution of India, Article 300A",
    ],
    "aadhaar": [
        "Aadhaar Act, 2016",
    ],
    "self-help group": [
        "Constitution of India, Article 14",
        "Constitution of India, Article 21",
    ],
    "micro-credit": [
        "Constitution of India, Article 14",
        "Constitution of India, Article 21",
    ],
    "divorce": [
        "Hindu Marriage Act, 1955",
    ],
    "cruelty and desertion": [
        "Hindu Marriage Act, 1955",
    ],
    "child custody": [
        "Guardians and Wards Act, 1890",
    ],
    "guardianship": [
        "Guardians and Wards Act, 1890",
    ],
    "hacking": [
        "Information Technology Act, 2000, Section 66",
    ],
    "unauthorized access": [
        "Information Technology Act, 2000, Section 43",
    ],
    "trade secrets": [
        "Indian Penal Code, Section 379",
    ],
}

# ---------------------------------------------------------------------------
# Outcome detection patterns
# ---------------------------------------------------------------------------
_OUTCOME_PATTERNS: list[tuple[str, str]] = [
    (r"set aside", "set aside"),
    (r"quashed", "quashed"),
    (r"upheld", "upheld"),
    (r"dismissed", "petition/appeal dismissed"),
    (r"allowed", "petition/appeal allowed"),
    (r"granted\s+bail", "bail granted"),
    (r"directed", "direction issued"),
    (r"awarded\s+(?:compensation|damages|Rs\.)", "compensation awarded"),
    (r"declared\s+(?:illegal|unlawful|unconstitutional)", "declared illegal/unconstitutional"),
    (r"struck\s+down", "struck down"),
    (r"reading\s+down", "read down"),
    (r"guidelines?\s+(?:laid\s+down|issued|established|formulated)", "guidelines issued"),
    (r"halted|stayed|restrained", "stay/injunction granted"),
    (r"reinstated?|reinstatement", "reinstatement ordered"),
    (r"closure\s+ordered", "closure ordered"),
]

# ---------------------------------------------------------------------------
# Legal-domain single-word vocabulary
# ---------------------------------------------------------------------------
_LEGAL_VOCAB: set[str] = set()
for _keywords in ISSUE_KEYWORDS.values():
    for kw in _keywords:
        _LEGAL_VOCAB.update(kw.lower().split())

_LEGAL_VOCAB.update({
    "constitution", "constitutional", "fundamental", "writ", "petition",
    "appeal", "plaintiff", "defendant", "respondent", "petitioner",
    "judgement", "judgment", "order", "decree", "injunction",
    "negligence", "liability", "damages", "compensation", "penalty",
    "conviction", "acquittal", "sentence", "bail", "arrest",
    "eviction", "tenant", "landlord", "lease", "possession",
    "divorce", "custody", "maintenance", "alimony", "guardianship",
    "pollution", "environment", "forest", "wildlife", "ecological",
    "privacy", "data", "cyber", "hacking", "digital", "surveillance",
    "harassment", "discrimination", "equality", "liberty", "freedom",
    "conspiracy", "terrorism", "detention", "habeas", "corpus",
    "retrenchment", "termination", "industrial", "wages", "employment",
    "consumer", "deficiency", "defective", "warranty", "refund",
    "property", "land", "construction", "demolition", "encroachment",
    "medical", "hospital", "patient", "doctor",
    "customs", "import", "tariff", "assessment", "excise",
    "bank", "loan", "secured", "credit", "mortgage",
    "pension", "welfare", "widow", "social", "scheme",
    "homosexuality", "lgbt", "lgbtq", "decriminalized",
    "women", "gender", "pil", "public", "interest",
    # Extra coverage from comparison gaps
    "criminal", "cruelty", "desertion", "matrimonial", "family",
    "factory", "emission", "waste", "ecological",
    "goods", "product", "service", "flat", "commercial",
    "trade", "secrets", "unauthorized", "access",
    "municipal", "trespass", "encroachment",
    "worker", "employer", "workplace", "dismissal",
    "forgery", "fraud", "speedy", "trial",
    "amendment", "doctrine",
    "protection", "violence", "economic", "abuse",
})

# ---------------------------------------------------------------------------
# Multi-word phrases to look for in text
# ---------------------------------------------------------------------------
_PHRASES: list[str] = [
    "basic structure", "fundamental rights", "right to life",
    "personal liberty", "due process", "natural justice",
    "sexual harassment", "domestic violence", "data protection",
    "unfair trade", "public interest", "habeas corpus",
    "preventive detention", "death sentence", "medical negligence",
    "wrongful termination", "consumer protection", "data localization",
    "financial inclusion", "right to privacy", "right to equality",
    "free speech", "speedy trial", "authorized construction",
    "rent control", "industrial dispute", "product liability",
    "workplace harassment", "amendment power", "basic structure doctrine",
    "women rights", "economic abuse", "protection order",
    "trade secrets", "unauthorized access", "secured assets",
    "delayed possession", "writ petition",
]


@dataclass
class AutoTags:
    """Generated tags for a single case."""
    keywords: list[str] = field(default_factory=list)
    outcome: str = ""
    legal_issues: list[str] = field(default_factory=list)
    statutes_referenced: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "keywords": self.keywords,
            "outcome": self.outcome,
            "legal_issues": self.legal_issues,
            "statutes_referenced": self.statutes_referenced,
        }


def generate_tags(
    title: str,
    headline: str,
    docsource: str,
    cite_titles: list[str] | None = None,
) -> AutoTags:
    """Generate enrichment tags from raw case data."""
    text = f"{title} {headline}"
    full_text = f"{text} {' '.join(cite_titles or [])}"

    tags = AutoTags()
    tags.keywords = _extract_keywords(text, docsource)
    tags.outcome = _infer_outcome(headline)
    tags.legal_issues = _detect_legal_issues(full_text)
    tags.statutes_referenced = _extract_statutes(full_text)

    return tags


# ---------------------------------------------------------------------------
# Internal extraction functions
# ---------------------------------------------------------------------------

def _extract_keywords(text: str, docsource: str = "") -> list[str]:
    """Extract domain-relevant keywords from text using vocabulary matching."""
    tokens = re.findall(r"[a-zA-Z]+", text.lower())

    seen: set[str] = set()
    keywords: list[str] = []

    # Single-word matches
    for token in tokens:
        if token in STOPWORDS or len(token) <= 2 or token in seen:
            continue
        if token in _LEGAL_VOCAB:
            keywords.append(token)
            seen.add(token)

    # Multi-word phrase matches
    text_lower = text.lower()
    for phrase in _PHRASES:
        if phrase in text_lower and phrase not in seen:
            keywords.append(phrase)
            seen.add(phrase)

    return keywords[:12]


def _infer_outcome(headline: str) -> str:
    """Infer case outcome from headline text using pattern matching."""
    for pattern, label in _OUTCOME_PATTERNS:
        if re.search(pattern, headline, re.IGNORECASE):
            sentences = re.split(r"[.;]", headline)
            for sent in sentences:
                if re.search(pattern, sent, re.IGNORECASE):
                    return sent.strip().rstrip(".")
            return label

    # Fallback: last sentence
    sentences = [s.strip() for s in headline.rstrip(".").split(".") if s.strip()]
    if len(sentences) > 1:
        return sentences[-1].rstrip(".")
    return "Outcome not determinable from headline"


def _detect_legal_issues(text: str) -> list[str]:
    """Detect legal issues by matching against ISSUE_KEYWORDS."""
    text_lower = text.lower()
    issues: list[str] = []

    for category, keywords in ISSUE_KEYWORDS.items():
        match_count = sum(1 for kw in keywords if kw in text_lower)
        if match_count >= 2:
            issues.append(category)

    # Sub-issue detection
    _SUB_ISSUES = {
        "basic structure doctrine": "Basic structure doctrine",
        "basic structure": "Basic structure doctrine",
        "right to life": "Right to life and personal liberty",
        "right to privacy": "Right to privacy",
        "right to equality": "Right to equality",
        "sexual harassment": "Sexual harassment at workplace",
        "domestic violence": "Domestic violence",
        "medical negligence": "Medical negligence",
        "wrongful termination": "Wrongful termination",
        "preventive detention": "Preventive detention",
        "environmental clearance": "Environmental clearance",
        "data protection": "Data protection",
        "consumer complaint": "Consumer rights dispute",
        "bail application": "Bail jurisprudence",
        "eviction": "Tenant eviction",
        "divorce": "Matrimonial dispute",
        "custody": "Child custody",
        "customs duty": "Customs/tariff dispute",
        "customs assessment": "Customs/tariff dispute",
        "imported goods": "Customs/tariff dispute",
        "retrenchment": "Industrial labor dispute",
        "pension": "Social welfare / pension",
        "widow pension": "Social welfare / pension rights",
        "habeas corpus": "Habeas corpus / personal liberty",
        "unauthorized construction": "Property / construction dispute",
        "demolition": "Property / construction dispute",
        "cheating and forgery": "Criminal fraud",
        "cheating": "Criminal fraud",
        "data localization": "Data governance",
        "micro-credit": "Financial inclusion",
        "self-help group": "Financial inclusion",
        "homosexual": "LGBTQ+ rights",
        "section 377": "Decriminalization of homosexuality",
        "decriminalized": "LGBTQ+ rights",
        "protection order": "Domestic violence / protection orders",
        "trade secrets": "Trade secret misappropriation",
        "hacking": "Cyber crime",
        "unauthorized access": "Cyber crime",
        "terrorism": "Terrorism / national security",
        "conspiracy": "Criminal conspiracy",
        "defective": "Consumer - defective product",
        "delayed possession": "Consumer - delayed delivery",
        "medical negligence": "Medical negligence / standard of care",
        "pollution clearance": "Environmental violation",
        "forest": "Forest conservation",
    }

    for pattern, issue in _SUB_ISSUES.items():
        if pattern in text_lower and issue not in issues:
            issues.append(issue)

    return issues[:5]


def _extract_statutes(text: str) -> list[str]:
    """Extract statute references using regex, shorthands, and context inference."""
    statutes: list[str] = []
    seen: set[str] = set()

    # 1. Article regex → "Constitution of India, Article XX"
    for match in _ARTICLE_RE.finditer(text):
        articles_str = match.group(1)
        individual = re.split(r"\s*,\s*|\s+and\s+", articles_str)
        for art in individual:
            art = art.strip()
            # Clean up: remove leading "and " that slips through
            if art.lower().startswith("and "):
                art = art[4:].strip()
            if art and art[0].isdigit():
                ref = f"Constitution of India, Article {art}"
                if ref not in seen:
                    statutes.append(ref)
                    seen.add(ref)

    # 2. Full Act names with years
    for match in _ACT_RE.finditer(text):
        act = match.group(1).strip()
        if act not in seen:
            statutes.append(act)
            seen.add(act)

    # 3. Shorthand statute references
    text_lower = text.lower()
    for shorthand, full_name in _STATUTE_KEYWORDS.items():
        if shorthand in text_lower and full_name not in seen:
            statutes.append(full_name)
            seen.add(full_name)

    # 4. Context-based inference — the key improvement!
    # If the text discusses a topic, infer the relevant statutes
    for context_phrase, inferred_statutes in _CONTEXT_STATUTES.items():
        if context_phrase in text_lower:
            for statute in inferred_statutes:
                if statute not in seen:
                    statutes.append(statute)
                    seen.add(statute)

    # 5. Standalone section references
    for match in _SECTION_RE.finditer(text):
        sections_str = match.group(1)
        individual = re.split(r"\s*,\s*|\s+and\s+", sections_str)
        for sec in individual:
            sec = sec.strip()
            if sec:
                ref = f"Section {sec}"
                if ref not in seen:
                    statutes.append(ref)
                    seen.add(ref)

    return statutes
