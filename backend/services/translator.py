import json
import logging
from typing import Dict, Optional, Any
from backend.services.llm_service import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Translator:
    """
    A service for translating structured legal drafts into a target language using an LLM.
    Strictly preserves formatting and meaning.
    """

    def __init__(self):
        """
        Initializes the Translator with an instance of LLMService.
        """
        self.llm_service = LLMService()

    def translate(self, legal_draft: str, target_language: str) -> Dict[str, str]:
        """
        Translates the provided legal draft into the target language.

        Args:
            legal_draft (str): The structured legal draft to be translated.
            target_language (str): The target language (e.g., "Hindi", "French").

        Returns:
            Dict[str, str]: A JSON object containing the translated text under the key "translated_text".
                            Returns an error message in the same format on failure.
        """
        if not legal_draft:
            return {"translated_text": "Error: No legal draft provided for translation."}

        if not target_language:
            return {"translated_text": "Error: No target language specified."}

        system_role = (
            "You are an expert legal translator. Your task is to translate legal documents accurately "
            "while strictly preserving the original structure, formatting (markdown, bullet points, indentation), "
            "and legal terminology."
        )

        prompt = (
            f"Please translate the following legal draft into {target_language}:\n\n"
            f"\"{legal_draft}\"\n\n"
            f"Strict Requirements:\n"
            f"1. Translate the text accurately into {target_language}.\n"
            f"2. Maintain the exact original formatting (markdown, bolding, lists, etc.).\n"
            f"3. Preserve the legal meaning and tone.\n"
            f"4. Output ONLY valid JSON in the following format:\n"
            f"   {{\n"
            f"       \"translated_text\": \"<your translated text here>\"\n"
            f"   }}"
        )

        try:
            # Call the LLM service to generate a JSON response
            response_json_str = self.llm_service.generate_json_response(
                prompt=prompt,
                system_role=system_role
            )

            if not response_json_str:
                logger.error("LLM Service returned no response for translation.")
                return {"translated_text": "Error: Failed to generate translation. Please try again."}

            # Parse the JSON string
            try:
                data = json.loads(response_json_str)
                
                # Validation: Ensure the key exists
                if "translated_text" not in data:
                    logger.error(f"Missing 'translated_text' key in response: {data}")
                    return {"translated_text": "Error: Helper service returned unexpected format."}
                
                return data

            except json.JSONDecodeError as e:
                logger.error(f"JSON Decode Error: {e}. Output was: {response_json_str}")
                return {"translated_text": "Error: Failed to process the translated text."}

        except Exception as e:
            logger.error(f"Unexpected error in Translator.translate: {str(e)}")
            return {"translated_text": "Error: An unexpected system error occurred during translation."}
