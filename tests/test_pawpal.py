from datetime import date

from pawpal_system import (
    DailyScheduler,
    DueWindow,
    Owner,
    OwnerConstraints,
    Pet,
    Task,
    TaskFrequency,
    TaskPriority,
)


def test_task_mark_complete_changes_status() -> None:
    task = Task(title="Meds", duration_minutes=5, priority=TaskPriority.HIGH)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_pet_add_task_increases_task_count() -> None:
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Evening Walk", duration_minutes=25, priority="medium"))

    assert len(pet.tasks) == 1


def test_pet_add_remove_and_complete_task() -> None:
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Walk", duration_minutes=20, priority=TaskPriority.HIGH)

    pet.add_task(task)
    assert len(pet.tasks) == 1
    assert len(pet.get_active_tasks()) == 1

    marked = pet.mark_task_complete(task.task_id)
    assert marked is True
    assert task.completed is True
    # Daily tasks create a follow-up occurrence when completed.
    assert len(pet.get_active_tasks()) == 1
    next_task = pet.get_active_tasks()[0]
    assert next_task.title == "Walk"
    assert next_task.completed is False
    assert next_task.task_id != task.task_id

    removed = pet.remove_task(task.task_id)
    assert removed is True
    assert len(pet.tasks) == 1


def test_owner_aggregates_tasks_across_pets() -> None:
    owner = Owner(name="Jordan")
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")

    mochi.add_task(Task(title="Morning Walk", duration_minutes=30, priority="high"))
    luna.add_task(Task(title="Feed", duration_minutes=10, priority="medium"))

    owner.add_pet(mochi)
    owner.add_pet(luna)

    all_tasks = owner.get_all_tasks(active_only=True)
    assert len(all_tasks) == 2

    grouped = owner.get_tasks_grouped_by_pet(active_only=True)
    assert set(grouped.keys()) == {"Mochi", "Luna"}
    assert len(grouped["Mochi"]) == 1
    assert len(grouped["Luna"]) == 1


def test_scheduler_generate_owner_plan_respects_time_limit() -> None:
    owner = Owner(name="Jordan")
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")

    # Total time = 65, so with 45 available some tasks should be skipped.
    mochi.add_task(Task(title="Walk", duration_minutes=30, priority="high"))
    mochi.add_task(Task(title="Breakfast", duration_minutes=15, priority="high"))
    luna.add_task(Task(title="Play", duration_minutes=20, priority="low"))

    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = DailyScheduler(available_minutes=45)
    plan = scheduler.generate_owner_plan(owner)

    assert plan.total_minutes() <= 45
    assert len(plan.scheduled_tasks) >= 1
    assert len(plan.skipped_tasks) >= 1
    assert any("Plan complete" in note for note in plan.reasoning_notes)


def test_task_normalizes_string_priority() -> None:
    task = Task(title="Meds", duration_minutes=5, priority="HIGH")
    assert task.priority == TaskPriority.HIGH


def test_task_once_frequency_does_not_create_follow_up() -> None:
    pet = Pet(name="Luna", species="cat")
    once_task = Task(
        title="Nail Trim",
        duration_minutes=10,
        priority="medium",
        frequency=TaskFrequency.ONCE,
    )
    pet.add_task(once_task)

    assert pet.mark_task_complete(once_task.task_id) is True
    assert len(pet.get_active_tasks()) == 0


def test_daily_completion_creates_next_day_occurrence() -> None:
    pet = Pet(name="Mochi", species="dog")
    task = Task(
        title="Meds",
        duration_minutes=5,
        priority="high",
        frequency=TaskFrequency.DAILY,
        due_date=date(2026, 3, 30),
    )
    pet.add_task(task)

    assert pet.mark_task_complete(task.task_id) is True

    active = pet.get_active_tasks()
    assert len(active) == 1
    assert active[0].due_date == date(2026, 3, 31)


def test_sort_tasks_groups_daily_before_weekly_and_other() -> None:
    scheduler = DailyScheduler(available_minutes=120)

    weekly = Task(
        title="Weekly Groom",
        duration_minutes=10,
        priority="high",
        frequency=TaskFrequency.WEEKLY,
    )
    daily = Task(
        title="Daily Feed",
        duration_minutes=60,
        priority="low",
        frequency=TaskFrequency.DAILY,
    )
    other = Task(
        title="As Needed Bath",
        duration_minutes=5,
        priority="high",
        frequency=TaskFrequency.AS_NEEDED,
    )

    ordered = scheduler.sort_tasks([weekly, other, daily])
    assert [task.frequency for task in ordered] == [
        TaskFrequency.DAILY,
        TaskFrequency.WEEKLY,
        TaskFrequency.AS_NEEDED,
    ]


def test_scheduler_respects_minimum_available_minutes_constraint() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task(title="Walk", duration_minutes=25, priority="high"))
    pet.add_task(Task(title="Breakfast", duration_minutes=10, priority="medium"))
    owner.add_pet(pet)

    constraints = OwnerConstraints(available_minutes=15)
    scheduler = DailyScheduler(available_minutes=60, constraints=constraints)
    plan = scheduler.generate_owner_plan(owner)

    assert plan.total_minutes() <= 15


def test_scheduler_detects_all_conflict_pairs_in_same_slot() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")

    for title in ["Feed", "Meds", "Walk"]:
        pet.add_task(
            Task(
                title=title,
                duration_minutes=5,
                priority="high",
                due_window=DueWindow.MORNING,
                due_date=date.today(),
            )
        )

    # ANYTIME should not contribute to fixed-slot conflicts.
    pet.add_task(
        Task(
            title="Anytime Play",
            duration_minutes=5,
            priority="high",
            due_window=DueWindow.ANYTIME,
            due_date=date.today(),
        )
    )

    owner.add_pet(pet)
    scheduler = DailyScheduler(available_minutes=60)
    plan = scheduler.generate_owner_plan(owner)

    assert len(plan.conflicts) == 3


def test_scheduler_returns_tasks_in_chronological_order() -> None:
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(
        Task(
            title="Evening meds",
            duration_minutes=10,
            priority="high",
            due_date=date(2026, 4, 1),
            due_window=DueWindow.EVENING,
        )
    )
    pet.add_task(
        Task(
            title="Morning walk",
            duration_minutes=10,
            priority="high",
            due_date=date(2026, 3, 31),
            due_window=DueWindow.MORNING,
        )
    )
    pet.add_task(
        Task(
            title="Afternoon feed",
            duration_minutes=10,
            priority="high",
            due_date=date(2026, 3, 31),
            due_window=DueWindow.AFTERNOON,
        )
    )

    scheduler = DailyScheduler(available_minutes=60)
    plan = scheduler.generate_plan(pet)

    ordered_titles = [task.title for task in plan.scheduled_tasks]
    assert ordered_titles == ["Morning walk", "Afternoon feed", "Evening meds"]


def test_marking_daily_task_complete_creates_following_day_task() -> None:
    pet = Pet(name="Luna", species="cat")
    daily_task = Task(
        title="Daily meds",
        duration_minutes=5,
        priority="high",
        frequency=TaskFrequency.DAILY,
        due_date=date(2026, 3, 30),
    )
    pet.add_task(daily_task)

    assert pet.mark_task_complete(daily_task.task_id) is True

    active = pet.get_active_tasks()
    assert len(active) == 1
    assert active[0].title == "Daily meds"
    assert active[0].due_date == date(2026, 3, 31)


def test_scheduler_flags_duplicate_times_as_conflicts() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(
        Task(
            title="Breakfast",
            duration_minutes=10,
            priority="high",
            due_window=DueWindow.MORNING,
            due_date=date(2026, 3, 31),
        )
    )
    pet.add_task(
        Task(
            title="Medication",
            duration_minutes=10,
            priority="high",
            due_window=DueWindow.MORNING,
            due_date=date(2026, 3, 31),
        )
    )
    owner.add_pet(pet)

    scheduler = DailyScheduler(available_minutes=60)
    plan = scheduler.generate_owner_plan(owner)

    assert len(plan.conflicts) == 1
    assert any("Schedule warning" in warning for warning in plan.warnings)
