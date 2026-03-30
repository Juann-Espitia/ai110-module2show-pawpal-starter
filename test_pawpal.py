import pytest
from pawpal_system import Owner, Pet, CareTask, DayScheduler


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def owner():
    return Owner(name="Jordan", available_start="08:00", available_end="20:00")


@pytest.fixture
def pet(owner):
    return Pet(name="Mochi", species="dog", breed="Shiba Inu", age_years=3.0, owner=owner)


@pytest.fixture
def scheduler(pet):
    return DayScheduler(pet=pet)


def make_task(title="Walk", duration=30, priority="medium", category="walk",
              scheduled_time=None, frequency="once", due_date=None):
    return CareTask(
        title=title,
        duration_minutes=duration,
        priority=priority,
        category=category,
        scheduled_time=scheduled_time,
        frequency=frequency,
        due_date=due_date,
    )


# ── CareTask: status & mark_complete ─────────────────────────────────────────

def test_task_starts_as_pending():
    assert make_task().status == "pending"


def test_mark_complete_changes_status():
    task = make_task()
    task.mark_complete()
    assert task.status == "complete"


def test_mark_complete_is_idempotent():
    task = make_task()
    task.mark_complete()
    task.mark_complete()
    assert task.status == "complete"


# ── CareTask: recurrence ──────────────────────────────────────────────────────

def test_once_task_returns_no_next_occurrence():
    task = make_task(frequency="once", due_date="2026-03-30")
    assert task.next_occurrence() is None


def test_once_task_without_due_date_returns_none():
    task = make_task(frequency="once")
    assert task.next_occurrence() is None


def test_daily_task_next_occurrence_is_next_day():
    task = make_task(frequency="daily", due_date="2026-03-30")
    next_task = task.next_occurrence()
    assert next_task is not None
    assert next_task.due_date == "2026-03-31"


def test_weekly_task_next_occurrence_is_seven_days_later():
    task = make_task(frequency="weekly", due_date="2026-03-30")
    next_task = task.next_occurrence()
    assert next_task is not None
    assert next_task.due_date == "2026-04-06"


def test_recurring_next_occurrence_preserves_task_fields():
    task = make_task(title="Meds", duration=5, priority="high",
                     category="medication", frequency="daily", due_date="2026-03-30")
    next_task = task.next_occurrence()
    assert next_task.title == "Meds"
    assert next_task.duration_minutes == 5
    assert next_task.priority == "high"
    assert next_task.category == "medication"
    assert next_task.status == "pending"


def test_recurring_next_occurrence_has_no_scheduled_time():
    task = make_task(frequency="daily", due_date="2026-03-30", scheduled_time="08:00")
    next_task = task.next_occurrence()
    assert next_task.scheduled_time is None


# ── DayScheduler: task count ──────────────────────────────────────────────────

def test_scheduler_starts_empty(scheduler):
    assert len(scheduler.tasks) == 0


def test_adding_one_task_increases_count(scheduler):
    scheduler.add_task(make_task())
    assert len(scheduler.tasks) == 1


def test_adding_three_tasks_increases_count(scheduler):
    scheduler.add_task(make_task("Walk"))
    scheduler.add_task(make_task("Feed"))
    scheduler.add_task(make_task("Meds"))
    assert len(scheduler.tasks) == 3


def test_removing_task_decreases_count(scheduler):
    scheduler.add_task(make_task("Walk"))
    scheduler.add_task(make_task("Feed"))
    scheduler.remove_task("Walk")
    assert len(scheduler.tasks) == 1


def test_removing_nonexistent_task_returns_false(scheduler):
    scheduler.add_task(make_task("Walk"))
    assert scheduler.remove_task("Grooming") is False
    assert len(scheduler.tasks) == 1


# ── DayScheduler: build_schedule ─────────────────────────────────────────────

def test_build_schedule_assigns_times(scheduler):
    scheduler.add_task(make_task("Walk", duration=30, priority="high"))
    scheduler.build_schedule()
    assert scheduler.tasks[0].scheduled_time == "08:00"


def test_build_schedule_orders_by_priority(scheduler):
    scheduler.add_task(make_task("Low task",  duration=10, priority="low"))
    scheduler.add_task(make_task("High task", duration=10, priority="high"))
    scheduler.build_schedule()
    times = {t.title: t.scheduled_time for t in scheduler.tasks}
    assert times["High task"] < times["Low task"]


def test_task_that_doesnt_fit_is_unscheduled(owner, pet):
    narrow = Owner(name="Busy", available_start="08:00", available_end="08:20")
    small_pet = Pet(name="Tiny", species="cat", breed="Mix", age_years=1.0, owner=narrow)
    s = DayScheduler(pet=small_pet)
    s.add_task(make_task("Short", duration=10, priority="high"))
    s.add_task(make_task("Long",  duration=60, priority="low"))
    s.build_schedule()
    assert s.unscheduled_tasks()[0].title == "Long"


def test_no_tasks_produces_empty_unscheduled(scheduler):
    scheduler.build_schedule()
    assert scheduler.unscheduled_tasks() == []


# ── DayScheduler: sort_by_time ────────────────────────────────────────────────

def test_sort_by_time_returns_chronological_order(scheduler):
    scheduler.add_task(make_task("C", scheduled_time="15:00"))
    scheduler.add_task(make_task("A", scheduled_time="08:00"))
    scheduler.add_task(make_task("B", scheduled_time="12:00"))
    result = scheduler.sort_by_time()
    assert [t.scheduled_time for t in result] == ["08:00", "12:00", "15:00"]


def test_sort_by_time_excludes_unscheduled(scheduler):
    scheduler.add_task(make_task("Scheduled",   scheduled_time="09:00"))
    scheduler.add_task(make_task("Unscheduled", scheduled_time=None))
    result = scheduler.sort_by_time()
    assert len(result) == 1
    assert result[0].title == "Scheduled"


def test_sort_by_time_empty_scheduler(scheduler):
    assert scheduler.sort_by_time() == []


# ── DayScheduler: filter_tasks ────────────────────────────────────────────────

def test_filter_by_status_pending(scheduler):
    scheduler.add_task(make_task("Walk"))
    scheduler.add_task(make_task("Feed"))
    scheduler.tasks[0].mark_complete()
    result = scheduler.filter_tasks(status="pending")
    assert len(result) == 1
    assert result[0].title == "Feed"


def test_filter_by_status_complete(scheduler):
    scheduler.add_task(make_task("Walk"))
    scheduler.tasks[0].mark_complete()
    result = scheduler.filter_tasks(status="complete")
    assert len(result) == 1


def test_filter_by_category(scheduler):
    scheduler.add_task(make_task("Walk",    category="walk"))
    scheduler.add_task(make_task("Feed",    category="feeding"))
    scheduler.add_task(make_task("Groom",   category="grooming"))
    result = scheduler.filter_tasks(category="feeding")
    assert len(result) == 1
    assert result[0].title == "Feed"


def test_filter_combined_status_and_category(scheduler):
    scheduler.add_task(make_task("Morning walk", category="walk"))
    scheduler.add_task(make_task("Evening walk", category="walk"))
    scheduler.tasks[0].mark_complete()
    result = scheduler.filter_tasks(status="pending", category="walk")
    assert len(result) == 1
    assert result[0].title == "Evening walk"


def test_filter_no_match_returns_empty(scheduler):
    scheduler.add_task(make_task("Walk", category="walk"))
    assert scheduler.filter_tasks(category="grooming") == []


# ── DayScheduler: complete_task with recurrence ───────────────────────────────

def test_complete_task_marks_it_done(scheduler):
    scheduler.add_task(make_task("Walk", frequency="once"))
    scheduler.complete_task("Walk")
    assert scheduler.tasks[0].status == "complete"


def test_complete_recurring_task_adds_new_occurrence(scheduler):
    scheduler.add_task(make_task("Feed", frequency="daily", due_date="2026-03-30"))
    scheduler.complete_task("Feed")
    assert len(scheduler.tasks) == 2
    assert scheduler.tasks[1].due_date == "2026-03-31"
    assert scheduler.tasks[1].status == "pending"


def test_complete_once_task_does_not_add_new_occurrence(scheduler):
    scheduler.add_task(make_task("Walk", frequency="once"))
    result = scheduler.complete_task("Walk")
    assert result is None
    assert len(scheduler.tasks) == 1


def test_complete_nonexistent_task_returns_none(scheduler):
    assert scheduler.complete_task("Ghost task") is None


# ── DayScheduler: detect_conflicts ───────────────────────────────────────────

def test_no_conflicts_when_tasks_dont_overlap(scheduler):
    scheduler.add_task(make_task("A", duration=30, scheduled_time="08:00"))
    scheduler.add_task(make_task("B", duration=30, scheduled_time="09:00"))
    assert scheduler.detect_conflicts() == []


def test_exact_same_time_is_a_conflict(scheduler):
    scheduler.add_task(make_task("A", duration=30, scheduled_time="08:00"))
    scheduler.add_task(make_task("B", duration=30, scheduled_time="08:00"))
    assert len(scheduler.detect_conflicts()) == 1


def test_partial_overlap_is_a_conflict(scheduler):
    scheduler.add_task(make_task("A", duration=30, scheduled_time="08:00"))  # ends 08:30
    scheduler.add_task(make_task("B", duration=30, scheduled_time="08:15"))  # starts 08:15
    assert len(scheduler.detect_conflicts()) == 1


def test_back_to_back_tasks_are_not_a_conflict(scheduler):
    scheduler.add_task(make_task("A", duration=30, scheduled_time="08:00"))  # ends 08:30
    scheduler.add_task(make_task("B", duration=30, scheduled_time="08:30"))  # starts 08:30
    assert scheduler.detect_conflicts() == []


def test_unscheduled_tasks_ignored_in_conflict_check(scheduler):
    scheduler.add_task(make_task("A", duration=30, scheduled_time="08:00"))
    scheduler.add_task(make_task("B", duration=30, scheduled_time=None))
    assert scheduler.detect_conflicts() == []


def test_conflict_message_contains_task_names(scheduler):
    scheduler.add_task(make_task("Morning walk", duration=30, scheduled_time="08:00"))
    scheduler.add_task(make_task("Vet call",     duration=30, scheduled_time="08:00"))
    warnings = scheduler.detect_conflicts()
    assert any("Morning walk" in w for w in warnings)
    assert any("Vet call" in w for w in warnings)
