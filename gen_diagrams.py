#!/usr/bin/env python3
"""Generate architecture diagram PNGs using Pillow."""
from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = "/workspace/SmartLearner/screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Helpers ---
def get_font(size=20):
    """Try to get a CJK-capable font, fall back to default."""
    candidates = [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def rounded_rect(draw, xy, radius, fill, outline=None, width=2):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def draw_arrow(draw, start, end, fill="#555", width=2, head_size=10):
    draw.line([start, end], fill=fill, width=width)
    import math
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.sqrt(dx*dx + dy*dy)
    if length == 0:
        return
    ux, uy = dx/length, dy/length
    px, py = -uy, ux
    tip = end
    left = (tip[0] - head_size*ux + head_size*0.5*px, tip[1] - head_size*uy + head_size*0.5*py)
    right = (tip[0] - head_size*ux - head_size*0.5*px, tip[1] - head_size*uy - head_size*0.5*py)
    draw.polygon([tip, left, right], fill=fill)


# ============================================================
# Diagram 1: System Overall Flow (system_architecture.png)
# ============================================================
def gen_system_architecture():
    W, H = 1200, 800
    img = Image.new("RGB", (W, H), "#FAFBFC")
    draw = ImageDraw.Draw(img)

    title_font = get_font(28)
    label_font = get_font(18)
    small_font = get_font(14)

    # Title
    draw.text((W//2, 30), "SmartLearner System Architecture", fill="#1a1a2e", font=title_font, anchor="mt")

    # --- User Layer ---
    y_user = 80
    rounded_rect(draw, (50, y_user, W-50, y_user+90), 12, fill="#E8F4FD", outline="#2196F3", width=2)
    draw.text((W//2, y_user+20), "User Layer", fill="#1565C0", font=label_font, anchor="mt")
    draw.text((W//2, y_user+50), "Web Browser (Next.js 14 + TailwindCSS)", fill="#424242", font=small_font, anchor="mt")

    # Arrow down
    draw_arrow(draw, (W//2, y_user+90), (W//2, y_user+120), fill="#2196F3")

    # --- API Gateway ---
    y_api = y_user + 120
    rounded_rect(draw, (200, y_api, W-200, y_api+50), 10, fill="#FFF3E0", outline="#FF9800", width=2)
    draw.text((W//2, y_api+25), "FastAPI Gateway (CORS / REST API / 19+ Endpoints)", fill="#E65100", font=small_font, anchor="mm")

    # Arrow down
    draw_arrow(draw, (W//2, y_api+50), (W//2, y_api+80), fill="#FF9800")

    # --- Four Modules ---
    y_mod = y_api + 80
    mod_w = 240
    mod_h = 160
    gap = 30
    total_w = 4 * mod_w + 3 * gap
    start_x = (W - total_w) // 2

    modules = [
        ("Course QA", "Course Q&A\nAssistant", "#E3F2FD", "#1565C0",
         ["RAG Retrieval", "Bloom Quiz", "Chat Q&A"]),
        ("Paper Reader", "Paper Reading\nCoach", "#F3E5F5", "#7B1FA2",
         ["Auto Summary", "Socratic Q&A", "Literature Rec"]),
        ("Knowledge Base", "Knowledge Base\nManager", "#E8F5E9", "#2E7D32",
         ["Hybrid Search", "Multi-format", "Precise Retrieval"]),
        ("Learning Path", "Learning Path\nPlanner", "#FFF8E1", "#F57F17",
         ["Custom Plans", "Progress Track", "Resource Push"]),
    ]

    for i, (short_name, name, bg, border, features) in enumerate(modules):
        x = start_x + i * (mod_w + gap)
        rounded_rect(draw, (x, y_mod, x+mod_w, y_mod+mod_h), 12, fill=bg, outline=border, width=2)
        draw.text((x+mod_w//2, y_mod+15), short_name, fill=border, font=label_font, anchor="mt")
        lines = name.split("\n")
        for li, line in enumerate(lines):
            draw.text((x+mod_w//2, y_mod+40+li*18), line, fill="#424242", font=small_font, anchor="mt")
        for fi, feat in enumerate(features):
            draw.text((x+mod_w//2, y_mod+85+fi*20), f"• {feat}", fill="#616161", font=small_font, anchor="mt")

        # Arrow from API to each module
        draw_arrow(draw, (W//2, y_api+50), (x+mod_w//2, y_mod), fill="#FF9800")

    # Arrow down from modules to core
    for i in range(4):
        x = start_x + i * (mod_w + gap) + mod_w//2
        draw_arrow(draw, (x, y_mod+mod_h), (x, y_mod+mod_h+30), fill="#607D8B")

    # --- Core Layer ---
    y_core = y_mod + mod_h + 30
    rounded_rect(draw, (80, y_core, W-80, y_core+110), 12, fill="#ECEFF1", outline="#607D8B", width=2)
    draw.text((W//2, y_core+12), "Core Engine Layer", fill="#37474F", font=label_font, anchor="mt")

    core_items = ["RAG Engine\n(FAISS)", "LLM Client\n(Qwen-Plus)", "Embedding\n(text-embedding-v2)", "Document Parser\n(PDF/DOCX/PPTX)", "Hybrid Search\n(Semantic+BM25)"]
    cx_start = 120
    cx_gap = (W - 240) // len(core_items)
    for ci, item in enumerate(core_items):
        cx = cx_start + ci * cx_gap + cx_gap//2
        lines = item.split("\n")
        for li, line in enumerate(lines):
            draw.text((cx, y_core+42+li*18), line, fill="#455A64", font=small_font, anchor="mt")

    # Arrow down
    draw_arrow(draw, (W//2, y_core+110), (W//2, y_core+140), fill="#795548")

    # --- Data Layer ---
    y_data = y_core + 140
    rounded_rect(draw, (150, y_data, W-150, y_data+70), 12, fill="#FBE9E7", outline="#795548", width=2)
    draw.text((W//2, y_data+20), "Data Layer", fill="#4E342E", font=label_font, anchor="mt")
    draw.text((W//2, y_data+48), "FAISS Vector Store  |  Document Chunks  |  Learning Progress JSON  |  Knowledge Base Metadata", fill="#6D4C41", font=small_font, anchor="mt")

    # --- External ---
    y_ext = y_data + 90
    rounded_rect(draw, (300, y_ext, W-300, y_ext+45), 10, fill="#F3E5F5", outline="#9C27B0", width=2)
    draw.text((W//2, y_ext+22), "DashScope API (Alibaba Cloud) — LLM + Embedding Service", fill="#6A1B9A", font=small_font, anchor="mm")
    draw_arrow(draw, (W//2, y_data+70), (W//2, y_ext), fill="#9C27B0")

    img.save(os.path.join(OUTPUT_DIR, "system_architecture.png"), dpi=(150, 150))
    print("✓ system_architecture.png generated")


# ============================================================
# Diagram 2: Three-Layer Architecture (architecture_detail.png)
# ============================================================
def gen_architecture_detail():
    W, H = 1200, 750
    img = Image.new("RGB", (W, H), "#FAFBFC")
    draw = ImageDraw.Draw(img)

    title_font = get_font(26)
    label_font = get_font(18)
    small_font = get_font(14)
    tiny_font = get_font(12)

    draw.text((W//2, 25), "SmartLearner Three-Layer Architecture", fill="#1a1a2e", font=title_font, anchor="mt")

    # --- Frontend Layer ---
    y = 65
    rounded_rect(draw, (40, y, W-40, y+160), 14, fill="#E3F2FD", outline="#1976D2", width=3)
    draw.text((100, y+10), "Presentation Layer (Next.js 14 + TailwindCSS)", fill="#0D47A1", font=label_font)

    pages = [
        ("Dashboard", "Overview &\nNavigation"),
        ("Course QA", "Chat + Quiz\n(Bloom's)"),
        ("Paper Reader", "Summary +\nSocratic + Rec"),
        ("Knowledge", "Search &\nManage Docs"),
        ("Learning Path", "Plan + Track\n+ Recommend"),
    ]
    px_start = 100
    px_gap = (W - 200) // len(pages)
    for pi, (name, desc) in enumerate(pages):
        px = px_start + pi * px_gap
        rounded_rect(draw, (px, y+45, px+px_gap-20, y+150), 8, fill="#BBDEFB", outline="#64B5F6", width=1)
        draw.text((px + (px_gap-20)//2, y+55), name, fill="#0D47A1", font=small_font, anchor="mt")
        for li, line in enumerate(desc.split("\n")):
            draw.text((px + (px_gap-20)//2, y+80+li*16), line, fill="#1565C0", font=tiny_font, anchor="mt")

    # Arrow
    draw_arrow(draw, (W//2, y+160), (W//2, y+185), fill="#388E3C")

    # --- Backend Layer ---
    y2 = y + 185
    rounded_rect(draw, (40, y2, W-40, y2+260), 14, fill="#E8F5E9", outline="#388E3C", width=3)
    draw.text((100, y2+10), "Application Layer (FastAPI + LangChain)", fill="#1B5E20", font=label_font)

    # Left: API Routes
    draw.text((100, y2+40), "API Routes:", fill="#2E7D32", font=small_font)
    routes = [
        "/api/course — Chat, Quiz, Sources",
        "/api/paper — Upload, Summary, Socratic, Rec",
        "/api/knowledge — KB CRUD, Search, Docs",
        "/api/learning — Plan, Progress, Session, Rec",
        "/api/upload — Multi-format File Parse",
    ]
    for ri, route in enumerate(routes):
        draw.text((120, y2+62+ri*20), route, fill="#388E3C", font=tiny_font)

    # Right: Core Modules
    draw.text((650, y2+40), "Core Modules:", fill="#2E7D32", font=small_font)
    modules_detail = [
        ("RAG Engine", "FAISS + Hybrid Search\n(Semantic 0.7 + BM25 0.3)"),
        ("LLM Client", "Qwen-Plus (Chat)\nQwen-Turbo (Fast)"),
        ("Embedding", "text-embedding-v2\n(1536-dim vectors)"),
        ("Doc Parser", "PDF / DOCX / PPTX\nTXT / MD"),
    ]
    for mi, (mname, mdesc) in enumerate(modules_detail):
        mx = 650 + (mi % 2) * 260
        my = y2 + 62 + (mi // 2) * 90
        rounded_rect(draw, (mx, my, mx+240, my+80), 8, fill="#C8E6C9", outline="#66BB6A", width=1)
        draw.text((mx+120, my+8), mname, fill="#1B5E20", font=small_font, anchor="mt")
        for li, line in enumerate(mdesc.split("\n")):
            draw.text((mx+120, my+30+li*16), line, fill="#2E7D32", font=tiny_font, anchor="mt")

    # Arrow
    draw_arrow(draw, (W//2, y2+260), (W//2, y2+285), fill="#E65100")

    # --- Data Layer ---
    y3 = y2 + 285
    rounded_rect(draw, (40, y3, W-40, y3+160), 14, fill="#FFF3E0", outline="#E65100", width=3)
    draw.text((100, y3+10), "Data & External Layer", fill="#BF360C", font=label_font)

    data_items = [
        ("FAISS Index", "Vector embeddings\nfor RAG retrieval", "#FFE0B2"),
        ("Document Store", "Parsed chunks &\nmetadata", "#FFCC80"),
        ("Progress Tracker", "Learning plans &\nstreak data (JSON)", "#FFB74D"),
        ("DashScope API", "Qwen LLM +\nEmbedding Cloud", "#FFA726"),
    ]
    dx_start = 80
    dx_gap = (W - 160) // len(data_items)
    for di, (dname, ddesc, dbg) in enumerate(data_items):
        dx = dx_start + di * dx_gap
        rounded_rect(draw, (dx, y3+40, dx+dx_gap-20, y3+148), 8, fill=dbg, outline="#FB8C00", width=1)
        draw.text((dx+(dx_gap-20)//2, y3+50), dname, fill="#BF360C", font=small_font, anchor="mt")
        for li, line in enumerate(ddesc.split("\n")):
            draw.text((dx+(dx_gap-20)//2, y3+75+li*16), line, fill="#E65100", font=tiny_font, anchor="mt")

    img.save(os.path.join(OUTPUT_DIR, "architecture_detail.png"), dpi=(150, 150))
    print("✓ architecture_detail.png generated")


# ============================================================
# Diagram 3: Four-Module Workflow (module_flow.png)
# ============================================================
def gen_module_flow():
    W, H = 1200, 900
    img = Image.new("RGB", (W, H), "#FAFBFC")
    draw = ImageDraw.Draw(img)

    title_font = get_font(26)
    label_font = get_font(17)
    small_font = get_font(13)
    tiny_font = get_font(11)

    draw.text((W//2, 25), "SmartLearner Four-Module Workflow", fill="#1a1a2e", font=title_font, anchor="mt")

    # 4 columns
    col_w = 270
    gap = 20
    total = 4 * col_w + 3 * gap
    sx = (W - total) // 2

    cols = [
        {
            "title": "Course Q&A",
            "color": "#1565C0",
            "bg": "#E3F2FD",
            "steps": [
                ("Upload Courseware", "PDF/DOCX/PPTX"),
                ("Parse & Chunk", "Document Parser"),
                ("Embed & Store", "FAISS Index"),
                ("RAG Retrieval", "Semantic + Keyword"),
                ("Chat Answer", "Qwen-Plus LLM"),
                ("Bloom Quiz", "6 Cognitive Levels"),
            ]
        },
        {
            "title": "Paper Reader",
            "color": "#7B1FA2",
            "bg": "#F3E5F5",
            "steps": [
                ("Upload Paper", "PDF/DOCX/MD"),
                ("Parse & Embed", "Text Chunks"),
                ("Auto Summary", "Key & Findings"),
                ("Socratic Q&A", "3 Depth Levels"),
                ("Literature Rec", "Related Papers"),
                ("Deep Analysis", "Methodology"),
            ]
        },
        {
            "title": "Knowledge Base",
            "color": "#2E7D32",
            "bg": "#E8F5E9",
            "steps": [
                ("Create KB", "Name & Desc"),
                ("Upload Docs", "Multi-format"),
                ("Build Index", "FAISS Vectors"),
                ("NL Search", "Hybrid Engine"),
                ("View Results", "Ranked Chunks"),
                ("Manage Docs", "CRUD Ops"),
            ]
        },
        {
            "title": "Learning Path",
            "color": "#F57F17",
            "bg": "#FFF8E1",
            "steps": [
                ("Set Goal", "Topic & Level"),
                ("Generate Plan", "Qwen LLM"),
                ("View Milestones", "Tasks & Hours"),
                ("Record Session", "Duration & Topic"),
                ("Track Progress", "Streak & %"),
                ("Get Recs", "Next Resources"),
            ]
        },
    ]

    for ci, col in enumerate(cols):
        cx = sx + ci * (col_w + gap)
        # Column header
        rounded_rect(draw, (cx, 60, cx+col_w, 100), 10, fill=col["bg"], outline=col["color"], width=2)
        draw.text((cx+col_w//2, 80), col["title"], fill=col["color"], font=label_font, anchor="mm")

        # Steps
        step_h = 55
        step_gap = 15
        for si, (step_name, step_desc) in enumerate(col["steps"]):
            sy = 115 + si * (step_h + step_gap)
            rounded_rect(draw, (cx+10, sy, cx+col_w-10, sy+step_h), 8, fill=col["bg"], outline=col["color"], width=1)
            draw.text((cx+col_w//2, sy+15), step_name, fill=col["color"], font=small_font, anchor="mt")
            draw.text((cx+col_w//2, sy+35), step_desc, fill="#757575", font=tiny_font, anchor="mt")

            # Arrow between steps
            if si < len(col["steps"]) - 1:
                arrow_y_start = sy + step_h
                arrow_y_end = sy + step_h + step_gap
                draw_arrow(draw, (cx+col_w//2, arrow_y_start), (cx+col_w//2, arrow_y_end), fill=col["color"], width=2, head_size=8)

    img.save(os.path.join(OUTPUT_DIR, "module_flow.png"), dpi=(150, 150))
    print("✓ module_flow.png generated")


if __name__ == "__main__":
    gen_system_architecture()
    gen_architecture_detail()
    gen_module_flow()
    print("\nAll diagrams generated successfully!")
