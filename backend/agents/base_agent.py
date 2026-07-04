import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger("drainguard.agents")

class BaseAgent:
    def __init__(self, name: str, system_instruction: str):
        self.name = name
        self.system_instruction = system_instruction
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-1.5-flash"
        self._initialized = False
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=self.system_instruction
                )
                self._initialized = True
                logger.info(f"Agent {self.name} initialized with live Gemini API.")
            except Exception as e:
                logger.warning(f"Failed to initialize live Gemini API for {self.name}: {e}. Falling back to simulation.")
                self._initialized = False

    def call_gemini(self, prompt: str) -> str:
        if self._initialized:
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.error(f"Error calling live Gemini for {self.name}: {e}. Falling back to simulation.")
                return ""
        return ""

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent logic. If a live API key is present, it formats a prompt,
        sends it to Gemini, and parses the response. Otherwise, it runs a realistic
        rule-based simulation.
        """
        raise NotImplementedError("Subclasses must implement run()")

    def _generate_mock_response(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback generator for running without an active Gemini API key.
        """
        raise NotImplementedError("Subclasses must implement _generate_mock_response()")
