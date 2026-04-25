"""
Analyzer — extracts patterns and key issues from retrieved context.

This module performs the first stage of structured reasoning:
  - Identifies key observations from the retrieved chunks
  - Extracts problems, gaps, and anomalies
  - Scores and ranks issues by severity
  - Prepares structured data for the reasoning engine
"""

from typing import List, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Negative / positive signal words for pattern extraction
# ---------------------------------------------------------------------------

NEGATIVE_SIGNALS = [
    "fail", "poor", "low", "weak", "lack", "miss", "absent", "below",
    "insufficient", "inadequate", "incorrect", "wrong", "error", "mistake",
    "problem", "issue", "difficulty", "struggle", "challenge", "gap",
    "decline", "drop", "decrease", "reduce", "worse", "bad", "terrible",
    "incomplete", "missing", "not", "never", "rarely", "seldom",
    "average", "mediocre", "underperform", "behind", "deficit",
]

POSITIVE_SIGNALS = [
    "good", "great", "excellent", "strong", "high", "above", "pass",
    "success", "achieve", "improve", "increase", "better", "best",
    "outstanding", "exceptional", "perfect", "complete", "full",
    "consistent", "reliable", "efficient", "effective", "proficient",
]

NUMERIC_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s*(%|percent|marks?|points?|score|grade|gpa|cgpa)\b", re.IGNORECASE)
SUBJECT_PATTERN = re.compile(r"\b(mathematics?|math|science|physics|chemistry|biology|english|history|geography|economics|computer|programming|statistics)\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_context(
    chunks: List[Dict[str, Any]],
    query: str,
    domain: str = "general",
) -> Dict[str, Any]:
    """
    Analyze retrieved context chunks and extract structured observations.

    Args:
        chunks:  List of chunk dicts from the retriever.
        query:   Original user query (for relevance scoring).
        domain:  Detected domain (academic / sports / resume / general).

    Returns:
        A structured analysis dict:
        {
            "key_observations": List[str],
            "key_issues":       List[str],
            "numeric_findings": List[Dict],
            "positive_aspects": List[str],
            "context_summary":  str,
            "chunk_count":      int,
            "sources":          List[Dict],
        }
    """
    if not chunks:
        return _empty_analysis()

    # Combine all chunk texts for analysis
    full_text = " ".join(c.get("text", "") for c in chunks)
    full_text_lower = full_text.lower()

    key_observations = _extract_observations(chunks, query)
    key_issues       = _extract_issues(full_text_lower, domain)
    numeric_findings = _extract_numeric_findings(full_text)
    positive_aspects = _extract_positive_aspects(full_text_lower, domain)
    context_summary  = _build_context_summary(chunks)
    sources          = _build_source_list(chunks)

    return {
        "key_observations": key_observations,
        "key_issues":       key_issues,
        "numeric_findings": numeric_findings,
        "positive_aspects": positive_aspects,
        "context_summary":  context_summary,
        "chunk_count":      len(chunks),
        "sources":          sources,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _empty_analysis() -> Dict[str, Any]:
    return {
        "key_observations": ["No relevant context was found in the uploaded documents."],
        "key_issues":       ["Insufficient data to identify specific issues."],
        "numeric_findings": [],
        "positive_aspects": [],
        "context_summary":  "No context available.",
        "chunk_count":      0,
        "sources":          [],
    }


def _extract_observations(chunks: List[Dict[str, Any]], query: str) -> List[str]:
    """
    Extract the most relevant sentences from top chunks as key observations.
    Prioritises sentences that contain query keywords.
    """
    query_words = set(query.lower().split())
    observations = []

    for chunk in chunks[:6]:  # top 6 chunks
        text = chunk.get("text", "")
        sentences = _split_sentences(text)

        for sent in sentences:
            sent_lower = sent.lower()
            # Score by query word overlap
            overlap = sum(1 for w in query_words if w in sent_lower and len(w) > 3)
            if overlap >= 1 and len(sent.split()) >= 8:
                observations.append(sent.strip())

    # Deduplicate and limit
    seen = set()
    unique_obs = []
    for obs in observations:
        key = obs[:60].lower()
        if key not in seen:
            seen.add(key)
            unique_obs.append(obs)

    # Fallback: use first sentence of top chunks
    if not unique_obs:
        for chunk in chunks[:3]:
            text = chunk.get("text", "")
            sentences = _split_sentences(text)
            if sentences:
                unique_obs.append(sentences[0].strip())

    return unique_obs[:6]


def _extract_issues(text_lower: str, domain: str) -> List[str]:
    """
    Identify problem areas by scanning for negative signal words.
    Returns a list of issue descriptions.
    """
    issues = []
    sentences = _split_sentences(text_lower)

    for sent in sentences:
        neg_count = sum(1 for sig in NEGATIVE_SIGNALS if sig in sent)
        if neg_count >= 1 and len(sent.split()) >= 6:
            # Capitalise and clean up
            clean = sent.strip().capitalize()
            if clean and clean not in issues:
                issues.append(clean)

    # Domain-specific issue patterns
    if domain == "academic":
        issues.extend(_academic_issues(text_lower))
    elif domain == "sports":
        issues.extend(_sports_issues(text_lower))
    elif domain == "resume":
        issues.extend(_resume_issues(text_lower))

    # Deduplicate
    seen = set()
    unique = []
    for issue in issues:
        key = issue[:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(issue)

    return unique[:6] if unique else ["No specific issues identified from the available context."]


def _extract_numeric_findings(text: str) -> List[Dict[str, Any]]:
    """Extract numeric scores, percentages, and grades from text."""
    findings = []
    matches = NUMERIC_PATTERN.finditer(text)

    for match in matches:
        value = match.group(1)
        unit  = match.group(2)
        # Get surrounding context (up to 60 chars before the match)
        start = max(0, match.start() - 60)
        context = text[start:match.end()].strip()
        findings.append({
            "value":   value,
            "unit":    unit,
            "context": context,
        })

    return findings[:10]


def _extract_positive_aspects(text_lower: str, domain: str) -> List[str]:
    """Identify strengths and positive signals in the context."""
    positives = []
    sentences = _split_sentences(text_lower)

    for sent in sentences:
        pos_count = sum(1 for sig in POSITIVE_SIGNALS if sig in sent)
        neg_count = sum(1 for sig in NEGATIVE_SIGNALS if sig in sent)
        # Only include if clearly positive (more positive than negative signals)
        if pos_count > neg_count and pos_count >= 1 and len(sent.split()) >= 6:
            clean = sent.strip().capitalize()
            if clean and clean not in positives:
                positives.append(clean)

    return positives[:4]


def _build_context_summary(chunks: List[Dict[str, Any]]) -> str:
    """Build a brief summary of the retrieved context."""
    if not chunks:
        return "No context available."

    doc_names = list({c.get("doc_name", "unknown") for c in chunks})
    pages     = sorted({c.get("page", 1) for c in chunks})
    total_words = sum(c.get("word_count", 0) for c in chunks)

    doc_str  = ", ".join(doc_names[:3])
    page_str = f"pages {pages[0]}–{pages[-1]}" if len(pages) > 1 else f"page {pages[0]}"

    return (
        f"Retrieved {len(chunks)} chunks from {doc_str} "
        f"({page_str}), totalling ~{total_words} words."
    )


def _build_source_list(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build a deduplicated list of source references."""
    seen = set()
    sources = []

    for chunk in chunks:
        doc  = chunk.get("doc_name", "unknown")
        page = chunk.get("page", 1)
        key  = f"{doc}:p{page}"

        if key not in seen:
            seen.add(key)
            sources.append({
                "doc_name": doc,
                "page":     page,
                "score":    round(chunk.get("score", 0.0), 4),
            })

    return sources


def _split_sentences(text: str) -> List[str]:
    """Simple sentence splitter."""
    # Split on period, exclamation, question mark followed by space or end
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


# ---------------------------------------------------------------------------
# Domain-specific issue extractors
# ---------------------------------------------------------------------------

def _academic_issues(text: str) -> List[str]:
    issues = []
    subjects = SUBJECT_PATTERN.findall(text)
    for subj in set(subjects):
        if any(neg in text for neg in ["low", "fail", "poor", "weak", "below"]):
            issues.append(f"Performance concerns identified in {subj.capitalize()}.")
    return issues


def _sports_issues(text: str) -> List[str]:
    issues = []
    if "injury" in text or "injured" in text:
        issues.append("Injury or physical condition may have impacted performance.")
    if "stamina" in text or "endurance" in text or "fatigue" in text:
        issues.append("Stamina or endurance issues detected.")
    if "technique" in text or "form" in text:
        issues.append("Technical form or technique may need improvement.")
    return issues


def _resume_issues(text: str) -> List[str]:
    issues = []
    if "gap" in text or "unemployed" in text:
        issues.append("Employment gaps detected in the timeline.")
    if "no experience" in text or "lack of experience" in text:
        issues.append("Limited relevant experience in key areas.")
    if "skill" in text and any(neg in text for neg in ["missing", "lack", "no"]):
        issues.append("Missing or underdeveloped skills identified.")
    return issues
