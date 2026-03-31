from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
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
class ScheduleConflict:
    """Represents a conflict where two scheduled tasks share the same time slot."""

    task_a_id: str
    task_b_id: str
    task_a_title: str
    task_b_title: str
    pet_a: str
    pet_b: str
    due_date: date
    due_window: DueWindow

    @property
    def is_same_pet_conflict(self) -> bool:
        """Return True when both conflicting tasks belong to the same pet."""
        return self.pet_a == self.pet_b


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
    due_date: Optional[date] = None
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

    def create_next_occurrence(self) -> Optional[Task]:
        """Create a new task instance for the next daily/weekly occurrence."""
        if self.frequency not in (TaskFrequency.DAILY, TaskFrequency.WEEKLY):
            return None

        if self.frequency == TaskFrequency.DAILY:
            delta = timedelta(days=1)
        else:
            delta = timedelta(days=7)

        base_date = self.due_date if self.due_date is not None else date.today()
        next_due_date = base_date + delta

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            frequency=self.frequency,
            due_window=self.due_window,
            due_date=next_due_date,
            completed=False,
        )


@dataclass
class Pet:
    """Data model for a pet and its care preferences/tasks."""

    name: str
    species: str
    age: Optional[int] = None
    care_preferences: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    task_dict: dict[str, Task] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize task dictionary for O(1) lookup by ID."""
        self.task_dict = {task.task_id: task for task in self.tasks}

    def add_task(self, task: Task) -> None:
        """Attach a new task to this pet."""
        self.tasks.append(task)
        self.task_dict[task.task_id] = task

    def get_active_tasks(self) -> list[Task]:
        """Return tasks that are not completed."""
        return [task for task in self.tasks if not task.completed]

    def mark_task_complete(self, task_id: str) -> bool:
        """Mark a task complete by ID; return success status (O(1) lookup)."""
        task = self.task_dict.get(task_id)
        if task is not None:
            task.mark_complete()
            next_task = task.create_next_occurrence()
            if next_task is not None:
                self.add_task(next_task)
            return True
        return False

    def mark_tasks_complete(self, task_ids: list[str]) -> int:
        """Mark multiple tasks complete; return count of successful updates."""
        count = 0
        for task_id in task_ids:
            if self.mark_task_complete(task_id):
                count += 1
        return count

    def remove_task(self, task_id: str) -> bool:
        """Remove the first task matching an ID; return success status (O(1) lookup)."""
        task = self.task_dict.get(task_id)
        if task is not None:
            self.tasks.remove(task)
            del self.task_dict[task_id]
            return True
        return False


@dataclass
class Owner:
    """Represents an owner that can manage multiple pets and their tasks."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    pet_dict: dict[str, Pet] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize pet dictionary for O(1) lookup by name."""
        self.pet_dict = {pet.name.lower(): pet for pet in self.pets}

    def add_pet(self, pet: Pet) -> None:
        """Attach a pet to this owner."""
        self.pets.append(pet)
        self.pet_dict[pet.name.lower()] = pet

    def remove_pet(self, pet_name: str) -> bool:
        """Remove first pet by name; return success status (O(1) lookup)."""
        normalized_name = pet_name.strip().lower()
        pet = self.pet_dict.get(normalized_name)
        if pet is not None:
            self.pets.remove(pet)
            del self.pet_dict[normalized_name]
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

    def filter_tasks(
        self,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> list[Task]:
        """Filter owner tasks by completion status, pet name, or both."""
        if pet_name is not None:
            pet = self.pet_dict.get(pet_name.strip().lower())
            if pet is None:
                return []
            candidate_tasks = list(pet.tasks)
        else:
            candidate_tasks = self.get_all_tasks(active_only=False)

        if completed is None:
            return candidate_tasks

        return [task for task in candidate_tasks if task.completed is completed]

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
        self.conflicts: list[ScheduleConflict] = []
        self.warnings: list[str] = []

    def total_minutes(self) -> int:
        """Return total minutes in scheduled tasks."""
        return sum(task.duration_minutes for task in self.scheduled_tasks)

    def add_reason(self, note: str) -> None:
        """Record a short explanation from scheduler decisions."""
        self.reasoning_notes.append(note)

    def add_warning(self, warning: str) -> None:
        """Record a non-fatal warning message for UI/log display."""
        self.warnings.append(warning)

    def summary(self) -> str:
        """Return a short summary suitable for UI display."""
        return (
            f"{len(self.scheduled_tasks)} scheduled, "
            f"{len(self.skipped_tasks)} skipped, "
            f"{self.total_minutes()} minutes total"
        )


class DailyScheduler:
    """Coordinates task selection and ordering for a single day."""

    # Class-level priority weights for O(1) lookup
    PRIORITY_WEIGHTS = {
        TaskPriority.HIGH: 3,
        TaskPriority.MEDIUM: 2,
        TaskPriority.LOW: 1,
    }
    WINDOW_ORDER = {
        DueWindow.MORNING: 0,
        DueWindow.AFTERNOON: 1,
        DueWindow.EVENING: 2,
        DueWindow.ANYTIME: 3,
    }

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
        self._score_cache: dict[str, float] = {}  # Cache task scores
        # Pre-cache constraint properties for faster access
        self._effective_minutes = self._effective_available_minutes()
        self._max_task_limit = constraints.max_tasks if constraints else None

    def _effective_available_minutes(self) -> int:
        """Resolve available minutes across scheduler and optional owner constraints."""
        if self.constraints is None:
            return self.available_minutes
        return min(self.available_minutes, self.constraints.available_minutes)

    def _priority_weight(self, task: Task) -> int:
        """Return the numeric weight associated with a task priority (dict lookup)."""
        return self.PRIORITY_WEIGHTS.get(task.priority, 1)

    def score_task(self, task: Task) -> float:
        """Return a score used to rank tasks (with caching)."""
        # Check cache first
        if task.task_id in self._score_cache:
            return self._score_cache[task.task_id]

        score = float(self._priority_weight(task) * 100)

        # Prefer shorter tasks to improve fit under tight time budgets
        score -= task.duration_minutes * 0.5

        # Bonus for tasks in preferred time windows
        if (
            self.constraints is not None
            and self.constraints.preferred_windows
            and task.due_window in self.constraints.preferred_windows
        ):
            score += 20.0

        # Bonus for recurring daily tasks
        if task.frequency == TaskFrequency.DAILY:
            score += 15.0

        # Cache and return
        self._score_cache[task.task_id] = score
        return score

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by scheduler strategy (frequency-aware)."""
        # Group tasks by frequency for logical ordering
        daily_tasks = [t for t in tasks if t.frequency == TaskFrequency.DAILY]
        weekly_tasks = [t for t in tasks if t.frequency == TaskFrequency.WEEKLY]
        other_tasks = [t for t in tasks if t.frequency not in (TaskFrequency.DAILY, TaskFrequency.WEEKLY)]

        # Sort each group independently
        for group in [daily_tasks, weekly_tasks, other_tasks]:
            group.sort(
                key=lambda task: (
                    self.score_task(task),
                    -task.duration_minutes,
                    task.title.lower(),
                ),
                reverse=True,
            )

        # Return combined sorted list (daily first, then weekly, then others)
        return daily_tasks + weekly_tasks + other_tasks

    def _chronological_sort_key(self, task: Task, plan_date: date) -> tuple[date, int, str]:
        """Return a key for chronological task display order in plan output."""
        task_date = task.due_date if task.due_date is not None else plan_date
        window_rank = self.WINDOW_ORDER.get(task.due_window, 3)
        return (task_date, window_rank, task.title.lower())

    def _detect_schedule_conflicts(
        self,
        scheduled_tasks: list[Task],
        plan_date: date,
        owner_by_task_id: Optional[dict[str, str]] = None,
        default_pet_name: str = "Unknown",
    ) -> list[ScheduleConflict]:
        """Detect same-slot task conflicts based on due date and due window."""
        slot_map: dict[tuple[date, DueWindow], list[Task]] = {}
        for task in scheduled_tasks:
            # ANYTIME is intentionally ignored because it does not represent a fixed slot.
            if task.due_window == DueWindow.ANYTIME:
                continue
            slot_date = task.due_date if task.due_date is not None else plan_date
            slot_map.setdefault((slot_date, task.due_window), []).append(task)

        conflicts: list[ScheduleConflict] = []
        for (slot_date, slot_window), tasks_in_slot in slot_map.items():
            if len(tasks_in_slot) < 2:
                continue

            for index in range(len(tasks_in_slot)):
                for inner_index in range(index + 1, len(tasks_in_slot)):
                    first = tasks_in_slot[index]
                    second = tasks_in_slot[inner_index]
                    first_pet = (
                        owner_by_task_id.get(first.task_id, default_pet_name)
                        if owner_by_task_id is not None
                        else default_pet_name
                    )
                    second_pet = (
                        owner_by_task_id.get(second.task_id, default_pet_name)
                        if owner_by_task_id is not None
                        else default_pet_name
                    )
                    conflicts.append(
                        ScheduleConflict(
                            task_a_id=first.task_id,
                            task_b_id=second.task_id,
                            task_a_title=first.title,
                            task_b_title=second.title,
                            pet_a=first_pet,
                            pet_b=second_pet,
                            due_date=slot_date,
                            due_window=slot_window,
                        )
                    )

        return conflicts

    def _detect_schedule_conflicts_lightweight(
        self,
        scheduled_tasks: list[Task],
        plan_date: date,
    ) -> list[str]:
        """Return lightweight conflict warnings without raising exceptions."""
        warnings: list[str] = []
        try:
            slot_counts: dict[tuple[date, DueWindow], int] = {}
            for task in scheduled_tasks:
                if task.due_window == DueWindow.ANYTIME:
                    continue
                slot_date = task.due_date if task.due_date is not None else plan_date
                slot_key = (slot_date, task.due_window)
                slot_counts[slot_key] = slot_counts.get(slot_key, 0) + 1

            for (slot_date, slot_window), count in slot_counts.items():
                if count > 1:
                    warnings.append(
                        "Schedule warning: "
                        f"{count} tasks share {slot_window.value} on {slot_date.isoformat()}."
                    )
        except Exception as error:
            warnings.append(
                "Schedule warning: lightweight conflict check could not complete "
                f"({error})."
            )
        return warnings

    def _build_plan(
        self,
        tasks: list[Task],
        owner_by_task_id: Optional[dict[str, str]] = None,
        default_pet_name: str = "Unknown",
    ) -> CarePlan:
        """Internal helper to create a plan from a prepared task list (optimized)."""
        # Filter out completed tasks upfront (O(n) once)
        active_tasks = [task for task in tasks if not task.completed]
        if not active_tasks:
            plan = CarePlan(plan_date=date.today())
            plan.add_reason("No active tasks to schedule.")
            return plan

        # Sort and separate high-priority tasks for guaranteed inclusion
        ranked_tasks = self.sort_tasks(active_tasks)
        high_priority_tasks = [t for t in ranked_tasks if t.priority == TaskPriority.HIGH]
        other_tasks = [t for t in ranked_tasks if t.priority != TaskPriority.HIGH]

        plan = CarePlan(plan_date=date.today())
        remaining_minutes = self._effective_minutes  # Use cached value
        max_tasks = self._max_task_limit  # Use cached value

        # Find minimum task duration for early exit optimization
        min_duration = min((t.duration_minutes for t in other_tasks), default=float('inf')) if other_tasks else float('inf')

        # Schedule high-priority tasks first
        for task in high_priority_tasks:
            if max_tasks is not None and len(plan.scheduled_tasks) >= max_tasks:
                plan.skipped_tasks.append(task)
                plan.add_reason(f"Skipped '{task.title}' because max_tasks limit was reached.")
                continue

            if task.duration_minutes <= remaining_minutes:
                plan.scheduled_tasks.append(task)
                remaining_minutes -= task.duration_minutes
                plan.add_reason(
                    f"Scheduled '{task.title}' (HIGH, {task.duration_minutes} min)."
                )
            else:
                plan.skipped_tasks.append(task)
                plan.add_reason(f"Skipped '{task.title}' due to time limit ({remaining_minutes} min left).")

        # Early exit if remaining time can't fit smallest other task
        if remaining_minutes < min_duration and other_tasks:
            plan.skipped_tasks.extend(other_tasks)
            plan.add_reason(f"Early exit: remaining {remaining_minutes}min < min task {min_duration}min. Skipped {len(other_tasks)} tasks.")
        else:
            # Schedule other tasks
            for task in other_tasks:
                if max_tasks is not None and len(plan.scheduled_tasks) >= max_tasks:
                    plan.skipped_tasks.append(task)
                    plan.add_reason(f"Skipped '{task.title}' because max_tasks limit was reached.")
                    continue

                if task.duration_minutes <= remaining_minutes:
                    plan.scheduled_tasks.append(task)
                    remaining_minutes -= task.duration_minutes
                    plan.add_reason(
                        f"Scheduled '{task.title}' ({task.priority.value}, {task.duration_minutes} min)."
                    )
                else:
                    plan.skipped_tasks.append(task)
                    plan.add_reason(
                        f"Skipped '{task.title}' due to time limit ({remaining_minutes} min left)."
                    )

        plan.add_reason(
            f"Plan complete: {len(plan.scheduled_tasks)} scheduled, "
            f"{len(plan.skipped_tasks)} skipped, {plan.total_minutes()} minutes used."
        )

        lightweight_warnings = self._detect_schedule_conflicts_lightweight(
            scheduled_tasks=plan.scheduled_tasks,
            plan_date=plan.plan_date,
        )
        for warning in lightweight_warnings:
            plan.add_warning(warning)

        try:
            plan.conflicts = self._detect_schedule_conflicts(
                scheduled_tasks=plan.scheduled_tasks,
                plan_date=plan.plan_date,
                owner_by_task_id=owner_by_task_id,
                default_pet_name=default_pet_name,
            )
        except Exception as error:
            plan.add_warning(
                "Schedule warning: detailed conflict detection failed; "
                f"continuing without detailed conflicts ({error})."
            )
            plan.conflicts = []

        if plan.conflicts:
            for conflict in plan.conflicts:
                conflict_scope = (
                    "same pet" if conflict.is_same_pet_conflict else "different pets"
                )
                plan.add_reason(
                    "Conflict detected: "
                    f"'{conflict.task_a_title}' ({conflict.pet_a}) and "
                    f"'{conflict.task_b_title}' ({conflict.pet_b}) at "
                    f"{conflict.due_window.value} on {conflict.due_date.isoformat()} "
                    f"[{conflict_scope}]."
                )

        # Return schedule in chronological order for predictable UI rendering.
        plan.scheduled_tasks.sort(
            key=lambda task: self._chronological_sort_key(task, plan.plan_date)
        )

        return plan

    def generate_plan(self, pet: Pet, tasks: Optional[list[Task]] = None) -> CarePlan:
        """Build and return a CarePlan for the day."""
        candidate_tasks = tasks if tasks is not None else pet.get_active_tasks()
        owner_by_task_id = {task.task_id: pet.name for task in candidate_tasks}
        return self._build_plan(
            candidate_tasks,
            owner_by_task_id=owner_by_task_id,
            default_pet_name=pet.name,
        )

    def generate_owner_plan(
        self,
        owner: Owner,
        tasks: Optional[list[Task]] = None,
    ) -> CarePlan:
        """Build a single daily plan using tasks across all pets for one owner."""
        candidate_tasks = tasks if tasks is not None else owner.get_all_tasks(active_only=True)

        owner_by_task_id: dict[str, str] = {}
        for pet in owner.pets:
            for task in pet.tasks:
                owner_by_task_id[task.task_id] = pet.name

        plan = self._build_plan(
            candidate_tasks,
            owner_by_task_id=owner_by_task_id,
            default_pet_name="Unknown",
        )
        plan.add_reason(f"Owner context: {owner.name} with {len(owner.pets)} pet(s).")
        return plan
