"""Generate the one-document homework report PDF."""

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
SCREENSHOTS = ROOT / "screenshots"
OUTPUT = ROOT / "ISE_Homework_Part1.pdf"
REPO_URL = "https://github.com/markusrussold/ise-homework-part-1"
MATRIKELNUMMER = "52010547"
REPORT_DATE = "05.09.2026"

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Consolas", r"C:\Windows\Fonts\consola.ttf"))

ACCENT = HexColor("#1f4e79")
MUTED = HexColor("#333333")
CODE_BG = HexColor("#f4f4f4")
RULE = HexColor("#c5d0dc")


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "CoverTitle",
            fontName="Arial-Bold",
            fontSize=18,
            leading=22,
            textColor=ACCENT,
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "CoverSub",
            fontName="Arial",
            fontSize=11,
            leading=14,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "RepoLink",
            fontName="Arial-Bold",
            fontSize=11,
            leading=14,
            textColor=ACCENT,
            alignment=TA_CENTER,
            spaceAfter=6 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Body",
            fontName="Arial",
            fontSize=10,
            leading=13,
            textColor=MUTED,
            alignment=TA_JUSTIFY,
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Heading",
            fontName="Arial-Bold",
            fontSize=12,
            leading=15,
            textColor=ACCENT,
            spaceBefore=2.5 * mm,
            spaceAfter=1.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "BulletLine",
            fontName="Arial",
            fontSize=10,
            leading=13,
            textColor=MUTED,
            leftIndent=6 * mm,
            spaceAfter=0.6 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Caption",
            fontName="Arial",
            fontSize=8,
            leading=10,
            textColor=MUTED,
            alignment=TA_LEFT,
            spaceBefore=0.8 * mm,
            spaceAfter=1.6 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "TableCell",
            fontName="Arial",
            fontSize=9,
            leading=12,
            textColor=MUTED,
        )
    )
    styles.add(
        ParagraphStyle(
            "TableHead",
            fontName="Arial-Bold",
            fontSize=9,
            leading=12,
            textColor=HexColor("#ffffff"),
        )
    )
    styles.add(
        ParagraphStyle(
            "CodeBlock",
            fontName="Consolas",
            fontSize=8,
            leading=11,
            textColor=HexColor("#222222"),
            backColor=CODE_BG,
            leftIndent=2 * mm,
            rightIndent=2 * mm,
            spaceBefore=1 * mm,
            spaceAfter=3 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "Footer",
            fontName="Arial",
            fontSize=8,
            textColor=HexColor("#666666"),
            alignment=TA_CENTER,
        )
    )
    return styles


def scaled_image(path: Path, max_width: float, max_height: float) -> Image:
    img = Image(str(path))
    scale = min(max_width / img.imageWidth, max_height / img.imageHeight)
    img.drawWidth = img.imageWidth * scale
    img.drawHeight = img.imageHeight * scale
    return img


def add_page_bits(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.4)
    canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.setFillColor(HexColor("#666666"))
    canvas.setFont("Arial", 8)
    canvas.drawString(18 * mm, 8.2 * mm, f"Matriculation number {MATRIKELNUMMER}")
    canvas.drawCentredString(A4[0] / 2, 8.2 * mm, REPORT_DATE)
    canvas.drawRightString(A4[0] - 18 * mm, 8.2 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build():
    styles = make_styles()
    tmp = OUTPUT.with_suffix(".tmp.pdf")
    doc = SimpleDocTemplate(
        str(tmp),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=20 * mm,
        title="ISE Industrial Computing – Homework Part 1",
        author="Markus Russold",
    )
    usable_w = A4[0] - 36 * mm

    story = []
    story.append(Paragraph("ISE Industrial Computing – Homework Part 1", styles["CoverTitle"]))
    story.append(Paragraph("Custom MCP Math &amp; Database Tool Server", styles["CoverSub"]))
    story.append(Paragraph("Markus Russold", styles["CoverSub"]))
    story.append(
        Paragraph(
            f"Matriculation number {MATRIKELNUMMER}  |  {REPORT_DATE}",
            styles["CoverSub"],
        )
    )
    story.append(
        Paragraph(
            f'Public GitHub repository (clickable): '
            f'<link href="{REPO_URL}" color="#1f4e79"><u>{REPO_URL}</u></link>',
            styles["RepoLink"],
        )
    )

    story.append(Paragraph("Overview", styles["Heading"]))
    story.append(
        Paragraph(
            "This homework extends the lecture samples (Sample 3 MCP / Sample 4 MCP Architecture) "
            "with a FastMCP HTTP server and a LiteLLM ReAct client. The server exposes three distinct "
            "tools. The client discovers those tools at runtime over Streamable HTTP and uses ReAct "
            "reasoning to call them. The repository is public so the submission can be inspected without "
            "a private-access request.",
            styles["Body"],
        )
    )

    story.append(Paragraph("MCP tools", styles["Heading"]))
    header = [
        Paragraph("Tool", styles["TableHead"]),
        Paragraph("Purpose", styles["TableHead"]),
    ]
    rows = [
        header,
        [
            Paragraph("lookup_inventory", styles["TableCell"]),
            Paragraph("SQLite lookup against inventory.db (products table)", styles["TableCell"]),
        ],
        [
            Paragraph("compute_tiered_discount", styles["TableCell"]),
            Paragraph("Tiered discount formula based on order volume", styles["TableCell"]),
        ],
        [
            Paragraph("append_audit_event", styles["TableCell"]),
            Paragraph("Append a timestamped event to logs/audit.log", styles["TableCell"]),
        ],
    ]
    table = Table(rows, colWidths=[55 * mm, usable_w - 55 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("BACKGROUND", (0, 1), (-1, -1), HexColor("#f7f9fb")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.3, RULE),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            "The audit file is also published as the MCP resource <font name='Consolas'>file://audit/events</font>.",
            styles["Body"],
        )
    )

    story.append(Paragraph("Discount brackets", styles["Heading"]))
    for line in (
        "1-9 units: 0%",
        "10-49 units: 5%",
        "50-99 units: 12%",
        "100-249 units: 18%",
        "250+ units: 25%",
    ):
        story.append(Paragraph(f"- {line}", styles["BulletLine"]))
    story.append(Spacer(1, 2 * mm))

    story.append(Paragraph("Environment setup", styles["Heading"]))
    story.append(
        Paragraph(
            "Requires Python 3.11+, uv, a local LiteLLM proxy, and SQLite (stdlib). "
            "Copy <font name='Consolas'>.env.example</font> to <font name='Consolas'>.env</font> "
            "and set <font name='Consolas'>LITELLM_API_BASE</font>, <font name='Consolas'>LITELLM_KEY</font>, "
            "<font name='Consolas'>LITELLM_DEFAULT_MODEL</font>, and <font name='Consolas'>MCP_SERVER_URL</font>.",
            styles["Body"],
        )
    )
    story.append(
        Preformatted(
            "python -m pip install uv\n"
            "python -m uv sync\n"
            "copy .env.example .env",
            styles["CodeBlock"],
        )
    )
    story.append(
        Paragraph(
            "The first server start creates <font name='Consolas'>inventory.db</font> if it is missing "
            "and seeds the <font name='Consolas'>products</font> table "
            "(id INTEGER PRIMARY KEY, name TEXT NOT NULL, quantity INTEGER NOT NULL).",
            styles["Body"],
        )
    )

    story.append(Paragraph("Run", styles["Heading"]))
    story.append(Paragraph("Terminal 1 – MCP server:", styles["Body"]))
    story.append(Preformatted("python -m uv run python server.py", styles["CodeBlock"]))
    story.append(Paragraph("Terminal 2 – ReAct client (LiteLLM):", styles["Body"]))
    story.append(Preformatted("python -m uv run python client.py", styles["CodeBlock"]))
    story.append(
        Paragraph(
            "The demo prompt looks up Hydraulic Pump, computes an 80-unit discount at $120, "
            "and writes an audit event. Captured output is in logs/execution.log.",
            styles["Body"],
        )
    )

    story.append(PageBreak())
    proof = [
        Paragraph("Proof of execution", styles["Heading"]),
        Paragraph(
            "Screenshots in required order: MCP server, ReAct client, then the local audit log.",
            styles["Body"],
        ),
        scaled_image(SCREENSHOTS / "HWP1_Exec1_MCPServer.png", usable_w, 52 * mm),
        Paragraph(
            "Figure 1. MCP server (server.py) – FastMCP Math_Database_Tools listening on "
            "http://0.0.0.0:8000/mcp and accepting client requests.",
            styles["Caption"],
        ),
        scaled_image(SCREENSHOTS / "HWP1_Exec2_MCPClient.png", usable_w, 98 * mm),
        Paragraph(
            "Figure 2. ReAct client (client.py) – discovers lookup_inventory, "
            "compute_tiered_discount and append_audit_event, then calls all three tools.",
            styles["Caption"],
        ),
        scaled_image(SCREENSHOTS / "HWP1_Exec1_AuditLog.png", usable_w, 32 * mm),
        Paragraph(
            "Figure 3. Audit log (logs/audit.log) – timestamped events written by append_audit_event, "
            "including stock (35), 12% discount and $8448 total.",
            styles["Caption"],
        ),
    ]
    story.append(KeepTogether(proof))

    doc.build(story, onFirstPage=add_page_bits, onLaterPages=add_page_bits)
    try:
        tmp.replace(OUTPUT)
    except PermissionError:
        import shutil

        shutil.copyfile(tmp, OUTPUT)
        tmp.unlink(missing_ok=True)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
