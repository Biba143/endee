"""
Planner — generates structured, actionable improvement plans.

This module takes the output of the analyzer and reasoning engine
and produces concrete, prioritised action steps tailored to the
detected domain and identified issues.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain-specific plan templates
# ---------------------------------------------------------------------------

ACADEMIC_PLAN_TEMPLATES = [
    "Review and re-study the topics where scores were lowest, focusing on foundational concepts first.",
    "Create a structured weekly study schedule with dedicated time blocks per subject.",
    "Practice with past exam papers and timed mock tests to build exam technique.",
    "Identify and address specific knowledge gaps by working through textbook exercises.",
    "Seek clarification from teachers or tutors on topics that remain unclear.",
    "Form or join a study group to reinforce learning through peer discussion.",
    "Use active recall techniques (flashcards, self-testing) instead of passive re-reading.",
    "Track progress weekly by setting measurable mini-goals for each subject.",
]

SPORTS_PLAN_TEMPLATES = [
    "Develop a structured training programme with progressive overload principles.",
    "Work with a coach to identify and correct specific technical weaknesses.",
    "Incorporate targeted conditioning drills to address stamina or strength gaps.",
    "Analyse match or performance footage to identify tactical errors.",
    "Establish a consistent recovery routine (sleep, nutrition, stretching).",
    "Set measurable performance benchmarks and track them weekly.",
    "Participate in more competitive practice sessions to build match experience.",
    "Focus on mental conditioning and pre-performance routines to manage pressure.",
]

RESUME_PLAN_TEMPLATES = [
    "Identify the top 3–5 skills most in demand for your target role and build them deliberately.",
    "Quantify achievements in your resume with specific metrics (e.g., 'increased sales by 20%').",
    "Fill experience gaps with freelance projects, open-source contributions, or certifications.",
    "Tailor your resume and cover letter for each application, mirroring the job description language.",
    "Build a portfolio of work samples that demonstrate your skills concretely.",
    "Expand your professional network through LinkedIn, industry events, and informational interviews.",
    "Prepare structured STAR-format answers for common behavioural interview questions.",
    "Obtain relevant certifications to validate skills and signal commitment to growth.",
]

GENERAL_PLAN_TEMPLATES = [
    "Break the problem into smaller, manageable sub-tasks and tackle them one at a time.",
    "Set clear, measurable goals with specific deadlines for each improvement area.",
    "Seek feedback from relevant stakeholders or mentors to gain external perspective.",
    "Document your progress and review it regularly to stay accountable.",
    "Identify and remove the top 2–3 obstacles that are blocking progress.",
    "Allocate dedicated time each week to work on the identified improvement areas.",
    "Learn from comparable cases or best practices in the relevant field.",
    "Celebrate small wins to maintain motivation throughout the improvement journey.",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_improvement_plan(
    analysis: Dict[str, Any],
    domain: str = "general",
    intent: str = "improve",
    query: str = "",
    max_steps: int = 6,
) -> Dict[str, Any]:
    """
    Generate a structured, prioritised improvement plan.

    Args:
        analysis:   Output of analyzer.analyze_context().
        domain:     Detected domain (academic / sports / resume / general).
        intent:     Detected intent (used to tune the plan focus).
        query:      Original user query (for personalisation).
        max_steps:  Maximum number of action steps to include.

    Returns:
        {
            "immediate_actions":  List[str],   # do this week
            "short_term_goals":   List[str],   # 1–4 weeks
            "long_term_strategy": List[str],   # 1–3 months
            "success_metrics":    List[str],   # how to measure progress
            "priority_areas":     List[str],   # top focus areas
            "domain":             str,
        }
    """
    issues   = analysis.get("key_issues", [])
    positives = analysis.get("positive_aspects", [])
    numerics  = analysis.get("numeric_findings", [])

    # Select domain-appropriate templates
    templates = _get_templates(domain)

    # Build personalised steps based on identified issues
    immediate_actions  = _build_immediate_actions(issues, templates, domain, query)
    short_term_goals   = _build_short_term_goals(issues, templates, domain)
    long_term_strategy = _build_long_term_strategy(domain, positives)
    success_metrics    = _build_success_metrics(domain, numerics)
    priority_areas     = _identify_priority_areas(issues, domain)

    return {
        "immediate_actions":  immediate_actions[:max_steps],
        "short_term_goals":   short_term_goals[:4],
        "long_term_strategy": long_term_strategy[:3],
        "success_metrics":    success_metrics[:4],
        "priority_areas":     priority_areas[:4],
        "domain":             domain,
    }


# ---------------------------------------------------------------------------
# Internal builders
# ---------------------------------------------------------------------------

def _get_templates(domain: str) -> List[str]:
    mapping = {
        "academic": ACADEMIC_PLAN_TEMPLATES,
        "sports":   SPORTS_PLAN_TEMPLATES,
        "resume":   RESUME_PLAN_TEMPLATES,
        "general":  GENERAL_PLAN_TEMPLATES,
    }
    return mapping.get(domain, GENERAL_PLAN_TEMPLATES)


def _build_immediate_actions(
    issues: List[str],
    templates: List[str],
    domain: str,
    query: str,
) -> List[str]:
    """
    Build immediate (this-week) action steps.
    Combines issue-specific actions with domain templates.
    """
    actions = []

    # Issue-driven actions
    for issue in issues[:3]:
        action = _issue_to_action(issue, domain)
        if action:
            actions.append(action)

    # Fill with domain templates
    for template in templates[:4]:
        if template not in actions:
            actions.append(template)

    return actions


def _build_short_term_goals(
    issues: List[str],
    templates: List[str],
    domain: str,
) -> List[str]:
    """Build 1–4 week goals."""
    goals = []

    if domain == "academic":
        goals = [
            "Complete a full revision cycle for all weak subjects within 2 weeks.",
            "Achieve at least 70% on practice tests before the next assessment.",
            "Establish a consistent daily study routine of at least 2 focused hours.",
            "Reduce careless errors by reviewing all work before submission.",
        ]
    elif domain == "sports":
        goals = [
            "Complete 3 targeted training sessions per week focused on identified weaknesses.",
            "Achieve measurable improvement in the key performance metric within 4 weeks.",
            "Establish a consistent pre-competition preparation routine.",
            "Review and implement at least 2 tactical adjustments from performance analysis.",
        ]
    elif domain == "resume":
        goals = [
            "Update and tailor the resume for at least 5 targeted job applications.",
            "Complete one relevant online course or certification within 3 weeks.",
            "Reach out to at least 10 new professional contacts for networking.",
            "Prepare and rehearse answers to the top 10 interview questions.",
        ]
    else:
        goals = [
            "Complete the first phase of the improvement plan within 2 weeks.",
            "Measure and document progress against the baseline metrics.",
            "Identify and address the single biggest obstacle to progress.",
            "Build a consistent daily habit around the primary improvement area.",
        ]

    return goals


def _build_long_term_strategy(domain: str, positives: List[str]) -> List[str]:
    """Build 1–3 month strategic direction."""
    if domain == "academic":
        return [
            "Build deep conceptual mastery rather than surface-level memorisation.",
            "Develop strong exam technique through regular timed practice.",
            "Cultivate a growth mindset — treat every mistake as a learning signal.",
        ]
    elif domain == "sports":
        return [
            "Build a periodised training plan with clear phases (base, build, peak).",
            "Develop both physical and mental resilience for high-pressure situations.",
            "Continuously analyse performance data to guide training adjustments.",
        ]
    elif domain == "resume":
        return [
            "Position yourself as a specialist in your target niche through consistent skill-building.",
            "Build a strong personal brand through thought leadership and online presence.",
            "Develop a long-term career roadmap with 1-year, 3-year, and 5-year milestones.",
        ]
    else:
        return [
            "Establish a continuous improvement cycle: measure, analyse, act, review.",
            "Build systems and habits that make improvement sustainable over time.",
            "Seek mentorship or coaching to accelerate progress in key areas.",
        ]


def _build_success_metrics(domain: str, numerics: List[Dict]) -> List[str]:
    """Define measurable success criteria."""
    metrics = []

    # Use numeric findings if available
    for nf in numerics[:2]:
        val  = nf.get("value", "")
        unit = nf.get("unit", "")
        if val and unit:
            metrics.append(f"Improve from current {val} {unit} by at least 15–20%.")

    # Domain defaults
    if domain == "academic":
        metrics.extend([
            "Achieve a minimum score of 75% in the next assessment.",
            "Complete all assignments on time with no missing submissions.",
            "Reduce error rate in practice tests by 50% within 4 weeks.",
        ])
    elif domain == "sports":
        metrics.extend([
            "Improve key performance metric by 10–15% within 6 weeks.",
            "Achieve consistent performance across 3 consecutive training sessions.",
            "Reduce recovery time between high-intensity efforts.",
        ])
    elif domain == "resume":
        metrics.extend([
            "Receive at least 3 interview invitations from 20 applications.",
            "Complete 2 new certifications or projects within 6 weeks.",
            "Grow professional network by 50+ relevant connections.",
        ])
    else:
        metrics.extend([
            "Achieve a measurable 20% improvement in the primary metric within 4 weeks.",
            "Complete all planned action steps on schedule.",
            "Receive positive feedback from at least one external reviewer.",
        ])

    return metrics[:4]


def _identify_priority_areas(issues: List[str], domain: str) -> List[str]:
    """Identify the top priority focus areas from the issues list."""
    if not issues or issues == ["No specific issues identified from the available context."]:
        # Generic priorities by domain
        if domain == "academic":
            return ["Subject knowledge depth", "Exam technique", "Time management", "Consistency"]
        elif domain == "sports":
            return ["Technical skills", "Physical conditioning", "Mental resilience", "Tactical awareness"]
        elif domain == "resume":
            return ["Skill development", "Experience building", "Networking", "Personal branding"]
        else:
            return ["Core competency", "Process improvement", "Consistency", "Measurement"]

    # Extract key nouns from issues as priority areas
    priorities = []
    for issue in issues[:4]:
        # Take first 5 words as a priority label
        words = issue.split()[:5]
        label = " ".join(words).rstrip(".,;:")
        if label:
            priorities.append(label)

    return priorities


def _issue_to_action(issue: str, domain: str) -> str:
    """Convert an identified issue into a concrete action step."""
    issue_lower = issue.lower()

    if "math" in issue_lower or "mathematics" in issue_lower:
        return "Dedicate extra daily practice to mathematics, focusing on problem-solving techniques."
    if "english" in issue_lower or "language" in issue_lower:
        return "Improve language skills through daily reading and structured writing practice."
    if "time" in issue_lower and ("manage" in issue_lower or "limit" in issue_lower):
        return "Implement a time-boxing strategy: allocate fixed time slots for each task."
    if "stamina" in issue_lower or "endurance" in issue_lower:
        return "Add 3 aerobic conditioning sessions per week to build base endurance."
    if "technique" in issue_lower or "form" in issue_lower:
        return "Schedule dedicated technique drills with video review to correct form issues."
    if "skill" in issue_lower and "miss" in issue_lower:
        return "Enrol in a targeted course or workshop to acquire the missing skill."
    if "gap" in issue_lower:
        return "Address the identified gap with a focused 2-week intensive study or practice block."

    # Generic: turn the issue into an action
    return f"Address the following area directly: {issue[:80]}"
