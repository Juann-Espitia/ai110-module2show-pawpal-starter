from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class Owner:
    """Represents a pet owner with scheduling preferences."""
    name: str
    available_start: str = "08:00"   # earliest care time (HH:MM)
    available_end: str = "20:00"     # latest care time (HH:MM)
    preferred_walk_time: str = "morning"  # morning | afternoon | evening

    @property
    def available_minutes(self) -> int:
        fmt = "%H:%M"
        start = datetime.strptime(self.available_start, fmt)
        end = datetime.strptime(self.available_end, fmt)
        return int((end - start).total_seconds() / 60)

    def __str__(self) -> str:
        return (
            f"Owner: {self.name} | Available {self.available_start}–{self.available_end} "
            f"| Prefers walks in the {self.preferred_walk_time}"
        )


@dataclass
class Pet:
    """Represents a pet with its basic info linked to an owner."""
    name: str
    species: str          # dog | cat | other
    breed: str
    age_years: float
    owner: Owner

    def needs_walk(self) -> bool:
        return self.species == "dog"

    def __str__(self) -> str:
        return (
            f"Pet: {self.name} ({self.breed}, {self.species}, {self.age_years}yr) "
            f"— owned by {self.owner.name}"
        )


@dataclass
class CareTask:
    """Represents a single pet care task."""
    PRIORITIES = {"low": 1, "medium": 2, "high": 3}

    title: str
    duration_minutes: int
    priority: str = "medium"   # low | medium | high
    category: str = "general"  # feeding | walk | medication | grooming | enrichment | general
    notes: str = ""
    scheduled_time: Optional[str] = None   # set by DayScheduler (HH:MM)

    @property
    def priority_value(self) -> int:
        return self.PRIORITIES.get(self.priority, 1)

    def schedule_at(self, time_str: str) -> None:
        self.scheduled_time = time_str

    def __str__(self) -> str:
        time_part = f" @ {self.scheduled_time}" if self.scheduled_time else " (unscheduled)"
        return (
            f"[{self.priority.upper()}] {self.title} ({self.duration_minutes} min)"
            f"{time_part} — {self.category}"
        )


@dataclass
class DayScheduler:
    """Builds and stores a daily care schedule for a pet."""
    pet: Pet
    tasks: list[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        self.tasks.append(task)

    def remove_task(self, title: str) -> bool:
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.title != title]
        return len(self.tasks) < before

    def build_schedule(self) -> list[CareTask]:
        """Sort tasks by priority (high first), then assign sequential time slots."""
        owner = self.pet.owner
        fmt = "%H:%M"
        current = datetime.strptime(owner.available_start, fmt)
        end = datetime.strptime(owner.available_end, fmt)

        sorted_tasks = sorted(self.tasks, key=lambda t: t.priority_value, reverse=True)
        scheduled = []

        for task in sorted_tasks:
            slot_end = current + timedelta(minutes=task.duration_minutes)
            if slot_end <= end:
                task.schedule_at(current.strftime(fmt))
                current = slot_end
                scheduled.append(task)
            else:
                task.scheduled_time = None  # won't fit today

        return scheduled

    def view_day(self) -> str:
        """Return a formatted string of today's scheduled tasks."""
        scheduled = [t for t in self.tasks if t.scheduled_time]
        if not scheduled:
            return "No tasks scheduled yet. Run build_schedule() first."

        sorted_tasks = sorted(scheduled, key=lambda t: t.scheduled_time or "")
        lines = [
            f"Daily Schedule for {self.pet.name} ({self.pet.owner.name})",
            "=" * 50,
        ]
        total = 0
        for task in sorted_tasks:
            lines.append(str(task))
            total += task.duration_minutes

        lines.append("=" * 50)
        lines.append(f"Total care time: {total} min")
        return "\n".join(lines)

    def unscheduled_tasks(self) -> list[CareTask]:
        return [t for t in self.tasks if not t.scheduled_time]
