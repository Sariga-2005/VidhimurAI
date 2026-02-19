import json
import logging
from typing import Dict, Any, List
from .llm_service import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchAIEnhancer:
    """
    Service to enhance legal research results using an LLM.
    Generates summaries and analyzes influence without altering core facts.
    """

    def __init__(self):
        self.llm_service = LLMService()

    def enhance_research(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhances the research results with AI-generated summaries and analysis.

        Args:
            research_data (Dict[str, Any]): The structured research results.

        Returns:
            Dict[str, Any]: The enhanced research data containing 'enhanced_cases' and 'most_influential_analysis'.
                            Returns an error structure on failure.
        """
        if not research_data:
             return {"enhanced_cases": [], "most_influential_analysis": ["Error: No research data provided."]}

        system_role = (
            "You are a strict legal research assistant. "
            "Your task is to summarize and analyze legal cases based strictly on the provided data. "
            "Do not hallucinate facts or citation metrics."
        )

        prompt = self._construct_prompt(research_data)

        try:
            response_json_str = self.llm_service.generate_json_response(
                prompt=prompt,
                system_role=system_role
            )

            if not response_json_str:
                return {"enhanced_cases": [], "most_influential_analysis": ["Error: AI service unavailable."]}

            # Output size protection
            if len(response_json_str) > 15000:
                logger.warning("LLM response exceeded character limit (15000).")
                return {"enhanced_cases": [], "most_influential_analysis": ["Error: AI response too large."]}

            try:
                data = json.loads(response_json_str)
                
                # Deep validation
                if not isinstance(data.get("enhanced_cases"), list):
                    logger.warning("Invalid format: 'enhanced_cases' is not a list.")
                    return {"enhanced_cases": [], "most_influential_analysis": ["Error: Invalid response format."]}

                for case in data["enhanced_cases"]:
                    if not all(k in case and isinstance(case[k], str) for k in ["case_name", "concise_holding", "influence_reason"]):
                        logger.warning("Invalid format: 'enhanced_cases' elements missing keys or not strings.")
                        return {"enhanced_cases": [], "most_influential_analysis": ["Error: Invalid case format."]}

                if not isinstance(data.get("most_influential_analysis"), list) or not all(isinstance(i, str) for i in data["most_influential_analysis"]):
                     logger.warning("Invalid format: 'most_influential_analysis' is not a list of strings.")
                     return {"enhanced_cases": [], "most_influential_analysis": ["Error: Invalid analysis format."]}

                return data

            except json.JSONDecodeError:
                logger.error("Failed to decode JSON from LLM response.")
                return {"enhanced_cases": [], "most_influential_analysis": ["Error: AI response parsing failed."]}

        except Exception as e:
            logger.error(f"Error in enhance_research: {str(e)}")
            return {"enhanced_cases": [], "most_influential_analysis": ["Error: internal system error."]}

    def _construct_prompt(self, data: Dict[str, Any]) -> str:
        """Constructs the strict analysis prompt."""
        return f"""
You are a legal research assistant.

You are given structured precedent ranking results from a deterministic engine.

STRICT RULES:
- Do NOT modify strength_score.
- Do NOT invent citation counts.
- Do NOT alter court or year.
- Use only provided information.
- Output must be valid JSON.
- Do NOT include explanations outside JSON.
- Do NOT include markdown formatting.
- Return ONLY a JSON object.

Your tasks:

1. For each case in top_cases, generate:
   - A concise holding summary (max 100 words)
   - Why this case is legally influential (based on citation_count, court, year)

2. Explain in 3 bullet points why the most_influential_case stands out compared to others.

Input JSON:
{json.dumps(data, indent=2)}

Output JSON format:
{{
  "enhanced_cases": [
    {{
      "case_name": "string",
      "concise_holding": "string",
      "influence_reason": "string"
    }}
  ],
  "most_influential_analysis": ["string", "string", "string"]
}}
"""
