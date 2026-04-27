# PawPal+ Applied AI System Diagram

```mermaid
flowchart TD
    A["Owner input<br/>pet profile, tasks, question"] --> B["Streamlit application"]
    B --> C["DayScheduler<br/>task priority, recurrence, conflicts"]
    B --> D["LocalKnowledgeBase<br/>markdown pet-care notes"]
    D --> E["Retriever<br/>keyword overlap ranking"]
    B --> F["Safety assessment<br/>routine, caution, emergency"]
    C --> G["Live planner context"]
    E --> H["Retrieved evidence"]
    F --> I["Response layer"]
    G --> I
    H --> I
    I --> J["OpenAI synthesis when key exists"]
    I --> K["Local grounded fallback"]
    J --> L["Final answer"]
    K --> L
    L --> M["Confidence score + cited sources"]
    L --> N["JSONL interaction log"]
    O["Automated tests and evaluation script"] --> N
    O --> M
```

## Architecture Notes

- The original scheduling engine remains the core product workflow.
- Retrieval is local and deterministic, which makes testing and explanation easier.
- Safety assessment sits in front of generation so high-risk questions can be escalated before the assistant tries to sound helpful.
- The response layer can use OpenAI for better phrasing, but the system still runs without an API key.
