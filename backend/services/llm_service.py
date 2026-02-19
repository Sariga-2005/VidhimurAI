import os
import logging
from typing import Optional, List, Dict, Any
from openai import OpenAI, OpenAIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    """
    A production-ready service class for interacting with OpenAI's LLM.
    Handles configuration, API calls, and graceful error handling.
    """

    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        Initialize the LLMService.

        Args:
            model_name (str): The default model to use for completions.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY environment variable is not set. LLM calls will fail.")
        
        # Initialize the OpenAI client
        # The client will automatically look for OPENAI_API_KEY env var, 
        # but explicit passing allows for flexibility if needed.
        self.client = OpenAI(api_key=self.api_key)

    def generate_response(self, prompt: str, system_role: str = "You are a helpful assistant.") -> Optional[str]:
        """
        Generates a response from the LLM based on the provided prompt and system role.

        Args:
            prompt (str): The user input or prompt for the LLM.
            system_role (str): The system instruction to set the behavior of the LLM.

        Returns:
            Optional[str]: The generated response content, or None if an error occurs.
        """
        if not self.api_key:
            logger.error("Attempted to call LLM without an API key.")
            return None

        try:
            messages = [
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt}
            ]

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,  # Requirement: Temperature = 0.3
            )

            if response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip()
            
            logger.warning("LLM response received but contained no content.")
            return None

        except OpenAIError as e:
            logger.error(f"OpenAI API Error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in LLMService: {str(e)}")
            return None

    def generate_json_response(self, prompt: str, system_role: str = "You are a helpful assistant.") -> Optional[str]:
        """
        Generates a response strictly in JSON format.
        Useful for structured data extraction.
        
        Args:
            prompt (str): The user input.
            system_role (str): The system instruction.
            
        Returns:
            Optional[str]: The JSON string response, or None on failure.
        """
        if not self.api_key:
             logger.error("Attempted to call LLM without an API key.")
             return None

        try:
            messages = [
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt}
            ]

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            if response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip()

            return None

        except OpenAIError as e:
            logger.error(f"OpenAI API Error (JSON mode): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in LLMService (JSON mode): {str(e)}")
            return None
