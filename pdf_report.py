"""
pdf_report.py  –  Generates a Hotelling T² summary PDF report.
"""
import io
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    HRFlowable,
    KeepTogether,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

_HERE     = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(_HERE, "logo.png.png")


# ── helpers ──────────────────────────────────────────────────────────────────

def _find_col(df, keyword):
    matches = [c for c in df.columns if keyword.lower() in c.lower()]
    if not matches:
        raise ValueError(f"Kolom '{keyword}' tidak ditemukan: {list(df.columns)}")
    return matches[0]


def _render_chart(hasil, ucl):
    fig, ax = plt.subplots(figsize=(7.5, 2.8))
    ic  = hasil["Status"] == "IC"
    ooc = hasil["Status"] == "OOC"

    ax.plot(hasil["Hour"], hasil["T2"],
            marker="o", linewidth=1.2, color="#1f77b4", zorder=1, markersize=4)
    ax.axhline(y=ucl, color="red", linestyle="--", linewidth=1.5,
               label=f"UCL = {ucl:.3f}")
    ax.scatter(hasil.loc[ic,  "Hour"], hasil.loc[ic,  "T2"],
               color="green", s=35, label="In Control", zorder=3)
    ax.scatter(hasil.loc[ooc, "Hour"], hasil.loc[ooc, "T2"],
               color="red",   s=50, label="Out of Control", zorder=3)

    ax.set_title("Hotelling T² Control Chart", fontsize=10, fontweight="bold")
    ax.set_xlabel("Jam", fontsize=8)
    ax.set_ylabel("Hotelling T²", fontsize=8)
    ax.legend(fontsize=7, loc="upper right")
    ax.tick_params(labelsize=6)
    ax.grid(linestyle="--", alpha=0.4)
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def _render_pie(n_ic, n_ooc):
    fig, ax = plt.subplots(figsize=(3, 3))
    ax.pie(
        [n_ic, n_ooc],
        labels=["In Control", "Out of Control"],
        colors=["#27ae60", "#e74c3c"],
        explode=(0, 0.05),
        autopct="%1.1f%%",
        startangle=90,
        textprops={"fontsize": 8},
    )
    ax.set_title("Status Kendali", fontsize=9, fontweight="bold", pad=8)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _base_ts(header_bg=None):
    if header_bg is None:
        header_bg = colors.HexColor("#1a3e72")
    return TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  header_bg),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, 0),  8.5),
        ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#eef2fa")]),
        ("FONTSIZE",       (0, 1), (-1, -1), 8),
        ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING",     (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
    ])


# ── public ────────────────────────────────────────────────────────────────────

def buat_pdf(tanggal: str, n_obs: int, output: dict) -> bytes:
    hasil  = output["hasil"]
    ucl    = float(output["ucl"])
    n_ooc  = int(output["jumlah_ooc"])
    n_ic   = int(output["jumlah_ic"])
    ooc_df = output["ooc"]

    col_flow = _find_col(hasil, "flow")
    col_pres = _find_col(hasil, "pressure")

    flow_mean     = float(hasil[col_flow].mean())
    flow_min      = float(hasil[col_flow].min())
    flow_max      = float(hasil[col_flow].max())
    pressure_mean = float(hasil[col_pres].mean())
    pressure_min  = float(hasil[col_pres].min())
    pressure_max  = float(hasil[col_pres].max())

    flow_min_hour     = str(hasil.loc[hasil[col_flow].idxmin(), "Hour"])
    flow_max_hour     = str(hasil.loc[hasil[col_flow].idxmax(), "Hour"])
    pressure_min_hour = str(hasil.loc[hasil[col_pres].idxmin(), "Hour"])
    pressure_max_hour = str(hasil.loc[hasil[col_pres].idxmax(), "Hour"])

    n_total = len(hasil)
    pct_ooc = n_ooc / n_total * 100 if n_total else 0.0

    # ── document ──────────────────────────────────────────────────────────────
    pdf_buf = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buf, pagesize=A4,
        leftMargin=1*cm, rightMargin=1*cm,
        topMargin=0.3*cm, bottomMargin=1*cm,
    )

    styles  = getSampleStyleSheet()
    W       = A4[0] - 2*cm

    title_s = ParagraphStyle("PT", parent=styles["Title"],
                             fontSize=14, textColor=colors.HexColor("#1a3e72"),
                             spaceAfter=1, alignment=TA_CENTER, leading=18)
    sub_s   = ParagraphStyle("PS", parent=styles["Normal"],
                             fontSize=9, textColor=colors.grey,
                             spaceAfter=1, alignment=TA_CENTER)
    meta_s  = ParagraphStyle("PM", parent=styles["Normal"],
                             fontSize=9, textColor=colors.HexColor("#333333"),
                             spaceAfter=0, alignment=TA_CENTER)
    sec_s   = ParagraphStyle("PSec", parent=styles["Heading2"],
                             fontSize=10, textColor=colors.HexColor("#1a3e72"),
                             spaceBefore=16, spaceAfter=4)
    body_s  = ParagraphStyle("PB", parent=styles["Normal"],
                             fontSize=8.5, leading=13, alignment=TA_JUSTIFY)
    foot_s  = ParagraphStyle("PF", parent=styles["Normal"],
                             fontSize=7, textColor=colors.grey, alignment=TA_CENTER)

    def sec(text):
        return [
            Paragraph(text, sec_s),
            HRFlowable(width="100%", thickness=0.5,
                       color=colors.HexColor("#1a3e72"), spaceAfter=4),
        ]

    story = []

    # ── HEADER ────────────────────────────────────────────────────────────────
    if os.path.exists(LOGO_PATH):
        logo = RLImage(LOGO_PATH, width=W, height=3.5*cm)
        logo.hAlign = "CENTER"
        story.append(logo)
    
    story.append(HRFlowable(width="100%", thickness=1.5,
                            color=colors.HexColor("#1a3e72"), spaceAfter=4))
    story.append(Paragraph("Laporan Monitoring Flow &amp; Pressure", title_s))
    story.append(Paragraph("Peta Kendali Hotelling T\u00b2 \u2013 PT. Air Minum Intan Banjar &nbsp;|&nbsp; DMA Anang Syahrani", sub_s))
    story.append(HRFlowable(width="100%", thickness=0.6,
                            color=colors.HexColor("#aaaaaa"), spaceAfter=2))
    story.append(Paragraph(
        f"Tanggal Analisis: <b>{tanggal}</b> &nbsp;|&nbsp; Jumlah Observasi: <b>{n_obs}</b>",
        meta_s))
    story.append(HRFlowable(width="100%", thickness=0.6,
                            color=colors.HexColor("#aaaaaa"), spaceAfter=6))

    # ── 1. Statistik Deskriptif ───────────────────────────────────────────────
    story += sec("1. Statistika Deskriptif")

    # Nilai + jam ditumpuk dalam satu cell pakai Paragraph
    jam_s = ParagraphStyle("Jam", parent=styles["Normal"],
                           fontSize=6.5, textColor=colors.HexColor("#888888"),
                           alignment=TA_CENTER, leading=9)
    val_s = ParagraphStyle("Val", parent=styles["Normal"],
                           fontSize=8, alignment=TA_CENTER, leading=11)

    def cell(val, jam):
        return [Paragraph(val, val_s), Paragraph(f"pukul {jam}", jam_s)]

    cw = [W * 0.34, W * 0.22, W * 0.22, W * 0.22]
    t_stats = Table(
        [
            ["Variabel",                    "Rata-rata",                      "Min",                                        "Maks"],
            ["Flow Distribusi (l/s)",       f"{flow_mean:.4f}",               cell(f"{flow_min:.4f}", flow_min_hour),        cell(f"{flow_max:.4f}", flow_max_hour)],
            ["Pressure Distribusi (Bar)",   f"{pressure_mean:.4f}",           cell(f"{pressure_min:.4f}", pressure_min_hour),cell(f"{pressure_max:.4f}", pressure_max_hour)],
        ],
        colWidths=cw,
    )
    t_stats.setStyle(_base_ts())
    story.append(t_stats)

    # ── 2. Peta Kendali ───────────────────────────────────────────────────────
    story += sec("2. Peta Kendali")
    chart_img = RLImage(_render_chart(hasil, ucl), width=W, height=7*cm)
    story.append(chart_img)
    story.append(Paragraph(
        "Setiap titik mewakili satu jam pengukuran. Titik hijau menunjukkan observasi "
        "yang berada dalam batas kendali, sedangkan titik merah menunjukkan observasi "
        "yang berada di luar batas kendali.",
        body_s))

    # ── 3. Ringkasan Status Kendali ───────────────────────────────────────────
    story += sec("3. Ringkasan Status Kendali")

    if n_ooc == 0:
        interp_text = (
            f"Dari {n_total} observasi, <b>seluruhnya ({n_ic})</b> berada dalam kondisi normal. "
            "Hal ini menunjukkan bahwa tidak terdeteksi adanya penyimpangan proses selama periode pengamatan "
            "sehingga kondisi sistem distribusi air dapat dikatakan berada dalam keadaan terkendali."
        )
    else:
        interp_text = (
            f"Dari {n_total} observasi, <b>{n_ooc} ({pct_ooc:.1f}%)</b> berada di luar kendali "
            f"dan <b>{n_ic} ({100-pct_ooc:.1f}%)</b> dalam kondisi normal. "
            "Observasi yang berada di luar batas kendali mengindikasikan adanya penyimpangan proses "
            "sehingga perlu dilakukan pemeriksaan lebih lanjut untuk mengetahui penyebabnya."
        )

    # Pie di kiri, teks interpretasi di kanan — dalam satu baris tabel
    pie_buf = _render_pie(n_ic, n_ooc)
    pie_img = RLImage(pie_buf, width=7*cm, height=7*cm)

    ring_table = Table(
        [[pie_img, Paragraph(interp_text, body_s)]],
        colWidths=[7.5*cm, W - 7.5*cm],
    )
    ring_table.setStyle(TableStyle([
        ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",   (0, 0), (0,  0),  "CENTER"),
        ("ALIGN",   (1, 0), (1,  0),  "LEFT"),
        ("LEFTPADDING",  (1, 0), (1, 0), 10),
        ("RIGHTPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))
    story.append(ring_table)

    # ── 4. Detail OOC ─────────────────────────────────────────────────────────
    story.append(PageBreak())
    story += sec("4. Detail Observasi Out of Control")

    if n_ooc == 0:
        story.append(Paragraph(
            "Tidak terdapat observasi yang berada di luar kendali pada periode ini.",
            body_s))
    else:
        story.append(Paragraph(
            f"Nilai T\u00b2 menunjukkan seberapa jauh kondisi Flow dan Pressure menyimpang " 
            "dari kondisi normal pada setiap jam pengamatan. UCL (Upper Control Limit) "
            f"merupakan batas kendali atas sebesar {ucl:.4f}. Semakin besar selisih nilai T\u00b2 "
            "dari UCL, maka semakin jauh pula indikasi penyimpangan terjadi pada observasi tersebut.",
            body_s))

        ooc_rows = [["Jam", "Flow Distribusi (l/s)", "Pressure Distribusi (Bar)", "T\u00b2", "Selisih (T\u00b2\u2212UCL)"]]
        for _, row in ooc_df.iterrows():
            t2_val = float(row['T2'])
            selisih = t2_val - ucl
            ooc_rows.append([
                str(row["Hour"]),
                f"{float(row[col_flow]):.4f}",
                f"{float(row[col_pres]):.4f}",
                f"{t2_val:.4f}",
                f"+{selisih:.4f}",
            ])

        ooc_cw = [W*0.14, W*0.22, W*0.24, W*0.20, W*0.20]
        ts_ooc = _base_ts(header_bg=colors.HexColor("#c0392b"))
        ts_ooc.add("ROWBACKGROUNDS", (0, 1), (-1, -1),
                   [colors.white, colors.HexColor("#fff0f0")])
        ts_ooc.add("FONTNAME",  (4, 1), (4, -1), "Helvetica-Bold")
        ts_ooc.add("TEXTCOLOR", (4, 1), (4, -1), colors.HexColor("#c0392b"))
        t_ooc = Table(ooc_rows, colWidths=ooc_cw)
        t_ooc.setStyle(ts_ooc)
        story.append(KeepTogether(t_ooc))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.grey, spaceAfter=3))
    story.append(Paragraph(
        f"Laporan dibuat secara otomatis oleh Dashboard Monitoring Hotelling T\u00b2"
        f" \u00b7 Tanggal: {tanggal}",
        foot_s))

    doc.build(story)
    return pdf_buf.getvalue()
