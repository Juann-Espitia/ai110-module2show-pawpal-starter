from pathlib import Path

import streamlit as st

from pawpal_ai import LocalKnowledgeBase, PawPalAssistant
from pawpal_system import Owner, Pet, CareTask, DayScheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("A planning and retrieval-assisted pet-care system with safety guardrails.")

BASE_DIR = Path(__file__).parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"
LOG_DIR = BASE_DIR / "logs"

# ── Session state init ────────────────────────────────────────────────────────
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None
if "schedule_output" not in st.session_state:
    st.session_state.schedule_output = None
if "unscheduled" not in st.session_state:
    st.session_state.unscheduled = []
if "assistant" not in st.session_state:
    knowledge_base = LocalKnowledgeBase.from_directory(KNOWLEDGE_DIR)
    st.session_state.assistant = PawPalAssistant(knowledge_base=knowledge_base, log_dir=LOG_DIR)
if "ai_result" not in st.session_state:
    st.session_state.ai_result = None

# ── 1. Owner & Pet Info ───────────────────────────────────────────────────────
st.header("1. Owner & Pet Info")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Owner")
    owner_name = st.text_input("Name", value="Jordan")
    available_start = st.text_input("Available from (HH:MM)", value="08:00")
    available_end = st.text_input("Available until (HH:MM)", value="20:00")
    preferred_walk = st.selectbox("Preferred walk time", ["morning", "afternoon", "evening"])

with col2:
    st.subheader("Pet")
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    breed = st.text_input("Breed", value="Shiba Inu")
    age = st.number_input("Age (years)", min_value=0.0, max_value=30.0, value=3.0, step=0.5)

if st.button("Save Owner & Pet", type="primary"):
    owner = Owner(
        name=owner_name,
        available_start=available_start,
        available_end=available_end,
        preferred_walk_time=preferred_walk,
    )
    pet = Pet(name=pet_name, species=species, breed=breed, age_years=age, owner=owner)
    st.session_state.scheduler = DayScheduler(pet=pet)
    st.session_state.schedule_output = None
    st.session_state.unscheduled = []
    st.session_state.ai_result = None
    st.success(
        f"Saved {pet_name} ({breed}, {species}) for {owner_name}. "
        f"Available window: {available_start}–{available_end} "
        f"({owner.available_minutes} min)"
    )

st.divider()

# ── 2. Manage Tasks ───────────────────────────────────────────────────────────
st.header("2. Manage Tasks")

if st.session_state.scheduler is None:
    st.info("Complete Step 1 first.")
else:
    with st.expander("Add a new task", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col4:
            category = st.selectbox(
                "Category",
                ["feeding", "walk", "medication", "grooming", "enrichment", "general"],
            )

        col_freq, col_due = st.columns(2)
        with col_freq:
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        with col_due:
            due_date = st.text_input("Due date (YYYY-MM-DD, for recurring)", value="")

        notes = st.text_input("Notes (optional)", value="")

        if st.button("Add task"):
            task = CareTask(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                category=category,
                notes=notes,
                frequency=frequency,
                due_date=due_date if due_date else None,
            )
            st.session_state.scheduler.add_task(task)
            st.session_state.schedule_output = None
            st.session_state.ai_result = None
            st.success(f"Added: **{task_title}** ({priority} priority, {frequency})")

    with st.expander("Remove or complete a task"):
        col_r, col_c = st.columns(2)
        with col_r:
            remove_title = st.text_input("Remove task by exact title", key="remove_input")
            if st.button("Remove task"):
                removed = st.session_state.scheduler.remove_task(remove_title)
                if removed:
                    st.session_state.schedule_output = None
                    st.session_state.ai_result = None
                    st.success(f"Removed: {remove_title}")
                else:
                    st.warning(f"No task named '{remove_title}' found.")

        with col_c:
            complete_title = st.text_input("Mark task complete", key="complete_input")
            if st.button("Mark complete"):
                next_task = st.session_state.scheduler.complete_task(complete_title)
                if next_task:
                    st.session_state.ai_result = None
                    st.success(
                        f"Done! Next recurrence scheduled for **{next_task.due_date}**."
                    )
                else:
                    # Still try to find and mark the task even if no recurrence
                    found = any(
                        t.title == complete_title
                        for t in st.session_state.scheduler.tasks
                    )
                    if found:
                        st.session_state.ai_result = None
                        st.success(f"Marked '{complete_title}' as complete.")
                    else:
                        st.warning(f"No task named '{complete_title}' found.")

    if st.session_state.scheduler.tasks:
        st.write("**All tasks:**")
        st.table([
            {
                "Title": t.title,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Category": t.category,
                "Frequency": t.frequency,
                "Status": t.status,
            }
            for t in st.session_state.scheduler.tasks
        ])
    else:
        st.info("No tasks added yet.")

st.divider()

# ── 3. View Day ───────────────────────────────────────────────────────────────
st.header("3. View Today's Schedule")

if st.session_state.scheduler is None:
    st.info("Complete Step 1 first.")
elif not st.session_state.scheduler.tasks:
    st.info("Add at least one task in Step 2 first.")
else:
    if st.button("Generate schedule", type="primary"):
        st.session_state.scheduler.build_schedule()
        st.session_state.schedule_output = st.session_state.scheduler.view_day()
        st.session_state.unscheduled = st.session_state.scheduler.unscheduled_tasks()

    if st.session_state.schedule_output:
        # Sorted timeline table
        sorted_tasks = st.session_state.scheduler.sort_by_time()
        if sorted_tasks:
            st.subheader("Timeline")
            st.table([
                {
                    "Time": t.scheduled_time,
                    "Task": t.title,
                    "Duration": f"{t.duration_minutes} min",
                    "Priority": t.priority.upper(),
                    "Category": t.category,
                    "Status": t.status,
                }
                for t in sorted_tasks
            ])

        # Conflict warnings — shown prominently so the owner can act on them
        conflicts = st.session_state.scheduler.detect_conflicts()
        if conflicts:
            st.subheader("Scheduling Conflicts")
            for warning in conflicts:
                st.warning(f"**Conflict detected:** {warning}")
            st.caption(
                "Two tasks overlap in time. Remove or reschedule one before following this plan."
            )
        else:
            st.success("No scheduling conflicts — your plan is clear!")

        # Tasks that didn't fit
        if st.session_state.unscheduled:
            names = ", ".join(t.title for t in st.session_state.unscheduled)
            st.warning(f"These tasks didn't fit in your available window: **{names}**")

st.divider()

# ── 4. Ask PawPal+ ────────────────────────────────────────────────────────────
st.header("4. Ask PawPal+")

question = st.text_area(
    "Ask a care question",
    value="How can I keep Mochi on track with feeding, medication, and exercise this week?",
    height=110,
)

if st.button("Run retrieval-assisted advice", type="primary"):
    if st.session_state.scheduler is None:
        st.warning("Complete Step 1 first so PawPal+ has pet context.")
    elif not question.strip():
        st.warning("Enter a question first.")
    else:
        st.session_state.ai_result = st.session_state.assistant.answer_question(
            question.strip(),
            scheduler=st.session_state.scheduler,
        )

if st.session_state.ai_result is not None:
    result = st.session_state.ai_result
    if result.safety.level == "emergency":
        st.error(result.answer)
    elif result.safety.level == "caution":
        st.warning(result.answer)
    else:
        st.success(result.answer)

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Confidence", f"{int(result.confidence * 100)}%")
    metric_col2.metric("Safety level", result.safety.level.title())
    metric_col3.metric("Generation mode", result.used_model)

    st.caption(result.safety.reason)
    st.caption(f"Interaction log: {result.log_path}")

    if result.retrieved:
        st.subheader("Retrieved Knowledge")
        st.table(
            [
                {
                    "Title": item.document.title,
                    "Source": item.document.source,
                    "Score": item.score,
                    "Matched terms": ", ".join(item.matched_terms[:5]),
                }
                for item in result.retrieved
            ]
        )
    else:
        st.info("No strong document match was found, so PawPal+ stayed conservative.")

st.divider()

# ── 5. Filter & Sort ──────────────────────────────────────────────────────────
st.header("5. Filter & Sort Tasks")

if st.session_state.scheduler is None:
    st.info("Complete Step 1 first.")
elif not st.session_state.scheduler.tasks:
    st.info("Add tasks in Step 2 to use filters.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by status", ["all", "pending", "complete"])
    with col2:
        category_filter = st.selectbox(
            "Filter by category",
            ["all", "feeding", "walk", "medication", "grooming", "enrichment", "general"],
        )
    with col3:
        sort_by = st.selectbox("Sort by", ["time (scheduled)", "priority"])

    s = st.session_state.scheduler
    filtered = s.filter_tasks(
        status=None if status_filter == "all" else status_filter,
        category=None if category_filter == "all" else category_filter,
    )

    if sort_by == "time (scheduled)":
        filtered = sorted(
            [t for t in filtered if t.scheduled_time],
            key=lambda t: t.scheduled_time or "",
        )
        if not filtered:
            st.info("No scheduled tasks match the filters. Generate a schedule in Step 3 first.")
    else:
        filtered = sorted(filtered, key=lambda t: t.priority_value, reverse=True)

    if filtered:
        st.table([
            {
                "Time": t.scheduled_time or "—",
                "Title": t.title,
                "Priority": t.priority,
                "Category": t.category,
                "Frequency": t.frequency,
                "Status": t.status,
            }
            for t in filtered
        ])
    elif sort_by != "time (scheduled)":
        st.info("No tasks match the selected filters.")
