# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Features

- Sorting by priority score and frequency groups (daily, weekly, then other recurring types)
- Chronological schedule output ordering by due date and time window
- Time-budget scheduling that prioritizes high-priority tasks and skips overflow tasks
- Constraint-aware planning (effective minutes, preferred windows bonus, optional max task cap)
- Conflict warnings for duplicate date/time slots, with detailed pairwise conflict reporting
- Daily and weekly recurrence generation when a recurring task is marked complete
- Owner-level aggregation across multiple pets with per-task pet ownership mapping
- Fast O(1) pet and task lookup using internal dictionaries

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Demo

Use the commands below to demo both the CLI and Streamlit versions.

### CLI demo

```bash
python main.py
```

### Streamlit demo

```bash
streamlit run app.py
```

### Demo screenshots


```html
<a href="/course_images/ai110/Screenshot%20from%202026-03-30%2021-40-41.png" target="_blank"><img src='/course_images/ai110/Screenshot%20from%202026-03-30%2021-40-41.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>
<a href="/course_images/ai110/Screenshot%20from%202026-03-30%2021-40-46.png" target="_blank"><img src='/course_images/ai110/Screenshot%20from%202026-03-30%2021-40-46.png' title='PawPal App - Schedule View' width='' alt='PawPal App - Schedule View' class='center-block' /></a>
```


### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Documentation standards

Use the project docstring guide to keep code documentation consistent:

- [`docs/docstrings.md`](docs/docstrings.md)

## Testing PawPal+

The test suite covers core scheduler behavior and key edge cases. Tests verify task lifecycle actions (add, complete, remove), recurrence logic (daily tasks create next-day follow-ups while one-time tasks do not), and scheduling correctness under time limits and constraints. They also validate plan output ordering, owner-level aggregation, and conflict detection when multiple tasks share the same due date and time window.
