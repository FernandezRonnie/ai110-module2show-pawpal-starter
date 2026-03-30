from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional
from uuid import uuid4


class TaskPriority(str, Enum):
    """Supported task priority values."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DueWindow(str, Enum):
    """Supported due-window values for daily planning."""

    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    ANYTIME = "anytime"


class TaskFrequency(str, Enum):
    """Supported recurrence values for pet care tasks."""

    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    AS_NEEDED = "as_needed"


@dataclass
class OwnerConstraints:
    """Optional owner-level constraints for scheduling decisions."""

    available_minutes: int
    preferred_windows: list[DueWindow] = field(default_factory=list)
    max_tasks: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate numeric limits and normalize preferred due windows."""
        if self.available_minutes <= 0:
            raise ValueError("available_minutes must be greater than 0")
        if self.max_tasks is not None and self.max_tasks <= 0:
            raise ValueError("max_tasks must be greater than 0 when provided")

        normalized_windows: list[DueWindow] = []
        for window in self.preferred_windows:
            if isinstance(window, str):
                normalized_windows.append(DueWindow(window.lower().strip()))
            else:
                normalized_windows.append(window)
        self.preferred_windows = normalized_windows


@dataclass
class Task:
    """Data model for one pet care task."""

    title: str
    duration_minutes: int
    priority: TaskPriority
    category: str = "general"
    frequency: TaskFrequency = TaskFrequency.DAILY
    due_window: DueWindow = DueWindow.ANYTIME
    completed: bool = False
    task_id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        """Validate and normalize task attributes into enum-backed values."""
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be greater than 0")

        if isinstance(self.priority, str):
            self.priority = TaskPriority(self.priority.lower().strip())

        if isinstance(self.frequency, str):
            self.frequency = TaskFrequency(self.frequency.lower().strip())

        if isinstance(self.due_window, str):
            self.due_window = DueWindow(self.due_window.lower().strip())

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

    def get_active_tasks(self) -> list[Task]:
        """Return tasks that are not completed."""
        return [task for task in self.tasks if not task.completed]

    def mark_task_complete(self, task_id: str) -> bool:
        """Mark a task complete by ID; return success status."""
        for task in self.tasks:
            if task.task_id == task_id:
                task.mark_complete()
                return True
        return False

    def remove_task(self, task_id: str) -> bool:
        """Remove the first task matching an ID; return success status."""
        for index, task in enumerate(self.tasks):
            if task.task_id == task_id:
                del self.tasks[index]
                return True
        return False


@dataclass
class Owner:
    """Represents an owner that can manage multiple pets and their tasks."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Attach a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove first pet by name; return success status."""
        normalized_name = pet_name.strip().lower()
        for index, pet in enumerate(self.pets):
            if pet.name.strip().lower() == normalized_name:
                del self.pets[index]
                return True
        return False

    def get_all_tasks(self, active_only: bool = True) -> list[Task]:
        """Return all tasks across every pet for this owner."""
        tasks: list[Task] = []
        for pet in self.pets:
            if active_only:
                tasks.extend(pet.get_active_tasks())
            else:
                tasks.extend(pet.tasks)
        return tasks

    def get_tasks_grouped_by_pet(self, active_only: bool = True) -> dict[str, list[Task]]:
        """Return tasks grouped by pet name for owner-level plan display."""
        grouped: dict[str, list[Task]] = {}
        for pet in self.pets:
            grouped[pet.name] = pet.get_active_tasks() if active_only else list(pet.tasks)
        return grouped


class CarePlan:
    """Container for a generated daily plan and scheduler reasoning."""

    def __init__(self, plan_date: date) -> None:
        """Initialize an empty care plan for a specific date."""
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

    def summary(self) -> str:
        """Return a short summary suitable for UI display."""
        return (
            f"{len(self.scheduled_tasks)} scheduled, "
            f"{len(self.skipped_tasks)} skipped, "
            f"{self.total_minutes()} minutes total"
        )


class DailyScheduler:
    """Coordinates task selection and ordering for a single day."""

    def __init__(
        self,
        available_minutes: int,
        constraints: Optional[OwnerConstraints] = None,
    ) -> None:
        """Create a scheduler with an available-time budget and constraints."""
        if available_minutes <= 0:
            raise ValueError("available_minutes must be greater than 0")
        self.available_minutes = available_minutes
        self.constraints = constraints

    def _effective_available_minutes(self) -> int:
        """Resolve available minutes across scheduler and optional owner constraints."""
        if self.constraints is None:
            return self.available_minutes
        return min(self.available_minutes, self.constraints.available_minutes)

    def _priority_weight(self, task: Task) -> int:
        """Return the numeric weight associated with a task priority."""
        if task.priority == TaskPriority.HIGH:
            return 3
        if task.priority == TaskPriority.MEDIUM:
            return 2
        return 1

    def score_task(self, task: Task) -> float:
        """Return a score used to rank tasks."""
        score = float(self._priority_weight(task) * 100)

        # Prefer shorter tasks slightly to improve fit under tight time budgets.
        score -= task.duration_minutes * 0.5

        if (
            self.constraints is not None
            and self.constraints.preferred_windows
            and task.due_window in self.constraints.preferred_windows
        ):
            score += 20.0

        if task.completed:
            score -= 1000.0

        return score

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by scheduler strategy."""
        return sorted(
            tasks,
            key=lambda task: (
                self.score_task(task),
                -task.duration_minutes,
                task.title.lower(),
            ),
            reverse=True,
        )

    def _build_plan(self, tasks: list[Task]) -> CarePlan:
        """Internal helper to create a plan from a prepared task list."""
        active_tasks = [task for task in tasks if not task.completed]
        ranked_tasks = self.sort_tasks(active_tasks)

        plan = CarePlan(plan_date=date.today())
        remaining_minutes = self._effective_available_minutes()
        max_tasks = None if self.constraints is None else self.constraints.max_tasks

        for task in ranked_tasks:
            if max_tasks is not None and len(plan.scheduled_tasks) >= max_tasks:
                plan.skipped_tasks.append(task)
                plan.add_reason(
                    f"Skipped '{task.title}' because max_tasks limit was reached."
                )
                continue

            if task.duration_minutes <= remaining_minutes:
                plan.scheduled_tasks.append(task)
                remaining_minutes -= task.duration_minutes
                plan.add_reason(
                    "Scheduled "
                    f"'{task.title}' "
                    f"({task.priority.value}, {task.duration_minutes} min)."
                )
            else:
                plan.skipped_tasks.append(task)
                plan.add_reason(
                    f"Skipped '{task.title}' due to time limit ({remaining_minutes} min left)."
                )

        plan.add_reason(
            "Plan complete: "
            f"{len(plan.scheduled_tasks)} tasks scheduled, "
            f"{len(plan.skipped_tasks)} skipped, "
            f"{plan.total_minutes()} minutes used."
        )
        return plan

    def generate_plan(self, pet: Pet, tasks: Optional[list[Task]] = None) -> CarePlan:
        """Build and return a CarePlan for the day."""
        candidate_tasks = tasks if tasks is not None else pet.get_active_tasks()
        return self._build_plan(candidate_tasks)

    def generate_owner_plan(
        self,
        owner: Owner,
        tasks: Optional[list[Task]] = None,
    ) -> CarePlan:
        """Build a single daily plan using tasks across all pets for one owner."""
        candidate_tasks = tasks if tasks is not None else owner.get_all_tasks(active_only=True)
        plan = self._build_plan(candidate_tasks)
        plan.add_reason(f"Owner context: {owner.name} with {len(owner.pets)} pet(s).")
        return plan
