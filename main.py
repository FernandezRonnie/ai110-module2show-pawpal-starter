from pawpal_system import DailyScheduler, Owner, Pet, Task, TaskPriority


def build_sample_owner() -> Owner:
    owner = Owner(name="Jordan")

    mochi = Pet(name="Mochi", species="dog", age=4)
    luna = Pet(name="Luna", species="cat", age=2)

    mochi.add_task(
        Task(
            title="Morning Walk",
            duration_minutes=30,
            priority=TaskPriority.HIGH,
        )
    )
    mochi.add_task(
        Task(
            title="Breakfast",
            duration_minutes=15,
            priority=TaskPriority.HIGH,
        )
    )
    luna.add_task(
        Task(
            title="Litter Box Cleanup",
            duration_minutes=10,
            priority=TaskPriority.MEDIUM,
        )
    )
    luna.add_task(
        Task(
            title="Play Session",
            duration_minutes=20,
            priority=TaskPriority.LOW,
        )
    )

    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner


def task_owner_lookup(owner: Owner) -> dict[str, str]:
    lookup: dict[str, str] = {}
    grouped = owner.get_tasks_grouped_by_pet(active_only=False)
    for pet_name, tasks in grouped.items():
        for task in tasks:
            lookup[task.task_id] = pet_name
    return lookup


def print_schedule() -> None:
    owner = build_sample_owner()
    scheduler = DailyScheduler(available_minutes=60)
    plan = scheduler.generate_owner_plan(owner)
    owner_by_task_id = task_owner_lookup(owner)

    print("Today's Schedule")
    print("=" * 40)

    print("Scheduled Tasks:")
    if not plan.scheduled_tasks:
        print("- None")
    else:
        for index, task in enumerate(plan.scheduled_tasks, start=1):
            pet_name = owner_by_task_id.get(task.task_id, "Unknown")
            print(
                f"{index}. {task.title} ({task.duration_minutes} min, {task.priority.value}) - {pet_name}"
            )

    print("\nSkipped Tasks:")
    if not plan.skipped_tasks:
        print("- None")
    else:
        for index, task in enumerate(plan.skipped_tasks, start=1):
            pet_name = owner_by_task_id.get(task.task_id, "Unknown")
            print(
                f"{index}. {task.title} ({task.duration_minutes} min, {task.priority.value}) - {pet_name}"
            )

    print("\nSummary:")
    print(plan.summary())


if __name__ == "__main__":
    print_schedule()
