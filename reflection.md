# PawPal+ Final Reflection

## Original Project Summary

My original Module 2 project was **PawPal+ Smart Daily Pet Care Planner**. It focused on helping a pet owner organize daily care tasks with priorities, recurrence, sorting, filtering, and conflict detection. The goal was to make pet care more consistent by turning a loose checklist into a structured daily schedule.

## How the Final System Evolved

For the final project, I kept the planner and expanded it into a larger applied AI system. The new version adds a retrieval layer, safety guardrails, confidence scoring, and interaction logging so the system can answer routine pet-care questions while still showing its limits. This made the project feel more like a trustworthy assistant instead of a task manager with a chatbot bolted onto it.

## Why I Built It This Way

I wanted the AI feature to change the product behavior in a meaningful way, not just generate text next to the schedule. In PawPal+, retrieval is integrated into the main workflow: the assistant pulls in pet-care notes, reasons over the live schedule context, and turns the result into concrete next steps. The answer is different because of the retrieved evidence, and the system can also choose not to answer normally when a question looks risky.

## Reliability and Testing

The reliability work happened in three layers:

- Existing scheduler tests verify core product logic like recurrence, filtering, sorting, and conflict detection.
- New AI tests verify retrieval, emergency escalation, caution-mode responses, and JSONL logging.
- The evaluation script checks three representative scenarios: routine planning, symptom monitoring, and emergency triage.

What worked well was the guardrail behavior. The emergency path is simple, explicit, and easy to validate. What remained weaker was semantic retrieval quality, because the local retriever uses keyword overlap rather than embeddings. That tradeoff made the system more explainable and easier to run locally, but it also means wording matters more than it would in a production system.

## Limitations and Biases

The biggest limitation is scope. The knowledge base is small, manually curated, and aimed at general pet-care support, not veterinary diagnosis. That means the system may miss breed-specific details, condition-specific nuance, or edge cases outside the included notes. There is also a bias toward routine care questions because that is what the knowledge base was designed to support.

## Misuse and Prevention

The clearest misuse case is treating PawPal+ like a substitute for a veterinarian. I addressed that by adding emergency triage guardrails and keeping symptom answers general instead of diagnostic. The assistant can still be helpful for planning and observation, but it is intentionally designed to stop short of pretending it can make medical decisions.

## What Surprised Me

The most surprising part of testing was how important it was to define what the assistant should do when it is uncertain. At first it seemed like answering cautiously would be enough, but the emergency scenarios showed that the safest behavior is often to stop generating a normal answer entirely and redirect to human help. That made the system feel much more responsible.

## Collaboration With AI

AI was especially helpful when suggesting concrete implementation pieces like test cases, response structure, and how to break the project into modules. One useful suggestion was to make the AI layer work with the existing scheduler context rather than treating Q&A as a separate feature. That idea strengthened the final architecture because it connected advice back to action.

One flawed suggestion earlier in development was to handle scheduling conflicts by raising an exception. That would have made the app brittle and frustrating for users. Replacing that behavior with plain-English warnings was a better design choice and a good reminder that AI suggestions still need product judgment.

## Final Takeaway

This project taught me that an applied AI system is not just a model call. The surrounding decisions about retrieval, safety, testing, logging, and user trust are what turn a prototype into something more professional. Building PawPal+ this way made the AI feel more grounded, more accountable, and more useful.
