"""
agent.py — StatGPT agent: retrieves data via RAG, calls LLM, returns structured response.
"""

import json
import traceback
from typing import Any, Dict, List
from dotenv import load_dotenv

from .llm_provider import get_llm_provider
from .system_prompt import SYSTEM_PROMPT

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from knowledge.knowledge_service import KnowledgeService

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Conversation history (in-memory; per-process)
# ─────────────────────────────────────────────────────────────────────────────
_history: List[Dict[str, str]] = []
MAX_HISTORY = 10  # keep last N turns


def _trim_history():
    global _history
    if len(_history) > MAX_HISTORY * 2:
        _history = _history[-(MAX_HISTORY * 2):]


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────
def run_agent(user_query: str, session_id: str | None = None) -> Dict[str, Any]:
    """
    1. Retrieve relevant data via Knowledge Service (RAG)
    2. Build a context-rich prompt with retrieved data and citations
    3. Call LLM provider
    4. Parse and return structured JSON response including RAG metadata
    """
    global _history

    try:
        llm = get_llm_provider()
    except Exception as e:
        return _provider_error_response(str(e))

    try:
        # Step 1: RAG Retrieval
        ks = KnowledgeService.get_instance()
        rag_result = ks.retrieve(user_query)
        
        evidence = rag_result["evidence"]
        citations = rag_result["citations"]
        confidence = rag_result["confidence"]
        query_type = rag_result["query_type"]
        
        # Step 2: Build the user message with data context
        prompt_enhancement = ""
        if query_type == "TREND_QUERY":
            prompt_enhancement = "Focus on time-series analysis. Mention percentage point changes over time explicitly."
        elif query_type == "COMPARISON_QUERY":
            prompt_enhancement = "Structure your answer as direct contrasts between the entities being compared."
            
        full_message = (
            f"USER QUERY: {user_query}\n\n"
            f"QUERY TYPE CLASSIFICATION: {query_type}\n"
            f"{prompt_enhancement}\n\n"
            f"RETRIEVED MOSPI EVIDENCE (USE ONLY THIS):\n{evidence}\n\n"
            f"Please respond using ONLY the evidence above. If the evidence is insufficient or says 'No official MoSPI evidence found', state exactly that you could not verify this from MoSPI sources. Return valid JSON matching the specified schema."
        )

        # Step 3: Build contents list with history
        messages = list(_history)
        messages.append({"role": "user", "text": full_message})

        # Step 4: Call LLM
        raw_text = llm.generate_content(SYSTEM_PROMPT, messages)

        # Step 5: Update history (store original query, not the augmented one)
        _history.append({"role": "user", "text": user_query})
        _history.append({"role": "model", "text": raw_text})
        _trim_history()

        # Step 6: Parse response
        parsed = _parse_response(raw_text)
        
        # Inject RAG metadata into the response
        parsed["citations"] = citations
        parsed["confidence"] = confidence
        parsed["query_type"] = query_type
        
        return parsed

    except Exception as e:
        traceback.print_exc()
        return {
            "answer": f"An error occurred while processing your query: {str(e)}",
            "data_table": [],
            "interpretation": "Please check the server logs for details.",
            "source": "N/A",
            "chart_config": None,
            "error": True,
            "citations": [],
            "confidence": "LOW",
            "query_type": "ERROR"
        }


def reset_history():
    """Clear conversation history."""
    global _history
    _history = []


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _parse_response(raw: str) -> Dict[str, Any]:
    """Extract JSON from LLM response (handles markdown code fences)."""
    import re
    # Strip markdown code fences if present
    clean = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    clean = re.sub(r"```\s*$", "", clean, flags=re.MULTILINE).strip()

    try:
        parsed = json.loads(clean)
        # Ensure required keys exist
        parsed.setdefault("answer", "")
        parsed.setdefault("data_table", [])
        parsed.setdefault("interpretation", "")
        parsed.setdefault("source", "")
        parsed.setdefault("chart_config", None)
        parsed.setdefault("error", False)
        return parsed
    except json.JSONDecodeError:
        # Fallback: return raw text as answer
        return {
            "answer": raw,
            "data_table": [],
            "interpretation": "",
            "source": "",
            "chart_config": None,
            "error": False,
            "raw": True,
        }


def _provider_error_response(msg: str) -> Dict[str, Any]:
    return {
        "answer": f"⚠️ LLM Provider Error: {msg}",
        "data_table": [],
        "interpretation": "Please check your .env configuration.",
        "source": "Configuration",
        "chart_config": None,
        "error": True,
        "citations": [],
        "confidence": "LOW",
        "query_type": "ERROR"
    }
