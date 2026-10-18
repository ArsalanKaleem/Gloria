"""Deterministic question router for the MVP.

Upgrade to model-driven tool calling once your provider supports it well;
keep this as the fallback so behaviour stays predictable.
"""

import re

# People: needs a specific person cue OR an email/contact cue. Keeps
# generic "who" from hijacking (e.g. "who is your creator" now falls
# through to documents).
PEOPLE_RX = re.compile(
    r"\b("
    r"hod|head\s+of|dean|chairman|chairperson|in[-\s]?charge|"
    r"professor|prof\.?|dr\.?|mr\.?|ms\.?|mrs\.?|"
    r"registrar|controller|director|"
    r"faculty\s+of|"           # only "faculty of X"
    r"email|phone|contact|extension|mailbox|"
    r"who\s+is\s+the"          # "who is the X" but not bare "who"
    r")\b",
    re.I,
)

# Department: needs "department" or "faculty of" — unchanged, this was fine.
DEPT_RX = re.compile(r"\b(department\s+of|faculty\s+of|school\s+of)\b", re.I)

# Program: only fires on strong program-shaped signals. No more bare
# "program" / "admission" hijacking generic questions.
PROG_RX = re.compile(
    r"\b("
    r"bs\s+\w+|"                                    # "BS Computer Science"
    r"ms\s+\w+|"                                    # "MS Chemistry"
    r"phd\s+\w+|"                                   # "PhD Physics"
    r"b\.?ed|bba|bs-?commerce|"                     # named programs
    r"degree\s+in|"                                 # "degree in X"
    r"admission\s+(criteria|requirements|process|procedure|form|deadline)|"
    r"how\s+(do\s+i|to)\s+apply"                    # "how to apply"
    r")\b",
    re.I,
)

HEC_RX = re.compile(r"\bhec\b", re.I)


def route(question: str) -> str:
    """Return one of: 'hec', 'people', 'department', 'program', 'documents'."""
    if HEC_RX.search(question):
        return "hec"
    if PEOPLE_RX.search(question):
        return "people"
    if DEPT_RX.search(question):
        return "department"
    if PROG_RX.search(question):
        return "program"
    return "documents"