import os
import json
import logging
import re
from pathlib import Path
from typing import Optional
from groq import Groq
from dotenv import load_dotenv

# Load .env file from the backend directory (parent of services)
backend_env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=backend_env_path)

# Also try root .env file (3 levels up)
root_env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=root_env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    """
    Groq LLM Service using hosted open-source models.
    """

    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_name = model_name
        self.client = None

        if not self.api_key:
            logger.warning("GROQ_API_KEY not set.")
        else:
            self.client = Groq(api_key=self.api_key)

    def generate_response(
        self,
        prompt: str,
        system_role: str = "You are a helpful assistant."
    ) -> Optional[str]:

        if not self.client:
            logger.warning("Groq client not initialized.")
            return None

        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            return completion.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Groq API Error: {str(e)}")
            return None

    def generate_json_response(
        self,
        prompt: str,
        system_role: str = "You are a helpful assistant."
    ) -> Optional[str]:

        response = self.generate_response(prompt, system_role)
        if not response:
            return None

        try:
            # Clean markdown if model adds it
            cleaned = response.strip()
            
            # Remove markdown code blocks if present
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            
            # Use regex to find the first JSON object block if not already clean
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                cleaned = json_match.group(0)

            # Attempt to validate JSON
            json.loads(cleaned)
            return cleaned

        except json.JSONDecodeError:
            # Attempt to fix common issues like newlines in strings
            try:
                # Replace literal newlines with space to make it valid JSON
                # This sacrifices formatting slightly but ensures validity
                fixed = cleaned.replace('\n', ' ').replace('\r', '')
                json.loads(fixed)
                return fixed
            except:
                pass

            logger.error(f"Invalid JSON returned from Groq. Raw Response: {response}")
            return None
