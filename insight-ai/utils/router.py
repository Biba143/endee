"""
Router — detects query intent and domain.

This module classifies user queries into:
  - WHY:      Root cause analysis
  - STRATEGY: Strategic insight
  - IMPROVE:  Improvement planning
  - SUMMARY:  General summary (default)

It also attempts to detect the domain:
  - academic (grades, marksheets, exams)
  - sports (performance, scores, matches)
  - resume (skills, experience, career)
  - general (everything else)
"""

from typing import Dict, Any, Tuple, List
import re


# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------

INTENT_WHY     = "why"
INTENT_STRATEGY = "strategy"
INTENT_IMPROVE = "improve"
INTENT_SUMMARY = "summary"

INTENT_KEYWORDS = {
    INTENT_WHY: [
        "why", "reason", "cause", "root cause", "explain", "what caused",
        "why did", "why was", "why have", "why has", "why are", "why is",
        "reason for", "cause of", "factors behind", "underlying reason",
    ],
    INTENT_STRATEGY: [
        "strategy", "strategic", "approach", "plan", "method", "tactic",
        "how to", "best way", "optimal", "recommend", "suggest", "advise",
        "what strategy", "what approach", "what method", "game plan",
        "winning strategy", "competitive advantage",
    ],
    INTENT_IMPROVE: [
        "improve", "better", "enhance", "increase", "boost", "upgrade",
        "how can i", "how to improve", "get better", "do better",
        "improvement", "progress", "develop", "grow", "advance",
        "action plan", "next steps", "what to do", "recommendations",
    ],
}


def detect_intent(query: str) -> str:
    """
    Classify query intent based on keyword matching.

    Returns one of: "why", "strategy", "improve", "summary".
    """
    query_lower = query.lower().strip()

    # Check for intent keywords (ordered by priority)
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                return intent

    # Default to summary
    return INTENT_SUMMARY


# ---------------------------------------------------------------------------
# Domain detection
# ---------------------------------------------------------------------------

DOMAIN_ACADEMIC = "academic"
DOMAIN_SPORTS   = "sports"
DOMAIN_RESUME   = "resume"
DOMAIN_GENERAL  = "general"

DOMAIN_KEYWORDS = {
    DOMAIN_ACADEMIC: [
        "grade", "score", "mark", "exam", "test", "assignment", "homework",
        "course", "subject", "teacher", "professor", "student", "school",
        "college", "university", "academic", "gpa", "cgpa", "percentage",
        "rank", "result", "transcript", "marksheet", "report card",
        "mathematics", "science", "english", "physics", "chemistry",
        "biology", "history", "geography", "economics",
    ],
    DOMAIN_SPORTS: [
        "sport", "game", "match", "tournament", "competition", "athlete",
        "player", "team", "coach", "training", "performance", "fitness",
        "score", "goal", "point", "win", "lose", "victory", "defeat",
        "football", "soccer", "basketball", "tennis", "cricket", "hockey",
        "baseball", "volleyball", "swimming", "running", "marathon",
        "olympics", "championship", "league", "season",
    ],
    DOMAIN_RESUME: [
        "resume", "cv", "curriculum vitae", "job", "career", "employment",
        "experience", "skill", "qualification", "certification", "degree",
        "project", "achievement", "accomplishment", "responsibility",
        "role", "position", "company", "employer", "interview",
        "application", "hire", "recruit", "promotion", "salary",
        "technical skill", "soft skill", "leadership", "teamwork",
    ],
}


def detect_domain(query: str, context_chunks: List[Dict[str, Any]] = None) -> str:
    """
    Detect the domain of the query based on keywords and context.

    Args:
        query:           User's question.
        context_chunks:  Retrieved chunks (optional) for additional clues.

    Returns:
        One of: "academic", "sports", "resume", "general".
    """
    query_lower = query.lower()
    text_to_scan = query_lower

    # If context is provided, add chunk texts to the scanning corpus
    if context_chunks:
        context_text = " ".join(ch.get("text", "").lower() for ch in context_chunks[:3])
        text_to_scan += " " + context_text

    # Count keyword matches per domain
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in text_to_scan:
                score += 1
        scores[domain] = score

    # Return domain with highest score, default to general
    if not scores:
        return DOMAIN_GENERAL

    best_domain = max(scores.items(), key=lambda x: x[1])[0]
    if scores[best_domain] == 0:
        return DOMAIN_GENERAL

    return best_domain


# ---------------------------------------------------------------------------
# Query transformation
# ---------------------------------------------------------------------------

def transform_query_for_intent(query: str, intent: str) -> str:
    """
    Augment the query to better retrieve relevant context for the detected intent.

    Example:
        Original: "Why did I score less?"
        Intent:   "why"
        Transformed: "reasons causes factors explanation why did I score less"
    """
    if intent == INTENT_WHY:
        # Add synonyms for causal reasoning
        return f"reasons causes factors explanation {query}"
    elif intent == INTENT_STRATEGY:
        # Add strategic terms
        return f"strategy approach plan method tactics {query}"
    elif intent == INTENT_IMPROVE:
        # Add improvement terms
        return f"improvement better enhance progress development {query}"
    else:
        # Keep original for summary
        return query


# ---------------------------------------------------------------------------
# Main router function
# ---------------------------------------------------------------------------

def route_query(
    query: str,
    context_chunks: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Full routing pipeline: detect intent, domain, and transform query.

    Returns a dict with:
        {
            "original_query": str,
            "intent":         "why"|"strategy"|"improve"|"summary",
            "domain":         "academic"|"sports"|"resume"|"general",
            "transformed_query": str,
        }
    """
    intent = detect_intent(query)
    domain = detect_domain(query, context_chunks)
    transformed = transform_query_for_intent(query, intent)

    return {
        "original_query": query,
        "intent": intent,
        "domain": domain,
        "transformed_query": transformed,
    }



