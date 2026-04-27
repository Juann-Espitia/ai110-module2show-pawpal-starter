import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pawpal_system import DayScheduler

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency at runtime
    OpenAI = None


TOKEN_PATTERN = re.compile(r"[a-zA-Z']+")


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


@dataclass
class KnowledgeDocument:
    doc_id: str
    title: str
    source: str
    content: str


@dataclass
class RetrievedDocument:
    document: KnowledgeDocument
    score: float
    matched_terms: list[str]


@dataclass
class SafetyAssessment:
    level: str
    reason: str


@dataclass
class PawPalAIResponse:
    answer: str
    confidence: float
    safety: SafetyAssessment
    retrieved: list[RetrievedDocument]
    used_model: str
    log_path: str


class LocalKnowledgeBase:
    def __init__(self, documents: list[KnowledgeDocument]):
        self.documents = documents

    @classmethod
    def from_directory(cls, directory: str | Path) -> "LocalKnowledgeBase":
        docs: list[KnowledgeDocument] = []
        path = Path(directory)
        for file_path in sorted(path.glob("*.md")):
            raw = file_path.read_text(encoding="utf-8").strip()
            sections = raw.split("\n", 2)
            title = file_path.stem.replace("_", " ").title()
            source = file_path.name
            content = raw
            for line in sections[:2]:
                if line.startswith("Title:"):
                    title = line.split(":", 1)[1].strip()
                elif line.startswith("Source:"):
                    source = line.split(":", 1)[1].strip()
            docs.append(
                KnowledgeDocument(
                    doc_id=file_path.stem,
                    title=title,
                    source=source,
                    content=content,
                )
            )
        return cls(docs)

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedDocument]:
        query_terms = set(_tokenize(query))
        if not query_terms:
            return []

        ranked: list[RetrievedDocument] = []
        for document in self.documents:
            doc_terms = _tokenize(document.content)
            if not doc_terms:
                continue
            overlap = sorted(query_terms.intersection(doc_terms))
            if not overlap:
                continue
            score = len(overlap) / max(len(query_terms), 1)
            ranked.append(
                RetrievedDocument(
                    document=document,
                    score=round(score, 3),
                    matched_terms=overlap,
                )
            )

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]


class PawPalAssistant:
    HIGH_RISK_TERMS = {
        "bleeding",
        "bloat",
        "breathing",
        "collapse",
        "collapsed",
        "emergency",
        "poison",
        "poisoning",
        "seizure",
        "seizures",
        "toxin",
        "toxic",
        "unresponsive",
        "vomiting blood",
        "hit by car",
        "can't breathe",
    }
    CAUTION_TERMS = {
        "diarrhea",
        "itching",
        "limping",
        "not eating",
        "skipped meal",
        "vomiting",
        "worms",
    }

    def __init__(
        self,
        knowledge_base: LocalKnowledgeBase,
        log_dir: str | Path = "logs",
        api_key: Optional[str] = None,
    ):
        self.knowledge_base = knowledge_base
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def answer_question(
        self,
        question: str,
        scheduler: Optional[DayScheduler] = None,
    ) -> PawPalAIResponse:
        retrieved = self.knowledge_base.retrieve(question)
        safety = self.assess_safety(question)
        confidence = self._score_confidence(question, retrieved, safety)

        if safety.level == "emergency":
            answer = self._emergency_message(question, scheduler)
            used_model = "guardrail"
        else:
            context = self._build_context(question, scheduler, retrieved, safety)
            llm_answer = self._generate_with_openai(context)
            if llm_answer:
                answer = llm_answer
                used_model = "openai"
            else:
                answer = self._generate_fallback(question, scheduler, retrieved, safety)
                used_model = "local-rag"

        log_path = self._log_interaction(
            question=question,
            answer=answer,
            confidence=confidence,
            safety=safety,
            retrieved=retrieved,
            used_model=used_model,
        )
        return PawPalAIResponse(
            answer=answer,
            confidence=confidence,
            safety=safety,
            retrieved=retrieved,
            used_model=used_model,
            log_path=str(log_path),
        )

    def assess_safety(self, question: str) -> SafetyAssessment:
        normalized = question.lower()
        if any(term in normalized for term in self.HIGH_RISK_TERMS):
            return SafetyAssessment(
                level="emergency",
                reason="The question mentions symptoms or events that may need urgent veterinary help.",
            )
        if any(term in normalized for term in self.CAUTION_TERMS):
            return SafetyAssessment(
                level="caution",
                reason="The question involves symptoms, so the answer should stay general and encourage monitoring.",
            )
        return SafetyAssessment(
            level="routine",
            reason="The question appears to be about routine care or planning.",
        )

    def _score_confidence(
        self,
        question: str,
        retrieved: list[RetrievedDocument],
        safety: SafetyAssessment,
    ) -> float:
        base = 0.35
        query_terms = len(set(_tokenize(question)))
        if retrieved:
            base += min(retrieved[0].score, 0.4)
            if len(retrieved) > 1:
                base += 0.1
        if query_terms >= 5:
            base += 0.05
        if safety.level == "caution":
            base -= 0.1
        if safety.level == "emergency":
            base = 0.95
        return round(max(0.1, min(base, 0.99)), 2)

    def _scheduler_summary(self, scheduler: Optional[DayScheduler]) -> str:
        if scheduler is None:
            return "No live pet schedule is attached."
        pet = scheduler.pet
        pending = [task for task in scheduler.tasks if task.status == "pending"]
        task_list = [
            f"- {task.title} ({task.category}, {task.priority}, {task.duration_minutes} min)"
            for task in pending[:6]
        ]
        task_text = "\n".join(task_list) if task_list else "- No pending tasks."
        return (
            f"Pet profile: {pet.name} is a {pet.age_years}-year-old {pet.breed} {pet.species}.\n"
            f"Owner availability: {pet.owner.available_start} to {pet.owner.available_end}.\n"
            f"Pending tasks:\n{task_text}"
        )

    def _build_context(
        self,
        question: str,
        scheduler: Optional[DayScheduler],
        retrieved: list[RetrievedDocument],
        safety: SafetyAssessment,
    ) -> str:
        sources = "\n\n".join(
            [
                f"Title: {item.document.title}\nSource: {item.document.source}\n{item.document.content}"
                for item in retrieved
            ]
        )
        return (
            "You are PawPal+, a grounded pet-care assistant.\n"
            "Use only the retrieved knowledge and the live schedule context.\n"
            "Do not diagnose. For emergencies, advise urgent veterinary contact.\n"
            f"Safety level: {safety.level}\n"
            f"Safety reason: {safety.reason}\n\n"
            f"User question: {question}\n\n"
            f"{self._scheduler_summary(scheduler)}\n\n"
            f"Retrieved knowledge:\n{sources if sources else 'No documents matched strongly.'}\n\n"
            "Respond with:\n"
            "1. A short answer\n"
            "2. Why you suggested it\n"
            "3. A practical next step"
        )

    def _generate_with_openai(self, context: str) -> Optional[str]:
        if not self.api_key or OpenAI is None:
            return None
        try:
            client = OpenAI(api_key=self.api_key)
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=context,
                temperature=0.2,
            )
            return response.output_text.strip()
        except Exception:
            return None

    def _generate_fallback(
        self,
        question: str,
        scheduler: Optional[DayScheduler],
        retrieved: list[RetrievedDocument],
        safety: SafetyAssessment,
    ) -> str:
        pet_name = scheduler.pet.name if scheduler else "your pet"
        opening = {
            "routine": f"For {pet_name}, here is a grounded care suggestion based on the PawPal+ knowledge base.",
            "caution": f"For {pet_name}, I can offer general guidance, but symptom questions should be watched carefully.",
        }.get(safety.level, f"For {pet_name}, this needs extra care.")

        if retrieved:
            top = retrieved[0]
            reason = (
                f"The strongest match was '{top.document.title}', which covered "
                f"{', '.join(top.matched_terms[:5])}."
            )
            guidance = self._extract_relevant_lines(top.document.content, question)
        else:
            reason = "I did not retrieve a strong document match, so I am staying conservative."
            guidance = (
                "Keep the advice simple, focus on observation, hydration, routine, "
                "and contact a veterinarian if symptoms are persistent or worsening."
            )

        next_step = self._suggest_next_step(question, scheduler, safety)
        return f"{opening}\n\n{guidance}\n\nWhy: {reason}\nNext step: {next_step}"

    def _extract_relevant_lines(self, content: str, question: str) -> str:
        query_terms = set(_tokenize(question))
        scored_lines = []
        for line in content.splitlines():
            line_terms = set(_tokenize(line))
            overlap = query_terms.intersection(line_terms)
            if overlap:
                scored_lines.append((len(overlap), line.strip("- ").strip()))
        scored_lines.sort(key=lambda item: item[0], reverse=True)
        selected = [line for _, line in scored_lines[:3] if line]
        if not selected:
            return "The retrieved note supports keeping routines calm, observant, and well-documented."
        return " ".join(selected)

    def _suggest_next_step(
        self,
        question: str,
        scheduler: Optional[DayScheduler],
        safety: SafetyAssessment,
    ) -> str:
        if safety.level == "caution":
            return "Monitor closely, write down timing and symptoms, and contact your veterinarian if it gets worse or repeats."
        if scheduler and scheduler.tasks:
            for task in scheduler.tasks:
                if task.category in {"feeding", "medication", "walk"} and task.status == "pending":
                    return f"Add or review the task '{task.title}' in today's plan so the advice turns into action."
        return "Turn the advice into a concrete care task in PawPal+ so it is easy to follow today."

    def _emergency_message(self, question: str, scheduler: Optional[DayScheduler]) -> str:
        pet_name = scheduler.pet.name if scheduler else "your pet"
        return (
            f"This sounds like a possible emergency for {pet_name}. PawPal+ should not diagnose this in chat.\n\n"
            "Please contact an emergency veterinarian or poison hotline now, especially if your pet is "
            "struggling to breathe, having seizures, collapsing, bleeding heavily, or may have eaten a toxin.\n\n"
            "Next step: stop using the assistant for this question, gather the substance or symptom details, "
            "and call a professional immediately."
        )

    def _log_interaction(
        self,
        question: str,
        answer: str,
        confidence: float,
        safety: SafetyAssessment,
        retrieved: list[RetrievedDocument],
        used_model: str,
    ) -> Path:
        log_path = self.log_dir / "pawpal_ai_log.jsonl"
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": question,
            "answer": answer,
            "confidence": confidence,
            "safety_level": safety.level,
            "safety_reason": safety.reason,
            "used_model": used_model,
            "sources": [
                {
                    "doc_id": item.document.doc_id,
                    "title": item.document.title,
                    "source": item.document.source,
                    "score": item.score,
                }
                for item in retrieved
            ],
        }
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
        return log_path
