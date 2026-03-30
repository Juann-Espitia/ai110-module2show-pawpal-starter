import streamlit as st
from pawpal_system import Owner, Pet, CareTask, DayScheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session state init ────────────────────────────────────────────────────────
# Check before creating so objects survive reruns instead of being reset each time
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None
if "schedule_output" not in st.session_state:
    st.session_state.schedule_output = None
if "unscheduled" not in st.session_state:
    st.session_state.unscheduled = []

# ── 1. Owner & Pet Info ───────────────────────────────────────────────────────
st.header("1. Owner & Pet Info")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_start = st.text_input("Available from (HH:MM)", value="08:00")
    available_end = st.text_input("Available until (HH:MM)", value="20:00")
    preferred_walk = st.selectbox("Preferred walk time", ["morning", "afternoon", "evening"])

with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    breed = st.text_input("Breed", value="Shiba Inu")
    age = st.number_input("Age (years)", min_value=0.0, max_value=30.0, value=3.0, step=0.5)

if st.button("Save Owner & Pet"):
    owner = Owner(
        name=owner_name,
        available_start=available_start,
        available_end=available_end,
        preferred_walk_time=preferred_walk,
    )
    pet = Pet(name=pet_name, species=species, breed=breed, age_years=age, owner=owner)
    st.session_state.scheduler = DayScheduler(pet=pet)
    st.session_state.schedule_output = None  # reset stale schedule
    st.session_state.unscheduled = []
    st.success(f"Saved! {pet} | Available minutes: {owner.available_minutes}")

st.divider()

# ── 2. Schedule Tasks ─────────────────────────────────────────────────────────
st.header("2. Schedule Tasks")

if st.session_state.scheduler is None:
    st.info("Save owner & pet info first.")
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        category = st.selectbox(
            "Category", ["feeding", "walk", "medication", "grooming", "enrichment", "general"]
        )
    notes = st.text_input("Notes (optional)", value="")

    col_add, col_remove = st.columns(2)
    with col_add:
        if st.button("Add task"):
            task = CareTask(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                category=category,
                notes=notes,
            )
            st.session_state.scheduler.add_task(task)
            st.session_state.schedule_output = None  # clear stale schedule
            st.success(f"Added: {task_title}")

    with col_remove:
        remove_title = st.text_input("Remove task by title", key="remove_input")
        if st.button("Remove task"):
            removed = st.session_state.scheduler.remove_task(remove_title)
            if removed:
                st.session_state.schedule_output = None  # clear stale schedule
                st.success(f"Removed: {remove_title}")
            else:
                st.warning(f"Task '{remove_title}' not found.")

    if st.session_state.scheduler.tasks:
        st.write("**Current tasks:**")
        task_data = [
            {
                "Title": t.title,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Category": t.category,
            }
            for t in st.session_state.scheduler.tasks
        ]
        st.table(task_data)
    else:
        st.info("No tasks added yet.")

st.divider()

# ── 3. View Day ───────────────────────────────────────────────────────────────
st.header("3. View Day")

if st.session_state.scheduler is None:
    st.info("Save owner & pet info first.")
elif not st.session_state.scheduler.tasks:
    st.info("Add at least one task before generating a schedule.")
else:
    if st.button("Generate schedule"):
        st.session_state.scheduler.build_schedule()
        # Store results in session_state so they survive the next rerun
        st.session_state.schedule_output = st.session_state.scheduler.view_day()
        st.session_state.unscheduled = st.session_state.scheduler.unscheduled_tasks()

    if st.session_state.schedule_output:
        st.code(st.session_state.schedule_output, language=None)

        conflicts = st.session_state.scheduler.detect_conflicts()
        if conflicts:
            for warning in conflicts:
                st.warning(warning)

        if st.session_state.unscheduled:
            st.warning(
                "These tasks didn't fit in the available window: "
                + ", ".join(t.title for t in st.session_state.unscheduled)
            )

st.divider()

# ── 4. Filter & Sort ──────────────────────────────────────────────────────────
st.header("4. Filter & Sort Tasks")

if st.session_state.scheduler is None:
    st.info("Save owner & pet info first.")
elif not st.session_state.scheduler.tasks:
    st.info("Add at least one task to use filters.")
else:
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filter by status", ["all", "pending", "complete"])
    with col2:
        category_filter = st.selectbox(
            "Filter by category",
            ["all", "feeding", "walk", "medication", "grooming", "enrichment", "general"],
        )

    sort_by = st.radio("Sort by", ["time", "priority"], horizontal=True)

    s = st.session_state.scheduler
    filtered = s.filter_tasks(
        status=None if status_filter == "all" else status_filter,
        category=None if category_filter == "all" else category_filter,
    )

    if sort_by == "time":
        # keep only tasks that have a scheduled time, sorted chronologically
        filtered = sorted(
            [t for t in filtered if t.scheduled_time],
            key=lambda t: t.scheduled_time or "",
        )
    else:
        filtered = sorted(filtered, key=lambda t: t.priority_value, reverse=True)

    if filtered:
        st.table([
            {
                "Time": t.scheduled_time or "—",
                "Title": t.title,
                "Priority": t.priority,
                "Category": t.category,
                "Status": t.status,
            }
            for t in filtered
        ])
    else:
        st.info("No tasks match the selected filters.")
