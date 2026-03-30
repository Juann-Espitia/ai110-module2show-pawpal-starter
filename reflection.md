# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

My initial UML design is organized around three core concerns: who is involved (owner and pet), what needs to happen (tasks), and how to plan the day (scheduler). The diagram uses four classes connected by ownership and composition relationships. `Owner` connects to `Pet`, `Pet` connects to `DayScheduler`, and `DayScheduler` aggregates many `CareTask` objects. This gave me a clear separation between data (owner/pet info), work items (tasks), and logic (scheduling).

- What classes did you include, and what responsibilities did you assign to each?

I ended up with four classes instead of three:

1. **`Owner`** — stores the owner's name, daily availability window (start and end time), and preferred walk time. It also computes how many total minutes are available in a day, which the scheduler uses to fit tasks.

2. **`Pet`** — stores the pet's name, species, breed, and age, and holds a reference to its `Owner`. It also has a `needs_walk()` helper that returns `True` for dogs, making it easy to apply species-specific logic later.

3. **`CareTask`** — represents a single care activity (walk, feeding, medication, grooming, etc.) with a title, duration in minutes, priority level (low/medium/high), category, and optional notes. It holds a `scheduled_time` field that gets set once the scheduler assigns it a slot.

4. **`DayScheduler`** — the central coordinator. It holds a reference to the `Pet` (and through it the `Owner`) and manages a list of `CareTask` objects. It exposes `add_task()`, `remove_task()`, `build_schedule()` (which sorts by priority and assigns sequential time slots), and `view_day()` (which prints the final agenda).

**b. Design changes**

- Did your design change during implementation?

Yes — the design grew significantly during the implementation phase. The initial plan had three classes and basic scheduling. By the end, `CareTask` gained a `status`, `frequency`, and `due_date` field, and a `next_occurrence()` method for recurring tasks. `DayScheduler` gained four new methods: `sort_by_time()`, `filter_tasks()`, `complete_task()`, and `detect_conflicts()`.

- If yes, describe at least one change and why you made it.

The most significant change was adding recurrence to `CareTask`. Originally, tasks were one-time events. The need to model real pet care — where feeding and medication happen every day — made it clear that a `frequency` field and `next_occurrence()` method were necessary. Rather than managing this logic in `DayScheduler`, it made more sense to put it on the task itself so each task knows how to reproduce itself.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

The scheduler considers three constraints: (1) **priority** — high-priority tasks are scheduled first and are guaranteed a slot before lower-priority ones; (2) **available time window** — tasks are only scheduled if they fit within the owner's `available_start` to `available_end` range; (3) **duration** — each task consumes a contiguous block of minutes, and no two tasks can occupy the same slot in `build_schedule()`.

- How did you decide which constraints mattered most?

Priority was chosen as the primary constraint because a pet owner's first concern is making sure critical care (medication, feeding) happens before optional enrichment. Time window was the secondary constraint because it reflects real-world limits. Duration is simply required for the logic to work at all.

**b. Tradeoffs**

The conflict detector checks for overlapping time windows using exact `datetime` comparisons — it catches cases where two tasks literally overlap in clock time, but it does not account for travel time between tasks or soft buffers (e.g., a dog needing 10 minutes to cool down after a walk before eating). This means the scheduler can produce a technically conflict-free plan that is still impractical in real life.

This tradeoff is reasonable for a first version because it keeps the logic simple and deterministic: no guessing at travel distances or pet-specific recovery times. A more accurate model would require additional data (location of tasks, species-specific cooldown rules) that we don't collect yet. For a pet owner using this as a rough daily guide, exact-overlap detection is already a useful safety net without overcomplicating the system.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project?

AI was used across every phase: brainstorming the class structure in the design stage, writing boilerplate dataclass code, suggesting method signatures for sorting and filtering, generating the initial test plan, and explaining the rationale behind edge cases like back-to-back tasks not being a conflict. The most productive use was asking "what edge cases should I test for a scheduler with recurring tasks?" — this surfaced scenarios (like `next_occurrence()` stripping the `scheduled_time`) that I might have missed.

- What kinds of prompts were most helpful?

Specific, scoped prompts worked best. "Add a `next_occurrence()` method to `CareTask` that uses `timedelta` to return a new task for the next due date" produced usable code immediately. Broad prompts like "make the scheduler smarter" produced suggestions that were too vague to implement directly. Framing prompts around a concrete behavior ("what should happen when a daily task is marked complete?") consistently gave better results than asking for general improvements.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

When asked to implement conflict detection, the AI initially suggested raising an exception when a conflict was found. I rejected this because crashing the program would be a poor user experience — a pet owner who accidentally schedules two overlapping tasks should see a warning, not an error. I changed the method to return a list of warning strings instead, which the UI could then display with `st.warning()`.

- How did you evaluate or verify what the AI suggested?

Every suggestion was verified by running the test suite. If a suggested implementation caused a test to fail, I examined the failing case directly rather than asking the AI to fix it blindly. I also read every generated method before adding it to make sure the logic matched my mental model of what the class was supposed to do.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

The 36-test suite covers: task status transitions (`pending` → `complete`), recurrence date math (`daily` +1 day, `weekly` +7 days), task count changes on add/remove, `build_schedule()` priority ordering and time assignment, `sort_by_time()` chronological ordering, `filter_tasks()` by status and category, `complete_task()` recurrence auto-append, and `detect_conflicts()` with overlap, no-overlap, back-to-back, and unscheduled task cases.

- Why were these tests important?

The recurrence and conflict tests were the most important because those features involve date arithmetic and pairwise comparisons — exactly the kind of logic where an off-by-one error or a wrong comparison operator produces a bug that's invisible until a specific input triggers it. Testing them with explicit date strings and known time windows made the behavior unambiguous.

**b. Confidence**

- How confident are you that your scheduler works correctly?

4 out of 5. The backend logic is well-covered. The one area of lower confidence is the Streamlit UI session-state behavior — specifically, whether the schedule correctly resets when a new owner/pet is saved mid-session, and whether the recurring task auto-append behaves correctly across multiple Streamlit reruns.

- What edge cases would you test next if you had more time?

A pet with zero tasks (view_day should return a clear message), tasks with identical titles (remove_task removes only the first match or all?), a due date at the end of a month or year (January 31 + 1 day = February 1, not February 31), and a scheduler whose available window is exactly equal to the total duration of all tasks.

---

## 5. Reflection

**a. What went well**

The class structure held up well throughout the entire build. The decision to give `CareTask` its own `next_occurrence()` method — rather than putting that logic in `DayScheduler` — paid off during testing because each class could be tested independently. The 4-section Streamlit UI (owner/pet, manage tasks, view day, filter/sort) also mapped cleanly onto the four main user actions, which made connecting the backend to the UI straightforward.

**b. What you would improve**

The biggest thing to redesign is the single-pet model. Right now, one `DayScheduler` serves one `Pet`. A real-world version would have one owner managing multiple pets, each with their own tasks, and a shared daily view that merges them. This would require either a list of schedulers or a higher-level `DailyPlanner` class that coordinates across pets and can detect cross-pet conflicts.

**c. Key takeaway**

The most important lesson was that AI tools are most valuable when you already have a clear design. When I knew what I wanted — "a method that returns warning strings for overlapping tasks" — the AI produced working code quickly. When I didn't have a clear picture, the AI's suggestions added features I hadn't thought through. Being the lead architect means deciding what the system should do before asking AI to help implement it, and then verifying every piece before trusting it.
