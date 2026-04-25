"""
Reasoning Engine — LLM-powered structured reasoning via OpenRouter.

Every reasoning function:
  1. Builds a rich context string from Endee-retrieved chunks
  2. Sends a structured prompt to the LLM (OpenRouter / Llama-3.1-8B)
  3. Parses the JSON response into a strict output dict
  4. Falls back to rule-based output if the LLM is unavailable

Intent routing:
  why      → generate_root_cause_analysis
  strategy → generate_strategy_analysis
  improve  → generate_improvement_plan_output
  summary  → generate_summary
"""

import json
import logging
import re
from typing import List, Dict, Any

from .analyzer import analyze_context
from .llm_client import chat, is_available

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt shared across all intents
# ---------------------------------------------------------------------------
_SYSTEM = """You are InsightAI, an expert reasoning engine.
You receive document context retrieved from a vector database (Endee) and a user question.
Your job is to produce a STRUCTURED JSON response — never plain prose.

Rules:
- Base every claim strictly on the provided context. Do not hallucinate.
- Be specific, actionable, and concise.
- All list values must be complete sentences.
- Return ONLY valid JSON — no markdown fences, no extra text before or after.
"""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_reasoning(
    query: str,
    chunks: List[Dict[str, Any]],
    intent: str,
    domain: str,
) -> Dict[str, Any]:
    """
    Full reasoning pipeline.
    Uses LLM when available, falls back to rule-based engine otherwise.
    """
    analysis = analyze_context(chunks, query, domain)
    context_text = _build_context_text(chunks)

    if is_available() and chunks:
        try:
            if intent == "why":
                result = _llm_root_cause(query, context_text, domain, analysis)
            elif intent == "strategy":
                result = _llm_strategy(query, context_text, domain, analysis)
            elif intent == "improve":
                result = _llm_improve(query, context_text, domain, analysis)
            else:
                result = _llm_summary(query, context_text, domain, analysis)
        except Exception as e:
            logger.warning("LLM reasoning failed, using fallback: %s", e)
            result = _fallback(intent, analysis, domain, query)
    else:
        result = _fallback(intent, analysis, domain, query)

    # Attach shared metadata
    result["intent"]          = intent
    result["domain"]          = domain
    result["query"]           = query
    result["sources"]         = analysis.get("sources", [])
    result["chunk_count"]     = analysis.get("chunk_count", 0)
    result["context_summary"] = analysis.get("context_summary", "")
    result.setdefault("numeric_findings", analysis.get("numeric_findings", []))

    return result


# ---------------------------------------------------------------------------
# LLM reasoning functions
# ---------------------------------------------------------------------------

def _llm_root_cause(query, context, domain, analysis) -> Dict[str, Any]:
    user_prompt = f"""Domain: {domain}
User question: {query}

Document context:
{context}

Return a JSON object with exactly these keys:
{{
  "analysis": ["observation 1", "observation 2", "observation 3"],
  "key_issues": ["issue 1", "issue 2", "issue 3"],
  "root_causes": ["root cause 1", "root cause 2", "root cause 3", "root cause 4"],
  "contributing_factors": ["factor 1", "factor 2", "factor 3"],
  "strategy_insight": "A 2-3 sentence strategic insight paragraph.",
  "improvement_plan": ["action step 1", "action step 2", "action step 3", "action step 4"]
}}"""

    raw = chat(_SYSTEM, user_prompt)
    parsed = _parse_json(raw)
    return _ensure_keys(parsed, ["analysis", "key_issues", "root_causes",
                                  "contributing_factors", "strategy_insight", "improvement_plan"])


def _llm_strategy(query, context, domain, analysis) -> Dict[str, Any]:
    user_prompt = f"""Domain: {domain}
User question: {query}

Document context:
{context}

Return a JSON object with exactly these keys:
{{
  "analysis": ["observation 1", "observation 2", "observation 3"],
  "key_issues": ["issue 1", "issue 2"],
  "strategic_pillars": ["pillar 1", "pillar 2", "pillar 3", "pillar 4"],
  "tactical_steps": ["step 1", "step 2", "step 3", "step 4", "step 5"],
  "strategy_insight": "A 2-3 sentence strategic insight paragraph.",
  "improvement_plan": ["action 1", "action 2", "action 3", "action 4"]
}}"""

    raw = chat(_SYSTEM, user_prompt)
    parsed = _parse_json(raw)
    return _ensure_keys(parsed, ["analysis", "key_issues", "strategic_pillars",
                                  "tactical_steps", "strategy_insight", "improvement_plan"])


def _llm_improve(query, context, domain, analysis) -> Dict[str, Any]:
    user_prompt = f"""Domain: {domain}
User question: {query}

Document context:
{context}

Return a JSON object with exactly these keys:
{{
  "analysis": ["observation 1", "observation 2", "observation 3"],
  "key_issues": ["issue 1", "issue 2", "issue 3"],
  "strategy_insight": "A 2-3 sentence strategic insight paragraph.",
  "improvement_plan": ["immediate action 1", "immediate action 2", "immediate action 3", "immediate action 4", "immediate action 5"],
  "short_term_goals": ["goal 1 (1-2 weeks)", "goal 2", "goal 3"],
  "long_term_strategy": ["strategy 1 (1-3 months)", "strategy 2", "strategy 3"],
  "success_metrics": ["metric 1", "metric 2", "metric 3"],
  "priority_areas": ["area 1", "area 2", "area 3"]
}}"""

    raw = chat(_SYSTEM, user_prompt)
    parsed = _parse_json(raw)
    return _ensure_keys(parsed, ["analysis", "key_issues", "strategy_insight",
                                  "improvement_plan", "short_term_goals",
                                  "long_term_strategy", "success_metrics", "priority_areas"])


def _llm_summary(query, context, domain, analysis) -> Dict[str, Any]:
    user_prompt = f"""Domain: {domain}
User question: {query}

Document context:
{context}

Return a JSON object with exactly these keys:
{{
  "analysis": ["key observation 1", "key observation 2", "key observation 3", "key observation 4"],
  "key_issues": ["issue 1", "issue 2"],
  "highlights": ["highlight 1", "highlight 2", "highlight 3"],
  "strategy_insight": "A 2-3 sentence summary insight paragraph.",
  "improvement_plan": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}"""

    raw = chat(_SYSTEM, user_prompt)
    parsed = _parse_json(raw)
    return _ensure_keys(parsed, ["analysis", "key_issues", "highlights",
                                  "strategy_insight", "improvement_plan"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_context_text(chunks: List[Dict[str, Any]], max_words: int = 2500) -> str:
    """Concatenate chunk texts into a numbered context block."""
    parts = []
    total = 0
    for i, ch in enumerate(chunks, 1):
        text = ch.get("text", "")
        doc  = ch.get("doc_name", "?")
        page = ch.get("page", "?")
        words = len(text.split())
        if total + words > max_words:
            remaining = max_words - total
            if remaining > 40:
                text = " ".join(text.split()[:remaining]) + "…"
            else:
                break
        parts.append(f"[{i}] (Source: {doc}, p.{page})\n{text}")
        total += words
    return "\n\n".join(parts) if parts else "No context available."


def _parse_json(raw: str) -> Dict[str, Any]:
    """
    Extract and parse JSON from LLM output.
    Handles cases where the model wraps JSON in markdown fences.
    """
    # Strip markdown fences if present
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Find the first { ... } block
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Attempt to fix common issues: trailing commas
        text = re.sub(r",\s*([}\]])", r"\1", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse LLM JSON output: {e}\nRaw: {raw[:300]}")


def _ensure_keys(data: Dict, required: List[str]) -> Dict:
    """Fill any missing keys with sensible defaults."""
    for key in required:
        if key not in data:
            if key == "strategy_insight":
                data[key] = "Analysis based on the provided document context."
            else:
                data[key] = []
    return data


# ---------------------------------------------------------------------------
# Rule-based fallback (used when LLM is unavailable or fails)
# ---------------------------------------------------------------------------

def _fallback(intent: str, analysis: Dict, domain: str, query: str) -> Dict[str, Any]:
    """Minimal rule-based fallback so the app never crashes."""
    from .planner import generate_improvement_plan

    obs    = analysis.get("key_observations", ["Context retrieved from uploaded documents."])
    issues = analysis.get("key_issues", ["No specific issues identified."])
    plan   = generate_improvement_plan(analysis, domain, intent, query, max_steps=5)

    base = {
        "analysis":        obs[:5],
        "key_issues":      issues[:5],
        "strategy_insight": _static_insight(domain, intent),
        "improvement_plan": plan.get("immediate_actions", [])[:5],
    }

    if intent == "why":
        base["root_causes"]          = [f"Root cause: {i[:80]}" for i in issues[:4]]
        base["contributing_factors"] = plan.get("short_term_goals", [])[:3]
    elif intent == "strategy":
        base["strategic_pillars"] = plan.get("long_term_strategy", [])[:4]
        base["tactical_steps"]    = plan.get("immediate_actions", [])[:5]
    elif intent == "improve":
        base["short_term_goals"]   = plan.get("short_term_goals", [])
        base["long_term_strategy"] = plan.get("long_term_strategy", [])
        base["success_metrics"]    = plan.get("success_metrics", [])
        base["priority_areas"]     = plan.get("priority_areas", [])
    else:
        base["highlights"] = analysis.get("positive_aspects", [])[:4]

    return base


def _static_insight(domain: str, intent: str) -> str:
    table = {
        ("academic", "why"):      "Performance gaps are typically rooted in foundational knowledge deficits and ineffective study strategies.",
        ("academic", "strategy"): "Combine mastery-based learning with deliberate practice in weak areas for maximum grade impact.",
        ("academic", "improve"):  "Build strong study systems — active recall, spaced repetition, and timed practice — rather than just studying more.",
        ("academic", "summary"):  "The document shows a mixed academic profile with identifiable strengths and clear areas for improvement.",
        ("sports",   "why"):      "Sports performance shortfalls stem from technical, physical, or mental gaps — identify the primary constraint first.",
        ("sports",   "strategy"): "Address the weakest performance pillar first; it acts as the bottleneck limiting overall results.",
        ("sports",   "improve"):  "Structured, periodised training with measurable targets is the most reliable path to improvement.",
        ("resume",   "why"):      "Career challenges often stem from misalignment between your positioning and what employers are seeking.",
        ("resume",   "strategy"): "Build on three pillars: skill alignment, quantified evidence of impact, and strategic networking.",
        ("resume",   "improve"):  "Targeted skill-building combined with a strong personal narrative will accelerate career progress.",
    }
    return table.get(
        (domain, intent),
        "A structured, systematic approach with measurable goals will produce the most reliable results."
    )
