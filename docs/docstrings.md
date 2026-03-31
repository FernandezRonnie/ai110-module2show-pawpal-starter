# PawPal+ Docstring Guide

This guide defines how to write docstrings in this project so code is easier to maintain, review, and test.

## Goals

- Explain intent, not obvious syntax.
- Document behavior and side effects.
- Clarify return values and error conditions.
- Keep style consistent across files.

## Style rules

- Use triple double quotes: `"""Docstring."""`
- Use an imperative first line for functions and methods.
- Keep the first line short and descriptive.
- Add a blank line before extra details when needed.
- Prefer concise prose over long parameter blocks unless the function is complex.

## What should have docstrings

- Every module (`app.py`, `main.py`, `pawpal_system.py`, test modules).
- Every public class.
- Every public function and method.
- Private helpers only when logic is non-obvious.

## Recommended format

### Module docstring

```python
"""Entry point for running a sample PawPal+ schedule in the terminal."""
```

### Function or method docstring

```python
def print_schedule() -> None:
    """Print today's generated schedule, skipped tasks, and summary details."""
```

### Multi-line docstring when behavior needs detail

```python
def generate_owner_plan(self, owner: Owner, tasks: Optional[list[Task]] = None) -> CarePlan:
    """Build a daily plan using tasks across all pets.

    Uses owner context to map task-to-pet relationships for conflict reporting.
    """
```

## Quality checklist

Before committing, verify each docstring:

- Describes what the code does and why.
- Mentions important constraints (time limits, sorting rules, recurrence behavior).
- Notes meaningful side effects (for example, creating follow-up recurring tasks).
- Stays aligned with current implementation.

## Suggested additions in this repo

The core scheduler in `pawpal_system.py` is already documented well. Prioritize these missing spots:

- Add a module docstring to `app.py`.
- Add docstrings for helper functions in `main.py`:
  - `build_sample_owner`
  - `task_owner_lookup`
  - `print_schedule`

## Example updates for `main.py`

```python
def build_sample_owner() -> Owner:
    """Create an owner with sample pets and tasks for local demo runs."""


def task_owner_lookup(owner: Owner) -> dict[str, str]:
    """Map each task ID to the owning pet name for display output."""


def print_schedule() -> None:
    """Generate and print a sample owner schedule with summary and warnings."""
```

## Maintenance notes

- Update docstrings when behavior changes.
- If a function signature changes, confirm the docstring still matches.
- Keep docstrings close to business rules so tests and docs stay in sync.