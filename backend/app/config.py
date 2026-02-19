"""Application configuration and constants."""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CASES_FILE = DATA_DIR / "cases.json"
KANOON_CASES_FILE = DATA_DIR / "kanoon_cases.json"    # Combined (legacy)
KANOON_RAW_FILE = DATA_DIR / "kanoon_raw.json"         # Pure API data
VIDHIMUR_TAGS_FILE = DATA_DIR / "vidhimur_tags.json"   # Our enrichment tags

# ---------------------------------------------------------------------------
# Court weights used by the ranking engine
# ---------------------------------------------------------------------------
COURT_WEIGHTS: dict[str, int] = {
    "Supreme Court": 10,
    "High Court": 7,
    "District Court": 4,
}

# ---------------------------------------------------------------------------
# Recency boost parameters
# ---------------------------------------------------------------------------
CURRENT_YEAR = 2026
RECENCY_MAX_BOOST = 5.0
RECENCY_DECAY_RATE = 0.25          # points lost per year of age

# ---------------------------------------------------------------------------
# Legal issue → category mapping (deterministic classification)
# ---------------------------------------------------------------------------
ISSUE_KEYWORDS: dict[str, list[str]] = {
    "Constitutional Law": [
        "fundamental rights", "constitution", "article 14", "article 19",
        "article 21", "right to equality", "free speech", "liberty",
        "writ petition", "constitutional", "directive principles",
    ],
    "Criminal Law": [
        "murder", "theft", "assault", "criminal", "ipc", "crpc", "bail",
        "fir", "arrest", "imprisonment", "culpable homicide", "robbery",
        "kidnapping", "fraud", "cheating", "forgery", "dowry",
    ],
    "Property Law": [
        "property", "land", "tenant", "landlord", "eviction", "rent",
        "possession", "title", "deed", "encroachment", "trespass",
        "security deposit", "lease",
    ],
    "Consumer Protection": [
        "consumer", "deficiency", "service", "product", "complaint",
        "unfair trade", "compensation", "defective", "goods",
        "consumer protection act",
    ],
    "Labor Law": [
        "employment", "worker", "wages", "termination", "industrial",
        "labour", "labor", "retrenchment", "gratuity", "provident fund",
        "workplace", "dismissal", "employer",
    ],
    "Cyber Law": [
        "cyber", "data", "privacy", "online", "internet", "hacking",
        "information technology", "it act", "digital", "electronic",
        "social media",
    ],
    "Environmental Law": [
        "environment", "pollution", "forest", "wildlife", "ngt",
        "green tribunal", "waste", "emission", "ecological", "climate",
    ],
    "Family Law": [
        "divorce", "custody", "alimony", "maintenance", "marriage",
        "domestic violence", "child", "adoption", "guardianship",
        "matrimonial",
    ],
}

# ---------------------------------------------------------------------------
# Action roadmap templates (keyed by legal area)
# ---------------------------------------------------------------------------
ACTION_ROADMAPS: dict[str, list[dict[str, str]]] = {
    "Constitutional Law": [
        {"step": "1", "title": "Document the Violation", "description": "Collect evidence of the fundamental rights violation."},
        {"step": "2", "title": "Consult a Constitutional Lawyer", "description": "Seek legal counsel specializing in constitutional matters."},
        {"step": "3", "title": "File a Writ Petition", "description": "Approach the High Court or Supreme Court under Article 226 or Article 32."},
        {"step": "4", "title": "Follow Up on Hearings", "description": "Attend scheduled court dates and comply with directions."},
    ],
    "Criminal Law": [
        {"step": "1", "title": "File an FIR", "description": "Report the crime at the nearest police station."},
        {"step": "2", "title": "Collect Evidence", "description": "Preserve all physical and digital evidence related to the crime."},
        {"step": "3", "title": "Engage a Criminal Lawyer", "description": "Hire an advocate experienced in criminal proceedings."},
        {"step": "4", "title": "Attend Court Proceedings", "description": "Cooperate with the investigation and attend all hearings."},
    ],
    "Property Law": [
        {"step": "1", "title": "Gather Property Documents", "description": "Collect title deeds, sale agreements, and registration papers."},
        {"step": "2", "title": "Serve a Legal Notice", "description": "Send a formal notice to the opposing party demanding resolution."},
        {"step": "3", "title": "Attempt Mediation", "description": "Try to resolve the dispute through an authorized mediator."},
        {"step": "4", "title": "File a Civil Suit", "description": "Approach the appropriate civil court for relief."},
    ],
    "Consumer Protection": [
        {"step": "1", "title": "Send a Written Complaint", "description": "Send a formal complaint to the service provider or manufacturer."},
        {"step": "2", "title": "File with Consumer Forum", "description": "Lodge a complaint with the District Consumer Disputes Redressal Forum."},
        {"step": "3", "title": "Attach Evidence", "description": "Include bills, receipts, warranties, and correspondence."},
        {"step": "4", "title": "Attend Hearings", "description": "Follow up on the complaint and attend scheduled hearings."},
    ],
    "Labor Law": [
        {"step": "1", "title": "Document Workplace Issue", "description": "Keep records of employment terms, communications, and violations."},
        {"step": "2", "title": "File Complaint with Labor Commissioner", "description": "Approach the labor commissioner or inspector in your jurisdiction."},
        {"step": "3", "title": "Seek Conciliation", "description": "Request conciliation through the industrial disputes mechanism."},
        {"step": "4", "title": "Approach the Labor Court", "description": "If unresolved, file a case before the Labor Court or Industrial Tribunal."},
    ],
    "Cyber Law": [
        {"step": "1", "title": "Report the Incident", "description": "File a complaint on the National Cyber Crime Reporting Portal."},
        {"step": "2", "title": "Preserve Digital Evidence", "description": "Take screenshots, save URLs, and keep communication records."},
        {"step": "3", "title": "File an FIR", "description": "Lodge an FIR at the nearest cyber crime police station."},
        {"step": "4", "title": "Engage a Cyber Law Expert", "description": "Consult an advocate skilled in IT Act and data privacy cases."},
    ],
    "Environmental Law": [
        {"step": "1", "title": "Document the Violation", "description": "Photograph or record evidence of the environmental damage."},
        {"step": "2", "title": "Complain to Pollution Control Board", "description": "File a complaint with the State or Central Pollution Control Board."},
        {"step": "3", "title": "Approach the NGT", "description": "File an application before the National Green Tribunal."},
        {"step": "4", "title": "Follow Up", "description": "Monitor compliance with any orders issued."},
    ],
    "Family Law": [
        {"step": "1", "title": "Document Your Situation", "description": "Gather marriage certificates, communications, and evidence of issues."},
        {"step": "2", "title": "Consult a Family Lawyer", "description": "Seek advice from an advocate specializing in family law."},
        {"step": "3", "title": "Attempt Mediation", "description": "Try to resolve disputes through family court counseling or mediation."},
        {"step": "4", "title": "File the Appropriate Petition", "description": "Approach the Family Court with the relevant application."},
    ],
}

# Default roadmap fallback
DEFAULT_ROADMAP: list[dict[str, str]] = [
    {"step": "1", "title": "Understand Your Rights", "description": "Research the legal provisions applicable to your situation."},
    {"step": "2", "title": "Consult a Lawyer", "description": "Seek professional legal advice from a qualified advocate."},
    {"step": "3", "title": "Send a Legal Notice", "description": "Issue a formal notice to the concerned parties."},
    {"step": "4", "title": "File in Court", "description": "Approach the appropriate court or tribunal for relief."},
]
