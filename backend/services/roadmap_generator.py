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
            "You are a legal strategy advisor. "
            "Generate a practical, step-by-step legal roadmap. "
            "Do NOT rewrite facts. "
            "Do NOT invent new laws beyond relevant_sections. "
            "Be realistic and procedural."
        )

        prompt = f"""
You are generating a structured legal roadmap.

Issue Type:
{structured_analysis["issue_type"]}

Relevant Laws:
{json.dumps(structured_analysis["relevant_sections"], indent=2)}

Legal Strength:
{structured_analysis["legal_strength"]}

Initial Action Steps:
{json.dumps(structured_analysis["action_steps"], indent=2)}

---------------------------------------
TASK:
Create a structured roadmap including:

1. Immediate Actions (next 7 days)
2. Evidence Checklist
3. Legal Notice Strategy
4. Pre-litigation Options
5. Litigation Strategy
6. Estimated Timeline
7. Cost Considerations
8. Risk Assessment
9. Escalation Path

---------------------------------------
OUTPUT FORMAT (STRICT JSON):

{{
  "roadmap": {{
    "immediate_actions": ["string"],
    "evidence_checklist": ["string"],
    "legal_notice_strategy": ["string"],
    "pre_litigation_options": ["string"],
    "litigation_strategy": ["string"],
    "estimated_timeline": "string",
    "cost_considerations": ["string"],
    "risk_assessment": ["string"],
    "escalation_path": ["string"]
  }}
}}

Return ONLY valid JSON.
Do NOT include markdown.
Do NOT include explanations outside JSON.
"""

        response = self.llm_service.generate_json_response(
            prompt=prompt,
            system_role=system_role
        )

        if not response:
            return {"roadmap": ["Unable to generate roadmap."]}

        try:
            return json.loads(response)
        except Exception:
            return {"roadmap": ["Invalid roadmap format."]}
