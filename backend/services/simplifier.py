import json
import logging
from typing import Dict, Any
from .llm_service import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Simplifier:
    """
    A service for simplifying complex legal summaries using an LLM.
    """

    def __init__(self):
        """
        Initializes the Simplifier with an instance of LLMService.
        """
        self.llm_service = LLMService()

    def simplify(self, legal_summary: str) -> Dict[str, str]:
        """
        Simplifies the provided legal summary into a layman explanation.

        Args:
            legal_summary (str): The legal summary to be simplified.

        Returns:
            Dict[str, str]: A dictionary containing the simplified summary.
                            Returns an error message in the same format on failure.
        """
        if not isinstance(legal_summary, str):
            return {"simplified_summary": "Error: Input must be a string."}

        legal_summary = legal_summary.strip()
        if not legal_summary:
            return {"simplified_summary": "Error: No summary provided."}

        system_role = (
            "You are a helpful legal assistant. Your goal is to simplify complex legal language "
            "into clear, concise, and layman-friendly explanations."
        )

        prompt = (
            f"Please simplify the following legal summary:\n\n"
            f"\"{legal_summary}\"\n\n"
            f"Requirements:\n"
            f"1. Generate a layman explanation.\n"
            f"2. Limit the explanation to a maximum of 150 words.\n"
            f"3. Use bullet points (•) and separate them with \\n.\n"
            f"4. Preserve the original meaning.\n"
            f"5. Do NOT include markdown.\n"
            f"6. Do NOT include explanations outside JSON.\n"
            f"7. Return ONLY a JSON object with the key 'simplified_summary'. Ensure the JSON string values are properly escaped."
        )

        try:
            response_json = self.llm_service.generate_json_response(prompt, system_role)
            
            if response_json:
                try:
                    data = json.loads(response_json)
                    
                    if "simplified_summary" not in data:
                         logger.warning("LLM response missing 'simplified_summary' key.")
                         return {"simplified_summary": "Error: Failed to process the summary format."}

                    if not isinstance(data["simplified_summary"], str):
                        logger.warning("LLM response 'simplified_summary' is not a string.")
                        return {"simplified_summary": "Error: Invalid response type."}

                    if len(data["simplified_summary"]) > 2000:
                        logger.warning("Simplified summary exceeded 2000 characters.")
                        return {"simplified_summary": "Error: Summary too long."}
                    
                    return data
                    
                except json.JSONDecodeError:
                    logger.error("Failed to decode JSON from LLM response.")
                    return {"simplified_summary": "Error: Failed to process the summary format."}
            else:
                logger.error("LLM service returned None.")
                return {"simplified_summary": "Error: Unable to generate simplification from LLM."}

        except Exception as e:
            logger.error(f"An error occurred during simplification: {str(e)}")
            return {"simplified_summary": "Error: An internal error occurred."}
