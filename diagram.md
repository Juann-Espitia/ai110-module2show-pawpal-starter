# PawPal+ Final Class Diagram

```mermaid
classDiagram
    class Owner {
        +str name
        +str available_start
        +str available_end
        +str preferred_walk_time
        +available_minutes() int
        +__str__() str
    }

    class Pet {
        +str name
        +str species
        +str breed
        +float age_years
        +Owner owner
        +needs_walk() bool
        +__str__() str
    }

    class CareTask {
        +str title
        +int duration_minutes
        +str priority
        +str category
        +str notes
        +str scheduled_time
        +str status
        +str frequency
        +str due_date
        +priority_value() int
        +mark_complete() None
        +next_occurrence() CareTask
        +schedule_at(time_str) None
        +__str__() str
    }

    class DayScheduler {
        +Pet pet
        +list~CareTask~ tasks
        +add_task(task) None
        +remove_task(title) bool
        +build_schedule() list~CareTask~
        +view_day() str
        +unscheduled_tasks() list~CareTask~
        +sort_by_time() list~CareTask~
        +filter_tasks(status, category) list~CareTask~
        +complete_task(title) CareTask
        +detect_conflicts() list~str~
    }

    Owner "1" --> "1..*" Pet : owns
    Pet "1" --> "1" Owner : belongs to
    DayScheduler "1" --> "1" Pet : schedules for
    DayScheduler "1" o-- "0..*" CareTask : manages
    CareTask ..> CareTask : next_occurrence()
```
