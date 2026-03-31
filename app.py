from datetime import date

import streamlit as st

from pawpal_system import (
    DailyScheduler,
    DueWindow,
    Owner,
    Pet,
    Task,
    TaskFrequency,
    TaskPriority,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")

if "current_pet" not in st.session_state:
    st.session_state.current_pet = None

owner = st.session_state.owner

owner_name = st.text_input("Owner name", value=owner.name)
owner.name = owner_name

pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Create/Select Pet"):
    pet = Pet(name=pet_name, species=species)
    owner.add_pet(pet)
    st.session_state.current_pet = pet
    st.success(f"Added {pet_name} to {owner_name}'s pets!")

st.markdown("### Tasks")
st.caption("Add tasks for the selected pet.")

if st.session_state.current_pet is None:
    if owner.pets:
        st.session_state.current_pet = owner.pets[0]
    else:
        st.info("Create a pet first.")

if st.session_state.current_pet is not None:
    current_pet = st.session_state.current_pet
    st.write(f"**Tasks for {current_pet.name}:**")

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    if st.button("Add task"):
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=TaskPriority(priority),
        )
        current_pet.add_task(task)
        st.session_state.current_pet = current_pet
        st.success(f"Added '{task_title}' to {current_pet.name}!")

    if current_pet.tasks:
        st.write("Current tasks:")
        task_data = [
            {
                "Title": t.title,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority.value,
                "Due Date": t.due_date.isoformat() if t.due_date else "",
                "Due Window": t.due_window.value,
                "Completed": "Yes" if t.completed else "No",
            }
            for t in current_pet.tasks
        ]
        task_data.sort(key=lambda row: (row["Completed"], row["Title"].lower()))
        st.table(task_data)
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate a daily plan based on available time and task priorities.")

available_minutes = st.slider(
    "Available minutes for pet care today", min_value=15, max_value=240, value=60
)

if st.button("Generate schedule"):
    if not owner.pets:
        st.error("Please create at least one pet first.")
    elif not owner.get_all_tasks():
        st.error("Please add at least one task.")
    else:
        scheduler = DailyScheduler(available_minutes=available_minutes)
        plan = scheduler.generate_owner_plan(owner)

        st.success("Schedule generated!")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Scheduled", len(plan.scheduled_tasks))
        with col2:
            st.metric("Skipped", len(plan.skipped_tasks))
        with col3:
            st.metric("Total Minutes", plan.total_minutes())

        task_owner: dict[str, str] = {}
        for pet in owner.pets:
            for task in pet.tasks:
                task_owner[task.task_id] = pet.name

        combined_rows: list[dict[str, str | int]] = []
        for task in plan.scheduled_tasks:
            combined_rows.append(
                {
                    "Status": "Scheduled",
                    "Pet": task_owner.get(task.task_id, "Unknown"),
                    "Title": task.title,
                    "Priority": task.priority.value,
                    "Duration (min)": task.duration_minutes,
                    "Due Date": task.due_date.isoformat() if task.due_date else "",
                    "Due Window": task.due_window.value,
                }
            )

        for task in plan.skipped_tasks:
            combined_rows.append(
                {
                    "Status": "Skipped",
                    "Pet": task_owner.get(task.task_id, "Unknown"),
                    "Title": task.title,
                    "Priority": task.priority.value,
                    "Duration (min)": task.duration_minutes,
                    "Due Date": task.due_date.isoformat() if task.due_date else "",
                    "Due Window": task.due_window.value,
                }
            )

        st.subheader("Task Results")
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            status_filter = st.multiselect(
                "Filter by status",
                ["Scheduled", "Skipped"],
                default=["Scheduled", "Skipped"],
            )
        with filter_col2:
            priority_filter = st.multiselect(
                "Filter by priority",
                ["high", "medium", "low"],
                default=["high", "medium", "low"],
            )
        with filter_col3:
            sort_by = st.selectbox(
                "Sort by",
                ["Due Date", "Priority", "Duration", "Title"],
                index=0,
            )

        priority_rank = {"high": 0, "medium": 1, "low": 2}
        filtered_rows = [
            row
            for row in combined_rows
            if row["Status"] in status_filter and row["Priority"] in priority_filter
        ]

        def row_sort_key(row: dict[str, str | int]) -> tuple:
            due_date_value = row["Due Date"] if row["Due Date"] else date.max.isoformat()
            if sort_by == "Priority":
                return (priority_rank.get(str(row["Priority"]), 99), str(row["Title"]).lower())
            if sort_by == "Duration":
                return (int(row["Duration (min)"]), str(row["Title"]).lower())
            if sort_by == "Title":
                return (str(row["Title"]).lower(),)
            return (due_date_value, str(row["Due Window"]).lower(), str(row["Title"]).lower())

        filtered_rows.sort(key=row_sort_key)

        if filtered_rows:
            st.success(f"Showing {len(filtered_rows)} task(s) after filtering.")
            st.table(filtered_rows)
        else:
            st.warning("No tasks match the selected filters.")

        if plan.warnings:
            for warning in plan.warnings:
                st.warning(warning)

        if plan.conflicts:
            st.warning(f"Detected {len(plan.conflicts)} scheduling conflict(s).")
            conflict_rows = [
                {
                    "Task A": conflict.task_a_title,
                    "Pet A": conflict.pet_a,
                    "Task B": conflict.task_b_title,
                    "Pet B": conflict.pet_b,
                    "Due Date": conflict.due_date.isoformat(),
                    "Window": conflict.due_window.value,
                }
                for conflict in plan.conflicts
            ]
            st.table(conflict_rows)

        with st.expander("Scheduling Reasoning"):
            for note in plan.reasoning_notes:
                st.write(f"• {note}")
