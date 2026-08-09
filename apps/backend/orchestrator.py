"""
Copilot Orchestrator
Handles the full multi-step workflow:
  1. Intent detection
  2. Asset resolution via MCP
  3. Alarm retrieval & priority scoring via MCP
  4. Operator recommendations via MCP
  5. Document retrieval via RAG
  6. Similar ticket search via MCP
  7. Draft ticket creation via MCP
  8. Grounded answer synthesis via LLM
"""
import asyncio
import logging
import uuid
import datetime
import os
import json
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
logger = logging.getLogger(__name__)

from mcp_client import DirectAlarmClient
from retriever import RAGRetriever
from guardrails import InputGuardrails, OutputGuardrails

_input_guard = InputGuardrails()
_output_guard = OutputGuardrails()

# Support both OpenAI and Ollama (OpenAI-compatible API)
# Set OLLAMA_MODEL=qwen3.5:2b to use Ollama instead of OpenAI
_ollama_model = os.getenv("OLLAMA_MODEL")
_openai_key = os.getenv("OPENAI_API_KEY")

if _ollama_model:
    openai_client = AsyncOpenAI(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key="ollama",  # Ollama doesn't need a real key
    )
    MODEL = _ollama_model
elif _openai_key:
    openai_client = AsyncOpenAI(api_key=_openai_key)
    MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
else:
    openai_client = None
    MODEL = "none"

class CopilotOrchestrator:
    def __init__(self):
        self.alarm_client = DirectAlarmClient()
        self.rag = RAGRetriever()

    def _new_trace(self) -> str:
        return str(uuid.uuid4())

    # ── Intent detection ───────────────────────────────────────────────────────
    async def detect_intent(self, message: str) -> str:
        message_lower = message.lower()
        if any(kw in message_lower for kw in [
            "prepare incident", "prepare an incident", "create ticket", "create an incident",
            "raise ticket", "open incident", "open a ticket", "open ticket",
            "file ticket", "file an incident", "log incident",
        ]):
            return "create_incident"
        if any(kw in message_lower for kw in ["similar ticket", "historical ticket", "past incident", "previous case"]):
            return "find_similar"
        if any(kw in message_lower for kw in ["summarize", "summarise", "what is", "describe", "explain", "tell me about"]):
            return "summarize_alarm"
        if any(kw in message_lower for kw in ["recommend", "action", "what should", "how to fix", "troubleshoot", "steps to"]):
            return "get_recommendations"
        if any(kw in message_lower for kw in ["investigate", "analyse", "analyze", "90 day", "trend", "history", "last 90", "recurring"]):
            return "investigate"
        if any(kw in message_lower for kw in ["correlat", "related alarm", "linked asset", "co-occur"]):
            return "correlate"
        if any(kw in message_lower for kw in [
            "open a ticket", "open ticket", "file ticket", "log incident",
        ]):
            return "create_incident"
        return "general_inquiry"

    # ── Asset resolution ───────────────────────────────────────────────────────
    async def resolve_asset(self, message: str, trace_id: str) -> Optional[dict]:
        # Extract asset name from message
        asset_names = [
            "Boiler Feed Pump 101", "Boiler Feed Pump 102",
            "Compressor C-201", "Compressor C-202", "Compressor C-301",
            "Motor M-501", "Motor M-502", "Turbine T-101",
            "Heat Exchanger HX-101", "BFP-101", "BFP-102",
            "C-201", "C-202", "C-301", "M-501",
        ]
        query = None
        msg_lower = message.lower()
        for name in asset_names:
            if name.lower() in msg_lower:
                query = name
                break

        # Extract site context
        site = None
        if "eastrefinery" in msg_lower or "east refinery" in msg_lower:
            site = "EastRefinery"
        elif "southplant" in msg_lower or "south plant" in msg_lower:
            site = "SouthPlant"

        if not query:
            # Try to pick up generic terms
            if "pump" in msg_lower:
                query = "pump"
            elif "compressor" in msg_lower:
                query = "compressor"
            elif "motor" in msg_lower:
                query = "motor"
            elif "turbine" in msg_lower:
                query = "turbine"
            else:
                query = "Boiler Feed Pump"  # default for demo

        try:
            result = await self.alarm_client.search_asset(query=query, site=site)
            if result.get("results"):
                asset = result["results"][0]
                logger.info(f"Resolved asset: {asset['name']} ({asset['asset_id']})")
                return asset
        except Exception as e:
            logger.warning(f"Asset resolution failed: {e}")
        return None

    # ── Ticket helpers ─────────────────────────────────────────────────────────
    async def search_similar_tickets(self, asset_id: str = None, query: str = "") -> List[dict]:
        try:
            payload: Dict[str, Any] = {"limit": 5}
            if asset_id:
                payload["asset_id"] = asset_id
            if query:
                payload["query"] = query
            data = await self.alarm_client.search_tickets(**payload)
            return data.get("tickets", [])
        except Exception as e:
            logger.warning(f"Ticket search failed: {e}")
            return []

    async def create_draft(
        self,
        title: str,
        description: str,
        asset_id: str,
        asset_name: str,
        alarm_ids: List[str],
        priority: str,
        recommended_actions: List[str],
        rag_sources: List[str],
    ) -> dict:
        return await self.alarm_client.create_ticket_draft(
            title=title,
            description=description,
            asset_id=asset_id,
            asset_name=asset_name,
            alarm_ids=alarm_ids,
            priority=priority,
            recommended_actions=recommended_actions,
            rag_sources=rag_sources,
        )

    async def confirm_ticket(self, draft_id: str, confirmed_by: str = "operator") -> dict:
        return await self.alarm_client.confirm_create_ticket(
            draft_id=draft_id,
            confirmed_by=confirmed_by,
        )

    async def get_draft(self, draft_id: str) -> Optional[dict]:
        data = await self.alarm_client.get_draft(draft_id=draft_id)
        return data.get("draft")

    async def list_tickets(self) -> List[dict]:
        data = await self.alarm_client.list_tickets()
        return data.get("tickets", [])

    # ── LLM synthesis ──────────────────────────────────────────────────────────
    async def synthesize_answer(
        self,
        user_query: str,
        alarm_data: dict,
        asset_data: dict,
        priority_data: dict,
        recommendations: dict,
        rag_docs: List[dict],
        similar_tickets: List[dict],
        draft: Optional[dict] = None,
    ) -> str:
        # Build context
        ctx_parts = []
        if asset_data:
            ctx_parts.append(f"ASSET:\n{json.dumps(asset_data, indent=2)}")
        if alarm_data:
            ctx_parts.append(f"ALARM:\n{json.dumps(alarm_data, indent=2)}")
        if priority_data:
            ctx_parts.append(f"PRIORITY SCORE:\n{json.dumps(priority_data, indent=2)}")
        if recommendations:
            ctx_parts.append(f"OPERATOR RECOMMENDATIONS:\n{json.dumps(recommendations, indent=2)}")
        if rag_docs:
            doc_text = "\n\n".join(
                f"[SOURCE: {d['source']} | Score: {d['score']:.2f}]\n{d['content'][:500]}"
                for d in rag_docs
            )
            ctx_parts.append(f"RELEVANT DOCUMENTATION:\n{doc_text}")
        if similar_tickets:
            ctx_parts.append(f"SIMILAR HISTORICAL TICKETS:\n{json.dumps(similar_tickets[:3], indent=2)}")

        context = "\n\n---\n\n".join(ctx_parts)

        system_prompt = """You are an expert industrial operations copilot for an alarm management system.

Your job is to:
1. Analyse alarm data and asset context
2. Synthesize operator recommendations with documentation evidence
3. Provide a clear, structured incident summary
4. Always cite which documents or tickets support your statements
5. Never fabricate technical details — only use what is in the context

Response format:
## Incident Summary
[2-3 sentences describing the alarm situation]

## Affected Asset
[Asset name, type, criticality, location]

## Alarm Details
[Key alarm info: name, severity, status, duration]

## Priority Assessment
[Priority score and label with reasoning]

## Likely Causes
[Numbered list based on recommendations and historical patterns]

## Recommended Actions
[Numbered step-by-step actions with urgency level]

## Evidence Sources
[List each document or ticket used with source name]

Keep your response factual and grounded in the provided context."""

        user_msg = f"""User query: {user_query}

Context data:
{context}

Provide a complete incident analysis grounded in the above data."""

        if not openai_client:
            return self._fallback_answer(
                user_query=user_query,
                asset_data=asset_data,
                alarm_data=alarm_data,
                priority_data=priority_data,
                recommendations=recommendations,
                rag_docs=rag_docs,
                similar_tickets=similar_tickets,
            )

        try:
            resp = await openai_client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=1200,
                temperature=0.2,
                timeout=150,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            return self._fallback_answer(
                user_query=user_query,
                asset_data=asset_data,
                alarm_data=alarm_data,
                priority_data=priority_data,
                recommendations=recommendations,
                rag_docs=rag_docs,
                similar_tickets=similar_tickets,
            )

    def _fallback_answer(
        self,
        user_query: str,
        asset_data: dict,
        alarm_data: dict,
        priority_data: dict,
        recommendations: dict,
        rag_docs: List[dict],
        similar_tickets: List[dict],
    ) -> str:
        actions = recommendations.get("recommended_actions", []) if isinstance(recommendations, dict) else []
        action_lines = []
        for a in actions[:5]:
            if isinstance(a, dict):
                action_lines.append(f"- Step {a.get('step', '?')}: {a.get('action', 'N/A')}")
            else:
                action_lines.append(f"- {str(a)}")

        citations = [f"- {d.get('source')} (score={d.get('score', 0):.2f})" for d in rag_docs[:5]]
        ticket_refs = [f"- {t.get('ticket_id')}: {t.get('title')}" for t in similar_tickets[:3]]

        return "\n".join(
            [
                "## Incident Summary",
                f"Query: {user_query}",
                f"Asset: {asset_data.get('name', 'Unknown')} ({asset_data.get('asset_id', 'N/A')})",
                f"Alarm: {alarm_data.get('alarm_id', 'N/A')} - {alarm_data.get('alarm_name', 'N/A')}",
                "",
                "## Priority Assessment",
                f"Priority label: {priority_data.get('priority_label', 'unknown')}",
                f"Priority score: {priority_data.get('priority_score', 'N/A')}",
                "",
                "## Recommended Actions",
                *(action_lines or ["- No recommendations were returned."]),
                "",
                "## Similar Tickets",
                *(ticket_refs or ["- No similar tickets found."]),
                "",
                "## Evidence Sources",
                *(citations or ["- No document citations available."]),
            ]
        )

    # ── Main orchestration entry point ─────────────────────────────────────────
    async def handle(self, user_message: str, conversation_id: str = None) -> dict:
        """
        Full orchestration pipeline.
        Returns structured response with answer, draft, citations, MCP trace.
        """
        trace_id = self._new_trace()
        conversation_id = conversation_id or str(uuid.uuid4())
        self.alarm_client.clear_trace()

        logger.info(f"[{trace_id}] Handling: {user_message[:80]}")

        result = {
            "conversation_id": conversation_id,
            "trace_id": trace_id,
            "intent": None,
            "answer": "",
            "asset": None,
            "alarm": None,
            "priority": None,
            "recommendations": None,
            "rag_citations": [],
            "similar_tickets": [],
            "draft": None,
            "mcp_trace": [],
            "guardrail_warnings": [],
            "error": None,
        }

        # ── Step 1: Input guardrails ──────────────────────────────────────────
        guard_in = _input_guard.run(user_message)
        if guard_in.blocked:
            result["error"] = guard_in.block_reason
            result["answer"] = f"\u26d4 {guard_in.block_reason}"
            return result
        clean_message = guard_in.text
        result["guardrail_warnings"].extend(guard_in.warnings)

        try:
            # ── Step 2: Intent ────────────────────────────────────────────────
            intent = await self.detect_intent(clean_message)
            result["intent"] = intent
            logger.info(f"Intent: {intent}")

            # ── Step 3: Asset resolution ──────────────────────────────────────
            asset = await self.resolve_asset(clean_message, trace_id)
            result["asset"] = asset

            # ── Step 4: Get alarms ────────────────────────────────────────────
            alarm_data = None
            top_alarm = None
            if asset:
                alarms_resp = await self.alarm_client.get_alarms(
                    asset_id=asset["asset_id"], trace_id=trace_id
                )
                alarms = alarms_resp.get("data", [])
                if alarms:
                    # Pick highest severity active alarm
                    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                    active = [a for a in alarms if a["status"] in ("active", "acknowledged")]
                    active.sort(key=lambda x: sev_order.get(x["severity"], 99))
                    top_alarm = active[0] if active else alarms[0]
                    alarm_data = await self.alarm_client.get_alarm_detail(
                        top_alarm["alarm_id"], trace_id=trace_id
                    )
                    result["alarm"] = alarm_data

            # ── Step 5: Priority score ────────────────────────────────────────
            priority_data = None
            if top_alarm:
                try:
                    priority_data = await self.alarm_client.priority_score(
                        top_alarm["alarm_id"], trace_id=trace_id
                    )
                    result["priority"] = priority_data
                except Exception as e:
                    logger.warning(f"Priority score failed: {e}")

            # ── Step 6: Operator recommendations ─────────────────────────────
            recommendations = None
            if top_alarm:
                try:
                    recommendations = await self.alarm_client.operator_recommendations(
                        top_alarm["alarm_id"], trace_id=trace_id
                    )
                    result["recommendations"] = recommendations
                except Exception as e:
                    logger.warning(f"Recommendations failed: {e}")

            # ── Step 7: RAG document retrieval ────────────────────────────────
            rag_query = clean_message
            if asset:
                rag_query = f"{asset.get('name', '')} {asset.get('asset_type', '')} {user_message}"
            if top_alarm:
                rag_query += f" {top_alarm.get('alarm_name', '')}"

            try:
                rag_docs = self.rag.retrieve(rag_query, k=4)
                result["rag_citations"] = rag_docs
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
                rag_docs = []

            # ── Step 8: Similar tickets ────────────────────────────────────────
            similar = await self.search_similar_tickets(
                asset_id=asset["asset_id"] if asset else None,
                query=user_message,
            )
            result["similar_tickets"] = similar

            # ── Step 9a: LLM synthesis ─────────────────────────────────────────
            answer = await self.synthesize_answer(
                user_query=clean_message,
                alarm_data=alarm_data or {},
                asset_data=asset or {},
                priority_data=priority_data or {},
                recommendations=recommendations or {},
                rag_docs=rag_docs,
                similar_tickets=similar,
            )
            # ── Step 9b: Output guardrails ─────────────────────────────────────
            guard_out = _output_guard.run(answer, rag_docs, alarm_data or {})
            result["answer"] = guard_out.text
            result["guardrail_warnings"].extend(guard_out.warnings)

            # ── Step 9c: Draft ticket (for incident intents) ───────────────────
            if intent in ("create_incident", "investigate") and asset and top_alarm:
                actions = []
                if recommendations and "recommended_actions" in recommendations:
                    actions = [
                        f"Step {a['step']}: {a['action']}"
                        for a in recommendations["recommended_actions"][:5]
                    ]
                rag_sources = [d["source"] for d in rag_docs[:3]]
                priority_label = priority_data.get("priority_label", "high") if priority_data else "high"

                draft = await self.create_draft(
                    title=f"{asset.get('name', 'Unknown Asset')} — {top_alarm.get('alarm_name', 'Alarm')}",
                    description=(
                        f"Alarm: {top_alarm.get('alarm_name')}\n"
                        f"Description: {top_alarm.get('description')}\n"
                        f"Severity: {top_alarm.get('severity')}\n"
                        f"Status: {top_alarm.get('status')}\n"
                        f"Site: {top_alarm.get('site')} / {top_alarm.get('unit')}\n"
                        f"Start time: {top_alarm.get('start_time')}\n\n"
                        f"Priority score: {priority_data.get('priority_score') if priority_data else 'N/A'}\n\n"
                        f"Recommended actions:\n" + "\n".join(actions)
                    ),
                    asset_id=asset["asset_id"],
                    asset_name=asset["name"],
                    alarm_ids=[top_alarm["alarm_id"]],
                    priority=priority_label,
                    recommended_actions=actions,
                    rag_sources=rag_sources,
                )
                result["draft"] = draft

        except Exception as e:
            logger.exception("Orchestration error")
            result["error"] = str(e)
            result["answer"] = f"Sorry, an error occurred: {e}"

        result["mcp_trace"] = self.alarm_client.get_trace()
        return result