from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Task:
    """Data model for one pet care task."""

    title: str
    duration_minutes: int
    priority: str
    category: str = "general"
    due_window: str = "anytime"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


@dataclass
class Pet:
    """Data model for a pet and its care preferences/tasks."""

    name: str
    species: str
    age: Optional[int] = None
    care_preferences: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a new task to this pet."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """Remove the first task that matches a title; return success status."""
        for index, task in enumerate(self.tasks):
            if task.title == title:
                del self.tasks[index]
                return True
        return False


class CarePlan:
    """Container for a generated daily plan and scheduler reasoning."""

    def __init__(self, plan_date: date) -> None:
        self.plan_date = plan_date
        self.scheduled_tasks: list[Task] = []
        self.skipped_tasks: list[Task] = []
        self.reasoning_notes: list[str] = []

    def total_minutes(self) -> int:
        """Return total minutes in scheduled tasks."""
        return sum(task.duration_minutes for task in self.scheduled_tasks)

    def add_reason(self, note: str) -> None:
        """Record a short explanation from scheduler decisions."""
        self.reasoning_notes.append(note)


class DailyScheduler:
    """Coordinates task selection and ordering for a single day."""

    def __init__(self, available_minutes: int) -> None:
        self.available_minutes = available_minutes

    def score_task(self, task: Task) -> float:
        """Return a score used to rank tasks (stub)."""
        raise NotImplementedError

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by scheduler strategy (stub)."""
        raise NotImplementedError

    def generate_plan(self, pet: Pet, tasks: Optional[list[Task]] = None) -> CarePlan:
        """Build and return a CarePlan for the day (stub)."""
        raise NotImplementedError
