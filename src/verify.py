"""Cross-check ISO 286 and ISO 2768 values before any PDF is built.

A single micrometre of disagreement aborts the build. Nothing is published
from a cell the two sources do not share.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import iso286 as iso

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# MechSheet ISO 286-1:2010 fundamental deviations, micrometres.
# Independent of the Roy Mech transcription in iso286.py.
# k is the IT4–IT7 value. t is None where MechSheet shows an em dash.
MECHSHEET_ES = {
    "a": [-270, -270, -280, -290, -290, -300, -300, -310, -320, -340, -360, -380, -410, -460, -520, -580, -660, -740, -820, -920, -1050, -1200, -1350, -1500, -1650],
    "b": [-140, -140, -150, -150, -150, -160, -160, -170, -180, -190, -200, -220, -240, -260, -280, -310, -340, -380, -420, -480, -540, -600, -680, -760, -840],
    "c": [-60, -70, -80, -95, -95, -110, -110, -120, -130, -140, -150, -170, -180, -200, -210, -230, -240, -260, -280, -300, -330, -360, -400, -440, -480],
    "d": [-20, -30, -40, -50, -50, -65, -65, -80, -80, -100, -100, -120, -120, -145, -145, -145, -170, -170, -170, -190, -190, -210, -210, -230, -230],
    "e": [-14, -20, -25, -32, -32, -40, -40, -50, -50, -60, -60, -72, -72, -85, -85, -85, -100, -100, -100, -110, -110, -125, -125, -135, -135],
    "f": [-6, -10, -13, -16, -16, -20, -20, -25, -25, -30, -30, -36, -36, -43, -43, -43, -50, -50, -50, -56, -56, -62, -62, -68, -68],
    "g": [-2, -4, -5, -6, -6, -7, -7, -9, -9, -10, -10, -12, -12, -14, -14, -14, -15, -15, -15, -17, -17, -18, -18, -20, -20],
}
MECHSHEET_EI = {
    "k47": [0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 5, 5],
    "m": [2, 4, 6, 7, 7, 8, 8, 9, 9, 11, 11, 13, 13, 15, 15, 15, 17, 17, 17, 20, 20, 21, 21, 23, 23],
    "n": [4, 8, 10, 12, 12, 15, 15, 17, 17, 20, 20, 23, 23, 27, 27, 27, 31, 31, 31, 34, 34, 37, 37, 40, 40],
    "p": [6, 12, 15, 18, 18, 22, 22, 26, 26, 32, 32, 37, 37, 43, 43, 43, 50, 50, 50, 56, 56, 62, 62, 68, 68],
    "r": [10, 15, 19, 23, 23, 28, 28, 34, 34, 41, 43, 51, 54, 63, 65, 68, 77, 80, 84, 94, 98, 108, 114, 126, 132],
    "s": [14, 19, 23, 28, 28, 35, 35, 43, 43, 53, 59, 71, 79, 92, 100, 108, 122, 130, 140, 158, 170, 190, 208, 232, 252],
    "t": [None, None, None, None, None, None, 41, 48, 54, 66, 75, 91, 104, 122, 134, 146, 166, 180, 196, 218, 240, 268, 294, 330, 360],
    "u": [18, 23, 28, 33, 33, 41, 48, 60, 70, 87, 102, 124, 144, 170, 190, 210, 236, 258, 284, 315, 350, 390, 435, 490, 540],
}

# IT5–IT11 by main step. Second publication: Engineers Edge chart titled
# ISO 286-1:2010, confirmed on the overlapping columns by the PREMSA chart.
ENGINEERS_EDGE_IT = {
    (0, 3): (4, 6, 10, 14, 25, 40, 60),
    (3, 6): (5, 8, 12, 18, 30, 48, 75),
    (6, 10): (6, 9, 15, 22, 36, 58, 90),
    (10, 18): (8, 11, 18, 27, 43, 70, 110),
    (18, 30): (9, 13, 21, 33, 52, 84, 130),
    (30, 50): (11, 16, 25, 39, 62, 100, 160),
    (50, 80): (13, 19, 30, 46, 74, 120, 190),
    (80, 120): (15, 22, 35, 54, 87, 140, 220),
    (120, 180): (18, 25, 40, 63, 100, 160, 250),
    (180, 250): (20, 29, 46, 72, 115, 185, 290),
    (250, 315): (23, 32, 52, 81, 130, 210, 320),
    (315, 400): (25, 36, 57, 89, 140, 230, 360),
    (400, 500): (27, 40, 63, 97, 155, 250, 400),
}

# MechSheet published delta table, IT5–IT8, for main steps above 3 mm.
MECHSHEET_DELTA = {
    (3, 6): {5: 1, 6: 3, 7: 4, 8: 6},
    (6, 10): {5: 2, 6: 3, 7: 6, 8: 7},
    (10, 18): {5: 3, 6: 3, 7: 7, 8: 9},
    (18, 30): {5: 3, 6: 4, 7: 8, 8: 12},
    (30, 50): {5: 4, 6: 5, 7: 9, 8: 14},
    (50, 80): {5: 5, 6: 6, 7: 11, 8: 16},
    (80, 120): {5: 5, 6: 7, 7: 13, 8: 19},
    (120, 180): {5: 6, 6: 7, 7: 15, 8: 23},
    (180, 250): {5: 6, 6: 9, 7: 17, 8: 26},
    (250, 315): {5: 7, 6: 9, 7: 20, 8: 29},
    (315, 400): {5: 7, 6: 11, 7: 21, 8: 32},
    (400, 500): {5: 7, 6: 13, 7: 23, 8: 34},
}

# MechSheet P7 (ES, EI), every substep. Delta is included in these limits.
MECHSHEET_P7 = [
    (-6, -16), (-8, -20), (-9, -24), (-11, -29), (-11, -29),
    (-14, -35), (-14, -35), (-17, -42), (-17, -42), (-21, -51),
    (-21, -51), (-24, -59), (-24, -59), (-28, -68), (-28, -68),
    (-28, -68), (-33, -79), (-33, -79), (-33, -79), (-36, -88),
    (-36, -88), (-41, -98), (-41, -98), (-45, -108), (-45, -108),
]

# ISO 2768-1:1989 linear deviations, millimetres, as ± values.
# Source A: UNI EN 22768-1, the European adoption of ISO 2768-1.
# Source B: the same figures in the SogaWorks and HLH reproductions of Table 1.
# Rows: (low exclusive or 0, high inclusive, f, m, c, v or None).
ISO2768_LINEAR = [
    (0.5, 3, 0.05, 0.1, 0.2, None),
    (3, 6, 0.05, 0.1, 0.3, 0.5),
    (6, 30, 0.1, 0.2, 0.5, 1.0),
    (30, 120, 0.15, 0.3, 0.8, 1.5),
    (120, 400, 0.2, 0.5, 1.2, 2.5),
    (400, 1000, 0.3, 0.8, 2.0, 4.0),
    (1000, 2000, 0.5, 1.2, 3.0, 6.0),
    (2000, 4000, None, 2.0, 4.0, 8.0),
]
# Second copy, typed from the SogaWorks table, must match exactly.
ISO2768_LINEAR_SOGA = [
    (0.5, 3, 0.05, 0.1, 0.2, None),
    (3, 6, 0.05, 0.1, 0.3, 0.5),
    (6, 30, 0.1, 0.2, 0.5, 1.0),
    (30, 120, 0.15, 0.3, 0.8, 1.5),
    (120, 400, 0.2, 0.5, 1.2, 2.5),
    (400, 1000, 0.3, 0.8, 2.0, 4.0),
    (1000, 2000, 0.5, 1.2, 3.0, 6.0),
    (2000, 4000, None, 2.0, 4.0, 8.0),
]

# Chamfer / external radius. f and m share a column; c and v share a column.
# "over 6" has no upper bound in ISO 2768-1 Table 2. A shop chart that stops
# the row at 30 mm was not followed.
ISO2768_CHAMFER = [
    (0.5, 3, 0.2, 0.4),
    (3, 6, 0.5, 1.0),
    (6, None, 1.0, 2.0),
]
ISO2768_CHAMFER_UNI = [
    (0.5, 3, 0.2, 0.4),
    (3, 6, 0.5, 1.0),
    (6, None, 1.0, 2.0),
]

# Angular, shorter side of the angle, millimetres.
# Values are (degrees, minutes) for (f and m), c, v.
# The coarse value over 120 up to 400 is 0°15'. A commercial chart printing
# 0°20' there was rejected; UNI EN 22768-1 and ISO 2768-1 Table 3 give 0°15'.
ISO2768_ANGULAR = [
    (0, 10, (1, 0), (1, 30), (3, 0)),
    (10, 50, (0, 30), (1, 0), (2, 0)),
    (50, 120, (0, 20), (0, 30), (1, 0)),
    (120, 400, (0, 10), (0, 15), (0, 30)),
    (400, None, (0, 5), (0, 10), (0, 20)),
]
ISO2768_ANGULAR_UNI = [
    (0, 10, (1, 0), (1, 30), (3, 0)),
    (10, 50, (0, 30), (1, 0), (2, 0)),
    (50, 120, (0, 20), (0, 30), (1, 0)),
    (120, 400, (0, 10), (0, 15), (0, 30)),
    (400, None, (0, 5), (0, 10), (0, 20)),
]


class VerificationError(RuntimeError):
    pass


def _fail(message: str) -> None:
    raise VerificationError(message)


def _eq(got, expected, where: str) -> None:
    if got != expected:
        _fail(f"{where}: got {got}, expected {expected}")


def check_fundamental_deviations() -> int:
    count = 0
    for letter, values in MECHSHEET_ES.items():
        _eq(len(values), 25, f"mechsheet {letter} length")
        _eq(iso.SHAFT_ES[letter], values, f"shaft es {letter}")
        count += len(values)
    for letter, values in MECHSHEET_EI.items():
        _eq(len(values), 25, f"mechsheet ei {letter} length")
        _eq(iso.SHAFT_EI[letter], values, f"shaft ei {letter}")
        count += len(values)
    for letter, values in iso.SHAFT_ES.items():
        _eq(len(values), 25, f"length {letter}")
    return count


def check_it_table() -> int:
    count = 0
    for step, values in ENGINEERS_EDGE_IT.items():
        got = tuple(iso.IT_MAIN[step][grade] for grade in iso.GRADES)
        _eq(got, values, f"IT {step}")
        count += len(values)
    return count


def check_delta() -> int:
    count = 0
    for step, grades in MECHSHEET_DELTA.items():
        index = iso.RANGES.index(step) if step in iso.RANGES else next(
            i for i, (low, high) in enumerate(iso.RANGES) if low == step[0]
        )
        # Delta is constant across substeps of a main step. Use the first substep.
        for grade, expected in grades.items():
            _eq(iso.delta(index, grade), expected, f"delta {step} IT{grade}")
            count += 1
    _eq(iso.delta(0, 7), 0, "delta at or below 3 mm")
    return count


def check_published_limits() -> list[dict]:
    """Third-source limit checks. Each item is an anchor stored in the report."""
    anchors = []

    def expect(kind, letter, grade, index, upper, lower, source):
        if kind == "shaft":
            got = iso.shaft_limits(letter, grade, index)
        else:
            got = iso.hole_limits(letter, grade, index)
        _eq(got, (float(upper), float(lower)), f"{source} {letter}{grade} {iso.RANGES[index]}")
        anchors.append(
            {
                "source": source,
                "feature": kind,
                "class": f"{letter}{grade}",
                "range": list(iso.RANGES[index]),
                "upper": upper,
                "lower": lower,
            }
        )

    # ISO 286-1:2010 Annex B worked examples. 36 mm is in 30–40, IT from 30–50.
    i36 = iso.RANGES.index((30, 40))
    expect("hole", "H", 8, i36, 39, 0, "ISO 286-1 Ek B, Ø36 H8")
    expect("shaft", "f", 7, i36, -25, -50, "ISO 286-1 Ek B, Ø36 f7")
    expect("hole", "H", 7, i36, 25, 0, "ISO 286-1 Ek B, Ø36 H7")
    expect("shaft", "n", 6, i36, 33, 17, "ISO 286-1 Ek B, Ø36 n6")
    expect("shaft", "s", 6, i36, 59, 43, "ISO 286-1 Ek B, Ø36 s6")

    # 40 mm is in 40–50. Annex B selects f7 as es = -25.
    i40 = iso.RANGES.index((40, 50))
    expect("shaft", "f", 7, i40, -25, -50, "ISO 286-1 Ek B, Ø40 f7")

    # Mechify hole chart, main steps that do not split the letter.
    # K7 / N7 / F8 / G7 / JS7.
    i18 = iso.RANGES.index((18, 24))
    expect("hole", "K", 7, i18, 6, -15, "Mechify K7, 18–30")
    expect("hole", "N", 7, i18, -7, -28, "Mechify N7, 18–30")
    expect("hole", "F", 8, i18, 53, 20, "Mechify F8, 18–30")
    expect("hole", "G", 7, i18, 28, 7, "Mechify G7, 18–30")
    expect("hole", "JS", 7, i18, 10.5, -10.5, "Mechify JS7, 18–30")
    expect("hole", "K", 7, i40, 7, -18, "Mechify K7, 30–50")
    expect("hole", "N", 7, i40, -8, -33, "Mechify N7, 30–50")

    i6 = iso.RANGES.index((6, 10))
    expect("hole", "K", 7, i6, 5, -10, "Mechify K7, 6–10")
    expect("hole", "N", 7, i6, -4, -19, "Mechify N7, 6–10")

    # Metronq common shaft classes, 30–50 main step (both substeps agree).
    for index in (iso.RANGES.index((30, 40)), iso.RANGES.index((40, 50))):
        expect("shaft", "g", 6, index, -9, -25, "Metronq g6, 30–50")
        expect("shaft", "k", 6, index, 18, 2, "Metronq k6, 30–50")
        expect("shaft", "p", 6, index, 42, 26, "Metronq p6, 30–50")
        expect("shaft", "h", 6, index, 0, -16, "Metronq h6, 30–50")
        expect("shaft", "f", 7, index, -25, -50, "Metronq f7, 30–50")
        expect("hole", "H", 7, index, 25, 0, "Metronq H7, 30–50")
        expect("hole", "H", 8, index, 39, 0, "Metronq H8, 30–50")

    # Teravin reading example: Ø25 is in 24–30.
    i25 = iso.RANGES.index((24, 30))
    expect("hole", "H", 7, i25, 21, 0, "Teravin Ø25 H7")
    expect("shaft", "g", 6, i25, -7, -20, "Teravin Ø25 g6")

    # Boundary: 30 mm stays in 24–30, 50 mm stays in 40–50.
    expect("shaft", "g", 6, i25, -7, -20, "sınır 30 mm g6")
    expect("shaft", "g", 6, i40, -9, -25, "sınır 50 mm g6")

    for index, (upper, lower) in enumerate(MECHSHEET_P7):
        expect("hole", "P", 7, index, upper, lower, "MechSheet P7")

    # js is exactly ±IT/2, including half micrometres. IT7 at 6–10 is 15.
    expect("shaft", "js", 7, i6, 7.5, -7.5, "MechSheet JS7 kuralı, 6–10")

    # Shaft k8 sits on zero; hole K8 still uses the IT4–IT7 deviation plus delta.
    expect("shaft", "k", 8, i18, 33, 0, "mil k8, 18–30")
    expect("hole", "K", 8, i18, 10, -23, "delik K8, 18–30")

    # K9 is not provided above 3 mm. N9 above 3 mm has ES = 0.
    if iso.hole_limits("K", 9, i18) is not None:
        _fail("K9 above 3 mm must be undefined")
    expect("hole", "N", 9, i18, 0, -52, "delik N9, 18–30, ES = 0")

    # M6 special case, 250–315 mm.
    i280 = iso.RANGES.index((280, 315))
    expect("hole", "M", 6, i280, -9, -41, "ISO 286-1 Tablo 2 not b, M6 250–315")
    # The neighbouring step is not the special case: 225–250, m ei = 17,
    # IT6 = 29, delta IT6 = 9, ES = -17 + 9 = -8.
    i225 = iso.RANGES.index((225, 250))
    expect("hole", "M", 6, i225, -8, -37, "M6 225–250, özel not uygulanmaz")

    # t is undefined through 18–24 and defined from 24–30.
    if iso.shaft_limits("t", 6, iso.RANGES.index((18, 24))) is not None:
        _fail("t6 must be undefined up to 24 mm")
    expect("shaft", "t", 6, i25, 54, 41, "mil t6, 24–30")

    # H7/p6 at <= 3 mm is a transition fit; at 30–50 mm it is interference.
    small = iso.fit_clearances("H", "p", 7, 6, 0)
    mid = iso.fit_clearances("H", "p", 7, 6, i40)
    _eq(small[2], "gecisli", "H7/p6 up to 3 mm")
    _eq(mid[2], "siki", "H7/p6 40–50 mm")
    _eq(mid[0], -42.0, "H7/p6 40–50 minimum clearance")
    _eq(mid[1], -1.0, "H7/p6 40–50 maximum clearance")

    # Annex B clearance numbers for Ø36 H8/f7: min 0.025 mm, max 0.089 mm.
    fit = iso.fit_clearances("H", "f", 8, 7, i36)
    _eq((fit[0], fit[1], fit[2]), (25.0, 89.0, "bosluklu"), "Ø36 H8/f7")
    fit_n = iso.fit_clearances("H", "n", 7, 6, i36)
    _eq((fit_n[0], fit_n[1], fit_n[2]), (-33.0, 8.0, "gecisli"), "Ø36 H7/n6")
    fit_s = iso.fit_clearances("H", "s", 7, 6, i36)
    _eq((fit_s[0], fit_s[1], fit_s[2]), (-59.0, -18.0, "siki"), "Ø36 H7/s6")
    return anchors


def check_iso2768() -> None:
    _eq(ISO2768_LINEAR, ISO2768_LINEAR_SOGA, "ISO 2768-1 doğrusal")
    _eq(ISO2768_CHAMFER, ISO2768_CHAMFER_UNI, "ISO 2768-1 pah")
    _eq(ISO2768_ANGULAR, ISO2768_ANGULAR_UNI, "ISO 2768-1 açı")
    # The disputed commercial cell must not be the value we publish.
    coarse_120 = ISO2768_ANGULAR[3][3]
    _eq(coarse_120, (0, 15), "120–400 mm kaba açı")


def _limits_block(kind: str) -> dict:
    letters = iso.SHAFT_LETTERS if kind == "shaft" else iso.HOLE_LETTERS
    function = iso.shaft_limits if kind == "shaft" else iso.hole_limits
    block = {}
    for letter in letters:
        rows = []
        for index, (low, high) in enumerate(iso.RANGES):
            grades = {}
            for grade in iso.GRADES:
                limits = function(letter, grade, index)
                if limits is None:
                    grades[str(grade)] = None
                else:
                    upper, lower = limits
                    grades[str(grade)] = {"upper": upper, "lower": lower}
            rows.append({"low": low, "high": high, "label": iso.range_label(index), "grades": grades})
        block[letter] = rows
    return block


def _fit_block(hole: str, hole_grade: int, shaft: str, shaft_grade: int) -> dict:
    rows = []
    for index, (low, high) in enumerate(iso.RANGES):
        result = iso.fit_clearances(hole, shaft, hole_grade, shaft_grade, index)
        if result is None:
            rows.append({"low": low, "high": high, "label": iso.range_label(index), "defined": False})
        else:
            minimum, maximum, kind = result
            rows.append(
                {
                    "low": low,
                    "high": high,
                    "label": iso.range_label(index),
                    "defined": True,
                    "minimum": minimum,
                    "maximum": maximum,
                    "kind": kind,
                    "hole": iso.hole_limits(hole, hole_grade, index),
                    "shaft": iso.shaft_limits(shaft, shaft_grade, index),
                }
            )
    return {
        "hole": hole,
        "hole_grade": hole_grade,
        "shaft": shaft,
        "shaft_grade": shaft_grade,
        "designation": f"{hole}{hole_grade}/{shaft}{shaft_grade}",
        "rows": rows,
    }


def build_tables(anchors: list[dict]) -> dict:
    it_rows = []
    for start, end in iso.MAIN_RANGES:
        it_rows.append(
            {
                "low": start,
                "high": end,
                "label": iso.main_label(start, end),
                "grades": {str(grade): iso.IT_MAIN[(start, end)][grade] for grade in iso.GRADES},
            }
        )
    fits = [
        _fit_block("H", 11, "c", 11),
        _fit_block("H", 9, "d", 9),
        _fit_block("H", 8, "f", 7),
        _fit_block("H", 7, "g", 6),
        _fit_block("H", 7, "h", 6),
        _fit_block("H", 7, "k", 6),
        _fit_block("H", 7, "n", 6),
        _fit_block("H", 7, "p", 6),
        _fit_block("H", 7, "s", 6),
        _fit_block("H", 7, "u", 6),
        _fit_block("F", 8, "h", 7),
        _fit_block("G", 7, "h", 6),
        _fit_block("K", 7, "h", 6),
        _fit_block("P", 7, "h", 6),
        _fit_block("S", 7, "h", 6),
    ]
    i30 = iso.RANGES.index((24, 30))
    i50 = iso.RANGES.index((40, 50))
    examples = {
        "30_H7g6": {
            "nominal": 30,
            "hole": iso.hole_limits("H", 7, i30),
            "shaft": iso.shaft_limits("g", 6, i30),
            "fit": iso.fit_clearances("H", "g", 7, 6, i30),
        },
        "50_H7g6": {
            "nominal": 50,
            "hole": iso.hole_limits("H", 7, i50),
            "shaft": iso.shaft_limits("g", 6, i50),
            "fit": iso.fit_clearances("H", "g", 7, 6, i50),
        },
    }
    return {
        "scope": {
            "standard": "ISO 286-1:2010",
            "size": "0 mm üzeri, 500 mm dahil",
            "grades": list(iso.GRADES),
            "unit": "µm",
        },
        "it": it_rows,
        "shafts": _limits_block("shaft"),
        "holes": _limits_block("hole"),
        "fits": fits,
        "examples": examples,
        "iso2768": {
            "standard": "ISO 2768-1:1989",
            "linear": [
                {"low": row[0], "high": row[1], "f": row[2], "m": row[3], "c": row[4], "v": row[5]}
                for row in ISO2768_LINEAR
            ],
            "chamfer": [
                {"low": row[0], "high": row[1], "fm": row[2], "cv": row[3]} for row in ISO2768_CHAMFER
            ],
            "angular": [
                {
                    "low": row[0],
                    "high": row[1],
                    "fm": list(row[2]),
                    "c": list(row[3]),
                    "v": list(row[4]),
                }
                for row in ISO2768_ANGULAR
            ],
        },
        "verification": {
            "anchor_count": len(anchors),
            "anchors": anchors,
            "omitted": [
                "j sayısal tablosu yok: açık yayımlanmış j5/j6 değerleri 18–30 mm bandında 1 µm ayrışıyor.",
                "cd, ef, fg ve v, x, y, z, za, zb, zc için limit tablosu yok; yalnız konumları anlatılır.",
                "IT01–IT4 ve IT12–IT18 için limit tablosu yok.",
                "500 mm üzeri yok.",
                "ISO 2768-2 H/K/L mikrometre tablosu yok; standart 2021'de yürürlükten kalkmıştır.",
                "İşleme yöntemine bağlı Ra sayıları yok; ISO bir yöntem için Ra zorunlu tutmaz.",
                "Metrik vida çap ve adım payları yok; bunlar ISO 965-2 tablosundadır.",
                "Kama kanalı payları yok; iki bağımsız sayısal kaynak bu belgeye alınmadı.",
                "Rulman geçme tablosu yok; seçim rulman kataloğuna bırakılır.",
                "Ham IT formülü bazı hücrelerde Tablo 1'den 1 µm saptığı için yayımlanmadı. Esas alınan, standardın tablosudur.",
            ],
            "sources": [
                "ISO 286-1:2010 Tablo 1 ve Ek B sayısal örnekleri",
                "Engineers Edge, ISO 286-1:2010 IT tablosu",
                "PREMSA IT5–IT11 tablosu, IT tablosuyla aynı",
                "Roy Mech mil temel sapma tablosu",
                "MechSheet ISO 286-1:2010 temel sapma ve P7 tablosu",
                "Mechify delik limitleri: K7, N7, F8, G7, JS7",
                "Metronq H7, H8, h6, g6, f7, k6, p6",
                "Teravin Ø25 H7 ve g6 okuma örneği",
                "ISO 2768-1:1989 ve UNI EN 22768-1 doğrusal, pah ve açı tabloları",
            ],
        },
    }


def main() -> None:
    check_fundamental_deviations()
    check_it_table()
    check_delta()
    anchors = check_published_limits()
    check_iso2768()
    tables = build_tables(anchors)
    DATA.mkdir(exist_ok=True)
    path = DATA / "tables.json"
    path.write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"verification passed: {len(anchors)} anchors")
    print(f"wrote {path}")


if __name__ == "__main__":
    try:
        main()
    except VerificationError as exc:
        print(f"VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
