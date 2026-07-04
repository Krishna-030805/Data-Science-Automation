"""
core/voice_engine.py — Logic for the interactive voice interview.
Handles requirement gathering via simulated or real voice interaction.
"""

import os
import json

class VoiceOnboardingEngine:
    """
    Manages the conversational flow to gather project requirements.
    """
    
    def __init__(self):
        self.questions = [
            "Welcome to DataSense AI! I'm your data co-pilot. To get started, what kind of dataset are we looking at today?",
            "Great! And what is the primary question or goal you want to solve with this data? (e.g., predicting sales, finding churn patterns, exploratory analysis)",
            "Do you have any specific domain context or 'known truths' I should be aware of before I start mining?",
            "Last question — is there a specific target column you want me to focus on for modeling?"
        ]
        self.current_step = 0
        self.responses = {}

    def get_next_question(self):
        if self.current_step < len(self.questions):
            return self.questions[self.current_step]
        return None

    def process_response(self, text):
        """
        Processes user audio-to-text. In a real SaaS, this would use an LLM 
        to extract structured entities. For now, we store the raw input.
        """
        step_keys = ["dataset_type", "primary_goal", "domain_context", "target_col"]
        if self.current_step < len(step_keys):
            key = step_keys[self.current_step]
            self.responses[key] = text
            self.current_step += 1
            return True
        return False

    def get_summary(self):
        """
        Uses an LLM pattern (simulated) to summarize requirements.
        """
        summary = f"**User Project Profile**\n"
        summary += f"- **Dataset**: {self.responses.get('dataset_type', 'Unknown')}\n"
        summary += f"- **Goal**: {self.responses.get('primary_goal', 'Exploratory')}\n"
        summary += f"- **Context**: {self.responses.get('domain_context', 'None')}\n"
        summary += f"- **Target**: {self.responses.get('target_col', 'Auto-detect')}"
        return summary

    def map_to_session_state(self):
        """
        Maps the gathered info to existing Streamlit session state keys.
        """
        mapped = {
            "hypothesis": self.responses.get("primary_goal", ""),
            "domain_context": self.responses.get("domain_context", ""),
            "target_col": self.responses.get("target_col", None),
            "goals": [self.responses.get("primary_goal", "Exploratory")]
        }
        return mapped

# ── Mock LLM Extraction ───────────────────────────────────────────────
def extract_requirements_from_transcript(transcript: str):
    """
    Simulates calling an LLM to parse a conversation transcript.
    """
    # In a full SaaS, we'd call OpenAI/Gemini here.
    return {
        "domain": "Sales Data",
        "objective": "Predict next month revenue",
        "target": "revenue",
        "caveats": "Ignore outliers from 2020 pandemic period"
    }
