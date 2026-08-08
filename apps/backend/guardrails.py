"""
Input and Output Guardrails.
Implements all guardrail layers from the system design:
  Input:  PII detection & masking, prompt injection guard, schema/length validation
  Output: response completeness check, confidence scoring, PII redaction
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


# ── PII patterns ───────────────────────────────────────────────────────────────
_PII_PATTERNS: List[Tuple[str, re.Pattern, str]] = [
    ("email",   re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL]"),
    ("phone",   re.compile(r"\b(?:\+?\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}\b"), "[PHONE]"),
    ("ip",      re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP]"),
    ("account", re.compile(r"\b(?:account|acc|acct)[\s#:]*\d{4,12}\b", re.I), "[ACCOUNT]"),
    ("password",re.compile(r"\b(?:password|passwd|pwd)\s*[=:]\s*\S+", re.I), "[CREDENTIAL]"),
    ("token",   re.compile(r"\b(?:api[-_]?key|token|bearer|secret)\s*[=:]\s*\S+", re.I), "[CREDENTIAL]"),
]

# ── Prompt injection patterns ──────────────────────────────────────────────────
_INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|context)", re.I),
    re.compile(r"you\s+are\s+now\s+a?\s*\w+\s*(mode|assistant|bot)", re.I),
    re.compile(r"(forget|disregard)\s+(your\s+)?(instructions?|rules?|guidelines?|constraints?)", re.I),
    re.compile(r"print\s+(your\s+)?(system|base)\s+prompt", re.I),
    re.compile(r"reveal\s+(your\s+)?(instructions?|prompts?|training\s+data)", re.I),
    re.compile(r"<\s*system\s*>", re.I),
    re.compile(r"\[INST\]|\[SYS\]|\[SYSTEM\]"),
    re.compile(r"jailbreak", re.I),
    re.compile(r"do\s+anything\s+now\s*[\(\[]?dan[\)\]]?", re.I),
]

# ── Policy: forbidden topics ───────────────────────────────────────────────────
_POLICY_VIOLATIONS: List[re.Pattern] = [
    re.compile(r"\b(hack|exploit|bypass|bypass\s+security|sql\s+inject)\b", re.I),
]

MAX_INPUT_LENGTH = 2000
MIN_INPUT_LENGTH = 3


# ── Data classes ──────────────────────────────────────────────────────────────
@dataclass
class GuardrailResult:
    passed: bool
    text: str                        # cleaned / masked text
    warnings: List[str] = field(default_factory=list)
    blocked: bool = False
    block_reason: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# INPUT GUARDRAILS
# ═══════════════════════════════════════════════════════════════════════════════
class InputGuardrails:

    def run(self, text: str) -> GuardrailResult:
        warnings: List[str] = []
        cleaned = text

        # 1. Schema / length validation
        if not isinstance(text, str):
            return GuardrailResult(passed=False, text="", blocked=True,
                                   block_reason="Input must be a string")
        if len(text.strip()) < MIN_INPUT_LENGTH:
            return GuardrailResult(passed=False, text="", blocked=True,
                                   block_reason="Input too short")
        if len(text) > MAX_INPUT_LENGTH:
            cleaned = cleaned[:MAX_INPUT_LENGTH]
            warnings.append(f"Input truncated to {MAX_INPUT_LENGTH} characters")

        # 2. Prompt injection detection
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(cleaned):
                return GuardrailResult(
                    passed=False, text="",
                    blocked=True,
                    block_reason="Prompt injection attempt detected — request blocked",
                    warnings=warnings,
                )

        # 3. Policy enforcement
        for pattern in _POLICY_VIOLATIONS:
            if pattern.search(cleaned):
                return GuardrailResult(
                    passed=False, text="",
                    blocked=True,
                    block_reason="Request violates usage policy",
                    warnings=warnings,
                )

        # 4. PII detection and masking
        pii_found: List[str] = []
        for name, pattern, placeholder in _PII_PATTERNS:
            if pattern.search(cleaned):
                cleaned = pattern.sub(placeholder, cleaned)
                pii_found.append(name)
        if pii_found:
            warnings.append(f"PII detected and masked: {', '.join(pii_found)}")

        return GuardrailResult(passed=True, text=cleaned, warnings=warnings)


# ═══════════════════════════════════════════════════════════════════════════════
# OUTPUT GUARDRAILS
# ═══════════════════════════════════════════════════════════════════════════════
class OutputGuardrails:

    _REQUIRED_SECTIONS = ["## Incident Summary", "## Recommended Actions", "## Evidence Sources"]
    _FABRICATION_PHRASES = [
        "I don't have access to",
        "I cannot verify",
        "I'm not sure",
        "As an AI",
        "I don't know",
    ]
    _CAVEAT = "\n\n> ⚠️ **Low confidence**: The above is based on limited evidence. Verify with on-site inspection before taking action."

    def run(
        self,
        answer: str,
        rag_docs: List[Dict[str, Any]],
        alarm_data: Dict[str, Any],
    ) -> GuardrailResult:
        warnings: List[str] = []
        cleaned = answer

        # 1. PII redaction in output
        pii_found: List[str] = []
        for name, pattern, placeholder in _PII_PATTERNS:
            if pattern.search(cleaned):
                cleaned = pattern.sub(placeholder, cleaned)
                pii_found.append(name)
        if pii_found:
            warnings.append(f"PII redacted from output: {', '.join(pii_found)}")

        # 2. Confidence scoring
        score = self._confidence_score(cleaned, rag_docs, alarm_data)

        # 3. Low confidence caveat
        if score < 0.40:
            cleaned += self._CAVEAT
            warnings.append(f"Low confidence response (score={score:.2f}) — caveat added")

        # 4. Completeness check
        if alarm_data and not any(s in cleaned for s in self._REQUIRED_SECTIONS):
            warnings.append("Response may be incomplete — expected structured sections not found")

        # 5. Basic hallucination heuristic (LLM admitting it doesn't know)
        for phrase in self._FABRICATION_PHRASES:
            if phrase.lower() in cleaned.lower():
                warnings.append("Response contains uncertainty phrase — verify before acting")
                break

        return GuardrailResult(passed=True, text=cleaned, warnings=warnings)

    def _confidence_score(
        self,
        answer: str,
        rag_docs: List[Dict[str, Any]],
        alarm_data: Dict[str, Any],
    ) -> float:
        """
        Heuristic confidence 0.0–1.0 based on:
          - Number of RAG documents retrieved
          - Average RAG relevance score
          - Presence of structured alarm data
        """
        score = 0.0

        # RAG contribution (up to 0.50)
        if rag_docs:
            avg_rag = sum(d.get("score", 0.0) for d in rag_docs) / len(rag_docs)
            rag_count_bonus = min(0.20, len(rag_docs) * 0.05)
            score += avg_rag * 0.30 + rag_count_bonus
        
        # Alarm data contribution (up to 0.30)
        if alarm_data and alarm_data.get("alarm_id"):
            score += 0.20
            if alarm_data.get("severity"):
                score += 0.10

        # Answer length heuristic (up to 0.20)
        word_count = len(answer.split())
        score += min(0.20, word_count / 500 * 0.20)

        return min(1.0, round(score, 2))
