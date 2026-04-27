from pawpal_ai import LocalKnowledgeBase, PawPalAssistant
from pawpal_system import Owner, Pet, CareTask, DayScheduler

SEP = "=" * 55

# ── Setup ─────────────────────────────────────────────────────────────────────
jordan = Owner(name="Jordan", available_start="08:00", available_end="20:00")
mochi  = Pet(name="Mochi", species="dog", breed="Shiba Inu", age_years=3.0, owner=jordan)
luna   = Pet(name="Luna",  species="cat", breed="Siamese",   age_years=5.0, owner=jordan)

# ── Step 1: Add tasks OUT OF ORDER to test sorting ────────────────────────────
print(SEP)
print("MOCHI'S SCHEDULE")
print(SEP)

mochi_scheduler = DayScheduler(pet=mochi)

# Added deliberately out of time order — sort_by_time() should fix this
mochi_scheduler.add_task(CareTask(
    title="Evening walk",
    duration_minutes=25, priority="high", category="walk",
    scheduled_time="17:00",
))
mochi_scheduler.add_task(CareTask(
    title="Breakfast feeding",
    duration_minutes=10, priority="high", category="feeding",
    scheduled_time="08:00",
))
mochi_scheduler.add_task(CareTask(
    title="Flea medication",
    duration_minutes=5, priority="medium", category="medication",
    frequency="weekly", due_date="2026-03-30",
    scheduled_time="08:10",
))
mochi_scheduler.add_task(CareTask(
    title="Lunch feeding",
    duration_minutes=10, priority="medium", category="feeding",
    frequency="daily", due_date="2026-03-30",
    scheduled_time="12:00",
))
mochi_scheduler.add_task(CareTask(
    title="Playtime",
    duration_minutes=20, priority="low", category="enrichment",
    scheduled_time="15:00",
))

# ── Step 2: Sort by time ──────────────────────────────────────────────────────
print("\n-- Sorted by time --")
for t in mochi_scheduler.sort_by_time():
    print(f"  {t.scheduled_time}  {t.title} ({t.duration_minutes} min) [{t.priority}]")

# ── Step 3: Filter by status and category ────────────────────────────────────
print("\n-- Filter: pending tasks --")
for t in mochi_scheduler.filter_tasks(status="pending"):
    print(f"  {t.title}")

print("\n-- Filter: feeding tasks --")
for t in mochi_scheduler.filter_tasks(category="feeding"):
    print(f"  {t.title} @ {t.scheduled_time}")

# ── Step 4: Recurring tasks ───────────────────────────────────────────────────
print("\n-- Recurring task: complete 'Lunch feeding' (daily) --")
next_task = mochi_scheduler.complete_task("Lunch feeding")
print(f"  Marked complete. Next occurrence: {next_task}")

print("\n-- Recurring task: complete 'Flea medication' (weekly) --")
next_task = mochi_scheduler.complete_task("Flea medication")
print(f"  Marked complete. Next occurrence: {next_task}")

print("\n-- Filter: pending tasks after completions --")
for t in mochi_scheduler.filter_tasks(status="pending"):
    print(f"  {t.title} (due: {t.due_date or 'n/a'})")

# ── Step 5: Conflict detection ────────────────────────────────────────────────
print("\n-- Conflict detection: adding overlapping task --")
mochi_scheduler.add_task(CareTask(
    title="Vet call",
    duration_minutes=30, priority="high", category="general",
    scheduled_time="08:05",   # overlaps Breakfast feeding (08:00–08:10)
))

conflicts = mochi_scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  WARNING: {warning}")
else:
    print("  No conflicts found.")

# ── Step 6: Luna's schedule ───────────────────────────────────────────────────
print(f"\n{SEP}")
print("LUNA'S SCHEDULE")
print(SEP)

luna_scheduler = DayScheduler(pet=luna)
luna_scheduler.add_task(CareTask(
    title="Breakfast feeding",
    duration_minutes=10, priority="high", category="feeding",
    frequency="daily", due_date="2026-03-30",
))
luna_scheduler.add_task(CareTask(
    title="Brush coat",
    duration_minutes=15, priority="medium", category="grooming",
))
luna_scheduler.add_task(CareTask(
    title="Evening play",
    duration_minutes=20, priority="low", category="enrichment",
))

luna_scheduler.build_schedule()
print(luna_scheduler.view_day())

conflicts = luna_scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  WARNING: {warning}")

# ── Step 7: Retrieval-assisted AI guidance ───────────────────────────────────
print(f"\n{SEP}")
print("PAWPAL+ AI ADVISOR")
print(SEP)

knowledge_base = LocalKnowledgeBase.from_directory("knowledge_base")
assistant = PawPalAssistant(knowledge_base=knowledge_base, log_dir="logs")

questions = [
    "How can I keep Mochi consistent with feeding and exercise on busy days?",
    "My dog skipped a meal and has diarrhea. What should I do next?",
    "My dog ate chocolate and is shaking. Is this an emergency?",
]

for question in questions:
    result = assistant.answer_question(question, scheduler=mochi_scheduler)
    print(f"\nQ: {question}")
    print(f"Safety: {result.safety.level}")
    print(f"Confidence: {result.confidence}")
    print(f"Mode: {result.used_model}")
    print("Sources:")
    for item in result.retrieved:
        print(f"  - {item.document.title} ({item.score})")
    print("Answer:")
    print(result.answer)
