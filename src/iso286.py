"""ISO 286-1:2010 limit deviations for 1 mm < size <= 500 mm, IT5–IT11.

Standard tolerances are the tabulated values of ISO 286-1:2010 Table 1.
The raw tolerance-factor formula is not used for published cells: ISO 286-1
states that the tables prevail where rounding was adjusted.

Fundamental deviations for shafts are the tabulated values. Hole deviations
are calculated from those values with the ISO 286-1 delta rule.
"""

from __future__ import annotations

# (above, up to and including), millimetres. A size on the boundary
# belongs to the step that ends there.
RANGES: list[tuple[int, int]] = [
    (0, 3),
    (3, 6),
    (6, 10),
    (10, 14),
    (14, 18),
    (18, 24),
    (24, 30),
    (30, 40),
    (40, 50),
    (50, 65),
    (65, 80),
    (80, 100),
    (100, 120),
    (120, 140),
    (140, 160),
    (160, 180),
    (180, 200),
    (200, 225),
    (225, 250),
    (250, 280),
    (280, 315),
    (315, 355),
    (355, 400),
    (400, 450),
    (450, 500),
]

MAIN_RANGES: list[tuple[int, int]] = [
    (0, 3),
    (3, 6),
    (6, 10),
    (10, 18),
    (18, 30),
    (30, 50),
    (50, 80),
    (80, 120),
    (120, 180),
    (180, 250),
    (250, 315),
    (315, 400),
    (400, 500),
]

# IT4 is kept only to form delta = ITn - IT(n-1) for IT5. It is not a
# published workshop column. Values: ISO 286-1:2010 Table 1, confirmed by
# the Engineers Edge ISO 286-1 chart.
IT_MAIN: dict[tuple[int, int], dict[int, int]] = {
    (0, 3): {4: 3, 5: 4, 6: 6, 7: 10, 8: 14, 9: 25, 10: 40, 11: 60},
    (3, 6): {4: 4, 5: 5, 6: 8, 7: 12, 8: 18, 9: 30, 10: 48, 11: 75},
    (6, 10): {4: 4, 5: 6, 6: 9, 7: 15, 8: 22, 9: 36, 10: 58, 11: 90},
    (10, 18): {4: 5, 5: 8, 6: 11, 7: 18, 8: 27, 9: 43, 10: 70, 11: 110},
    (18, 30): {4: 6, 5: 9, 6: 13, 7: 21, 8: 33, 9: 52, 10: 84, 11: 130},
    (30, 50): {4: 7, 5: 11, 6: 16, 7: 25, 8: 39, 9: 62, 10: 100, 11: 160},
    (50, 80): {4: 8, 5: 13, 6: 19, 7: 30, 8: 46, 9: 74, 10: 120, 11: 190},
    (80, 120): {4: 10, 5: 15, 6: 22, 7: 35, 8: 54, 9: 87, 10: 140, 11: 220},
    (120, 180): {4: 12, 5: 18, 6: 25, 7: 40, 8: 63, 9: 100, 10: 160, 11: 250},
    (180, 250): {4: 14, 5: 20, 6: 29, 7: 46, 8: 72, 9: 115, 10: 185, 11: 290},
    (250, 315): {4: 16, 5: 23, 6: 32, 7: 52, 8: 81, 9: 130, 10: 210, 11: 320},
    (315, 400): {4: 18, 5: 25, 6: 36, 7: 57, 8: 89, 9: 140, 10: 230, 11: 360},
    (400, 500): {4: 20, 5: 27, 6: 40, 7: 63, 8: 97, 9: 155, 10: 250, 11: 400},
}

# Upper deviation es of shafts a–g, micrometres. h is 0.
# Source transcribed from Roy Mech ISO shaft fundamental deviations and
# checked in verify.py against the MechSheet ISO 286-1:2010 table.
SHAFT_ES: dict[str, list[int]] = {
    "a": [-270, -270, -280, -290, -290, -300, -300, -310, -320, -340, -360, -380, -410, -460, -520, -580, -660, -740, -820, -920, -1050, -1200, -1350, -1500, -1650],
    "b": [-140, -140, -150, -150, -150, -160, -160, -170, -180, -190, -200, -220, -240, -260, -280, -310, -340, -380, -420, -480, -540, -600, -680, -760, -840],
    "c": [-60, -70, -80, -95, -95, -110, -110, -120, -130, -140, -150, -170, -180, -200, -210, -230, -240, -260, -280, -300, -330, -360, -400, -440, -480],
    "d": [-20, -30, -40, -50, -50, -65, -65, -80, -80, -100, -100, -120, -120, -145, -145, -145, -170, -170, -170, -190, -190, -210, -210, -230, -230],
    "e": [-14, -20, -25, -32, -32, -40, -40, -50, -50, -60, -60, -72, -72, -85, -85, -85, -100, -100, -100, -110, -110, -125, -125, -135, -135],
    "f": [-6, -10, -13, -16, -16, -20, -20, -25, -25, -30, -30, -36, -36, -43, -43, -43, -50, -50, -50, -56, -56, -62, -62, -68, -68],
    "g": [-2, -4, -5, -6, -6, -7, -7, -9, -9, -10, -10, -12, -12, -14, -14, -14, -15, -15, -15, -17, -17, -18, -18, -20, -20],
}

# Lower deviation ei. k47 applies to IT4–IT7. From IT8 upward, shaft k has ei = 0.
# None means the letter is not defined for that step (t below 24 mm).
SHAFT_EI: dict[str, list[int | None]] = {
    "k47": [0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 5, 5],
    "m": [2, 4, 6, 7, 7, 8, 8, 9, 9, 11, 11, 13, 13, 15, 15, 15, 17, 17, 17, 20, 20, 21, 21, 23, 23],
    "n": [4, 8, 10, 12, 12, 15, 15, 17, 17, 20, 20, 23, 23, 27, 27, 27, 31, 31, 31, 34, 34, 37, 37, 40, 40],
    "p": [6, 12, 15, 18, 18, 22, 22, 26, 26, 32, 32, 37, 37, 43, 43, 43, 50, 50, 50, 56, 56, 62, 62, 68, 68],
    "r": [10, 15, 19, 23, 23, 28, 28, 34, 34, 41, 43, 51, 54, 63, 65, 68, 77, 80, 84, 94, 98, 108, 114, 126, 132],
    "s": [14, 19, 23, 28, 28, 35, 35, 43, 43, 53, 59, 71, 79, 92, 100, 108, 122, 130, 140, 158, 170, 190, 208, 232, 252],
    "t": [None, None, None, None, None, None, 41, 48, 54, 66, 75, 91, 104, 122, 134, 146, 166, 180, 196, 218, 240, 268, 294, 330, 360],
    "u": [18, 23, 28, 33, 33, 41, 48, 60, 70, 87, 102, 124, 144, 170, 190, 210, 236, 258, 284, 315, 350, 390, 435, 490, 540],
}

SHAFT_LETTERS = list("abcdefgh") + ["js", "k", "m", "n", "p", "r", "s", "t", "u"]
HOLE_LETTERS = [letter.upper() if letter != "js" else "JS" for letter in SHAFT_LETTERS]
GRADES = (5, 6, 7, 8, 9, 10, 11)
CLEARANCE_SHAFTS = set("abcdefgh")
INTERFERENCE_SHAFTS = set("kmnprstu")


def main_of(index: int) -> tuple[int, int]:
    low, high = RANGES[index]
    for start, end in MAIN_RANGES:
        if low >= start and high <= end:
            return start, end
    raise ValueError(f"no main step for {RANGES[index]}")


def standard_tolerance(index: int, grade: int) -> int:
    if grade not in GRADES and grade != 4:
        raise ValueError(grade)
    return IT_MAIN[main_of(index)][grade]


def delta(index: int, grade: int) -> int:
    """ITn - IT(n-1). Zero at or below 3 mm: the delta rule is not applied there."""
    low, _high = RANGES[index]
    if low < 3:
        return 0
    if grade < 5 or grade > 8:
        raise ValueError(grade)
    main = main_of(index)
    return IT_MAIN[main][grade] - IT_MAIN[main][grade - 1]


def _shaft_fundamental_ei(letter: str, index: int, grade: int) -> int | None:
    if letter == "k":
        key = "k47" if grade <= 7 else None
        if key is None:
            return 0
        value = SHAFT_EI["k47"][index]
        return value
    value = SHAFT_EI[letter][index]
    return value


def shaft_limits(letter: str, grade: int, index: int) -> tuple[float, float] | None:
    """Return (es, ei) in micrometres, or None if the class is not defined."""
    letter = letter.lower()
    if grade not in GRADES:
        raise ValueError(grade)
    it = standard_tolerance(index, grade)
    if letter in CLEARANCE_SHAFTS:
        es = 0 if letter == "h" else SHAFT_ES[letter][index]
        return float(es), float(es - it)
    if letter == "js":
        half = it / 2.0
        return half, -half
    if letter in INTERFERENCE_SHAFTS:
        ei = _shaft_fundamental_ei(letter, index, grade)
        if ei is None:
            return None
        return float(ei + it), float(ei)
    raise ValueError(letter)


def hole_limits(letter: str, grade: int, index: int) -> tuple[float, float] | None:
    """Return (ES, EI) in micrometres, or None if the class is not defined."""
    letter = letter.upper()
    if grade not in GRADES:
        raise ValueError(grade)
    it = standard_tolerance(index, grade)
    low, high = RANGES[index]
    if letter in "ABCDEFGH":
        shaft = shaft_limits(letter.lower(), grade, index)
        if shaft is None:
            return None
        es, _ei = shaft
        ei_hole = -es
        return float(ei_hole + it), float(ei_hole)
    if letter == "JS":
        half = it / 2.0
        return half, -half
    if letter not in "KMNPRSTU":
        raise ValueError(letter)

    if letter == "K" and grade > 8 and low >= 3:
        return None

    if letter == "K":
        ei = SHAFT_EI["k47"][index]
    else:
        ei = SHAFT_EI[letter.lower()][index]
    if ei is None:
        return None

    if letter == "N" and grade > 8 and low >= 3:
        es_hole = 0
    elif letter == "M" and grade == 6 and low >= 250 and high <= 315:
        # ISO 286-1:2010 Table 2, note b. Calculated value would be -11 µm.
        es_hole = -9
    else:
        es_hole = -ei
        above_3 = low >= 3
        if above_3 and letter in "KMN" and grade <= 8:
            es_hole += delta(index, grade)
        elif above_3 and letter in "PRSTU" and grade <= 7:
            es_hole += delta(index, grade)
    return float(es_hole), float(es_hole - it)


def fit_clearances(
    hole: str, shaft: str, grade_hole: int, grade_shaft: int, index: int
) -> tuple[float, float, str] | None:
    """Return (minimum clearance, maximum clearance, kind) in micrometres.

    Positive is clearance, negative is interference.
    minimum = lower hole limit deviation - upper shaft limit deviation.
    """
    hole_lim = hole_limits(hole, grade_hole, index)
    shaft_lim = shaft_limits(shaft, grade_shaft, index)
    if hole_lim is None or shaft_lim is None:
        return None
    es_h, ei_h = hole_lim
    es_s, ei_s = shaft_lim
    minimum = ei_h - es_s
    maximum = es_h - ei_s
    if minimum >= 0:
        kind = "bosluklu"
    elif maximum <= 0:
        kind = "siki"
    else:
        kind = "gecisli"
    return minimum, maximum, kind


def range_label(index: int) -> str:
    low, high = RANGES[index]
    if low == 0:
        return "3'e kadar"
    return f"{low} üzeri – {high} dahil"


def main_label(start: int, end: int) -> str:
    if start == 0:
        return "3'e kadar"
    return f"{start} üzeri – {end} dahil"
