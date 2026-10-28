"""Build the workshop tolerance reference from verified tables.json only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Flowable,
    Frame,
    KeepTogether,
    ListFlowable,
    ListItem,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Tolerans_Referansi.pdf"

NAVY = HexColor("#1B3A4B")
INK = HexColor("#1C2430")
MUTED = HexColor("#5C6B7A")
LINE = HexColor("#D5DDE3")
ZEBRA = HexColor("#F4F7F8")
NOTE_BG = HexColor("#E8F0F4")
WARN_BG = HexColor("#F8F1E3")
ZONE_H = HexColor("#2F6F8F")
ZONE_G = HexColor("#3E7A4E")
ZONE_K = HexColor("#A56A1A")
ZONE_P = HexColor("#8C3A3A")

PAGE_W, PAGE_H = A4
LEFT = 14 * mm
RIGHT = 14 * mm
TOP = 16 * mm
BOTTOM = 14 * mm
CONTENT_W = PAGE_W - LEFT - RIGHT


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))


def styles() -> dict[str, ParagraphStyle]:
    return {
        "cover_kicker": ParagraphStyle(
            "cover_kicker", fontName="Arial", fontSize=10, textColor=MUTED,
            alignment=TA_LEFT, tracking=0.6, leading=14,
        ),
        "cover_title": ParagraphStyle(
            "cover_title", fontName="Arial-Bold", fontSize=26, textColor=NAVY,
            leading=30, alignment=TA_LEFT, spaceAfter=6,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", fontName="Arial", fontSize=12, textColor=INK, leading=16, spaceAfter=4,
        ),
        "H1": ParagraphStyle(
            "H1", fontName="Arial-Bold", fontSize=14, textColor=NAVY, leading=18,
            spaceBefore=0, spaceAfter=8,
        ),
        "contents_title": ParagraphStyle(
            "contents_title", fontName="Arial-Bold", fontSize=14, textColor=NAVY, leading=18,
            spaceBefore=0, spaceAfter=8,
        ),
        "H2": ParagraphStyle(
            "H2", fontName="Arial-Bold", fontSize=11, textColor=NAVY, leading=14,
            spaceBefore=8, spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body", fontName="Arial", fontSize=9.5, textColor=INK, leading=13,
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "body_left": ParagraphStyle(
            "body_left", fontName="Arial", fontSize=9.5, textColor=INK, leading=13,
            alignment=TA_LEFT, spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "small", fontName="Arial", fontSize=8, textColor=INK, leading=10.5, spaceAfter=3,
        ),
        "caption": ParagraphStyle(
            "caption", fontName="Arial", fontSize=8, textColor=MUTED, leading=10.5, spaceBefore=1, spaceAfter=6,
        ),
        "th": ParagraphStyle(
            "th", fontName="Arial-Bold", fontSize=7.5, textColor=white, leading=9, alignment=TA_CENTER,
        ),
        "td": ParagraphStyle(
            "td", fontName="Arial", fontSize=7.5, textColor=INK, leading=9, alignment=TA_CENTER,
        ),
        "td_left": ParagraphStyle(
            "td_left", fontName="Arial", fontSize=7.5, textColor=INK, leading=9, alignment=TA_LEFT,
        ),
        "footer": ParagraphStyle(
            "footer", fontName="Arial", fontSize=8, textColor=MUTED, alignment=TA_LEFT,
        ),
        "toc": ParagraphStyle(
            "toc", fontName="Arial", fontSize=11, textColor=INK, leading=16,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName="Arial", fontSize=9.5, textColor=INK, leading=13, leftIndent=8,
        ),
    }


S = None  # filled in main


def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def P(text: str, style: str = "body") -> Paragraph:
    return Paragraph(esc(text), S[style])


def rich(markup: str, style: str = "body") -> Paragraph:
    """Markup is already reportlab XML. Caller must escape dynamic text."""
    return Paragraph(markup, S[style])


def fmt_um(value) -> str:
    if value is None:
        return "—"
    number = float(value)
    if abs(number) < 1e-9:
        return "0"
    sign = "+" if number > 0 else "−"
    magnitude = abs(number)
    if abs(magnitude - round(magnitude)) < 1e-6:
        body = str(int(round(magnitude)))
    else:
        body = f"{magnitude:.1f}".replace(".", ",")
    return sign + body


def pair(limits) -> str:
    if not limits:
        return "—"
    return f"{fmt_um(limits[0])} / {fmt_um(limits[1])}"


def fmt_mm(nominal: float, micrometres: float) -> str:
    value = nominal + float(micrometres) / 1000.0
    half = abs(float(micrometres) * 2 - round(float(micrometres) * 2)) < 1e-6
    whole = abs(float(micrometres) - round(float(micrometres))) < 1e-6
    digits = 4 if half and not whole else 3
    return f"{value:.{digits}f}".replace(".", ",")


def kind_tr(kind: str) -> str:
    return {"bosluklu": "Boşluklu", "gecisli": "Geçişli", "siki": "Sıkı"}[kind]


def h1(text: str) -> Paragraph:
    return Paragraph(esc(text), S["H1"])


def h2(text: str) -> Paragraph:
    return Paragraph(esc(text), S["H2"])


def callout(text: str, warn: bool = False) -> Table:
    bg = WARN_BG if warn else NOTE_BG
    inner = Paragraph(esc(text), S["body_left"])
    table = Table([[inner]], colWidths=[CONTENT_W])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBEFORE", (0, 0), (0, -1), 3, NAVY if not warn else HexColor("#8A6232")),
            ]
        )
    )
    table.spaceAfter = 8
    return table


def data_table(header: list[str], rows: list[list[str]], widths: list[float], font: float = 7.5) -> Table:
    head = [Paragraph(esc(item), S["th"]) for item in header]
    body = []
    for row in rows:
        styled = []
        for index, item in enumerate(row):
            style = "td_left" if index == 0 else "td"
            styled.append(Paragraph(esc(item), S[style]))
        body.append(styled)
    table = Table([head] + body, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.3, LINE),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, ZEBRA]),
            ]
        )
    )
    table.spaceAfter = 8
    return table


def lookup(block: dict, letter: str, low: int, high: int, grade: int):
    for row in block[letter]:
        if row["low"] == low and row["high"] == high:
            return row["grades"][str(grade)]
    raise KeyError((letter, low, high, grade))


class ZoneDiagram(Flowable):
    """Tolerance zones relative to the nominal-size line. Original drawing."""

    def __init__(self, title: str, zones: list[tuple[str, float, float, Color]], y_min: float, y_max: float):
        super().__init__()
        self.title = title
        self.zones = zones
        self.y_min = y_min
        self.y_max = y_max
        self.width = CONTENT_W
        self.height = 62 * mm

    def draw(self):
        c = self.canv
        c.setFillColor(INK)
        c.setFont("Arial-Bold", 8)
        c.drawString(0, self.height - 10, self.title)
        left = 18 * mm
        right = self.width - 4 * mm
        top = self.height - 18
        bottom = 8
        span = self.y_max - self.y_min

        def y_of(value: float) -> float:
            return bottom + (value - self.y_min) / span * (top - bottom)

        c.setStrokeColor(HexColor("#9AA8B3"))
        c.setLineWidth(0.4)
        for tick in range(int(self.y_min), int(self.y_max) + 1, 10):
            y = y_of(tick)
            c.line(left - 2, y, right, y)
            c.setFillColor(MUTED)
            c.setFont("Arial", 6.5)
            c.drawRightString(left - 3, y - 2, str(tick))
        zero = y_of(0)
        c.setStrokeColor(NAVY)
        c.setLineWidth(1.1)
        c.line(left, zero, right, zero)
        c.setFillColor(NAVY)
        c.setFont("Arial", 7)
        c.drawString(right - 52, zero + 3, "anma ölçüsü")

        count = max(len(self.zones), 1)
        band = (right - left - 8) / count
        for index, (name, lower, upper, color) in enumerate(self.zones):
            x = left + 6 + index * band
            y1 = y_of(min(lower, upper))
            y2 = y_of(max(lower, upper))
            c.setFillColor(color)
            c.setStrokeColor(color)
            c.roundRect(x, y1, min(16 * mm, band - 6), max(y2 - y1, 1.2), 1, fill=1, stroke=0)
            c.setFillColor(INK)
            c.setFont("Arial-Bold", 7.5)
            c.drawString(x, y2 + 3, name)
            c.setFont("Arial", 6.5)
            c.setFillColor(MUTED)
            c.drawString(x, y1 - 8, f"{fmt_um(upper)} / {fmt_um(lower)}")


def bullet_list(items: list[str]) -> ListFlowable:
    flow = []
    for item in items:
        flow.append(ListItem(Paragraph(esc(item), S["bullet"]), leftIndent=12, bulletColor=NAVY))
    return ListFlowable(flow, bulletType="bullet", start="•", bulletFontName="Arial", bulletFontSize=9, spaceAfter=6)


def on_cover(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 8 * mm, PAGE_W, 8 * mm, fill=1, stroke=0)
    canvas.rect(0, 0, PAGE_W, 8 * mm, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont("Arial", 8)
    canvas.drawString(LEFT, 3.2 * mm, "Atölye referansı  ·  28 Ekim 2026")
    canvas.restoreState()


def on_body(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 8 * mm, PAGE_W, 8 * mm, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont("Arial", 8)
    canvas.drawString(LEFT, PAGE_H - 5.4 * mm, "Tolerans Referansı")
    canvas.drawRightString(PAGE_W - RIGHT, PAGE_H - 5.4 * mm, "Sapmalar mikrometredir")
    canvas.setFillColor(MUTED)
    canvas.setFont("Arial", 8)
    canvas.drawString(LEFT, 6 * mm, "Sınırdaki anma ölçüsü, dahil olan alt adıma girer.")
    canvas.drawRightString(PAGE_W - RIGHT, 6 * mm, str(doc.page))
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.4)
    canvas.line(LEFT, 11 * mm, PAGE_W - RIGHT, 11 * mm)
    canvas.restoreState()


class ReferenceDoc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "H1":
            text = flowable.getPlainText()
            self.notify("TOCEntry", (0, text, self.page))
            key = f"sec-{text}"
            self.canv.bookmarkPage(key)
            try:
                self.canv.addOutlineEntry(text, key, level=0, closed=False)
            except Exception:
                pass


def grade_header() -> list[str]:
    return ["Ölçü adımı"] + [f"IT{grade}" for grade in range(5, 12)]


def grade_widths() -> list[float]:
    first = 46 * mm
    other = (CONTENT_W - first) / 7
    return [first] + [other] * 7


def limit_table(rows: list[dict]) -> Table:
    body = []
    for row in rows:
        line = [row["label"]]
        for grade in range(5, 12):
            item = row["grades"][str(grade)]
            if item is None:
                line.append("—")
            else:
                line.append(f"{fmt_um(item['upper'])} / {fmt_um(item['lower'])}")
        body.append(line)
    return data_table(grade_header(), body, grade_widths(), font=7)


def letter_block(letter: str, intro: str, rows: list[dict]) -> list:
    return [
        CondPageBreak(150 * mm),
        h2(letter),
        Paragraph(esc(intro), S["small"]),
        limit_table(rows),
    ]


SHAFT_INTRO = {
    "a": "Boşluk tarafının en uzak konumudur. Üst sapma bütün derecelerde aynıdır; alt sapma = üst sapma − IT. 1 mm ve altında a kullanılmaz.",
    "b": "a'dan daha dar bir boşluk konumudur. Üst sapma sabittir. 1 mm ve altında b kullanılmaz.",
    "c": "Geniş boşluk konumudur. Üst sapma sabittir, alt sapma derece genişledikçe anma ölçüsünden uzaklaşır.",
    "d": "Belirgin boşluk konumudur. Üst sapma negatiftir ve dereceye bağlı değildir.",
    "e": "Orta boşluk konumudur. Üst sapma negatiftir.",
    "f": "Hareketli geçmelerde sık seçilen boşluk konumudur. Üst sapma negatiftir.",
    "g": "Sıfıra yakın küçük boşluk konumudur. Kayarak takılan geçmelerde sık görülür.",
    "h": "Mil esas sistemin temel milidir. Üst sapma her derecede 0'dır. Alt sapma = −IT.",
    "js": "Bölge anma ölçüsünün iki yanında eşit durur: ±IT/2. IT tek sayıysa sapma yarım mikrometredir. Bu belge o yarımı tam sayıya yuvarlamaz.",
    "k": "IT5–IT7'de sıfırın biraz üstündedir. IT8–IT11'de alt sapma 0, üst sapma +IT olur. Delik K ile aynı sayıyı paylaşmaz.",
    "m": "Sıfırın üstünde, k'dan daha içeridedir. Alt sapma dereceye bağlı değildir; üst sapma = alt sapma + IT.",
    "n": "m'den daha sıkı taraftadır. Alt sapma sabittir.",
    "p": "Çoğu ölçüde sıkı geçme tarafındadır. Küçük ölçülerde H7 ile birleşince geçiş de çıkabilir; geçme tablosuna bakın.",
    "r": "p'den daha sıkı konumdadır. Ara ölçü adımlarında değeri değişir.",
    "s": "Sıkı geçme konumudur. 30–40 mm ile 40–50 mm aynı sayıyı taşımaz.",
    "t": "s'den daha sıkıdır. 24 mm ve altına kadar tanımlı değildir; o satırlar boştur.",
    "u": "Bu belgedeki en sıkı mil konumudur. Daha sıkı v, x, y, z, za, zb, zc harfleri anlatılır, tablolaştırılmaz.",
}

# Fix the typo "taraf fromıdır" - I'll correct in the dict. Let me fix before the file is used.
# I'll fix with search_replace after write if I leave the typo. Let me not leave it.
# I already have the typo in the string. I'll correct it in a follow-up replace.

HOLE_INTRO = {
    "A": "Aynı harfli milin üst sapmasının ters işaretlisidir. Alt sapma pozitiftir; üst sapma = alt sapma + IT. 1 mm ve altında A kullanılmaz.",
    "B": "B miliyle simetrik boşluk konumudur. 1 mm ve altında B kullanılmaz.",
    "C": "Geniş delik konumudur. Alt sapma, c milinin üst sapmasının tersidir.",
    "D": "Belirgin boşluk konumudur. Delta düzeltmesi uygulanmaz.",
    "E": "Orta boşluk konumudur. Alt sapma pozitiftir.",
    "F": "f milinin karşılığıdır. Alt sapma = −(f üst sapması).",
    "G": "Küçük boşluk konumudur. Alt sapma = −(g üst sapması).",
    "H": "Delik esas sistemin temel deliğidir. Alt sapma her derecede 0, üst sapma +IT'dir.",
    "JS": "js ile aynı simetrik bölgedir: ±IT/2. Yarım mikrometre aynen bırakılır.",
    "K": "3 mm üzeri IT5–IT8: üst sapma = −(k'nın IT5–IT7 sapması) + delta. IT9–IT11, 3 mm üzeri tanımlı değildir. IT8 deliği, k8 miliyle aynı sayıyı taşımaz.",
    "M": "3 mm üzeri IT5–IT8'de delta eklenir, IT9–IT11'de eklenmez. 250 mm üzeri – 315 mm dahil M6 için üst sapma −9 µm'dir; düzeltmesiz hesap −11 µm verirdi.",
    "N": "3 mm üzeri IT5–IT8'de delta eklenir. IT9–IT11'de üst sapma 0'dır, alt sapma −IT'dir. 1 mm ve altında bu kaba N sınıfları kullanılmaz.",
    "P": "3 mm üzeri IT5–IT7'de delta eklenir, IT8–IT11'de eklenmez. Bu yüzden P7, p6'nın birebir tersi değildir.",
    "R": "P ile aynı delta kuralı. Ara ölçü adımlarında değeri değişir.",
    "S": "Sıkı delik konumudur. IT7'ye kadar delta vardır.",
    "T": "24 mm ve altında tanımlı değildir. Tanımlı olduğu yerde IT7'ye kadar delta eklenir.",
    "U": "Bu belgedeki en sıkı delik konumudur. IT7'ye kadar delta eklenir.",
}


def build_story(tables: dict) -> list:
    story: list = []
    ex30 = tables["examples"]["30_H7g6"]
    ex50 = tables["examples"]["50_H7g6"]

    story.append(Spacer(1, 28 * mm))
    story.append(Paragraph("ATÖLYE REFERANSI", S["cover_kicker"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Tolerans Referansı", S["cover_title"]))
    story.append(Paragraph("Mil ve delik geçmeleri, düz ölçüler, yüzey ve şekil-konum", S["cover_sub"]))
    story.append(Spacer(1, 6 * mm))
    story.append(P(
        "Anma ölçüsü 0 mm üzeri ile 500 mm dahil arasındadır. Sayısal mil ve delik tabloları IT5–IT11 içindir. "
        "Hücreler üst sapma / alt sapma olarak mikrometre verir. Resimdeki ölçü milimetredir: 1 µm = 0,001 mm."
    ))
    story.append(P(
        "Dayanaklar: ISO 286-1:2010, ISO 2768-1:1989, ISO 1101:2017, ISO 21920-1:2021 ve ISO 965-1. "
        "Harf konumları ve sık görülen geçmeler bu çerçevede anlatılır."
    ))
    story.append(callout(
        "Anlaşmazlıkta satın alınmış standart metni geçerlidir. Bu belge, o tabloların kontrol edilmiş atölye dökümüdür. "
        "Doğrulanamayan sayı boş bırakılmıştır. Uygulama cümleleri bilgi amaçlıdır; resimdeki toleransın yerine geçmez.",
        warn=True,
    ))
    story.append(Spacer(1, 8 * mm))
    story.append(P("İçindekiler bir sonraki sayfadadır. PDF yer imleri aynı başlıklara gider.", "body_left"))

    story.append(NextPageTemplate("body"))
    story.append(PageBreak())
    story.append(Paragraph("İçindekiler", S["contents_title"]))
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            name="TOCEntry", fontName="Arial", fontSize=11, textColor=INK, leading=18, leftIndent=4,
        )
    ]
    story.append(toc)
    story.append(PageBreak())

    story.append(h1("Nasıl okunur"))
    story.append(P(
        "Bir tolerans sınıfı iki parçadır. Harf, tolerans bölgesinin anma ölçüsüne göre yerini söyler. "
        "Sayı, bölgenin genişliğini söyler. Genişlik IT derecesidir. Ø50 H7/g6 yazısında anma ölçü 50 mm, "
        "delik H7, mil g6'dır. Büyük harf delik, küçük harf mildir. İkisinin anma ölçüsü aynıdır."
    ))
    story.append(P(
        "Delikte üst sapma ES, alt sapma EI'dir. Milde üst sapma es, alt sapma ei'dir. "
        "Tablodaki ilk sayı üst sapmadır. Bölgenin anma ölçüsüne yakın olan ucu temel sapmadır; "
        "diğer uç, temel sapmaya IT genişliği eklenerek veya çıkarılarak bulunur."
    ))
    story.append(bullet_list([
        "Mil a–h: üst sapma temel sapmadır, alt sapma = üst sapma − IT.",
        "Mil k–u: alt sapma temel sapmadır, üst sapma = alt sapma + IT.",
        "Delik A–H: alt sapma, aynı harfli milin üst sapmasının ters işaretlisidir.",
        "Delik K, M, N, P, R, S, T, U: 3 mm üzerinde ve belirli derecelerde bir delta düzeltmesi vardır. Delik bölümünde yazılıdır.",
        "H deliğinin alt sapması 0'dır. h milinin üst sapması 0'dır.",
        "js ve JS simetriktir: üst sapma +IT/2, alt sapma −IT/2.",
    ]))
    story.append(h2("Sınırdaki ölçü"))
    story.append(P(
        "Adımlar 'üzeri – dahil' diye okunur. 30 mm, 24 üzeri – 30 dahil adımındadır; 30 üzeri – 40 dahil adımında değildir. "
        "50 mm, 40 üzeri – 50 dahil adımındadır. IT genişliği ana adımdan, r, s, t, u gibi harfler ara adımdan okunur."
    ))

    h30u, h30l = ex30["hole"]
    s30u, s30l = ex30["shaft"]
    h50u, h50l = ex50["hole"]
    s50u, s50l = ex50["shaft"]
    story.append(h2("Örnek: Ø30 H7/g6 ve Ø50 H7/g6"))
    story.append(P(
        f"Ø30, 24 üzeri – 30 dahil adımındadır. H7 delik {fmt_um(h30u)} / {fmt_um(h30l)} µm, "
        f"yani {fmt_mm(30, h30l)} mm ile {fmt_mm(30, h30u)} mm arasındadır. "
        f"g6 mil {fmt_um(s30u)} / {fmt_um(s30l)} µm, "
        f"yani {fmt_mm(30, s30l)} mm ile {fmt_mm(30, s30u)} mm arasındadır. "
        f"En küçük boşluk {fmt_um(ex30['fit'][0]).replace('+', '')} µm, en büyük boşluk {fmt_um(ex30['fit'][1]).replace('+', '')} µm'dir. Geçme boşlukludur."
    ))
    story.append(P(
        f"Ø50, 40 üzeri – 50 dahil adımındadır. H7 delik {fmt_um(h50u)} / {fmt_um(h50l)} µm, "
        f"{fmt_mm(50, h50l)} mm ile {fmt_mm(50, h50u)} mm. "
        f"g6 mil {fmt_um(s50u)} / {fmt_um(s50l)} µm, "
        f"{fmt_mm(50, s50l)} mm ile {fmt_mm(50, s50u)} mm. "
        f"En küçük boşluk {fmt_um(ex50['fit'][0]).replace('+', '')} µm, en büyük boşluk {fmt_um(ex50['fit'][1]).replace('+', '')} µm'dir. "
        "30 mm için bulunan −7 / −20, 50 mm'ye taşınmaz."
    ))
    story.append(Paragraph(
        "Hesap: en küçük = deliğin alt sapması − milin üst sapması. En büyük = deliğin üst sapması − milin alt sapması. "
        "Pozitif sonuç boşluktur, negatif sonuç sıkılıktır.",
        S["caption"],
    ))

    k6 = lookup(tables["shafts"], "k", 40, 50, 6)
    p6 = lookup(tables["shafts"], "p", 40, 50, 6)
    h6 = lookup(tables["shafts"], "h", 40, 50, 6)
    g7 = lookup(tables["holes"], "G", 40, 50, 7)
    p7 = lookup(tables["holes"], "P", 40, 50, 7)
    h7 = lookup(tables["holes"], "H", 40, 50, 7)
    story.append(ZoneDiagram(
        "Ø50 civarı, delik esas sistem. Düşey eksen mikrometredir.",
        [
            ("H7", h7["lower"], h7["upper"], ZONE_H),
            ("g6", s50l, s50u, ZONE_G),
            ("k6", k6["lower"], k6["upper"], ZONE_K),
            ("p6", p6["lower"], p6["upper"], ZONE_P),
        ],
        -40,
        50,
    ))
    story.append(Paragraph(
        "H7 anma ölçüsünün üstündedir. g6 tamamen altındadır; bu çift her zaman boşluk bırakır. "
        "k6 sıfırın biraz üstündedir. p6 daha içeridedir.",
        S["caption"],
    ))
    story.append(ZoneDiagram(
        "Ø50 civarı, mil esas sistem. Mil h6 sabittir.",
        [
            ("G7", g7["lower"], g7["upper"], ZONE_G),
            ("H7", h7["lower"], h7["upper"], ZONE_H),
            ("h6", h6["lower"], h6["upper"], ZONE_K),
            ("P7", p7["lower"], p7["upper"], ZONE_P),
        ],
        -50,
        40,
    ))
    story.append(Paragraph(
        "Mil esas sistemde milin üst sapması 0 tutulur, delik harfi değiştirilir. P7, delta yüzünden p6'nın birebir tersi değildir.",
        S["caption"],
    ))

    story.append(h2("İki sistem"))
    story.append(P(
        "Delik esas sistemde delik H'dir; boşluk veya sıkılık milin harfiyle ayarlanır. "
        "Mil esas sistemde mil h'dir; ayar deliğin harfiyle yapılır. "
        "Yaygın uygulama delik esas sistemdir, çünkü bir delik toleransı birçok mile uyar. "
        "Mil esas sistem, aynı milin üzerine farklı delikler geçirilecekse seçilir. İkisi de ISO 286'nın parçasıdır."
    ))
    story.append(h2("Geçmenin türü"))
    story.append(P(
        "En küçük ve en büyük sonuç da sıfır veya pozitifse geçme boşlukludur. H7/h6 bu gruptadır; en küçük boşluk sıfır olabilir. "
        "İki sonuç da sıfır veya negatifse geçme sıkıdır. Biri pozitif, biri negatifse geçme geçişlidir: takılan çift boşluklu da çıkabilir, sıkı da. "
        "Aynı harf çifti küçük ölçüde geçişli, büyük ölçüde sıkı olabilir. Tür, her ölçü adımı için geçme tablosunda ayrı yazılır."
    ))

    story.append(PageBreak())
    story.append(h1("IT dereceleri"))
    story.append(P(
        "IT, uluslararası tolerans derecesidir. Sayı küçüldükçe bölge daralır. "
        "IT7, IT6'dan geniştir. Harf olmadan IT yalnız genişliği söyler; bölgenin anma ölçüsünün neresinde durduğunu söylemez. "
        "Sınıf yazılırken IT harfleri düşer: IT7 genişliğindeki H deliği H7 diye yazılır."
    ))
    story.append(P(
        "Aşağıdaki genişlikler ISO 286-1:2010 Tablo 1 değerleridir ve ikinci bir yayımlanmış tabloyla satır satır karşılaştırılmıştır. "
        "Ham formül bazı hücrelerde bu tablodan 1 µm sapar. Standart, yuvarlama düzeltmesi yapılmış tabloyu esas alır; bu belge de tabloyu esas alır."
    ))
    it_rows = []
    for row in tables["it"]:
        it_rows.append([row["label"]] + [str(row["grades"][str(grade)]) for grade in range(5, 12)])
    story.append(data_table(
        ["Anma ölçüsü"] + [f"IT{grade}" for grade in range(5, 12)],
        it_rows,
        grade_widths(),
    ))
    story.append(Paragraph("Değerler mikrometredir. 30–50 ana adımı, 30 üzeri – 50 dahil aralığıdır.", S["caption"]))
    story.append(callout(
        "IT5 ve IT6 çoğu atölyede taşlama veya hassas delik işiyle anılır. IT7, rayba ve dikkatli talaş için sık hedeflenir. "
        "IT8–IT9 olağan talaş, IT10–IT11 daha geniş bölgelerdir. Bu eşleştirme standartta yoktur; tezgâh değiştikçe değişir. "
        "Dereceyi resim seçer.",
    ))
    story.append(P(
        "IT01–IT4 daha da dardır ve çoğunlukla mastar ile çok hassas işlerde görülür. IT12–IT18 daha geniştir. "
        "Bu iki uç bu belgenin sayısal tablolarında yoktur. Bir resimde IT4 veya IT12 görürseniz ISO 286-2 tablosuna bakın; buradaki IT5 veya IT11 sayısını kaydırmayın."
    ))

    story.append(PageBreak())
    story.append(h1("Harflerin anlamı"))
    story.append(P(
        "Harf, bölgenin yeridir. Kullanılmayan harfler I, L, O, Q ve W'dir; küçükleri de kullanılmaz. "
        "cd, ef ve fg, komşu harflerin arasındadır. v, x, y, z, za, zb ve zc, u'dan daha sıkı konumlara gider. "
        "Bu ara ve uç harflerin limit tablosu bu belgede yoktur."
    ))
    story.append(P(
        "j, js değildir. j simetrik değildir ve yalnız bazı derecelerde tanımlıdır. "
        "Açık cetveller j5/j6 için 18–30 mm bandında 1 µm ayrıştığı için j sayısı yayımlanmamıştır."
    ))
    meaning_rows = [
        ["a / A", "Boşluk tarafının en uzağı. Milin üst sapması büyük ve negatiftir.", "Delik anma ölçüsünden belirgin büyüktür."],
        ["b / B", "a'dan daha yakın, yine geniş boşluk.", "A ile aynı mantık, daha küçük pay."],
        ["c / C", "Geniş boşluk.", "Karşılık delik C."],
        ["d / D", "Belirgin boşluk.", "Karşılık delik D."],
        ["e / E", "Orta boşluk.", "Karşılık delik E."],
        ["f / F", "Hareketli geçmelerde sık görülen boşluk.", "Karşılık delik F."],
        ["g / G", "Sıfıra yakın küçük boşluk.", "Karşılık delik G."],
        ["h / H", "Mil h: üst sapma 0. Mil esas sistem.", "Delik H: alt sapma 0. Delik esas sistem."],
        ["js / JS", "Tam simetrik, ±IT/2.", "Aynı simetri. Yarım mikrometre korunur."],
        ["j / J", "Simetrik değil. Sayı bu belgede yok.", "Aynı nedenle sayı yok."],
        ["k / K", "IT5–IT7'de sıfırın biraz üstü. IT8 ve kabada alt sapma 0.", "IT8'e kadar delta var. IT9 ve kaba, 3 mm üzeri tanımsız."],
        ["m / M", "k'dan daha içeride.", "IT8'e kadar delta. M6'nın bir özel notu vardır."],
        ["n / N", "Geçiş veya hafif sıkılık tarafı.", "IT8'e kadar delta. Daha kabada üst sapma 0."],
        ["p / P", "Çoğu ölçüde sıkı taraf.", "IT7'ye kadar delta. IT8 ve kabada deltasız."],
        ["r / R", "p'den sıkı. Ara adımda değişir.", "Aynı delta kuralı."],
        ["s / S", "Sıkı geçme tarafı.", "Aynı delta kuralı."],
        ["t / T", "s'den sıkı. 24 mm ve altında yok.", "Tanımsız olduğu satır boştur."],
        ["u / U", "Bu belgedeki en sıkı konum.", "IT7'ye kadar delta."],
    ]
    story.append(data_table(
        ["Harf", "Mil", "Delik"],
        meaning_rows,
        [28 * mm, (CONTENT_W - 28 * mm) / 2, (CONTENT_W - 28 * mm) / 2],
    ))
    story.append(callout(
        "Delik harfi, mil harfinin her derecede birebir tersi değildir. 3 mm üzerinde K, M ve N için IT8'e kadar, "
        "P'den U'ya kadar IT7'ye kadar üst sapmaya delta eklenir. Delta, o derecenin IT değerinden bir ince derecenin IT değerinin çıkarılmasıdır. "
        "Amaç, H7/p6 ile P7/h6 gibi komşu derece çiftlerinde aynı boşluk veya sıkılığı korumaktır.",
        warn=True,
    ))

    story.append(PageBreak())
    story.append(h1("Sık kullanılan sınıflar"))
    story.append(P(
        "Günlük bakış için altı sınıf bir aradadır. Hücre üst sapma / alt sapma, mikrometredir. "
        "s6 ara adımda değiştiği için tablo ara adımlarla verilmiştir. Diğer sınıflar da aynı adımlardadır; "
        "ana adım içinde IT değişmez, harf değişebilir."
    ))
    quick_letters = [("H", 7, "holes"), ("H", 8, "holes"), ("g", 6, "shafts"), ("h", 6, "shafts"), ("k", 6, "shafts"), ("p", 6, "shafts"), ("s", 6, "shafts")]
    header = ["Ölçü adımı"] + [f"{letter}{grade}" for letter, grade, _kind in quick_letters]
    rows = []
    for index, row in enumerate(tables["shafts"]["h"]):
        line = [row["label"]]
        for letter, grade, kind in quick_letters:
            item = tables[kind][letter][index]["grades"][str(grade)]
            line.append("—" if item is None else f"{fmt_um(item['upper'])} / {fmt_um(item['lower'])}")
        rows.append(line)
    first = 40 * mm
    rest = (CONTENT_W - first) / len(quick_letters)
    story.append(data_table(header, rows, [first] + [rest] * len(quick_letters)))
    story.append(Paragraph("Örnek: 40 üzeri – 50 dahil satırındaki H7, +25 / 0'dır. 50 mm bu satırdadır.", S["caption"]))

    story.append(PageBreak())
    story.append(h1("Mil limitleri"))
    story.append(P(
        "Her sayfadaki hücre üst sapma / alt sapmadır, birimi mikrometredir. "
        "Boş hücre, o harfin o ölçüde tanımlı olmadığı anlamına gelir. Tanımsız hücrenin yerine komşu harfi koymayın."
    ))
    for letter in ["a", "b", "c", "d", "e", "f", "g", "h", "js", "k", "m", "n", "p", "r", "s", "t", "u"]:
        story.extend(letter_block(f"Mil {letter}", SHAFT_INTRO[letter], tables["shafts"][letter]))

    story.append(PageBreak())
    story.append(h1("Delik limitleri"))
    story.append(P(
        "A–H ve JS, mil kurallarının delik karşılığıdır. K'dan U'ya kadar olan harflerde, 3 mm üzerinde şu düzeltme vardır: "
        "K, M ve N için IT8 dahil, P, R, S, T ve U için IT7 dahil, üst sapma = −(mil temel sapması) + delta. "
        "Delta = ITn − IT(n−1). 3 mm ve altında delta eklenmez."
    ))
    story.append(P(
        "K9, K10 ve K11, 3 mm üzerinde tanımlı değildir. N9, N10 ve N11, 3 mm üzerinde üst sapması 0 olan sınıflardır. "
        "250 mm üzeri – 315 mm dahil M6, ISO 286-1:2010 Tablo 2 notuna göre −9 / −41 µm'dir."
    ))
    for letter in ["A", "B", "C", "D", "E", "F", "G", "H", "JS", "K", "M", "N", "P", "R", "S", "T", "U"]:
        story.extend(letter_block(f"Delik {letter}", HOLE_INTRO[letter], tables["holes"][letter]))

    story.append(PageBreak())
    story.append(h1("Geçmeler"))
    story.append(P(
        "Geçme, aynı anma ölçüsündeki delik ile milin birlikte verdiği boşluk veya sıkılıktır. "
        "Aşağıdaki çiftler yaygın atölye seçimidir. ISO 286-1'in bu baskısındaki ek, bu listeyi 'önerilen dizi' diye adlandırmaz; "
        "liste burada o adla verilmez. Her satırın türü, o adımdaki hesaplanmış uç değerlere göredir."
    ))
    story.append(P(
        "Sütunlar: delik üst/alt, mil üst/alt, en küçük sonuç, en büyük sonuç. "
        "Pozitif boşluk, negatif sıkılıktır. En küçük = delik alt − mil üst. En büyük = delik üst − mil alt."
    ))
    notes = {
        "H11/c11": "Geniş boşluk. Kaba konumlama ve kirli ortamda dönen parçalar için bilgi amaçlı örnektir.",
        "H9/d9": "Belirgin boşluklu geçme. Hareket serbest olsun istenen kaba eşleşmelerde görülür.",
        "H8/f7": "Hareketli boşluklu geçme. Yağlanan, dönen yataklarda sık seçilir.",
        "H7/g6": "Küçük ve her zaman var olan boşluk. Kaydırılarak takılan, yağlanan parçalar.",
        "H7/h6": "En küçük boşluk sıfırdır. Konumlama ve elle takılıp sökülen parçalar. Geçişli değildir.",
        "H7/k6": "Geçişli bölge. Çift, payların gelişine göre boşluklu veya hafif sıkı olabilir.",
        "H7/n6": "Çoğu ölçüde geçişli, büyük ölçüde sıkıya kayabilir. Satırdaki türe bakın.",
        "H7/p6": "Küçük ölçüde geçişli, daha büyük ölçüde sıkı olabilir. Tek cümleyle 'hep pres' demeyin.",
        "H7/s6": "Sıkı geçme. Sökmek için genellikle pres veya ısı gerekir.",
        "H7/u6": "Daha yüksek sıkılık. Tanımsız olduğu küçük ölçüler boştur.",
        "F8/h7": "H8/f7 ile aynı en küçük ve en büyük boşluğu verir. Mil esas sistemdedir.",
        "G7/h6": "H7/g6 ile aynı en küçük ve en büyük boşluğu verir. Mil esas sistemdedir.",
        "K7/h6": "Geçişli bölgenin mil esas sistemdeki karşılığı. 3 mm üzerinde K7 tanımlıdır.",
        "P7/h6": "H7/p6 ile aynı uç sıkılığı verecek şekilde delta uygulanmış delik.",
        "S7/h6": "Sıkı geçmenin mil esas sistemdeki karşılığı.",
    }
    for fit in tables["fits"]:
        designation = fit["designation"]
        rows = []
        for row in fit["rows"]:
            if not row["defined"]:
                rows.append([row["label"], "—", "—", "—", "—", "—"])
            else:
                rows.append([
                    row["label"],
                    pair(row["hole"]),
                    pair(row["shaft"]),
                    fmt_um(row["minimum"]),
                    fmt_um(row["maximum"]),
                    kind_tr(row["kind"]),
                ])
        story.append(CondPageBreak(145 * mm))
        story.append(KeepTogether([
            h2(designation),
            Paragraph(esc(notes[designation]), S["small"]),
        ]))
        story.append(data_table(
            ["Ölçü adımı", "Delik", "Mil", "En küçük", "En büyük", "Tür"],
            rows,
            [40 * mm, 30 * mm, 30 * mm, 28 * mm, 28 * mm, 26 * mm],
        ))

    story.append(PageBreak())
    story.append(h1("Düz ölçüler, ISO 2768-1"))
    story.append(P(
        "ISO 2768-1:1989, yanında ayrıca tolerans yazılmamış doğrusal ve açısal ölçülere genel tolerans verir. "
        "1989 baskısı 2022'de gözden geçirilip yürürlükte bırakılmıştır; yeni bir baskı hazırlanmaktadır. Bu bölüm 1989 baskısınadır. "
        "Kapsam, talaş kaldırılarak veya sac şekillendirilerek yapılan parçalardır. Döküm bu standart değildir."
    ))
    story.append(P(
        "Harfler: f ince, m orta, c kaba, v çok kaba. Antette ISO 2768-m yazısı, toleransı ayrıca verilmemiş ölçülere orta sınıfı uygular. "
        "Ölçünün yanında zaten bir tolerans veya sınır varsa genel tolerans o ölçünün yerine geçmez. "
        "0,5 mm altındaki anma ölçüleri için sapma, ölçünün yanında ayrıca yazılır."
    ))
    story.append(h2("Doğrusal ölçüler"))
    story.append(P("Kırık kenar, dış radyüs ve pah bu tabloda değildir. Değerler milimetre cinsinden ± sapmadır."))
    linear_rows = []
    for row in tables["iso2768"]["linear"]:
        low, high = row["low"], row["high"]
        if low == 0.5:
            label = "0,5 – 3 dahil"
        else:
            label = f"{_num(low)} üzeri – {_num(high)} dahil"

        def cell_mm(value):
            if value is None:
                return "—"
            return "±" + _num(value)

        linear_rows.append([label, cell_mm(row["f"]), cell_mm(row["m"]), cell_mm(row["c"]), cell_mm(row["v"])])
    story.append(data_table(
        ["Anma ölçüsü (mm)", "f ince", "m orta", "c kaba", "v çok kaba"],
        linear_rows,
        [52 * mm, 32.5 * mm, 32.5 * mm, 32.5 * mm, 32.5 * mm],
    ))
    story.append(h2("Pah ve dış radyüs"))
    story.append(P("f ile m aynı sütundadır, c ile v aynı sütundadır. 6 mm üzerinin üst sınırı tabloda kapatılmamıştır."))
    chamfer_rows = []
    for row in tables["iso2768"]["chamfer"]:
        if row["high"] is None:
            label = "6 üzeri"
        elif row["low"] == 0.5:
            label = "0,5 – 3 dahil"
        else:
            label = f"{_num(row['low'])} üzeri – {_num(row['high'])} dahil"
        chamfer_rows.append([label, "±" + _num(row["fm"]), "±" + _num(row["cv"])])
    story.append(data_table(
        ["Anma ölçüsü (mm)", "f ve m", "c ve v"],
        chamfer_rows,
        [70 * mm, 55 * mm, 55 * mm],
    ))
    story.append(h2("Açılar"))
    story.append(P(
        "Adım, açının kısa kenarının uzunluğudur. f ile m yine aynıdır. "
        "120 mm üzeri – 400 mm dahil kaba sınıf ±0°15'tir. Bunu ±0°20' diye basan bazı ticari cetveller bu belgeye alınmamıştır."
    ))
    angular_rows = []
    for row in tables["iso2768"]["angular"]:
        if row["low"] == 0:
            label = "10 mm'ye kadar"
        elif row["high"] is None:
            label = "400 mm üzeri"
        else:
            label = f"{_num(row['low'])} üzeri – {_num(row['high'])} dahil"
        angular_rows.append([label, _angle(row["fm"]), _angle(row["c"]), _angle(row["v"])])
    story.append(data_table(
        ["Kısa kenar", "f ve m", "c kaba", "v çok kaba"],
        angular_rows,
        [58 * mm, 40 * mm, 40 * mm, 40 * mm],
    ))
    story.append(callout(
        "Genel toleransın dışına çıkan parça, işlevi bozulmuyorsa yalnız bu yüzden otomatik reddedilmez. "
        "Bu kural ISO 2768-1'in kendi metnindedir. İşlev bozuluyorsa ret kararı durur. Kararı resmin sahibi verir.",
    ))

    story.append(PageBreak())
    story.append(h1("Eski ISO 2768-mK yazısı"))
    story.append(callout(
        "ISO 2768-2:1989 yürürlükten kalkmıştır. Yerine ISO 22081:2021 gelmiştir. Yeni resme H, K veya L yazmayın.",
        warn=True,
    ))
    story.append(P(
        "Eski antetlerde ISO 2768-mK görülür. Buradaki m, hâlâ yürürlükte olan ISO 2768-1 orta doğrusal ve açısal sınıftır. "
        "K, yürürlükten kalkan ISO 2768-2'nin geometrik genel tolerans sınıfıdır. O standartta H ince, K orta, L kaba geometrik sınıftı."
    ))
    story.append(P(
        "ISO 22081, geometriyi H/K/L harfiyle seçtirmez. Genel geometrik şart resimde veya modelde açık yazılır. "
        "Bu belgede H/K/L için mikrometre tablosu yoktur; eski tablo yeni işe kopyalanmasın diye konmamıştır. "
        "Eski bir resmi okurken K harfini bugünkü bir IT derecesi veya ISO 286 harfi sanmayın."
    ))

    story.append(h1("Yüzey"))
    story.append(P(
        "Yüzey dokusunun resimde gösterimi ISO 21920-1:2021'e göredir. Bu standart, ISO 1302:2002'nin yerine geçmiştir. "
        "Ra bir tolerans harfi değildir, bir IT derecesi değildir ve ISO 2768 sınıfı değildir. "
        "Ra, değerlendirilen profilin aritmetik ortalama yüksekliğidir."
    ))
    story.append(P(
        "Rz, ISO 21920-2'de profilin en büyük yüksekliğidir. Eski resimlerde Rz, ISO 4287'deki başka bir tanımla kullanılmış olabilir. "
        "Eski bir Rz sayısını, yeni tanımdaki Rz ile aynı şart saymayın. Hangi standardın geçerli olduğunu resim veya sipariş söyler."
    ))
    story.append(bullet_list([
        "Açık yüzey işareti: imalat yöntemi serbesttir.",
        "İşaretin üzerinde yatay çizgi: talaş kaldırmak gerekir.",
        "İşaretin içinde daire: talaş kaldırmak yasaktır.",
        "Ra 1,6 gibi bir yazı, aksi resimde belirtilmedikçe o parametrenin üst sınırıdır.",
        "ISO 21920-1'de varsayılan kabul kuralı maksimum kuralıdır: ölçülen değer sınırı aşamaz.",
        "Filtre, değerlendirme uzunluğu ve işleme izinin yönü yazılacaksa kurallar ISO 21920-1'dedir. Eski altı kutulu ISO 1302 şeması yeni resmin kuralı diye kullanılmaz.",
    ]))
    story.append(callout(
        "ISO, frezeleme veya tornalama için zorunlu bir Ra sayısı vermez. Tezgâh ilanlarındaki 'tipik Ra' değerleri standart şartı değildir. "
        "Bu belgeye o sayılar konmamıştır. Resimde yazan parametre ve sınır geçerlidir.",
    ))

    story.append(PageBreak())
    story.append(h1("Şekil ve konum"))
    story.append(P(
        "ISO 1101:2017, şekil, yön, yer ve salgı toleranslarının sembol dilidir. "
        "Bu bölüm her sembolün neyi sınırladığını bir cümleyle söyler. Sayısal genel değer vermez; resimdeki değer geçerlidir. "
        "Aynı görünen sembol ASME Y14.5'te her zaman aynı kuralla okunmaz. Buradaki okuma ISO 1101 içindir."
    ))
    story.append(P(
        "Tolerans çerçevesi soldan sağa okunur: sembol, tolerans değeri, varsa çap işareti, sonra referans harfleri. "
        "Referans, harfle işaretlenmiş elemandır. Konum ve yön toleransları bu elemanlara göre durur. Şekil toleransları referanssız olabilir."
    ))
    gdt_rows = [
        ["Doğrusallık", "Şekil", "Eleman, belirtilen yönde iki paralel doğru arasında kalır."],
        ["Düzlemsellik", "Şekil", "Yüzey, iki paralel düzlem arasında kalır."],
        ["Dairesellik", "Şekil", "Her enine kesit, iki eş merkezli daire arasında kalır."],
        ["Silindiriklik", "Şekil", "Yüzey, iki eş eksenli silindir arasında kalır."],
        ["Çizgi profili", "Şekil", "Çizgi, teorik profile göre bir bant içinde kalır."],
        ["Yüzey profili", "Şekil", "Yüzey, teorik profile göre bir bant içinde kalır."],
        ["Paralellik", "Yön", "Eleman, referansa paralel bir bölge içinde kalır."],
        ["Diklik", "Yön", "Eleman, referansa dik bir bölge içinde kalır."],
        ["Açısallık", "Yön", "Eleman, referansa göre verilen açıda bir bölge içinde kalır."],
        ["Konum", "Yer", "Elemanın yeri, referanslara göre sınırlanan bölgenin içinde kalır."],
        ["Eş eksenlilik", "Yer", "Türetilmiş eksen, referans eksenine göre bir silindirin içinde kalır."],
        ["Simetri", "Yer", "Orta eleman, referansa göre simetri bölgesinde kalır."],
        ["Dairesel salgı", "Salgı", "Parça referans ekseninde dönerken bir kesitteki salgı sınırlıdır."],
        ["Toplam salgı", "Salgı", "Parça dönerken yüzeyin bütünündeki salgı sınırlıdır."],
    ]
    story.append(data_table(
        ["Sembolün adı", "Grup", "Neyi sınırlar"],
        gdt_rows,
        [38 * mm, 22 * mm, CONTENT_W - 60 * mm],
    ))
    story.append(P(
        "Çap işareti, tolerans bölgesinin silindir veya daire olduğunu söyler. İşaret yoksa bölge, belirtilen yönde iki paralel düzlem veya iki paralel doğru arasındadır. "
        "Ayrıntılı birleştirme kuralları, malzeme ilkesi ve referans sistemi ISO 1101 ve ona bağlı GPS standartlarındadır."
    ))

    story.append(h1("Metrik vida"))
    story.append(P(
        "Genel amaçlı metrik vida toleransı ISO 965'e göredir. Sınıf, bir tolerans derecesi ile bir konum harfinden oluşur. "
        "Sayı bölgenin genişliğidir; küçük sayı daha dar bölgedir. Harf, bölgenin yeridir. Bu harf ve sayı ISO 286 IT sınıfının aynısı değildir; mikrometre tablosu paylaşılmaz."
    ))
    story.append(bullet_list([
        "İç vida konum harfleri G ve H'dir. H'de temel sapma sıfırdır. G, iç vidayı büyütür ve boşluk bırakır.",
        "Dış vida konum harfleri e, f, g ve h'dir. h'de temel sapma sıfırdır. g, f ve e dış vidayı küçültür; e en geniş boşluğu verir.",
        "Orta sınıfın yaygın eşleşmesi 6H/6g'dir. Yazım: M10×1,5-6H iç vida, M10×1,5-6g dış vida.",
        "Çap ve adıma bağlı sayısal paylar ISO 965-2 tablolarındadır. Bu belgeye konmamıştır.",
    ]))
    story.append(callout(
        "Resimde yalnız M10 yazıp sınıf yazmamak, atölyeye 6H veya 6g seçme hakkı vermez. Sınıf yazılmamışsa siparişin veya standardın varsayılanına bakılır; tahmin edilmez.",
        warn=True,
    ))

    story.append(PageBreak())
    story.append(h1("Bu belgede olmayanlar"))
    story.append(bullet_list([
        "Rulman iç ve dış bilezik geçmeleri burada yoktur. Yükün yönü, hangi bileziğin döndüğü ve rulman tipi seçimi değiştirir. H7/k6 her rulman için doğru geçme değildir. Katalog kullanılır.",
        "Kama ve kama kanalı payları burada yoktur. Kanal ISO 286 harfiyle yazılsa bile sayı, kama standardının kendi tablosundadır. İki bağımsız sayı bu belgeye alınmadığı için hücre konmamıştır.",
        "Döküm genel toleransları ISO 8062 ailesindedir. ISO 2768-1 döküm tablosu değildir.",
        "İnç toleransları ve ASME Y14.5 varsayılan sayıları yoktur.",
        "500 mm üzeri, IT01–IT4, IT12–IT18, j ve cd–zc uç harflerinin limitleri yoktur.",
    ]))

    story.append(h1("Kontrol notu"))
    story.append(P(
        f"Sayısal mil ve delik hücreleri, iki bağımsız temel sapma tablosu birebir uyuştuktan sonra IT genişliğiyle hesaplanmıştır. "
        f"Hesabın uç değerleri {tables['verification']['anchor_count']} örnekte üçüncü kaynaklarla karşılaştırılmıştır. "
        "Bir mikrometre fark olsaydı o hücre yayımlanmazdı."
    ))
    story.append(h2("Karşılaştırılan örnekler"))
    anchor_rows = []
    for anchor in tables["verification"]["anchors"]:
        if anchor["source"].startswith("MechSheet P7") and anchor["range"] != [30, 40]:
            continue
        if anchor["source"].startswith("Metronq") and anchor["range"] != [40, 50]:
            continue
        low, high = anchor["range"]
        label = "3'e kadar" if low == 0 else f"{low}–{high}"
        anchor_rows.append([
            anchor["source"],
            anchor["class"],
            label,
            f"{fmt_um(anchor['upper'])} / {fmt_um(anchor['lower'])}",
        ])
    story.append(data_table(
        ["Kaynak", "Sınıf", "Adım", "Üst / alt"],
        anchor_rows,
        [78 * mm, 22 * mm, 32 * mm, 40 * mm],
    ))
    story.append(Paragraph(
        "MechSheet P7'nin 25 adımının tamamı ve Metronq'nun 30–40 ile 40–50 adımları kontrolde vardı. Tabloda tekrarlar kısaltılmıştır.",
        S["caption"],
    ))
    story.append(h2("Dayanaklar"))
    story.append(bullet_list(tables["verification"]["sources"]))
    story.append(h2("Bilerek dışarıda bırakılanlar"))
    story.append(bullet_list(tables["verification"]["omitted"]))
    story.append(callout(
        "Ø36 H8/f7 için ISO 286-1 Ek B, en küçük boşluğu 0,025 mm ve en büyük boşluğu 0,089 mm verir. "
        "Ø36 H7/n6 geçişlidir: 0,033 mm sıkılık ve 0,008 mm boşluk. "
        "Ø36 H7/s6 sıkıdır: 0,059 mm ve 0,018 mm. Bu üç hesap belgedeki tablolarla aynıdır.",
    ))
    return story


def _num(value) -> str:
    if isinstance(value, int) or (isinstance(value, float) and value == int(value)):
        return str(int(value))
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


def _angle(pair_value: list[int]) -> str:
    degrees, minutes = pair_value
    if minutes == 0:
        return f"±{degrees}°"
    return f"±{degrees}°{minutes}′"


def main() -> None:
    global S
    register_fonts()
    S = styles()
    verify.main()
    tables = json.loads((ROOT / "data" / "tables.json").read_text(encoding="utf-8"))
    # The worked examples are part of the contract with the reader.
    ex50 = tables["examples"]["50_H7g6"]
    if ex50["hole"] != [25.0, 0.0] or ex50["shaft"] != [-9.0, -25.0] or ex50["fit"][:2] != [9.0, 50.0]:
        raise SystemExit("Ø50 H7/g6 örneği doğrulanmış değerlerden saptı")
    ex30 = tables["examples"]["30_H7g6"]
    if ex30["hole"] != [21.0, 0.0] or ex30["shaft"] != [-7.0, -20.0] or ex30["fit"][:2] != [7.0, 41.0]:
        raise SystemExit("Ø30 H7/g6 örneği doğrulanmış değerlerden saptı")

    doc = ReferenceDoc(
        str(OUT),
        pagesize=A4,
        title="Tolerans Referansı",
        author="Atölye referansı",
        subject="ISO 286, ISO 2768-1, ISO 1101, ISO 21920 ve ISO 965 atölye dökümü",
    )
    frame_cover = Frame(LEFT, BOTTOM, CONTENT_W, PAGE_H - TOP - BOTTOM, id="cover", showBoundary=0)
    frame_body = Frame(LEFT, BOTTOM + 4 * mm, CONTENT_W, PAGE_H - TOP - BOTTOM - 6 * mm, id="body", showBoundary=0)
    doc.addPageTemplates(
        [
            PageTemplate(id="cover", frames=[frame_cover], onPage=on_cover),
            PageTemplate(id="body", frames=[frame_body], onPage=on_body),
        ]
    )
    doc.multiBuild(build_story(tables))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
