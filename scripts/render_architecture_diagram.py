"""
One-off script to render docs/architecture-diagram.png from the ASCII
architecture diagram in README.md, using Pillow (no extra dependencies).

Run: .venv/bin/python scripts/render_architecture_diagram.py
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1400, 1000
BG = (255, 255, 255)
BOX_FILL = (235, 244, 255)
BOX_BORDER = (30, 80, 160)
ACCENT_FILL = (255, 244, 224)
ACCENT_BORDER = (180, 110, 20)
TEXT = (20, 20, 20)
ARROW = (90, 90, 90)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

try:
    font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    font_h = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    font_b = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
except Exception:
    font_title = font_h = font_b = ImageFont.load_default()


def box(xy, title, lines, fill=BOX_FILL, border=BOX_BORDER):
    d.rounded_rectangle(xy, radius=10, fill=fill, outline=border, width=2)
    x0, y0, x1, _ = xy
    d.text((x0 + 12, y0 + 8), title, font=font_h, fill=TEXT)
    ty = y0 + 32
    for line in lines:
        d.text((x0 + 12, ty), line, font=font_b, fill=TEXT)
        ty += 18


def arrow(p0, p1, label=None):
    d.line([p0, p1], fill=ARROW, width=2)
    x1, y1 = p1
    d.polygon([(x1 - 5, y1 - 5), (x1 + 5, y1 - 5), (x1, y1 + 6)], fill=ARROW)
    if label:
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        d.text((mx + 6, my - 8), label, font=font_b, fill=ARROW)


d.text((W / 2 - 260, 15), "Incident & Ticket Enrichment Copilot — Architecture", font=font_title, fill=TEXT)

# GUI
box((80, 60, 420, 130), "OPERATOR (Browser)", ["Gradio GUI :7860", "7 tabs incl. MCP Trace, Audit Log"])

# Backend / Orchestrator
box((80, 180, 900, 560), "COPILOT BACKEND :8080 (FastAPI)", [])
d.text((100, 205), "Input Guardrails: PII mask, prompt-injection block, length/policy checks", font=font_b, fill=TEXT)
d.text((100, 228), "Orchestrator — 9 step pipeline:", font=font_b, fill=TEXT)
steps = [
    "1. Intent detection",
    "2. Asset resolution        (MCP client)",
    "3. Alarm retrieval/detail  (MCP client)",
    "4. Priority scoring        (MCP client)",
    "5. Operator recommendations(MCP client)",
    "6. Similar ticket search   (MCP client)",
    "7. RAG retrieval           (ChromaDB + Ollama embeddings)",
    "8. LLM answer synthesis    (Ollama / OpenAI)",
    "9. Draft ticket creation   (MCP client, no write yet)",
]
ty = 250
for s in steps:
    d.text((120, ty), s, font=font_b, fill=TEXT)
    ty += 20
d.text((100, ty + 6), "Output Guardrails: confidence scoring, PII redaction, low-confidence caveat", font=font_b, fill=TEXT)

# Auth boundary note
d.rectangle((80, 570, 900, 600), outline=(160, 30, 30), width=1)
d.text((90, 577), "AUTH BOUNDARY: only MCP servers hold ALARM_API_TOKEN — backend never calls alarm-api directly", font=font_b, fill=(160, 30, 30))

# MCP servers
box((80, 630, 460, 760), "ALARM MANAGEMENT MCP :9000", [
    "13 tools: search_asset, get_alarms,",
    "priority_score, operator_recommendations,",
    "correlate_alarms, flood_analysis, ...",
    "Retry + timeout + trace_id propagation",
])
box((520, 630, 900, 760), "TICKETING MCP :9001", [
    "7 tools: search_tickets, create_ticket_draft,",
    "confirm_create_ticket (HITL write gate),",
    "update_ticket, get_draft, list_tickets",
])

# Alarm API
box((80, 800, 460, 930), "ALARM API SIMULATOR :8000", [
    "FastAPI, Bearer token auth",
    "7 assets, 7 alarms, 14 endpoints",
    "Observability: structured logs",
])

# RAG pipeline
box((960, 180, 1340, 560), "RAG PIPELINE", [])
d.text((980, 205), "rag/documents/ (6 markdown docs)", font=font_b, fill=TEXT)
d.text((980, 228), "rag/ingestion/ingest.py", font=font_b, fill=TEXT)
d.text((1000, 248), "chunk (900/150) -> embed", font=font_b, fill=TEXT)
d.text((1000, 268), "(Ollama nomic-embed-text)", font=font_b, fill=TEXT)
d.text((980, 292), "ChromaDB PersistentClient", font=font_b, fill=TEXT)
d.text((1000, 312), "rag/.chromadb/ (60 chunks)", font=font_b, fill=TEXT)
d.text((980, 340), "rag/retrieval/retriever.py", font=font_b, fill=TEXT)
d.text((1000, 360), "cosine similarity search", font=font_b, fill=TEXT)
d.text((1000, 380), "BM25 fallback if unavailable", font=font_b, fill=TEXT)
d.text((980, 408), "Citations -> {source, score, chunk_id}", font=font_b, fill=TEXT)

# LLM box
box((960, 630, 1340, 760), "LLM PROVIDER", [
    "Ollama (qwen3.5:2b) via OpenAI-compatible API",
    "or OpenAI gpt-4o-mini",
    "Structured fallback answer if neither configured",
], fill=ACCENT_FILL, border=ACCENT_BORDER)

# Observability note box
box((520, 800, 900, 930), "OBSERVABILITY", [
    "MCP trace log: tool, server, duration_ms,",
    "success/error — surfaced in GUI 'MCP Trace' tab",
    "Structured logging in every service",
])

# Arrows
arrow((250, 130), (250, 178))
arrow((270, 560), (270, 628))
arrow((700, 560), (700, 628))
arrow((270, 760), (270, 798))
arrow((900, 370), (960, 370), "embeddings")
arrow((900, 700), (958, 700), "chat completion")

img.save("docs/architecture-diagram.png")
print("Saved docs/architecture-diagram.png")
