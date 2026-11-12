"""One-shot: print-ready A4 PDF of the IB AA HL generator audit."""

from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfgen import canvas as pdfcanvas

OUT = Path(__file__).resolve().parent / "IB_AA_HL_generator_audit.pdf"
INK = colors.HexColor("#1e293b")
MUTED = colors.HexColor("#475569")
LINE = colors.HexColor("#cbd5e1")
HEAD = colors.HexColor("#0f172a")
BAND = colors.HexColor("#e2e8f0")
WARN = colors.HexColor("#9a3412")
WARN_BG = colors.HexColor("#ffedd5")
OK = colors.HexColor("#14532d")
DANGER_BG = colors.HexColor("#fee2e2")
P0_BG = colors.HexColor("#fef3c7")


def _fonts():
    folder = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    pdfmetrics.registerFont(TTFont("DejaVu", str(folder / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(folder / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Oblique", str(folder / "DejaVuSans-Oblique.ttf")))


class Numbered(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self._decorate(n)
            super().showPage()
        super().save()

    def _decorate(self, n):
        self.saveState()
        self.setStrokeColor(LINE)
        self.setLineWidth(0.4)
        self.line(18 * mm, A4[1] - 14 * mm, A4[0] - 18 * mm, A4[1] - 14 * mm)
        self.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
        self.setFillColor(MUTED)
        self.setFont("DejaVu", 8)
        self.drawString(18 * mm, A4[1] - 11 * mm, "IB DP Mathematics AA HL  —  audyt generatorów i silnika składania")
        self.drawRightString(A4[0] - 18 * mm, A4[1] - 11 * mm, "poufne / ocena produktu")
        self.drawString(18 * mm, 9 * mm, "stem-generator  ·  11 listopada 2026")
        self.drawRightString(A4[0] - 18 * mm, 9 * mm, f"strona {self._pageNumber} / {n}")
        self.restoreState()


def styles():
    return {
        "h1": ParagraphStyle("h1", fontName="DejaVu-Bold", fontSize=16, leading=20, textColor=HEAD, spaceAfter=8),
        "h2": ParagraphStyle("h2", fontName="DejaVu-Bold", fontSize=12.5, leading=16, textColor=HEAD, spaceBefore=12, spaceAfter=6),
        "h3": ParagraphStyle("h3", fontName="DejaVu-Bold", fontSize=10.5, leading=14, textColor=HEAD, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body", fontName="DejaVu", fontSize=9, leading=12.5, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=6),
        "small": ParagraphStyle("small", fontName="DejaVu", fontSize=8, leading=11, textColor=MUTED, spaceAfter=4),
        "cell": ParagraphStyle("cell", fontName="DejaVu", fontSize=7.4, leading=9.6, textColor=INK),
        "cellb": ParagraphStyle("cellb", fontName="DejaVu-Bold", fontSize=7.4, leading=9.6, textColor=HEAD),
        "th": ParagraphStyle("th", fontName="DejaVu-Bold", fontSize=7.4, leading=9.6, textColor=colors.white),
        "code": ParagraphStyle("code", fontName="DejaVu", fontSize=8, leading=11, textColor=HEAD, backColor=BAND, leftIndent=4, rightIndent=4, spaceBefore=2, spaceAfter=6),
        "verdict": ParagraphStyle("verdict", fontName="DejaVu", fontSize=9, leading=12.5, textColor=WARN, backColor=WARN_BG, leftIndent=6, rightIndent=6, spaceBefore=4, spaceAfter=8, borderPadding=6),
        "li": ParagraphStyle("li", fontName="DejaVu", fontSize=9, leading=12.2, textColor=INK),
        "foot": ParagraphStyle("foot", fontName="DejaVu-Oblique", fontSize=8, leading=11, textColor=MUTED, spaceAfter=6),
    }


def P(text, style):
    return Paragraph(text, style)


def bullets(items, st):
    return ListFlowable(
        [ListItem(P(item, st["li"]), leftIndent=8, bulletColor=INK) for item in items],
        bulletType="bullet",
        start="•",
        leftIndent=14,
        bulletFontName="DejaVu",
        bulletFontSize=8,
        spaceAfter=6,
    )


def grid(headers, rows, col_widths, st, tone=None):
    head = [P(escape(h), st["th"]) for h in headers]
    body = []
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cells.append(P(cell if "<" in str(cell) else escape(str(cell)), st["cellb"] if i == 0 else st["cell"]))
        body.append(cells)
    data = [head] + body
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEAD),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("GRID", (0, 0), (-1, -1), 0.25, LINE),
    ]
    if tone:
        for index, kind in tone:
            bg = DANGER_BG if kind == "danger" else P0_BG if kind == "warn" else colors.HexColor("#dcfce7")
            cmds.append(("BACKGROUND", (0, index + 1), (-1, index + 1), bg))
    tbl.setStyle(TableStyle(cmds))
    return tbl


def build():
    _fonts()
    st = styles()
    usable = A4[0] - 36 * mm
    story = []

    story.append(P("Audyt generatorów i silnika składania", st["h1"]))
    story.append(P("IB DP Mathematics AA HL  ·  ocena produktu edukacyjnego i komercyjnego", st["small"]))
    story.append(P(
        "Zakres: katalog <b>generators/</b>, silnik <b>core/</b>, składanie arkusza w <b>app.py</b> i rejestr w <b>registry.py</b>. "
        "Cel: trzy kohorty (A, B, C) nie mogą być trywialnymi kopiami ze zmienioną jedną liczbą, "
        "a jednocześnie uczeń wariantu B nie może dostać zadania istotnie dłuższego przy tej samej liczbie punktów.",
        st["body"],
    ))
    story.append(P(
        "<b>Werdykt.</b> Silnik poprawnie trzyma sumy punktów i graf części wewnątrz jednego poziomu trudności, "
        "ale kohorty A/B/C są <b>bliźniakami liczbowymi, nie bliźniakami poznawczymi</b>. "
        "Detekcja duplikatów porównuje <b>latex_main + „|” + archetype</b> i na 12. próbie <b>zawsze</b> akceptuje kolizję. "
        "Przełączenie standard → challenging zmienia liczbę operacji GDC/analitycznych, więc nie wolno używać go do wariantowania kohort. "
        "Mark scheme nie spełnia standardu IB (brak FT, brak zasady 3 s.f. dla egzaminatora, kody G2).",
        st["verdict"],
    ))
    story.append(P(
        "Pule zmierzono przez import generatorów (runtime). Identity key w produkcji: "
        "<b>candidate.latex_main + \"|\" + candidate.archetype</b>  (app.py, _compose_papers).",
        st["foot"],
    ))

    story.append(P("1. Głębokość banków i ryzyko kolizji", st["h2"]))
    story.append(P("1.1 Jak dziś mierzona jest „unikalność”", st["h3"]))
    story.append(P(
        "Pętla kohort jest w <b>_compose_papers</b> (<b>app.py:64–122</b>). Dla każdego tematu wykonuje do 12 prób z nasionem "
        "<b>{seed}-{difficulty}-{A|B|C}-{key}-try{attempt}</b>. Kandydat przechodzi, gdy klucz "
        "<b>latex_main|archetype</b> nie wystąpił wcześniej — albo gdy <b>attempt == 11</b> (ostatnia próba, indeks 0-based). "
        "To samo lustro jest w <b>tests/test_pdf_layout.py:43–51</b>, więc testy zatwierdzają cichą kolizję.",
        st["body"],
    ))
    story.append(P(
        "<b>call_generator</b> (<b>registry.py:784–794</b>) sprawdza tylko typ Task i zgodność sumy marek z TASK_REGISTRY. "
        "Nie sprawdza archetype_id, grafu części ani kosztu GDC.",
        st["body"],
    ))

    story.append(grid(
        ["Luka", "Skutek"],
        [
            ["Klucz ignoruje intro, table_data, family, treść parts",
             "Trzy konteksty w ext_gdc_stat._contexts() (apples / rods / lifetime) nie liczą się do unikalności."],
            ["Stały string archetype",
             "Unikalność spada do samego latex_main (gdc_intersect, gdc_area, gdc_trig, gdc_dist)."],
            ["Pusty latex_main przy χ² niezależności",
             "Klucz degeneruje do „|” + archetype — dobre dla tabel, bezużyteczne dla sformułowania."],
            ["attempt == 11",
             "Przy wyczerpanej puli kohorta C dostaje kopię A lub B bez błędu i bez flagi."],
        ],
        [usable * 0.38, usable * 0.62],
        st,
    ))
    story.append(Spacer(1, 8))

    story.append(P("1.2 Mock Paper 2 — pule przy difficulty = standard, 3 kohorty", st["h3"]))
    story.append(P(
        "Preset <b>mock_p2</b> (<b>registry.py:754–779</b>): 10 pytań Section A (65 mk) + 2 Section B (35 mk) = 100 mk.",
        st["body"],
    ))
    story.append(grid(
        ["Klucz", "Pula (standard)", "Struktura", "Ryzyko 3 kohort"],
        [
            ["gdc_intersect", "2 pary (1,2) i (1,3); filtr slope=1", "stały archetype, stem ln x = x − c", "Krytyczne"],
            ["gdc_area", "c ∈ {1,2,3}, granice zawsze [0,2]", "stały archetype, tylko √(x³+c)", "Wysokie"],
            ["gdc_dist", "n ∈ [10,20], 5 wartości p", "stały archetype binomial", "Średnie liczby; struktura zamrożona"],
            ["bivar", "6 tabel; 3 okładki w _story", "2 archetypy: interpolacja vs ekstrapolacja", "Okładka losowana poza kluczem"],
            ["kin_gdc", "11 itemów, 3 z 1 zmianą znaku", "ten sam s(t)=t²cos t + c t sin t", "Wysokie — pula 3 na 3 kohorty"],
            ["gdc_trig", "6 poziomów → 3 przeżywają 3 s.f.", "zawsze sin x = k, 3 pierwiastki; difficulty jest del", "Wysokie"],
            ["gdc_curve", "4 kandydaty; przeżywają 2, oba a=1", "ten sam e^{−x} ln(1+x); challenging cicho wraca do tych 2", "Krytyczne"],
            ["gdc_system", "24 unikalne 3×3; 57 parametrycznych", "standard = punkt; challenging = k i det=0", "Liczby OK; graf części inny"],
            ["gdc_chi", "5 tabel 2×2, 3 tabele 2×3", "etykiety zawsze Group 1/2, Type A/B", "Wysokie — permutacja komórek"],
            ["gdc_chi_gof", "54 łącznie; standard = 18 kości", "zawsze fair die, 6 klas", "Liczby OK; zawsze ekwiprawdopodobne"],
            ["ext_gdc_model", "4 itemy, po 2 na a=1 i a=2", "łańcuch (a)…(e), 16 mk", "Krytyczne Section B: 2 itemy / 3 kohorty"],
            ["ext_gdc_stat", "8 zestawów × 3 konteksty", "archetype = tylko liczby; story = choice()", "Historie istnieją i są marnowane"],
        ],
        [usable * 0.18, usable * 0.28, usable * 0.32, usable * 0.22],
        st,
        tone=[
            (0, "danger"), (1, "warn"), (4, "warn"), (5, "danger"),
            (6, "danger"), (8, "warn"), (10, "danger"), (11, "warn"),
        ],
    ))
    story.append(Spacer(1, 6))
    story.append(P(
        "<b>gdc_curve</b> w praktyce: oba ocalałe itemy mają ten sam punkt stacjonarny 0,763 i wysokość 0,264; "
        "różni się tylko górna granica pola (2 vs 3). Plik <b>generators/gdc_curve.py:47–67</b>. "
        "Challenging filtruje a=2; pula pusta; fallback na te same dwa itemy.",
        st["body"],
    ))
    story.append(P(
        "Źródła pul: paper2_gdc.py _LOG_LINES 19–25; gdc_chi_squared.py _bank 38–109; "
        "gdc_chi_gof.py _build_bank 41–119; gdc_extended_stat.py _contexts 41–61 i _BANK 157; "
        "gdc_extended_model.py _bank 61–78; gdc_linear_system.py _UNIQUE 212; "
        "kinematics_gdc.py _bank 90–110; gdc_trigonometry.py _bank 33–56; "
        "statistics_bivariate.py _RAW 101–108 i _story 142–160.",
        st["foot"],
    ))

    story.append(P("1.3 Paper 1 / core — wybrane pule", st["h3"]))
    story.append(P(
        "Generatory parametryczne (sample_cubic w core/randomizer.py:121–145, SKEW_POOL = 32) dają dużo liczb przy zamrożonym grafie pytania. "
        "Wąskie banki stałe:",
        st["body"],
    ))
    story.append(grid(
        ["Klucz", "Pula", "Uwaga"],
        [
            ["prob_bayes", "6 linii (probability_bayes.py:9–16)", "Zawsze dwie maszyny; challenging odwraca warunek (77–88) — to nie izomorfizm."],
            ["trig_rform", "5; standard bierze pierwsze 2", "Wąska pula sformułowań."],
            ["trig_inv", "5; standard 2", "Wąska pula."],
            ["trig_identity", "3 + 3 funkcje", "Inny dowód = inny czas."],
            ["calc_euler", "5 krótkich / 4 długie", "2 vs 3 kroki Eulera."],
            ["binomial_frac", "9 (4+5)", "Split całkowite vs ułamkowe."],
            ["paper3_geo / paper3_mac", "3 / 4", "Śledztwa 16 mk."],
            ["prob_rv binomial / Poisson", "56 / 24", "Duża pula liczb; dwa różne prawa w jednym kluczu."],
        ],
        [usable * 0.28, usable * 0.28, usable * 0.44],
        st,
    ))
    story.append(Spacer(1, 6))
    story.append(P(
        "<b>Wniosek kolizyjny.</b> Przy trzech oficjalnych mockach największe ryzyko identycznego stemu mają "
        "gdc_curve, ext_gdc_model, gdc_intersect, gdc_trig, gdc_chi 2×2. "
        "Przy trzech klasówkach największe ryzyko tej samej historii mają wszystkie tematy grupy (a), "
        "bo silnik w ogóle nie wymaga różnego cover_id.",
        st["body"],
    ))

    story.append(P("2. Koszt czasowy i poznawczy (isomorphic cognitive load)", st["h2"]))
    story.append(P(
        "<b>Zasada.</b> Parametr difficulty w generatorach to inny papier, nie inna kohorta. "
        "W _compose_papers wszystkie kohorty muszą dostać ten sam difficulty. "
        "Split standard/challenging służy wyłącznie do dwóch produktów (sprawdzian vs exam-trap), nigdy do A vs B vs C.",
        st["body"],
    ))
    story.append(grid(
        ["Klucz", "standard", "challenging", "Zmiana obciążenia"],
        [
            ["gdc_dist", "Binomial: binomPdf + cdf + np", "Inverse normal invNorm", "Inne klawisze GDC (gdc_statistics.py:151–155)"],
            ["gdc_chi", "2×2, df=1, 4 komórki E", "2×3, df=2, 6 komórek", "Więcej arytmetyki (gdc_chi_squared.py:138)"],
            ["gdc_system", "3 płaszczyzny, 1 punkt", "parametr k, det=0, none/infinite", "Inna algebra (gdc_linear_system.py:222–270)"],
            ["kin_gdc", "1 zero v(t)", "2 zera", "Dodatkowy kawałek ∫|v| (kinematics_gdc.py:128)"],
            ["gdc_chi_gof", "fair die, 6 klas, df=5", "genetics/survey, 4 klasy", "Inny df i historia (gdc_chi_gof.py:128)"],
            ["gdc_area", "granice [0,2]", "[1,3]", "Ten sam GDC path — wyjątek izomorficzny"],
            ["prob_bayes", "P(A|D)", "P(B|D')", "Ten sam wzór, inna gałąź — granica izomorfizmu"],
            ["ext_calculus", "pole pod cubikiem", "warunek y=k jedna interpolacja", "Inna część (e) (section_b.py:104–118)"],
            ["ext_model", "Newton cooling", "drug clearance", "Całkiem inny model (section_b.py:231–234)"],
            ["calc_parts / calc_euler", "1× parts / 2 kroki", "2× parts / 3 kroki", "Extra integracja / extra wiersz"],
            ["complex_demoivre", "n=3", "n=4", "Extra pierwiastek"],
        ],
        [usable * 0.20, usable * 0.26, usable * 0.26, usable * 0.28],
        st,
    ))

    story.append(P("2.1 Grupa (a) — kandydaci do wariantowania", st["h3"]))
    story.append(P(
        "Te tematy można opowiedzieć inaczej przy identycznej sekwencji GDC/kroków i identycznym wektorze punktów. "
        "W nawiasie: part_graph_id do zamrożenia. Dla każdego: 2–3 równoważne archetypy.",
        st["body"],
    ))
    story.append(grid(
        ["Temat", "Zamrożony graf", "Archetypy izomorficzne (2–3)"],
        [
            ["gdc_dist (tylko binomial)", "binomPdf → binomCdf → np  [2+2+2]",
             "(i) wadliwe sztuki w partii; (ii) zdane testy w klasie; (iii) kiełkowanie nasion. Nie mieszać z invNorm."],
            ["gdc_chi (tylko 2×2)", "H0/H1 → Eij → χ²calc → porównanie z χ²crit podanym  [2+2+2+2]",
             "(i) leczenie vs placebo × poprawa/brak; (ii) język nauczania × pass/fail; (iii) zmiana vs brak × defekt. Dziś etykiety sztywne (linie 147–151)."],
            ["gdc_chi_gof (6 klas równych)", "H0 → Ei=n/6 → χ² → wniosek  [2+2+2+2]",
             "(i) kość; (ii) spinner 6 sektorów; (iii) przyjazdy w 6 przedziałach dnia. Nie wrzucać Mendla 9:3:3:1 do kohorty B."],
            ["bivar", "r → y=ax+b → estimate + reliability  [2+2+2]",
             "Okładki już w kodzie: temperatura–gaz / godziny–wynik / nawóz–plon (_story 142–160). Trzeba je pinować per kohorta, nie losować."],
            ["ext_gdc_stat", "normalCdf → invNorm k → układ μ,σ → B(n,p) ogon → E(zysk)  [3+4+4+4+4=19]",
             "Archetypy już w _contexts(): jabłka / żywotność / pręty. Identity key ich nie widzi."],
            ["gdc_trig", "ostre → π−x → x+2π  [2+2+2]",
             "(i) sin x = k; (ii) cos x = k z trzema analogicznymi pierwiastkami; (iii) sin(x−α)=k przy danym α. Nie dodawać 4. pierwiastka ani tan."],
            ["gdc_intersect", "równanie → 2 pierwiastki GDC → y  [1+3+2]",
             "(i) ln x = mx−c (obecny); (ii) e^{−x}=mx−c z dokładnie dwoma dodatnimi przecięciami; (iii) ln(x+1)=m(x)−c. Warunek: zawsze dwa pierwiastki."],
            ["gdc_area", "∫ GDC → t : połowa pola  [3+3]",
             "(i) √(x³+c) (obecny); (ii) √(x⁴+c); (iii) e^{−x²}+c. Wszystkie bez elementarnej całki, te same dwa naciśnięcia GDC, granice tej samej długości."],
            ["stat_normal", "cdf tablicowy, ten sam z",
             "wzrost / masa opakowania / czas dojazdu — te same ogony."],
            ["prob_cond / prob_bayes", "drzewo dwugałęziowe",
             "Bayes: (i) dwie maszyny (obecny); (ii) dwa testery medyczne; (iii) dwa filtry spamu. Trzymać P(A|D) we wszystkich kohortach."],
            ["alg_quad, log_eq, seq_*, trig_eq, trig_triangle, geom_sector", "klasyczne Section A, jedna metoda",
             "Inne liczby / inna historia słowna. Nie zamieniać cosine rule na ambiguous case."],
            ["calc_tangent / parts×1 / sub / euler×2 / implicit / l'Hôpital×1", "ten sam wektor M/A",
             "Zmiana wzoru z tej samej rodziny, nie zmiana metody."],
            ["induction", "baza, założenie, krok",
             "Inny wzór sumy/podzielności; nie inny typ indukcji (nierówność vs podzielność to już granica)."],
        ],
        [usable * 0.24, usable * 0.32, usable * 0.44],
        st,
    ))

    story.append(P("2.2 Grupa (b) — tematy chronione (strict isomorphic)", st["h3"]))
    story.append(P(
        "Zmiana struktury pytania rozjeżdża czas przy tej samej liczbie punktów. "
        "Kohorty mogą różnić się tylko liczbami wewnątrz tego samego part_graph_id. "
        "Task.__post_init__ wymusza litery a.. bez luk (task_contract.py:80–85) — nie dokładać „ciekawszego” (f) w kohorcie C.",
        st["body"],
    ))
    story.append(grid(
        ["Temat", "Dlaczego chroniony", "Dozwolona zmiana A/B/C"],
        [
            ["gdc_system", "unique point vs k/det=0 to inny egzamin", "inne 3×3 z puli _UNIQUE (24)"],
            ["kin_gdc", "1 vs 2 zera v(t)", "inny c i T przy 1 zmianie kierunku"],
            ["gdc_curve, ext_gdc_model", "łańcuch stacjonarny → y → pole → (średnia, połowa y)", "retuning a,T po powiększeniu banku do ≥8; nie zmieniać rodziny e^{−ax}ln(…)"],
            ["ext_gdc_stat (a)…(e)", "19 mk, 5 GDC-kroków, Hence-chain", "tylko cover + liczby; nie wyjmować (c) μ,σ"],
            ["ext_calculus, ext_vectors, ext_ln", "Section B 12–16 mk, zależne części", "liczby; nie zamieniać (e) area ↔ warunek y=k"],
            ["ext_model", "Newton vs clearance", "jeden model na cały mock; drugi model = osobny produkt"],
            ["paper3_geo, paper3_mac", "śledztwo 16 mk, n-zależne", "parametry w tej samej siatce n"],
            ["vol_rev / diff_eq / maclaurin", "disk vs washer; separation vs IF; różne rozwinięcia", "jedna metoda / jedna rodzina na papier"],
            ["trig_amb / alg_partial / complex_demoivre", "ostry vs rozwarty; mianownik; n=3 vs n=4", "jeden przypadek, stałe n"],
            ["fn_rational / seq_infinite / proof_*", "liczba asymptot; zbieżny vs trap; inny kształt argumentu", "stały szablon / ten sam szkielet dowodu"],
            ["calc_diff challenging", "inna rodzina funkcji + normalna", "freeze builder"],
        ],
        [usable * 0.24, usable * 0.38, usable * 0.38],
        st,
    ))

    story.append(P("3. Mark scheme względem standardu IB", st["h2"]))
    story.append(P("3.1 Kontrakt w kodzie", st["h3"]))
    story.append(P(
        "SchemeStep (core/task_contract.py:17–20) ma tylko pola <b>desc, tex, code</b>. "
        "Brak: part, ft, note (3 s.f. / alternative), accept. Fabryka step() (linia 127) też tego nie ma.",
        st["body"],
    ))
    story.append(P(
        "to_paper_dict (linie 100–109) spłaszcza schemat w poprzek części. "
        "PDF renderuje płaską listę (pdf_engine.py:811–826). "
        "Egzaminator nie widzi, że A1 w wierszu 7 należy do (c) i ma iść FT z błędnego (a). "
        "Na mark scheme wychodzi też surowy archetype (756–757) — metadana deweloperska, nie IB.",
        st["body"],
    ))

    story.append(P("3.2 Braki względem AA HL", st["h3"]))
    story.append(bullets([
        "<b>Follow-through.</b> Żaden generator nie emituje FT. Przy ext_gdc_stat (d) używa p z (a) i (e) używa E(Y) z (d) — klasyczny łańcuch FT. Dziś MS pokazuje tylko „słuszne” liczby, więc błędny (a) zeruje całą resztę w oczach niedoświadczonego nauczyciela.",
        "<b>3 significant figures.</b> core/rounding.py:three_sf zaokrągla odpowiedź drukowaną. Instrukcja dla ucznia jest w intro. Nie ma adnotacji egzaminatorskiej: award A1 for 3 s.f. only; do not award A0A1. Kody „A1 A1” w gdc_statistics.py:141 nie mówią, który A1 jest za wartość, a który za zaokrąglenie.",
        "<b>Metody alternatywne.</b> Schemat podaje jedną ścieżkę GDC. Brak OR. gdc_system dopuszcza GDC albo redukcję wierszy w jednym M1 A1 A1. χ²: uczeń może wziąć p-value z GDC — kod zawsze każe porównać ze wstawioną wartością krytyczną (gdc_chi_squared.py:196, gdc_chi_gof.py:183–185).",
        "<b>Kody nieoficjalne G2</b> w gdc_statistics.py:54 i :132 oraz statistics_bivariate.py:200, 210. IB AA używa M/A/R/N. Odczyt z GDC to zwykle A1 (lub M1+A1). R1 jest używane poprawnie (wniosek, reliability).",
        "<b>χ² (d) podaje crit.</b> Świadoma decyzja izomorficzna (ten sam czas porównywania), ale MS nie mówi „A1 za wniosek zgodny z ich statystyką (FT)”. W prawdziwym P2 często ν i crit są na uczniu.",
        "<b>Brak N (accuracy) vs A.</b> Paper 2 IB często rozdziela N1 za 3 s.f. Studio skleja wszystko w A.",
    ], st))

    story.append(P("3.3 Co jest już zgodne", st["h3"]))
    story.append(bullets([
        "Suma marek części = TASK_REGISTRY[key][\"marks\"] (call_generator).",
        "Presety sumują się do 24 / 65 / 100 (registry.py:_check_presets).",
        "Części mają litery a.. bez luk.",
        "Większość kroków to M1 A1 / M1 A1 A1 — czytelne dla nauczyciela IB, tylko niekompletne.",
    ], st))

    story.append(P("4. Rekomendacja architektury skalowania", st["h2"]))
    story.append(P("4.1 Fabryka archetypów wewnątrz generatora", st["h3"]))
    story.append(P(
        "Nie ruszać sygnatury call_generator(key, clean_integers, difficulty). "
        "Rozszerzyć zwracany Task o trzy jawne identyfikatory. Przykład w generators/gdc_chi_squared.py:",
        st["body"],
    ))
    story.append(P(
        escape("COVERS_2X2 = (Cover(\"treatment\", ...), Cover(\"language\", ...), Cover(\"shift\", ...))\n"
               "graph = \"chi2_indep_2x2_crit_given\"   # part_graph_id\n"
               "item  = choice(_NARROW)                 # numeric_id\n"
               "cover = choice(COVERS_2X2)              # cover_id\n"
               "archetype = f\"{graph}|{cover.id}|{item.fingerprint}\""),
        st["code"],
    ))
    story.append(grid(
        ["Pole", "Znaczenie", "Strict Parallel", "Cognitive Twin"],
        [
            ["part_graph_id", "wektor marek + sekwencja GDC/analityczna", "identyczny A/B/C", "identyczny A/B/C"],
            ["cover_id", "historia / etykiety / fenomen", "identyczny (jak dwie sesje IB) albo pinowany zestaw trzech okładek o tym samym koszcie", "różny obowiązkowo"],
            ["numeric_id", "konkretna tabela / parametry", "różny obowiązkowo; jeśli bank < kohort → fail", "może się powtórzyć, jeśli bank < 3"],
        ],
        [usable * 0.18, usable * 0.28, usable * 0.27, usable * 0.27],
        st,
    ))
    story.append(Spacer(1, 6))
    story.append(P(
        "Identity produkcyjna: Strict = (part_graph_id, cover_id, numeric_id) z unikalnym numeric_id; "
        "Twin = (part_graph_id, cover_id) z unikalnym cover_id. "
        "Nigdy więcej latex_main|archetype. Nigdy attempt == 11 jako cicha zgoda. "
        "Po wyczerpaniu puli: fail głośny albo automatyczny fallback do Twin z logiem.",
        st["body"],
    ))

    story.append(P("4.2 Dwa tryby w app.py", st["h3"]))
    story.append(P(
        "Dodać argument cohort_mode: \"strict_parallel\" | \"cognitive_twin\" do generate_all_papers / _compose_papers "
        "(sygnatura dziś: app.py:57, 64). UI: radio przy presetach mock.",
        st["body"],
    ))
    story.append(P(
        "<b>Strict Parallel</b> (oficjalny mock, sprzedaż „jak IB”): freeze difficulty; pin part_graph_id i cover_id z kohorty A; "
        "wymagaj różnego numeric_id; jeśli bank za płytki — nie generuj, pokaż komunikat; "
        "odrzuć item, którego filtr difficulty zmieniłby graf (invNorm, parametr k, 2 zera kinematyki).",
        st["body"],
    ))
    story.append(P(
        "<b>Cognitive Twin</b> (sprawdzian klasowy): ten sam part_graph_id; różny cover_id obowiązkowo; "
        "numeric_id może się powtórzyć — to odblokowuje banki wielkości 2 na 3 papiery, pod warunkiem że okładka jest inna "
        "i liczby nie są trywialną zamianą 2↔3 przy tym samym wykresie. "
        "Dla gdc_curve Twin nie wystarczy przy obecnym banku (ten sam punkt stacjonarny) — najpierw powiększyć pulę.",
        st["body"],
    ))
    story.append(P(
        "Walidator po złożeniu papieru (nowa funkcja w core/, wołana z _compose_papers): "
        "równe part_graph_id we wszystkich kohortach; w Strict — unikalne numeric_id i równe cover_id; "
        "w Twin — unikalne cover_id; wektory marek identyczne.",
        st["body"],
    ))

    story.append(P("4.3 Rejestr grafów, nie tylko tematów", st["h3"]))
    story.append(P(
        "W TASK_REGISTRY dodać opcjonalnie graphs (dozwolone part_graph_id) oraz cohort_variant: cover | numeric_only | protected. "
        "gdc_dist ma dziś dwa grafy w jednym kluczu — rozciąć na gdc_binom i gdc_invnorm albo pinować graph_id w presecie. "
        "Analogicznie prob_rv losuje ciągłą/dyskretną/binomial/Poisson: dla mock P1 pin family z kohorty A.",
        st["body"],
    ))

    story.append(P("4.4 Mark scheme — minimalny kontrakt v2", st["h3"]))
    story.append(P(
        escape("SchemeStep(desc, tex, code, part=\"c\", ft=False, rounding=\"A1 for 3 s.f. only; do not award A0A1\", alternative=\"OR p-value from GDC\")"),
        st["code"],
    ))
    story.append(P(
        "to_paper_dict grupuje po part. PDF: nagłówek (c) przed krokami. Zastąpić G2 → A1 (odczyt) lub M1 A1. "
        "Dodać FT na łańcuchach Section B: ext_gdc_stat (d)(e), ext_gdc_model (b)(d)(e), gdc_area (b) stąd z (a).",
        st["body"],
    ))

    story.append(P("5. Backlog (priorytet merytoryczny)", st["h2"]))
    story.append(P("P0 — bez tego nie sprzedawać 3 kohort jako równoległe egzaminy", st["h3"]))
    story.append(bullets([
        "<b>Nowy identity key</b> (part_graph_id, cover_id, numeric_id). Usunąć or attempt == 11. Przy kolizji: fail albo jawny fallback z logiem. Pliki: app.py:77–87, tests/test_pdf_layout.py:48–51, core/task_contract.py pola Task.",
        "<b>Tryby Strict Parallel / Cognitive Twin</b> w _compose_papers + radio w UI. Freeze difficulty. Walidacja wektora marek i grafu po złożeniu.",
        "<b>Rozciąć albo spiąć grafy ukryte w difficulty:</b> gdc_dist, gdc_chi, gdc_system, kin_gdc, gdc_chi_gof, ext_model, ext_calculus (e). Mock P2 w Strict Parallel używa wyłącznie gałęzi standard.",
    ], st))
    story.append(P("P1 — unikalność bez rozjechania czasu", st["h3"]))
    story.append(bullets([
        "<b>Trzy izomorficzne okładki</b> (pinowane, nie losowane) dla: gdc_dist binomial, gdc_chi 2×2, gdc_chi_gof 6-klas, bivar (okładki już są), ext_gdc_stat (okładki już są — podłączyć do identity), prob_bayes.",
        "<b>Powiększyć banki numeric do ≥8 na graf:</b> gdc_curve (dziś 2, oba a=1, challenging fallback), ext_gdc_model (2 na graf), gdc_intersect slope=1 (2), gdc_trig (3), kin_gdc singles (3). Bez tego Strict Parallel na 3 kohorty jest matematycznie niemożliwy.",
        "<b>Naprawić gdc_curve:</b> dodać pary (a,T) które przeżywają 3 s.f. dla a=2, albo nie reklamować challenging jako osobnej puli.",
    ], st))
    story.append(P("P2 — mark scheme IB", st["h3"]))
    story.append(bullets([
        "Rozszerzyć SchemeStep: part, ft, rounding, alternative. Przestać spłaszczać MS. PDF: grupowanie po części.",
        "Zastąpić G2 w gdc_statistics.py i statistics_bivariate.py. Dodać notę 3 s.f. (award A1 for 3 s.f. only). FT na łańcuchach Section B i gdc_area(b).",
        "Opcjonalny drugi graf χ²: uczeń liczy ν i crit z GDC/tabel — osobny graph_id, nie split kohort.",
    ], st))
    story.append(P("P3 — produkt egzaminacyjny", st["h3"]))
    story.append(bullets([
        "Section B: Hence po (a) bez zmiany wektora marek (ext_gdc_stat (d) już mówi „value found in part (a)” — ujednolicić język).",
        "Strona instrukcji IB (GDC required, 3 s.f., formula booklet, candidate details) — layout, nie bank.",
        "Rozciąć prob_rv i gdc_dist w rejestrze na osobne klucze, żeby preset pinował rodzinę.",
    ], st))
    story.append(P("Świadomie nie robić", st["h3"]))
    story.append(bullets([
        "Używać challenging jako kohorty B.",
        "Dokładać 2×3 χ² albo Mendla do „urozmaicenia” mocku 3-kohortowego.",
        "Akceptować duplikat na ostatniej próbie, żeby Streamlit nigdy nie padł — lepiej błąd „bank too shallow” niż fałszywy egzamin równoległy.",
    ], st))

    story.append(P("Stan na dziś względem celu edukacyjno-komercyjnego", st["h2"]))
    story.append(P(
        "Jeden wariant (kohorta A, standard) jest używalny jako mock treningowy. "
        "Trzy kohorty w obecnej pętli nie są równoważnymi egzaminami: albo są trywialnymi kopiami "
        "(ln x = x−2 vs x−3, te same etykiety χ²), albo — jeśli ktoś kiedyś podłączy difficulty do wariantu — staną się nierównymi czasowo. "
        "Najpierw identity + tryby + okładki na tematach grupy (a); banki P1 na gdc_curve / ext_gdc_model; dopiero potem MS v2.",
        st["body"],
    ))
    story.append(P(
        "Ten dokument jest wydrukiem raportu technicznego z sesji audytu. "
        "Nie zastępuje kodu źródłowego; odniesienia do plików i linii są aktualne na 11 listopada 2026.",
        st["foot"],
    ))

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Audyt generatorów IB AA HL",
        author="stem-generator audit",
        subject="Collision, cognitive load, mark scheme, architecture",
    )
    doc.build(story, canvasmaker=Numbered)
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
    print(path.stat().st_size)
