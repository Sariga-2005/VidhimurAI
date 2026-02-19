import json
import logging
from typing import Dict, Any
from .llm_service import LLMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoadmapGenerator:
    """
    Generates a structured legal action roadmap based on structured EMPOWER output.
    """

    def __init__(self):
        self.llm_service = LLMService()

    @staticmethod
    def _compress_roadmap(data: Dict[str, Any]) -> Dict[str, Any]:
        """Hard-truncate every bullet to max 12 words."""
        if "roadmap" not in data or not isinstance(data["roadmap"], dict):
            return data
        roadmap = data["roadmap"]
        for key, val in roadmap.items():
            if isinstance(val, list):
                roadmap[key] = [
                    " ".join(item.split()[:12]).rstrip(".,;") + "."
                    if len(item.split()) > 12 else item
                    for item in val[:3]  # also cap at 3 items
                ]
        return data

    def generate_roadmap(self, structured_analysis: Dict[str, Any]) -> Dict[str, Any]:

        required_keys = [
            "issue_type",
            "relevant_sections",
            "legal_strength",
            "action_steps"
        ]

        if not all(k in structured_analysis for k in required_keys):
            return {"roadmap": ["Invalid structured analysis data."]}

        system_role = (
            "You are a legal roadmap engine. HARD RULES: "
            "1. ONLY use statutes listed in 'Laws' below. Do NOT invent or add any other statute. "
            "2. issue_type is a HARD DOMAIN BOUNDARY. Do NOT cross into unrelated legal domains. "
            "3. Max 2 bullets per section. Max 10 words per bullet. "
            "4. Start each bullet with an action verb. "
            "5. No adjectives, no qualifiers, no explanations. "
            "6. FORBIDDEN words: consider, explore, potential, relevant, appropriate, ensure, necessary, applicable. "
            "7. If issue_type is 'Motor Vehicle Accident', do NOT mention Consumer Protection, Environment, or Property law. "
            "8. If issue_type is 'Consumer Protection', do NOT mention Motor Vehicles Act, criminal law, or property law. "
            "9. Mirror the action_steps provided. Do NOT invent new strategies."
        )

        laws = ", ".join(structured_analysis["relevant_sections"])
        issue = structured_analysis["issue_type"]
        steps = json.dumps(structured_analysis["action_steps"])

        prompt = f"""
Issue: {issue}
Laws: {laws}
Strength: {structured_analysis["legal_strength"]}
Action Steps Already Identified: {steps}

DOMAIN BOUNDARY: You may ONLY reference "{issue}" domain and "{laws}". Nothing else.

Generate roadmap. Max 2 bullets per array. Max 10 words per bullet.

ONLY output JSON:
{{
  "roadmap": {{
    "immediate_actions": [],
    "evidence_checklist": [],
    "legal_notice_strategy": [],
    "pre_litigation_options": [],
    "litigation_strategy": [],
    "estimated_timeline": "",
    "cost_considerations": [],
    "risk_assessment": [],
    "escalation_path": []
  }}
}}
"""

        response = self.llm_service.generate_json_response(
            prompt=prompt,
            system_role=system_role,
            temperature=0.1
        )

        if not response:
            return {"roadmap": ["Unable to generate roadmap."]}

        try:
            result = json.loads(response)
            return self._compress_roadmap(result)
        except Exception:
            return {"roadmap": ["Invalid roadmap format."]}
