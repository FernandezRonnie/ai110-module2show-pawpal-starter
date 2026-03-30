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
                "Completed": "✓" if t.completed else "",
            }
            for t in current_pet.tasks
        ]
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

        if plan.scheduled_tasks:
            st.subheader("✓ Scheduled Tasks")
            for idx, task in enumerate(plan.scheduled_tasks, 1):
                st.write(f"{idx}. **{task.title}** ({task.duration_minutes} min, {task.priority.value})")

        if plan.skipped_tasks:
            st.subheader("✗ Skipped Tasks (time limit reached)")
            for idx, task in enumerate(plan.skipped_tasks, 1):
                st.write(f"{idx}. {task.title} ({task.duration_minutes} min, {task.priority.value})")

        with st.expander("Scheduling Reasoning"):
            for note in plan.reasoning_notes:
                st.write(f"• {note}")
