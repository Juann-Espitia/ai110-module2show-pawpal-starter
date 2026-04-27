import json
from pathlib import Path

from pawpal_ai import LocalKnowledgeBase, PawPalAssistant
from pawpal_system import CareTask, DayScheduler, Owner, Pet


def build_scheduler() -> DayScheduler:
    owner = Owner(name="Jordan", available_start="08:00", available_end="18:00")
    pet = Pet(name="Mochi", species="dog", breed="Shiba Inu", age_years=3.0, owner=owner)
    scheduler = DayScheduler(pet=pet)
    scheduler.add_task(CareTask("Breakfast feeding", 10, priority="high", category="feeding"))
    scheduler.add_task(CareTask("Evening walk", 25, priority="high", category="walk"))
    scheduler.build_schedule()
    return scheduler


def build_assistant(tmp_path: Path) -> PawPalAssistant:
    project_dir = Path(__file__).resolve().parent.parent
    knowledge_base = LocalKnowledgeBase.from_directory(project_dir / "knowledge_base")
    return PawPalAssistant(knowledge_base=knowledge_base, log_dir=tmp_path)


def test_retrieval_returns_ranked_documents():
    project_dir = Path(__file__).resolve().parent.parent
    knowledge_base = LocalKnowledgeBase.from_directory(project_dir / "knowledge_base")
    results = knowledge_base.retrieve("feeding exercise routine for busy days")
    assert results
    assert results[0].document.title
    assert results[0].score >= results[-1].score


def test_emergency_question_triggers_guardrail(tmp_path: Path):
    assistant = build_assistant(tmp_path)
    scheduler = build_scheduler()
    result = assistant.answer_question(
        "My dog ate chocolate and is shaking. Is this an emergency?",
        scheduler=scheduler,
    )
    assert result.safety.level == "emergency"
    assert result.used_model == "guardrail"
    assert "emergency veterinarian" in result.answer.lower()


def test_routine_question_returns_retrieved_sources(tmp_path: Path):
    assistant = build_assistant(tmp_path)
    scheduler = build_scheduler()
    result = assistant.answer_question(
        "How can I stay consistent with feeding and exercise on busy days?",
        scheduler=scheduler,
    )
    assert result.safety.level == "routine"
    assert result.retrieved
    assert result.confidence >= 0.4


def test_caution_question_stays_general(tmp_path: Path):
    assistant = build_assistant(tmp_path)
    scheduler = build_scheduler()
    result = assistant.answer_question(
        "My dog skipped a meal and has diarrhea. What should I do?",
        scheduler=scheduler,
    )
    assert result.safety.level == "caution"
    assert "veterinarian" in result.answer.lower() or "monitor" in result.answer.lower()


def test_interaction_is_logged(tmp_path: Path):
    assistant = build_assistant(tmp_path)
    scheduler = build_scheduler()
    result = assistant.answer_question(
        "How should I manage medication reminders?",
        scheduler=scheduler,
    )
    log_path = Path(result.log_path)
    assert log_path.exists()

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    payload = json.loads(lines[-1])
    assert payload["question"] == "How should I manage medication reminders?"
    assert "confidence" in payload
