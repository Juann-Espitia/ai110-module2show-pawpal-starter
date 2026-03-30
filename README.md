# PawPal+

A smart daily pet care planner built with Python and Streamlit. PawPal+ helps busy pet owners stay consistent with feeding, walks, medication, and enrichment by generating a prioritized daily schedule and flagging conflicts automatically.

## Features

- **Owner & pet profiles** — store the owner's name, available care window, and preferred walk time alongside the pet's name, species, breed, and age.
- **Task management** — add and remove care tasks with a title, duration, priority (low / medium / high), category, and optional notes.
- **Priority scheduling** — `build_schedule()` sorts tasks highest-priority first and fits them into the owner's available time window, leaving out anything that won't fit.
- **Sort by time** — `sort_by_time()` uses `sorted()` with a lambda key on `HH:MM` strings to display the day's tasks in chronological order.
- **Filter tasks** — `filter_tasks(status, category)` lets you view only pending tasks, only feeding tasks, or any combination of both.
- **Recurring tasks** — tasks can be marked `daily` or `weekly`. When completed, `next_occurrence()` uses `timedelta` to compute the next due date and automatically adds it to the schedule.
- **Conflict detection** — `detect_conflicts()` compares every pair of scheduled tasks for time-window overlap and surfaces a plain-English warning in the UI so the owner can fix it before following the plan.

## Demo


## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run the terminal demo

```bash
python main.py
```

## Smarter Scheduling

PawPal+ goes beyond a simple task list with four algorithmic features:

- **Sort by time** — chronological ordering via `sort_by_time()` regardless of the order tasks were added.
- **Filter tasks** — slice the task list by completion status or category via `filter_tasks()`.
- **Recurring tasks** — `once` / `daily` / `weekly` frequency with automatic next-occurrence generation using `timedelta`.
- **Conflict detection** — `detect_conflicts()` flags overlapping time windows with a human-readable warning instead of crashing.

## Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest test_pawpal.py -v
```

The suite contains **36 tests** organized into 7 groups:

| Group | What is tested |
|---|---|
| Task status | Default `pending` state, `mark_complete()`, idempotency |
| Recurrence | `once` returns `None`, `daily` adds +1 day, `weekly` adds +7 days, fields preserved |
| Task count | Add, remove, remove non-existent task |
| `build_schedule` | Times assigned, priority ordering, tasks that exceed window are unscheduled |
| `sort_by_time` | Chronological order, unscheduled tasks excluded, empty scheduler |
| `filter_tasks` | Filter by status, by category, combined filters, no-match returns empty list |
| Conflict detection | No overlap, exact same time, partial overlap, back-to-back (not a conflict), unscheduled tasks ignored, warning contains task names |

**Confidence level: ★★★★☆**
Core scheduling behaviors are fully covered with happy-path and edge-case tests. The one gap is UI-level integration — the Streamlit session-state flow requires manual verification.

## Project structure

```
pawpal_system.py   # All classes: Owner, Pet, CareTask, DayScheduler
app.py             # Streamlit UI
main.py            # Terminal demo / feature showcase
test_pawpal.py     # 36-test automated suite
diagram.md         # Final Mermaid UML class diagram
reflection.md      # Design and AI collaboration reflection
```
