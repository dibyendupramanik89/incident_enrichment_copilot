"""Incident & Ticket Enrichment Copilot — Gradio frontend.

Panels:
  Tab 1 Investigation  : free-form chat, answer markdown, example prompts
  Tab 2 Alarm & Asset  : alarm details + priority badge + recommendations
  Tab 3 Ticket Draft   : editable title / description / priority, confirm HITL
  Tab 4 Similar Tickets: dataframe of historical matches
  Tab 5 RAG Citations  : source list with relevance scores
  Tab 6 MCP Trace      : dataframe of every MCP tool call + latency
  Tab 7 Audit Log      : running session log
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import gradio as gr
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
TIMEOUT = int(os.getenv("BACKEND_TIMEOUT", "180"))

# ── Sample prompts ─────────────────────────────────────────────────────────────
EXAMPLE_PROMPTS = [
    "Prepare an incident for the highest-priority active alarm in EastRefinery",
    "What is the status of BFP-101 and any active alarms?",
    "Recommend actions for the current compressor alarm in SouthPlant",
    "Find similar historical tickets for motor overload events",
    "Investigate recurring low suction pressure alarms on BFP-101 over last 90 days",
    "Summarise all active critical alarms and their recommended responses",
]

# ── Helpers ────────────────────────────────────────────────────────────────────
def _safe_post(path: str, payload: dict) -> dict:
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        return {"error": f"Cannot connect to backend at {BACKEND_URL}. Is the server running?"}
    except requests.Timeout:
        return {"error": "Backend timed out. The investigation took too long."}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def _fmt_list(items: list[str], bullet: str = "•") -> str:
    return "\n".join(f"{bullet} {i}" for i in items) if items else "—"


def _alarm_markdown(alarm: Optional[dict]) -> str:
    if not alarm:
        return "*No alarm data available.*"
    sev = alarm.get("severity", "unknown")
    sev_colour = {
        "critical": "#FF4444",
        "high": "#FF8800",
        "medium": "#FFCC00",
        "low": "#44BB44",
    }.get(sev, "#888888")
    lines = [
        f"**Alarm ID:** `{alarm.get('alarm_id', 'N/A')}`",
        f"**Name:** {alarm.get('alarm_name', 'N/A')}",
        f"**Severity:** <span style='color:{sev_colour}; font-weight:bold;'>{sev.upper()}</span>",
        f"**Status:** {alarm.get('status', 'N/A')}",
        f"**Description:** {alarm.get('description', 'N/A')}",
        f"**Start Time:** {alarm.get('start_time', 'N/A')}",
        f"**Site / Unit:** {alarm.get('site', 'N/A')} / {alarm.get('unit', 'N/A')}",
        f"**Tag:** `{alarm.get('tag', 'N/A')}`",
    ]
    return "  \n".join(lines)


def _asset_markdown(asset: Optional[dict]) -> str:
    if not asset:
        return "*No asset data available.*"
    crit = asset.get("criticality", "unknown")
    crit_colour = {
        "critical": "#FF4444",
        "high": "#FF8800",
        "medium": "#FFCC00",
    }.get(crit, "#44BB44")
    lines = [
        f"**Asset ID:** `{asset.get('asset_id', 'N/A')}`",
        f"**Name:** {asset.get('name', 'N/A')}",
        f"**Type:** {asset.get('asset_type', 'N/A')}",
        f"**Criticality:** <span style='color:{crit_colour}; font-weight:bold;'>{crit.upper()}</span>",
        f"**Site:** {asset.get('site', 'N/A')}",
        f"**Unit:** {asset.get('unit', 'N/A')}",
        f"**Manufacturer:** {asset.get('manufacturer', 'N/A')}",
        f"**Model:** {asset.get('model', 'N/A')}",
    ]
    return "  \n".join(lines)


def _priority_badge(priority: Optional[dict]) -> str:
    if not priority:
        return "*Priority not evaluated yet.*"
    label = priority.get("priority_label", "unknown").upper()
    score = priority.get("priority_score", "N/A")
    drivers = _fmt_list(priority.get("drivers", []))
    colours = {"CRITICAL": "#FF4444", "HIGH": "#FF8800", "MEDIUM": "#FFCC00", "LOW": "#44BB44"}
    colour = colours.get(label, "#888888")
    return (
        f"<div style='padding:12px;border-radius:8px;background:{colour}22;border:2px solid {colour};'>"
        f"<b style='color:{colour};font-size:1.3em;'>{label}</b>  (score: {score})"
        f"<br/><b>Drivers:</b> {drivers}</div>"
    )


def _recommendations_markdown(recs: Optional[dict]) -> str:
    if not recs:
        return "*No recommendations available.*"
    actions = recs.get("recommended_actions", [])
    causes = recs.get("likely_causes", [])
    lines = ["### Likely Causes"]
    for i, c in enumerate(causes[:5], 1):
        lines.append(f"{i}. {c}")
    lines += ["", "### Recommended Actions"]
    for a in actions[:6]:
        if isinstance(a, dict):
            urgency = a.get("urgency", "")
            tag = f" *(urgency: {urgency})*" if urgency else ""
            lines.append(f"- **Step {a.get('step', '?')}**: {a.get('action', 'N/A')}{tag}")
        else:
            lines.append(f"- {a}")
    return "\n".join(lines)


def _rag_citations_data(docs: list[dict]) -> list[list]:
    return [
        [
            d.get("source", ""),
            f"{d.get('score', 0):.3f}",
            d.get("content", "")[:250] + ("..." if len(d.get("content", "")) > 250 else ""),
        ]
        for d in docs
    ]


def _mcp_trace_data(trace: list[dict]) -> list[list]:
    return [
        [
            t.get("tool", ""),
            t.get("server", ""),
            t.get("duration_ms", ""),
            "✅" if t.get("success") else f"❌ {t.get('error', '')}",
        ]
        for t in trace
    ]


def _similar_tickets_data(tickets: list[dict]) -> list[list]:
    return [
        [
            t.get("ticket_id", ""),
            t.get("title", ""),
            t.get("status", ""),
            t.get("priority", ""),
            t.get("asset_name", ""),
        ]
        for t in tickets
    ]


def _audit_entry(action: str, data: dict) -> str:
    ts = datetime.now().strftime("%H:%M:%S")
    intent = data.get("intent", "—")
    trace = data.get("trace_id", "—")[:8]
    warn_count = len(data.get("guardrail_warnings", []))
    return f"[{ts}] {action} | intent={intent} trace={trace} warnings={warn_count}"


# ── Core handlers ──────────────────────────────────────────────────────────────
def run_investigation(message: str, audit_log: list[str]):
    """Calls /chat and fans out the response into all UI panels."""
    _empty = ("*Please enter a message.*", "—", "—", "—", "", "—", "", "", "", "high", [], [], [], audit_log)
    if not message.strip():
        return _empty

    data = _safe_post("/chat", {"message": message})

    if "error" in data and data["error"]:
        err_md = f"\u26d4 **Error:** {data['error']}"
        return (err_md, "—", "—", "—", "", "—", "", "", "", "high", [], [], [], audit_log)

    # ── Investigation tab ──────────────────────────────────────────────────────
    answer_md = data.get("answer", "*No answer returned.*")
    intent_md = f"**Intent detected:** `{data.get('intent', '—')}`"
    warnings = data.get("guardrail_warnings", [])
    if warnings:
        intent_md += "\n\n⚠️ **Guardrail Warnings:**\n" + _fmt_list(warnings)

    # ── Alarm & Asset tab ──────────────────────────────────────────────────────
    alarm_md = _alarm_markdown(data.get("alarm"))
    asset_md = _asset_markdown(data.get("asset"))
    priority_md = _priority_badge(data.get("priority"))
    recs_md = _recommendations_markdown(data.get("recommendations"))

    # ── Ticket Draft tab ──────────────────────────────────────────────────────
    draft = data.get("draft") or {}
    draft_id_val = draft.get("draft_id", "")
    draft_title = draft.get("title", "")
    draft_desc = draft.get("description", "")
    draft_priority = draft.get("priority", "high")

    # ── Similar Tickets tab ───────────────────────────────────────────────────
    similar_data = _similar_tickets_data(data.get("similar_tickets", []))

    # ── RAG Citations tab ─────────────────────────────────────────────────────
    rag_data = _rag_citations_data(data.get("rag_citations", []))

    # ── MCP Trace tab ─────────────────────────────────────────────────────────
    trace_data = _mcp_trace_data(data.get("mcp_trace", []))

    # ── Audit log ─────────────────────────────────────────────────────────────
    new_log = list(audit_log) + [_audit_entry("INVESTIGATE", data)]

    return (
        answer_md,
        intent_md,
        alarm_md,
        asset_md,
        priority_md,
        recs_md,
        draft_id_val,
        draft_title,
        draft_desc,
        draft_priority,
        similar_data,
        rag_data,
        trace_data,
        new_log,
    )


def confirm_ticket(draft_id_val: str, confirmed_by: str, audit_log: list[str]):
    """Calls /confirm-ticket and updates the confirmation status panel."""
    if not draft_id_val.strip():
        return "*No draft ID provided. Run an investigation first.*", audit_log

    data = _safe_post("/confirm-ticket", {"draft_id": draft_id_val, "confirmed_by": confirmed_by or "operator"})

    if "error" in data and data["error"]:
        return f"\u26d4 **Error:** {data['error']}", audit_log

    ticket = data.get("ticket", data)
    lines = [
        "### ✅ Ticket Created",
        f"**Ticket ID:** `{ticket.get('ticket_id', 'N/A')}`",
        f"**Title:** {ticket.get('title', 'N/A')}",
        f"**Status:** {ticket.get('status', 'N/A')}",
        f"**Priority:** {ticket.get('priority', 'N/A')}",
        f"**Created By:** {ticket.get('confirmed_by', confirmed_by)}",
        f"**Created At:** {ticket.get('created_at', 'N/A')}",
    ]
    new_log = list(audit_log) + [
        f"[{datetime.now().strftime('%H:%M:%S')}] CONFIRM_TICKET | "
        f"draft={draft_id_val} → ticket={ticket.get('ticket_id', '?')}"
    ]
    return "\n".join(lines), new_log


def load_example(example_text: str):
    return example_text


# ── UI ──────────────────────────────────────────────────────────────────────────
css = """
.gr-button-primary { font-weight: bold !important; }
#answer-box { font-size: 14px; }
.priority-badge { border-radius: 8px; padding: 10px; }
"""

with gr.Blocks(
    title="Incident & Ticket Enrichment Copilot",
) as app:
    gr.Markdown(
        """# 🏭 Incident & Ticket Enrichment Copilot
> Alarm-aware operations assistant — MCP + BM25 RAG + HITL confirmation"""
    )

    audit_state = gr.State([])

    with gr.Tab("🔍 Investigation"):
        with gr.Row():
            with gr.Column(scale=3):
                message_box = gr.Textbox(
                    label="Ask the Copilot",
                    placeholder="e.g. Prepare an incident for the highest-priority active alarm in EastRefinery",
                    lines=3,
                    elem_id="message-box",
                )
                with gr.Row():
                    run_btn = gr.Button("🚀 Run Investigation", variant="primary")
                    clear_btn = gr.Button("🗑️ Clear")
                intent_display = gr.Markdown(label="Intent", value="")
            with gr.Column(scale=1):
                gr.Markdown("### Example Prompts")
                for prompt in EXAMPLE_PROMPTS:
                    btn = gr.Button(prompt[:55] + ("..." if len(prompt) > 55 else ""), size="sm")
                    btn.click(fn=lambda p=prompt: p, outputs=message_box)

        answer_display = gr.Markdown(
            label="Copilot Answer",
            value="*Run an investigation to see results here.*",
            elem_id="answer-box",
        )

    with gr.Tab("🚨 Alarm & Asset"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Asset Information")
                asset_display = gr.Markdown(value="*Run an investigation first.*")
            with gr.Column():
                gr.Markdown("### Active Alarm")
                alarm_display = gr.Markdown(value="*Run an investigation first.*")
        gr.Markdown("### Priority Assessment")
        priority_display = gr.HTML(value="<i>Run an investigation first.</i>")
        gr.Markdown("### Operator Recommendations")
        recs_display = gr.Markdown(value="*Run an investigation first.*")

    with gr.Tab("🎫 Ticket Draft"):
        gr.Markdown(
            """### Human-in-the-Loop Ticket Confirmation
> Review the draft below, optionally edit, then click **Confirm Ticket** to create it in the ticketing system."""
        )
        draft_id_display = gr.Textbox(label="Draft ID", interactive=False, placeholder="(populated after investigation)")
        draft_title_box = gr.Textbox(label="Title", lines=1, placeholder="Edit draft title...")
        draft_desc_box = gr.Textbox(label="Description", lines=8, placeholder="Edit draft description...")
        draft_priority_box = gr.Dropdown(
            label="Priority",
            choices=["critical", "high", "medium", "low"],
            value="high",
        )
        with gr.Row():
            confirmed_by_box = gr.Textbox(label="Confirmed By", value="operator", placeholder="operator")
            confirm_btn = gr.Button("✅ Confirm Ticket Creation", variant="primary")
        confirm_output = gr.Markdown(value="*No ticket confirmed yet.*")

    with gr.Tab("📋 Similar Tickets"):
        gr.Markdown("### Historically Matched Tickets")
        similar_table = gr.Dataframe(
            headers=["Ticket ID", "Title", "Status", "Priority", "Asset"],
            datatype=["str", "str", "str", "str", "str"],
            interactive=False,
            wrap=True,
        )

    with gr.Tab("📚 RAG Citations"):
        gr.Markdown("### Retrieved Documentation Chunks (BM25)")
        rag_table = gr.Dataframe(
            headers=["Source", "Score", "Content Snippet"],
            datatype=["str", "str", "str"],
            interactive=False,
            wrap=True,
        )

    with gr.Tab("🔗 MCP Trace"):
        gr.Markdown("### MCP Tool Call Trace")
        trace_table = gr.Dataframe(
            headers=["Tool", "Server", "Duration (ms)", "Result"],
            datatype=["str", "str", "number", "str"],
            interactive=False,
            wrap=True,
        )

    with gr.Tab("📝 Audit Log"):
        gr.Markdown("### Session Audit Log")
        audit_display = gr.Textbox(
            label="Log",
            lines=20,
            interactive=False,
            placeholder="Session events will appear here...",
        )

    # ── Wire up the Run button ─────────────────────────────────────────────────
    inv_outputs = [
        answer_display,
        intent_display,
        alarm_display,
        asset_display,
        priority_display,
        recs_display,
        draft_id_display,
        draft_title_box,
        draft_desc_box,
        draft_priority_box,
        similar_table,
        rag_table,
        trace_table,
        audit_state,
    ]

    run_btn.click(
        fn=run_investigation,
        inputs=[message_box, audit_state],
        outputs=inv_outputs,
    )

    # ── Clear button ───────────────────────────────────────────────────────────
    clear_btn.click(
        fn=lambda: ["", "", "*Run an investigation first.*", "*Run an investigation first.*",
                    "<i>Run an investigation first.</i>", "*Run an investigation first.*",
                    "", "", "", "high", [], [], [], []],
        outputs=inv_outputs,
    )

    # ── Confirm ticket ─────────────────────────────────────────────────────────
    confirm_btn.click(
        fn=confirm_ticket,
        inputs=[draft_id_display, confirmed_by_box, audit_state],
        outputs=[confirm_output, audit_state],
    )

    # ── Sync audit log state → display ────────────────────────────────────────
    audit_state.change(
        fn=lambda log: "\n".join(reversed(log)),
        inputs=audit_state,
        outputs=audit_display,
    )


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        show_error=True,
        theme=gr.themes.Soft(),
        css=css,
    )

