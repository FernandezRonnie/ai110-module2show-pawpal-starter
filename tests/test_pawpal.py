from pawpal_system import DailyScheduler, Owner, Pet, Task, TaskPriority


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
    assert len(pet.get_active_tasks()) == 0

    removed = pet.remove_task(task.task_id)
    assert removed is True
    assert len(pet.tasks) == 0


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
