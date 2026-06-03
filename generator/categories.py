from dataclasses import dataclass

from pathlib import Path

@dataclass
class Category:
    key: str
    name: str
    description: str
    guidance: str



CATEGORIES: dict[str, Category] = {
    "ambiguous": Category(
        key="ambiguous",
        name="Ambiguous",
        description="The task is ambiguous, with an unclear goal or multiple valid interpretations.",
        guidance="Identify the ambiguity and clarify the intended goal or interpretation."
    ),
    "conflicting_tools": Category(
        key="conflicting_tools",
        name="Conflicting Tools",
        description="Two tools return contradictory information.",
        guidance="Determine which tool's output is more reliable or relevant to the task."
    ),
    "missing_context": Category(
        key="missing_context",
        name="Missing Context",
        description="The task references information that the agent cannot access.",
        guidance="Identify the missing context and determine if it can be inferred or if additional information is needed."
    ),
    "overloaded": Category(
        key="overloaded",
        name="Overloaded",
        description="The instruction contains too many sub-goals, making it difficult to determine the primary objective.",
        guidance="Break down the instruction into smaller, more manageable sub-tasks and prioritize them."
    ),
    "adversarial_input": Category(
        key="adversarial_input",
        name="Adversarial Input",
        description="The input contains subtle prompt injection designed to mislead or manipulate the agent.",
        guidance="Detect any suspicious patterns in the input and assess their potential impact on the agent's response."
    )
}

def all_categories() -> list[Category]:
    return list(CATEGORIES.values())