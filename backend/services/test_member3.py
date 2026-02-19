import os
from .draft_generator import DraftGenerator
from .simplifier import Simplifier
from .translator import Translator
from .research_ai_enhancer import ResearchAIEnhancer
import sys
import io

# Fix for Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ensure API key exists
if not os.getenv("GROQ_API_KEY"):
    print("GROQ_API_KEY not found in environment.")

# -------------------------------
# MOCK EMPOWER DATA
# -------------------------------

empower_data = {
    "issue_type": "Tenant Deposit Dispute",
    "relevant_sections": ["Section 108 Transfer of Property Act"],
    "precedents": [
        {
            "case_name": "ABC vs XYZ",
            "court": "High Court",
            "year": 2020,
            "citation_count": 12,
            "strength_score": 18.5,
            "summary": "Court held landlord must return deposit unless damage proven."
        }
    ],
    "legal_strength": "Moderate",
    "action_steps": ["Send legal notice", "File civil suit"]
}

print("\n====================")
print("Testing DraftGenerator")
print("====================")

dg = DraftGenerator()
print(dg.generate_draft(empower_data))

print("\n====================")
print("Testing Simplifier")
print("====================")

simp = Simplifier()
print(simp.simplify("The Court held that bail requires strict compliance with statutory conditions."))

print("\n====================")
print("Testing Translator")
print("====================")

import json
translator = Translator()
result = translator.translate("This is a legal complaint draft.", "Hindi")
print(json.dumps(result, ensure_ascii=True))

print("\n====================")
print("Testing ResearchAIEnhancer")
print("====================")

research_data = {
    "total_cases": 1,
    "top_cases": [
        {
            "case_name": "ABC vs XYZ",
            "court": "High Court",
            "year": 2020,
            "citation_count": 12,
            "strength_score": 18.5,
            "summary": "Court held landlord must return deposit unless damage proven."
        }
    ],
    "most_influential_case": {
        "case_name": "ABC vs XYZ",
        "court": "High Court",
        "year": 2020,
        "citation_count": 12,
        "strength_score": 18.5,
        "summary": "Court held landlord must return deposit unless damage proven."
    }
}

enhancer = ResearchAIEnhancer()
print(enhancer.enhance_research(research_data))
