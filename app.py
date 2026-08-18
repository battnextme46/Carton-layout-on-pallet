
import math
from itertools import combinations

import plotly.graph_objects as go
import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================
APP_VERSION = "V0.2.1"
MODULE_NAME = "Module 02 — Carton Palletizing Optimizer"
EPS = 1e-9
MAX_EXHAUSTIVE_PARTIAL_COMBINATIONS = 50000

st.set_page_config(
    page_title=f"Carton Palletizing Optimizer {APP_VERSION}",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.55rem;
            padding-bottom: 2rem;
        }

        .chip {
            display: inline-block;
            padding: .18rem .48rem;
            margin-right: .28rem;
            margin-bottom: .25rem;
            border: 1px solid rgba(148,163,184,.45);
            border-radius: 999px;
            font-size: .76rem;
        }

        .ok-chip {
            border-color: rgba(34,197,94,.65);
        }

        .warn-chip {
            border-color: rgba(245,158,11,.65);
        }

        .locked-chip {
            border-color: rgba(239,68,68,.55);
        }

        .smart-note {
            padding: .78rem .95rem;
            border-radius: .55rem;
            border: 1px solid rgba(56,189,248,.28);
            background: rgba(14,116,144,.12);
            margin: .3rem 0 .8rem 0;
        }

        .small-note {
            font-size: .84rem;
            opacity: .80;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================
st.title("📦 Carton Palletizing Layout Optimizer")
st.caption(
    f"{APP_VERSION} • NPI Packaging Engineering Toolkit • {MODULE_NAME} "
    "— V0.2 Solver + True-scale Engineering View + Lightweight 3D + Performance Update"
)


# =========================================================
# SIDEBAR — CARTON INPUTS
# =========================================================
st.sidebar.header("1. ข้อมูลกล่องสินค้า (mm & kg)")

box_w = st.sidebar.number_input(
    "ความกว้างกล่อง (Width - W)",
    min_value=1.0,
    value=370.0,
    step=10.0,
)

box_l = st.sidebar.number_input(
    "ความยาวกล่อง (Length - L)",
    min_value=1.0,
    value=250.0,
    step=10.0,
)

box_h = st.sidebar.number_input(
    "ความสูงกล่อง (Height - H)",
    min_value=1.0,
    value=125.0,
    step=10.0,
)

box_weight = st.sidebar.number_input(
    "น้ำหนักรวมต่อกล่อง (Gross Weight / Carton) kg",
    min_value=0.01,
    value=5.0,
    step=0.5,
)

st.sidebar.caption(
    "Gross Weight / Carton ควรรวม Product + Inner Packaging + Carton แล้ว"
)


# =========================================================
# SIDEBAR — ORIENTATION PERMISSION
# =========================================================
st.sidebar.header("2. ข้อจำกัดทิศทางกล่อง")

allow_h_up = st.sidebar.checkbox(
    "H Up — การวางปกติ (Recommended Default)",
    value=True,
    help="ให้มิติ H ของกล่องเป็นแนวดิ่ง",
)

allow_l_up = st.sidebar.checkbox(
    "L Up — อนุญาตให้นอนตะแคงด้าน L",
    value=False,
    help="เปิดเฉพาะเมื่อ Product / Customer Requirement อนุญาต",
)

allow_w_up = st.sidebar.checkbox(
    "W Up — อนุญาตให้นอนตะแคงด้าน W",
    value=False,
    help="เปิดเฉพาะเมื่อ Product / Customer Requirement อนุญาต",
)

if not any([allow_h_up, allow_l_up, allow_w_up]):
    st.error("❌ กรุณาอนุญาต Orientation อย่างน้อย 1 แบบ")
    st.stop()

if allow_l_up or allow_w_up:
    st.sidebar.warning(
        "⚠️ Non-normal orientation ถูกเปิดใช้งาน กรุณายืนยันว่า Product / "
        "Customer / Label orientation อนุญาตจริง"
    )


# =========================================================
# SIDEBAR — PALLET INPUTS
# =========================================================
st.sidebar.header("3. ข้อมูลพาเลทและข้อจำกัด (mm & kg)")

pallet_w = st.sidebar.number_input(
    "ความกว้างพาเลท (Pallet W)",
    min_value=1.0,
    value=1200.0,
    step=50.0,
)

pallet_l = st.sidebar.number_input(
    "ความยาวพาเลท (Pallet L)",
    min_value=1.0,
    value=800.0,
    step=50.0,
)

pallet_h = st.sidebar.number_input(
    "ความหนาพาเลท (Pallet H)",
    min_value=0.0,
    value=150.0,
    step=10.0,
)

max_total_height = st.sidebar.number_input(
    "จำกัดความสูงรวม Pallet + Product",
    min_value=1.0,
    value=1500.0,
    step=50.0,
)

pallet_tare_weight = st.sidebar.number_input(
    "น้ำหนักพาเลทเปล่า (Pallet Tare Weight) kg",
    min_value=0.0,
    value=25.0,
    step=5.0,
)

max_pallet_gross_weight = st.sidebar.number_input(
    "น้ำหนักรวมสูงสุดต่อพาเลท (Max Pallet Gross Weight) kg",
    min_value=0.01,
    value=1000.0,
    step=50.0,
)

st.sidebar.caption(
    "Max Pallet Gross Weight เป็นค่าที่ผู้ใช้กำหนดเอง — "
    "ควรอ้างอิงข้อกำหนดของลูกค้า / Handling / Logistics จริง"
)


# =========================================================
# SIDEBAR — TOLERANCES / SEARCH
# =========================================================
st.sidebar.header("4. ระยะเผื่อและ Optimization")

box_tolerance = st.sidebar.slider(
    "ระยะเผื่อระหว่างกล่อง",
    min_value=0.0,
    max_value=10.0,
    value=2.0,
    step=0.5,
)

overhang_allowance = st.sidebar.slider(
    "ระยะกล่องยื่นนอกขอบต่อด้าน (Allowed Overhang)",
    min_value=0.0,
    max_value=50.0,
    value=0.0,
    step=5.0,
)

advanced_residual_search = st.sidebar.checkbox(
    "Advanced Residual-space Search",
    value=True,
    help=(
        "เปิด Residual L-Fill เพิ่มจาก Simple Grid, Mixed Rows "
        "และ Mixed Columns"
    ),
)

prefer_simple_on_safe_tie = st.sidebar.checkbox(
    "Safe Qty เท่ากัน ให้เลือก Layout ที่เรียบง่ายกว่า",
    value=True,
)

st.sidebar.caption(
    "V0.2.1 ใช้ Smart Floor Solver เดิมจาก V0.2 และปรับ Visualization / Performance "
    "โดยการหมุนกล่องบนพื้น 90° ยังไม่ถือว่าเป็นการเปลี่ยน H-Up / L-Up / W-Up"
)


# =========================================================
# SIDEBAR — 3D DISPLAY
# =========================================================
st.sidebar.header("5. 3D Display Options")

show_corner_guards = st.sidebar.checkbox(
    "แสดง Corner Guards / Top Edge Guards",
    value=True,
)

show_straps = st.sidebar.checkbox(
    "แสดง Straps",
    value=True,
)

show_height_plane = st.sidebar.checkbox(
    "แสดง Height Limit Plane",
    value=True,
)

st.sidebar.caption(
    "3D Packaging Accessories เป็น Illustration เพื่อช่วยสื่อสารเท่านั้น "
    "ไม่ใช่การ Recommendation ว่าจำเป็นต้องใช้จริง"
)


# =========================================================
# VALIDATION / WORKING DIMENSIONS
# =========================================================
available_cargo_height = max_total_height - pallet_h

if available_cargo_height <= 0:
    st.error(
        "❌ Max Total Height ต้องสูงกว่า Pallet Height "
        "เพื่อให้มีพื้นที่สำหรับกล่องสินค้า"
    )
    st.stop()

if max_pallet_gross_weight <= pallet_tare_weight:
    st.error(
        "❌ Max Pallet Gross Weight ต้องมากกว่า Pallet Tare Weight"
    )
    st.stop()

allowable_w = pallet_w + (2 * overhang_allowance)
allowable_l = pallet_l + (2 * overhang_allowance)
allowed_x0 = -overhang_allowance
allowed_y0 = -overhang_allowance


# =========================================================
# ORIENTATION GROUPS
# =========================================================
ORIENTATION_GROUPS = [
    {
        "UP_AXIS": "H",
        "ALLOWED": allow_h_up,
        "NORMAL": True,
        "LABEL": "H Up — Normal",
        "A_NAME": "W×L",
        "A_W": box_w,
        "A_L": box_l,
        "B_NAME": "L×W",
        "B_W": box_l,
        "B_L": box_w,
        "BOX_VERTICAL_H": box_h,
    },
    {
        "UP_AXIS": "L",
        "ALLOWED": allow_l_up,
        "NORMAL": False,
        "LABEL": "L Up — Side Orientation",
        "A_NAME": "W×H",
        "A_W": box_w,
        "A_L": box_h,
        "B_NAME": "H×W",
        "B_W": box_h,
        "B_L": box_w,
        "BOX_VERTICAL_H": box_l,
    },
    {
        "UP_AXIS": "W",
        "ALLOWED": allow_w_up,
        "NORMAL": False,
        "LABEL": "W Up — Side Orientation",
        "A_NAME": "L×H",
        "A_W": box_l,
        "A_L": box_h,
        "B_NAME": "H×L",
        "B_W": box_h,
        "B_L": box_l,
        "BOX_VERTICAL_H": box_w,
    },
]


# =========================================================
# SMART FLOOR OPTIMIZER — GEOMETRY HELPERS
# =========================================================
def fit_count_1d(available, item, gap):
    """
    Number of items that fit in one axis when gap is only required
    BETWEEN adjacent cartons, not after the final carton.

    n * item + (n-1) * gap <= available
    """
    if available <= 0 or item <= 0:
        return 0

    return max(
        int(math.floor((available + gap + EPS) / (item + gap))),
        0,
    )


def span_1d(count, item, gap):
    if count <= 0:
        return 0.0

    return count * item + (count - 1) * gap


def placement_bounds(placements):
    if not placements:
        return {
            "MIN_X": 0.0,
            "MIN_Y": 0.0,
            "MAX_X": 0.0,
            "MAX_Y": 0.0,
            "SPAN_W": 0.0,
            "SPAN_L": 0.0,
        }

    min_x = min(p["x"] for p in placements)
    min_y = min(p["y"] for p in placements)
    max_x = max(p["x"] + p["w"] for p in placements)
    max_y = max(p["y"] + p["l"] for p in placements)

    return {
        "MIN_X": min_x,
        "MIN_Y": min_y,
        "MAX_X": max_x,
        "MAX_Y": max_y,
        "SPAN_W": max_x - min_x,
        "SPAN_L": max_y - min_y,
    }


def center_placements(placements):
    """
    Centers a completed layer layout inside the allowed footprint.
    Coordinates remain relative to the physical pallet:
    pallet = [0..W] × [0..L]
    allowed overhang area = [-OH..W+OH] × [-OH..L+OH]
    """
    if not placements:
        return []

    p = [dict(x) for x in placements]
    bounds = placement_bounds(p)

    target_center_x = pallet_w / 2.0
    target_center_y = pallet_l / 2.0

    current_center_x = (
        bounds["MIN_X"] + bounds["MAX_X"]
    ) / 2.0

    current_center_y = (
        bounds["MIN_Y"] + bounds["MAX_Y"]
    ) / 2.0

    dx = target_center_x - current_center_x
    dy = target_center_y - current_center_y

    for item in p:
        item["x"] += dx
        item["y"] += dy

    return p


def grid_in_rect(
    rect_x,
    rect_y,
    rect_w,
    rect_l,
    box_w_used,
    box_l_used,
    rotation_code,
):
    nx = fit_count_1d(
        rect_w,
        box_w_used,
        box_tolerance,
    )

    ny = fit_count_1d(
        rect_l,
        box_l_used,
        box_tolerance,
    )

    if nx <= 0 or ny <= 0:
        return []

    used_w = span_1d(
        nx,
        box_w_used,
        box_tolerance,
    )

    used_l = span_1d(
        ny,
        box_l_used,
        box_tolerance,
    )

    start_x = rect_x + (rect_w - used_w) / 2.0
    start_y = rect_y + (rect_l - used_l) / 2.0

    placements = []

    for ix in range(nx):
        for iy in range(ny):
            placements.append(
                {
                    "x": (
                        start_x
                        + ix * (box_w_used + box_tolerance)
                    ),
                    "y": (
                        start_y
                        + iy * (box_l_used + box_tolerance)
                    ),
                    "w": box_w_used,
                    "l": box_l_used,
                    "ROT": rotation_code,
                }
            )

    return placements


def interleaved_sequence(count_a, count_b):
    """
    A simple balanced order for row / column types.
    It does not affect capacity; it only improves the visual distribution.
    """
    seq = []
    a = count_a
    b = count_b
    last = None

    while a > 0 or b > 0:
        if a > 0 and b > 0:
            if a > b:
                pick = "A"
            elif b > a:
                pick = "B"
            else:
                pick = "A" if last != "A" else "B"
        elif a > 0:
            pick = "A"
        else:
            pick = "B"

        seq.append(pick)
        last = pick

        if pick == "A":
            a -= 1
        else:
            b -= 1

    return seq


def normalized_layout_key(placements):
    """
    Used to remove duplicated physical layouts created by different search paths.
    """
    normalized = center_placements(placements)

    rows = []

    for p in normalized:
        rows.append(
            (
                round(p["x"], 3),
                round(p["y"], 3),
                round(p["w"], 3),
                round(p["l"], 3),
            )
        )

    return tuple(sorted(rows))


def finalize_candidate(
    strategy,
    complexity,
    placements,
    orientation_a_count,
    orientation_b_count,
):
    centered = center_placements(placements)
    bounds = placement_bounds(centered)

    return {
        "STRATEGY": strategy,
        "COMPLEXITY": complexity,
        "PLACEMENTS": centered,
        "COUNT": len(centered),
        "A_COUNT": orientation_a_count,
        "B_COUNT": orientation_b_count,
        "ENVELOPE_W": bounds["SPAN_W"],
        "ENVELOPE_L": bounds["SPAN_L"],
        "ENVELOPE_AREA": (
            bounds["SPAN_W"] * bounds["SPAN_L"]
        ),
    }


# =========================================================
# STRATEGY SEARCH
# =========================================================
def generate_simple_candidates(group):
    candidates = []

    for rot, bw, bl in [
        ("A", group["A_W"], group["A_L"]),
        ("B", group["B_W"], group["B_L"]),
    ]:
        placements = grid_in_rect(
            allowed_x0,
            allowed_y0,
            allowable_w,
            allowable_l,
            bw,
            bl,
            rot,
        )

        candidates.append(
            finalize_candidate(
                strategy=(
                    f"Simple Grid — "
                    f"{group['A_NAME'] if rot == 'A' else group['B_NAME']}"
                ),
                complexity=0,
                placements=placements,
                orientation_a_count=(
                    len(placements)
                    if rot == "A"
                    else 0
                ),
                orientation_b_count=(
                    len(placements)
                    if rot == "B"
                    else 0
                ),
            )
        )

    return candidates


def generate_mixed_row_candidates(group):
    candidates = []

    a_w = group["A_W"]
    a_l = group["A_L"]
    b_w = group["B_W"]
    b_l = group["B_L"]

    per_row_a = fit_count_1d(
        allowable_w,
        a_w,
        box_tolerance,
    )

    per_row_b = fit_count_1d(
        allowable_w,
        b_w,
        box_tolerance,
    )

    max_rows_a = fit_count_1d(
        allowable_l,
        a_l,
        box_tolerance,
    )

    max_rows_b = fit_count_1d(
        allowable_l,
        b_l,
        box_tolerance,
    )

    for rows_a in range(max_rows_a + 1):
        for rows_b in range(max_rows_b + 1):
            total_rows = rows_a + rows_b

            if total_rows <= 0:
                continue

            total_depth = (
                rows_a * a_l
                + rows_b * b_l
                + max(total_rows - 1, 0) * box_tolerance
            )

            if total_depth > allowable_l + EPS:
                continue

            # Pure A / Pure B patterns are already represented by Simple Grid.
            if rows_a == 0 or rows_b == 0:
                continue

            sequence = interleaved_sequence(
                rows_a,
                rows_b,
            )

            start_y = (
                allowed_y0
                + (allowable_l - total_depth) / 2.0
            )

            y = start_y
            placements = []
            a_count = 0
            b_count = 0

            for row_type in sequence:
                if row_type == "A":
                    bw = a_w
                    bl = a_l
                    per_row = per_row_a
                else:
                    bw = b_w
                    bl = b_l
                    per_row = per_row_b

                if per_row <= 0:
                    y += bl + box_tolerance
                    continue

                row_used_w = span_1d(
                    per_row,
                    bw,
                    box_tolerance,
                )

                start_x = (
                    allowed_x0
                    + (allowable_w - row_used_w) / 2.0
                )

                for ix in range(per_row):
                    placements.append(
                        {
                            "x": (
                                start_x
                                + ix * (bw + box_tolerance)
                            ),
                            "y": y,
                            "w": bw,
                            "l": bl,
                            "ROT": row_type,
                        }
                    )

                    if row_type == "A":
                        a_count += 1
                    else:
                        b_count += 1

                y += bl + box_tolerance

            candidates.append(
                finalize_candidate(
                    strategy="Mixed Rows",
                    complexity=1,
                    placements=placements,
                    orientation_a_count=a_count,
                    orientation_b_count=b_count,
                )
            )

    return candidates


def generate_mixed_column_candidates(group):
    candidates = []

    a_w = group["A_W"]
    a_l = group["A_L"]
    b_w = group["B_W"]
    b_l = group["B_L"]

    per_col_a = fit_count_1d(
        allowable_l,
        a_l,
        box_tolerance,
    )

    per_col_b = fit_count_1d(
        allowable_l,
        b_l,
        box_tolerance,
    )

    max_cols_a = fit_count_1d(
        allowable_w,
        a_w,
        box_tolerance,
    )

    max_cols_b = fit_count_1d(
        allowable_w,
        b_w,
        box_tolerance,
    )

    for cols_a in range(max_cols_a + 1):
        for cols_b in range(max_cols_b + 1):
            total_cols = cols_a + cols_b

            if total_cols <= 0:
                continue

            total_width = (
                cols_a * a_w
                + cols_b * b_w
                + max(total_cols - 1, 0) * box_tolerance
            )

            if total_width > allowable_w + EPS:
                continue

            if cols_a == 0 or cols_b == 0:
                continue

            sequence = interleaved_sequence(
                cols_a,
                cols_b,
            )

            start_x = (
                allowed_x0
                + (allowable_w - total_width) / 2.0
            )

            x = start_x
            placements = []
            a_count = 0
            b_count = 0

            for col_type in sequence:
                if col_type == "A":
                    bw = a_w
                    bl = a_l
                    per_col = per_col_a
                else:
                    bw = b_w
                    bl = b_l
                    per_col = per_col_b

                if per_col <= 0:
                    x += bw + box_tolerance
                    continue

                col_used_l = span_1d(
                    per_col,
                    bl,
                    box_tolerance,
                )

                start_y = (
                    allowed_y0
                    + (allowable_l - col_used_l) / 2.0
                )

                for iy in range(per_col):
                    placements.append(
                        {
                            "x": x,
                            "y": (
                                start_y
                                + iy * (bl + box_tolerance)
                            ),
                            "w": bw,
                            "l": bl,
                            "ROT": col_type,
                        }
                    )

                    if col_type == "A":
                        a_count += 1
                    else:
                        b_count += 1

                x += bw + box_tolerance

            candidates.append(
                finalize_candidate(
                    strategy="Mixed Columns",
                    complexity=1,
                    placements=placements,
                    orientation_a_count=a_count,
                    orientation_b_count=b_count,
                )
            )

    return candidates


def generate_residual_l_fill_candidates(group):
    """
    Residual L-Fill:
    - build a main rectangle using one floor rotation,
    - use the opposite rotation in the right residual strip,
    - use the opposite rotation in the top residual strip.

    The right strip only occupies the height of the main block;
    the top strip occupies the full pallet width. This avoids overlap.
    """
    candidates = []

    orientations = [
        (
            "A",
            group["A_W"],
            group["A_L"],
            "B",
            group["B_W"],
            group["B_L"],
        ),
        (
            "B",
            group["B_W"],
            group["B_L"],
            "A",
            group["A_W"],
            group["A_L"],
        ),
    ]

    for (
        main_rot,
        main_w,
        main_l,
        residual_rot,
        residual_w,
        residual_l,
    ) in orientations:

        max_nx = fit_count_1d(
            allowable_w,
            main_w,
            box_tolerance,
        )

        max_ny = fit_count_1d(
            allowable_l,
            main_l,
            box_tolerance,
        )

        for nx in range(1, max_nx + 1):
            for ny in range(1, max_ny + 1):
                main_span_w = span_1d(
                    nx,
                    main_w,
                    box_tolerance,
                )

                main_span_l = span_1d(
                    ny,
                    main_l,
                    box_tolerance,
                )

                if (
                    main_span_w > allowable_w + EPS
                    or main_span_l > allowable_l + EPS
                ):
                    continue

                placements = []

                # Main block starts from local (0,0), then whole layout is centered.
                for ix in range(nx):
                    for iy in range(ny):
                        placements.append(
                            {
                                "x": (
                                    ix
                                    * (main_w + box_tolerance)
                                ),
                                "y": (
                                    iy
                                    * (main_l + box_tolerance)
                                ),
                                "w": main_w,
                                "l": main_l,
                                "ROT": main_rot,
                            }
                        )

                # Right residual strip.
                right_x = main_span_w + box_tolerance
                right_w = allowable_w - right_x

                if right_w > 0:
                    placements.extend(
                        grid_in_rect(
                            rect_x=right_x,
                            rect_y=0.0,
                            rect_w=right_w,
                            rect_l=main_span_l,
                            box_w_used=residual_w,
                            box_l_used=residual_l,
                            rotation_code=residual_rot,
                        )
                    )

                # Top residual strip.
                top_y = main_span_l + box_tolerance
                top_l = allowable_l - top_y

                if top_l > 0:
                    placements.extend(
                        grid_in_rect(
                            rect_x=0.0,
                            rect_y=top_y,
                            rect_w=allowable_w,
                            rect_l=top_l,
                            box_w_used=residual_w,
                            box_l_used=residual_l,
                            rotation_code=residual_rot,
                        )
                    )

                # Local residual search uses coordinates from 0..allowable.
                # Re-center into physical pallet / allowed overhang coordinates.
                for p in placements:
                    p["x"] += allowed_x0
                    p["y"] += allowed_y0

                a_count = sum(
                    1
                    for p in placements
                    if p["ROT"] == "A"
                )

                b_count = len(placements) - a_count

                if a_count <= 0 or b_count <= 0:
                    continue

                candidates.append(
                    finalize_candidate(
                        strategy="Residual L-Fill",
                        complexity=2,
                        placements=placements,
                        orientation_a_count=a_count,
                        orientation_b_count=b_count,
                    )
                )

    return candidates


def generate_floor_candidates(group):
    raw = []

    raw.extend(
        generate_simple_candidates(group)
    )

    raw.extend(
        generate_mixed_row_candidates(group)
    )

    raw.extend(
        generate_mixed_column_candidates(group)
    )

    if advanced_residual_search:
        raw.extend(
            generate_residual_l_fill_candidates(group)
        )

    dedup = {}

    for candidate in raw:
        key = normalized_layout_key(
            candidate["PLACEMENTS"]
        )

        if key not in dedup:
            dedup[key] = candidate
        else:
            current = dedup[key]

            # Keep simpler strategy when physical placement is identical.
            if (
                candidate["COMPLEXITY"],
                candidate["STRATEGY"],
            ) < (
                current["COMPLEXITY"],
                current["STRATEGY"],
            ):
                dedup[key] = candidate

    return list(dedup.values())


# =========================================================
# CAPACITY / ENGINEERING METRICS
# =========================================================
def candidate_metrics(group, candidate):
    boxes_per_layer = candidate["COUNT"]

    height_layers = (
        int(
            math.floor(
                available_cargo_height
                / group["BOX_VERTICAL_H"]
            )
        )
        if group["BOX_VERTICAL_H"] > 0
        else 0
    )

    geometry_total = (
        boxes_per_layer * height_layers
    )

    available_weight_for_cartons = (
        max_pallet_gross_weight
        - pallet_tare_weight
    )

    weight_capacity = max(
        int(
            math.floor(
                available_weight_for_cartons
                / box_weight
            )
        ),
        0,
    )

    safe_total = min(
        geometry_total,
        weight_capacity,
    )

    safe_layers_used = (
        int(
            math.ceil(
                safe_total
                / boxes_per_layer
            )
        )
        if safe_total > 0
        and boxes_per_layer > 0
        else 0
    )

    partial_top_layer_qty = (
        safe_total % boxes_per_layer
        if boxes_per_layer > 0
        else 0
    )

    geometry_total_height = (
        pallet_h
        + height_layers
        * group["BOX_VERTICAL_H"]
        if geometry_total > 0
        else pallet_h
    )

    safe_total_height = (
        pallet_h
        + safe_layers_used
        * group["BOX_VERTICAL_H"]
        if safe_total > 0
        else pallet_h
    )

    geometry_gross_weight = (
        pallet_tare_weight
        + geometry_total * box_weight
    )

    safe_gross_weight = (
        pallet_tare_weight
        + safe_total * box_weight
    )

    carton_floor_area = (
        group["A_W"]
        * group["A_L"]
    )

    pallet_area = (
        pallet_w * pallet_l
    )

    allowed_area = (
        allowable_w * allowable_l
    )

    actual_carton_area = (
        boxes_per_layer
        * carton_floor_area
    )

    carton_area_coverage = (
        actual_carton_area
        / pallet_area
        * 100.0
        if pallet_area > 0
        and boxes_per_layer > 0
        else 0.0
    )

    allowed_footprint_util = (
        actual_carton_area
        / allowed_area
        * 100.0
        if allowed_area > 0
        and boxes_per_layer > 0
        else 0.0
    )

    envelope_coverage = (
        candidate["ENVELOPE_AREA"]
        / pallet_area
        * 100.0
        if pallet_area > 0
        and boxes_per_layer > 0
        else 0.0
    )

    bounds = placement_bounds(
        candidate["PLACEMENTS"]
    )

    overhang_left = max(
        -bounds["MIN_X"],
        0.0,
    )

    overhang_right = max(
        bounds["MAX_X"] - pallet_w,
        0.0,
    )

    overhang_front = max(
        -bounds["MIN_Y"],
        0.0,
    )

    overhang_back = max(
        bounds["MAX_Y"] - pallet_l,
        0.0,
    )

    remaining_height_safe = max(
        max_total_height
        - safe_total_height,
        0.0,
    )

    remaining_weight_safe = max(
        max_pallet_gross_weight
        - safe_gross_weight,
        0.0,
    )

    if not group["ALLOWED"]:
        primary_limiter = "Orientation"
        limiter_detail = (
            "Up orientation is locked and is not eligible "
            "for recommendation."
        )
    elif boxes_per_layer <= 0:
        primary_limiter = "Floor Space"
        limiter_detail = (
            "No carton pattern fits the allowed pallet footprint."
        )
    elif height_layers <= 0:
        primary_limiter = "Height"
        limiter_detail = (
            "Carton vertical height exceeds available cargo height."
        )
    elif weight_capacity < geometry_total:
        primary_limiter = "Pallet Weight"
        limiter_detail = (
            "Max Pallet Gross Weight limits the recommended quantity."
        )
    else:
        primary_limiter = "Geometry"
        limiter_detail = (
            "Floor pattern and height limit determine the current capacity."
        )

    return {
        **candidate,
        "UP_AXIS": group["UP_AXIS"],
        "NORMAL": group["NORMAL"],
        "ALLOWED": group["ALLOWED"],
        "LABEL": group["LABEL"],
        "A_NAME": group["A_NAME"],
        "B_NAME": group["B_NAME"],
        "BOX_VERTICAL_H": group["BOX_VERTICAL_H"],
        "HEIGHT_LAYERS": height_layers,
        "GEOMETRY_TOTAL": geometry_total,
        "WEIGHT_CAPACITY": weight_capacity,
        "SAFE_TOTAL": safe_total,
        "SAFE_LAYERS_USED": safe_layers_used,
        "PARTIAL_TOP_LAYER_QTY": partial_top_layer_qty,
        "GEOMETRY_TOTAL_HEIGHT": geometry_total_height,
        "SAFE_TOTAL_HEIGHT": safe_total_height,
        "GEOMETRY_GROSS_WEIGHT": geometry_gross_weight,
        "SAFE_GROSS_WEIGHT": safe_gross_weight,
        "CARTON_AREA_COVERAGE": carton_area_coverage,
        "ALLOWED_FOOTPRINT_UTIL": allowed_footprint_util,
        "ENVELOPE_COVERAGE": envelope_coverage,
        "OVERHANG_LEFT": overhang_left,
        "OVERHANG_RIGHT": overhang_right,
        "OVERHANG_FRONT": overhang_front,
        "OVERHANG_BACK": overhang_back,
        "REMAINING_HEIGHT_SAFE": remaining_height_safe,
        "REMAINING_WEIGHT_SAFE": remaining_weight_safe,
        "PRIMARY_LIMITER": primary_limiter,
        "LIMITER_DETAIL": limiter_detail,
    }


def geometry_candidate_key(item):
    return (
        item["COUNT"],
        -item["COMPLEXITY"],
        item["ALLOWED_FOOTPRINT_UTIL"],
        -item["ENVELOPE_AREA"],
    )


def practical_candidate_key(item):
    """
    Safe quantity first.
    When Safe Qty ties, V0.2 can prefer the simpler physical pattern.
    """
    if prefer_simple_on_safe_tie:
        return (
            item["SAFE_TOTAL"],
            -item["COMPLEXITY"],
            -item["SAFE_TOTAL_HEIGHT"],
            item["COUNT"],
            item["ALLOWED_FOOTPRINT_UTIL"],
        )

    return (
        item["SAFE_TOTAL"],
        item["COUNT"],
        -item["COMPLEXITY"],
        -item["SAFE_TOTAL_HEIGHT"],
        item["ALLOWED_FOOTPRINT_UTIL"],
    )


# =========================================================
# BUILD UP-ORIENTATION SCENARIOS — CACHED V0.2 SOLVER
# =========================================================
def group_cache_tuple(group):
    return (
        group["UP_AXIS"],
        group["ALLOWED"],
        group["NORMAL"],
        group["LABEL"],
        group["A_NAME"],
        float(group["A_W"]),
        float(group["A_L"]),
        group["B_NAME"],
        float(group["B_W"]),
        float(group["B_L"]),
        float(group["BOX_VERTICAL_H"]),
    )


def group_from_cache_tuple(values):
    (
        up_axis,
        allowed,
        normal,
        label,
        a_name,
        a_w,
        a_l,
        b_name,
        b_w,
        b_l,
        box_vertical_h,
    ) = values

    return {
        "UP_AXIS": up_axis,
        "ALLOWED": allowed,
        "NORMAL": normal,
        "LABEL": label,
        "A_NAME": a_name,
        "A_W": a_w,
        "A_L": a_l,
        "B_NAME": b_name,
        "B_W": b_w,
        "B_L": b_l,
        "BOX_VERTICAL_H": box_vertical_h,
    }


@st.cache_data(show_spinner=False)
def solve_group_cached(
    group_values,
    pallet_w_key,
    pallet_l_key,
    pallet_h_key,
    max_total_height_key,
    available_cargo_height_key,
    box_weight_key,
    pallet_tare_weight_key,
    max_pallet_gross_weight_key,
    box_tolerance_key,
    overhang_allowance_key,
    advanced_residual_search_key,
    prefer_simple_on_safe_tie_key,
):
    """
    Cache boundary for the unchanged V0.2 Smart Floor Solver.

    The *_key arguments intentionally participate in Streamlit's cache key.
    The geometry functions use the matching current-run globals, so a cached
    result is reused only when every solver-relevant engineering input matches.
    """
    group = group_from_cache_tuple(group_values)

    floor_candidates = generate_floor_candidates(group)

    evaluated = [
        candidate_metrics(group, candidate)
        for candidate in floor_candidates
    ]

    evaluated.sort(
        key=geometry_candidate_key,
        reverse=True,
    )

    geometry_best = max(
        evaluated,
        key=geometry_candidate_key,
    )

    practical_best = max(
        evaluated,
        key=practical_candidate_key,
    )

    return {
        "GROUP": group,
        "EVALUATED": evaluated,
        "GEOMETRY_BEST": geometry_best,
        "PRACTICAL_BEST": practical_best,
        "LAYOUT_COUNT": len(evaluated),
    }


scenarios = []

for group in ORIENTATION_GROUPS:
    scenarios.append(
        solve_group_cached(
            group_cache_tuple(group),
            float(pallet_w),
            float(pallet_l),
            float(pallet_h),
            float(max_total_height),
            float(available_cargo_height),
            float(box_weight),
            float(pallet_tare_weight),
            float(max_pallet_gross_weight),
            float(box_tolerance),
            float(overhang_allowance),
            bool(advanced_residual_search),
            bool(prefer_simple_on_safe_tie),
        )
    )


# =========================================================
# CROSS-ORIENTATION RECOMMENDATION
# =========================================================
allowed_scenarios = [
    s
    for s in scenarios
    if s["GROUP"]["ALLOWED"]
]

if not allowed_scenarios:
    st.error(
        "❌ ไม่มี Up Orientation ที่ได้รับอนุญาต"
    )
    st.stop()


def scenario_recommendation_key(scenario):
    item = scenario["PRACTICAL_BEST"]

    return (
        item["SAFE_TOTAL"],
        1 if scenario["GROUP"]["NORMAL"] else 0,
        -item["SAFE_TOTAL_HEIGHT"],
        -item["COMPLEXITY"],
        item["COUNT"],
        item["ALLOWED_FOOTPRINT_UTIL"],
    )


best_overall_scenario = max(
    allowed_scenarios,
    key=scenario_recommendation_key,
)

normal_scenario = next(
    (
        s
        for s in allowed_scenarios
        if s["GROUP"]["NORMAL"]
    ),
    None,
)

alternative_scenarios = [
    s
    for s in allowed_scenarios
    if not s["GROUP"]["NORMAL"]
]

best_alternative_scenario = (
    max(
        alternative_scenarios,
        key=scenario_recommendation_key,
    )
    if alternative_scenarios
    else None
)


# =========================================================
# PARTIAL TOP-LAYER BALANCE
# =========================================================
def subset_centroid_offset(
    placements,
    indices,
):
    if not indices:
        return 0.0

    centers = [
        (
            placements[i]["x"]
            + placements[i]["w"] / 2.0,
            placements[i]["y"]
            + placements[i]["l"] / 2.0,
        )
        for i in indices
    ]

    cx = sum(x for x, _ in centers) / len(centers)
    cy = sum(y for _, y in centers) / len(centers)

    return math.hypot(
        cx - pallet_w / 2.0,
        cy - pallet_l / 2.0,
    )


def balanced_partial_subset(
    placements,
    qty,
):
    if qty <= 0:
        return []

    if qty >= len(placements):
        return [
            dict(p)
            for p in placements
        ]

    combo_count = math.comb(
        len(placements),
        qty,
    )

    if (
        combo_count
        <= MAX_EXHAUSTIVE_PARTIAL_COMBINATIONS
    ):
        best_indices = None
        best_score = None

        for idx_tuple in combinations(
            range(len(placements)),
            qty,
        ):
            offset = subset_centroid_offset(
                placements,
                idx_tuple,
            )

            radial_sum = sum(
                (
                    (
                        placements[i]["x"]
                        + placements[i]["w"] / 2.0
                        - pallet_w / 2.0
                    ) ** 2
                    + (
                        placements[i]["y"]
                        + placements[i]["l"] / 2.0
                        - pallet_l / 2.0
                    ) ** 2
                )
                for i in idx_tuple
            )

            score = (
                round(offset, 8),
                radial_sum,
            )

            if (
                best_score is None
                or score < best_score
            ):
                best_score = score
                best_indices = idx_tuple

        return [
            dict(placements[i])
            for i in best_indices
        ]

    # Fallback: nearest-to-center heuristic.
    ranked = sorted(
        placements,
        key=lambda p: (
            (
                p["x"]
                + p["w"] / 2.0
                - pallet_w / 2.0
            ) ** 2
            + (
                p["y"]
                + p["l"] / 2.0
                - pallet_l / 2.0
            ) ** 2
        ),
    )

    return [
        dict(p)
        for p in ranked[:qty]
    ]


def build_display_stack(
    layout,
    carton_count,
):
    """
    Returns a list of layer placement lists.
    Full layers repeat the selected Smart Floor Pattern.
    Partial final layer uses geometric-balance selection.
    """
    if (
        carton_count <= 0
        or layout["COUNT"] <= 0
    ):
        return []

    base_pattern = [
        dict(p)
        for p in layout["PLACEMENTS"]
    ]

    full_layers = (
        carton_count
        // layout["COUNT"]
    )

    remainder = (
        carton_count
        % layout["COUNT"]
    )

    layers = []

    for _ in range(full_layers):
        layers.append(
            [
                dict(p)
                for p in base_pattern
            ]
        )

    if remainder > 0:
        layers.append(
            balanced_partial_subset(
                base_pattern,
                remainder,
            )
        )

    return layers


# =========================================================
# VISUALIZATION — SVG TOP VIEW
# =========================================================
def generate_svg_layer(
    layout,
    border_color,
):
    pad = max(
        pallet_w,
        pallet_l,
    ) * 0.105

    view_w = (
        pallet_w
        + 2 * overhang_allowance
        + 2 * pad
    )

    view_h = (
        pallet_l
        + 2 * overhang_allowance
        + 2 * pad
    )

    origin_x = (
        pad + overhang_allowance
    )

    origin_y = (
        pad + overhang_allowance
    )

    svg = (
        f'<svg width="100%" height="auto" '
        f'viewBox="0 0 {view_w} {view_h}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="background:#ffffff;'
        f'border:2px solid #cbd5e1;'
        f'border-radius:12px;">'
    )

    if overhang_allowance > 0:
        svg += (
            f'<rect x="{pad}" y="{pad}" '
            f'width="{allowable_w}" '
            f'height="{allowable_l}" '
            f'fill="none" '
            f'stroke="#94a3b8" '
            f'stroke-width="3" '
            f'stroke-dasharray="10,8" '
            f'rx="8"/>'
        )

    svg += (
        f'<rect x="{origin_x}" '
        f'y="{origin_y}" '
        f'width="{pallet_w}" '
        f'height="{pallet_l}" '
        f'fill="#f8fafc" '
        f'stroke="{border_color}" '
        f'stroke-width="6" '
        f'rx="8"/>'
    )

    color_map = {
        "A": {
            "fill": "#ffedd5",
            "stroke": "#ea580c",
            "text": "#9a3412",
        },
        "B": {
            "fill": "#dbeafe",
            "stroke": "#2563eb",
            "text": "#1e3a8a",
        },
    }

    for p in layout["PLACEMENTS"]:
        x = origin_x + p["x"]
        y = origin_y + p["y"]

        c = color_map[p["ROT"]]

        svg += (
            f'<rect x="{x}" y="{y}" '
            f'width="{p["w"]}" '
            f'height="{p["l"]}" '
            f'fill="{c["fill"]}" '
            f'stroke="{c["stroke"]}" '
            f'stroke-width="2.4" '
            f'rx="4"/>'
        )

        label_size = max(
            12,
            min(
                22,
                int(
                    min(
                        p["w"],
                        p["l"],
                    )
                    * 0.085
                ),
            ),
        )

        svg += (
            f'<text '
            f'x="{x + p["w"]/2}" '
            f'y="{y + p["l"]/2 + label_size/3}" '
            f'font-family="system-ui,sans-serif" '
            f'font-size="{label_size}" '
            f'font-weight="700" '
            f'fill="{c["text"]}" '
            f'text-anchor="middle">'
            f'{int(p["w"])}×{int(p["l"])}'
            f'</text>'
        )

    svg += (
        f'<text x="{origin_x + pallet_w/2}" '
        f'y="{view_h - 18}" '
        f'font-size="23" '
        f'font-weight="700" '
        f'fill="#334155" '
        f'text-anchor="middle">'
        f'Pallet W: {int(pallet_w)} mm'
        f'</text>'
    )

    svg += (
        f'<text x="25" '
        f'y="{origin_y + pallet_l/2}" '
        f'font-size="23" '
        f'font-weight="700" '
        f'fill="#334155" '
        f'text-anchor="middle" '
        f'transform="rotate(-90,25,{origin_y + pallet_l/2})">'
        f'Pallet L: {int(pallet_l)} mm'
        f'</text>'
    )

    svg += "</svg>"

    return svg


# =========================================================
# VISUALIZATION — TRUE-SCALE ENGINEERING ELEVATION (SVG)
# =========================================================
def visible_face_segments(layer_positions, view_type):
    """
    Hidden-line-aware orthographic projection.

    Front view looks from negative Y toward +Y and uses X horizontally.
    Side view looks from negative X toward +X and uses Y horizontally.
    Only the nearest carton face is drawn for every visible horizontal span.
    This prevents rear carton edges from being drawn on top of the front row.
    """
    if not layer_positions:
        return []

    prepared = []

    for idx, p in enumerate(layer_positions):
        if view_type == "front":
            start = p["x"]
            end = p["x"] + p["w"]
            depth = p["y"]
        else:
            start = p["y"]
            end = p["y"] + p["l"]
            depth = p["x"]

        prepared.append(
            {
                "id": idx,
                "start": start,
                "end": end,
                "depth": depth,
                "rot": p["ROT"],
            }
        )

    boundaries = sorted(
        {
            round(v, 6)
            for item in prepared
            for v in (item["start"], item["end"])
        }
    )

    segments = []

    for i in range(len(boundaries) - 1):
        a = boundaries[i]
        b = boundaries[i + 1]

        if b - a <= EPS:
            continue

        mid = (a + b) / 2.0

        covering = [
            item
            for item in prepared
            if item["start"] - EPS <= mid <= item["end"] + EPS
        ]

        if not covering:
            continue

        visible = min(
            covering,
            key=lambda item: (item["depth"], item["id"]),
        )

        if (
            segments
            and segments[-1]["id"] == visible["id"]
            and abs(segments[-1]["end"] - a) <= 1e-5
        ):
            segments[-1]["end"] = b
        else:
            segments.append(
                {
                    "id": visible["id"],
                    "start": a,
                    "end": b,
                    "rot": visible["rot"],
                }
            )

    return segments


def generate_true_scale_elevation_svg(
    layout,
    carton_count,
    box_vertical_h,
):
    """
    Front + Side engineering elevation in ONE SVG.

    Both views share the exact same SVG world scale, therefore 1 mm in W/L
    uses the same graphical scale as 1 mm in H. This removes the distortion
    caused by separate fixed-size Matplotlib canvases.
    """
    layers = build_display_stack(layout, carton_count)

    displayed_height = (
        pallet_h + len(layers) * box_vertical_h
        if layers
        else pallet_h
    )

    side_margin = max(95.0, overhang_allowance + 60.0)
    view_gap = 180.0
    top_title = 135.0
    bottom_space = 120.0

    front_group_w = pallet_w + 2 * overhang_allowance
    side_group_w = pallet_l + 2 * overhang_allowance

    front_group_x = side_margin
    front_pallet_x = front_group_x + overhang_allowance

    side_group_x = (
        front_group_x
        + front_group_w
        + view_gap
    )
    side_pallet_x = side_group_x + overhang_allowance

    view_w = (
        side_margin
        + front_group_w
        + view_gap
        + side_group_w
        + side_margin
    )

    view_h = top_title + max_total_height + bottom_space

    svg = (
        f'<svg width="100%" height="auto" '
        f'viewBox="0 0 {view_w} {view_h}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="background:#ffffff;border:2px solid #cbd5e1;'
        f'border-radius:12px;">'
    )

    # Overall title / scale note.
    svg += (
        f'<text x="{view_w/2}" y="42" '
        f'font-family="system-ui,sans-serif" font-size="30" '
        f'font-weight="800" fill="#0f172a" text-anchor="middle">'
        f'True-scale Engineering Elevation — 1:1 relative W / L / H scale'
        f'</text>'
    )

    svg += (
        f'<text x="{view_w/2}" y="78" '
        f'font-family="system-ui,sans-serif" font-size="20" '
        f'fill="#475569" text-anchor="middle">'
        f'Displayed load: {carton_count} cartons • Height {displayed_height:.0f} mm '
        f'• Limit {max_total_height:.0f} mm'
        f'</text>'
    )

    def world_y(z_top):
        return top_title + (max_total_height - z_top)

    def draw_view(
        group_x,
        pallet_x,
        horizontal_dim,
        view_type,
        title,
        axis_label,
    ):
        nonlocal svg

        # Titles.
        svg += (
            f'<text x="{group_x + (horizontal_dim + 2*overhang_allowance)/2}" '
            f'y="112" font-family="system-ui,sans-serif" font-size="25" '
            f'font-weight="800" fill="#111827" text-anchor="middle">'
            f'{title}</text>'
        )

        # Height grid every 250 mm to support engineering reading.
        grid_step = 250.0
        z = 0.0
        while z <= max_total_height + EPS:
            y = world_y(z)
            svg += (
                f'<line x1="{group_x}" y1="{y}" '
                f'x2="{group_x + horizontal_dim + 2*overhang_allowance}" y2="{y}" '
                f'stroke="#e2e8f0" stroke-width="1.4"/>'
            )
            if z > 0:
                svg += (
                    f'<text x="{group_x - 16}" y="{y + 7}" '
                    f'font-family="system-ui,sans-serif" font-size="18" '
                    f'fill="#64748b" text-anchor="end">{int(z)}</text>'
                )
            z += grid_step

        # Max-height line.
        limit_y = world_y(max_total_height)
        svg += (
            f'<line x1="{group_x}" y1="{limit_y}" '
            f'x2="{group_x + horizontal_dim + 2*overhang_allowance}" y2="{limit_y}" '
            f'stroke="#dc2626" stroke-width="4" stroke-dasharray="16,10"/>'
        )
        svg += (
            f'<text x="{group_x + 8}" y="{limit_y + 28}" '
            f'font-family="system-ui,sans-serif" font-size="18" '
            f'font-weight="700" fill="#b91c1c">Height limit {max_total_height:.0f}</text>'
        )

        # Physical pallet.
        pallet_y = world_y(pallet_h)
        svg += (
            f'<rect x="{pallet_x}" y="{pallet_y}" '
            f'width="{horizontal_dim}" height="{pallet_h}" '
            f'fill="#cbd5e1" stroke="#475569" stroke-width="3"/>'
        )
        svg += (
            f'<text x="{pallet_x + horizontal_dim/2}" '
            f'y="{pallet_y + pallet_h/2 + 7}" '
            f'font-family="system-ui,sans-serif" font-size="19" '
            f'font-weight="800" fill="#334155" text-anchor="middle">'
            f'Pallet H {pallet_h:.0f} mm</text>'
        )

        fill_by_rot = {
            "A": "#f2dfbd",
            "B": "#e4dcc7",
        }

        for layer_idx, layer_positions in enumerate(layers):
            z_bottom = pallet_h + layer_idx * box_vertical_h
            z_top = z_bottom + box_vertical_h
            y = world_y(z_top)

            visible_segments = visible_face_segments(
                layer_positions,
                view_type,
            )

            for segment in visible_segments:
                x = pallet_x + segment["start"]
                width = segment["end"] - segment["start"]
                fill = fill_by_rot.get(segment["rot"], "#efe3cc")

                svg += (
                    f'<rect x="{x}" y="{y}" width="{width}" '
                    f'height="{box_vertical_h}" fill="{fill}" '
                    f'stroke="#4b5563" stroke-width="2.2"/>'
                )

        # Displayed height line.
        load_y = world_y(displayed_height)
        svg += (
            f'<line x1="{group_x}" y1="{load_y}" '
            f'x2="{group_x + horizontal_dim + 2*overhang_allowance}" y2="{load_y}" '
            f'stroke="#15803d" stroke-width="4"/>'
        )
        svg += (
            f'<text x="{group_x + horizontal_dim + 2*overhang_allowance - 8}" '
            f'y="{load_y - 12}" font-family="system-ui,sans-serif" '
            f'font-size="18" font-weight="800" fill="#166534" text-anchor="end">'
            f'Load {displayed_height:.0f} mm</text>'
        )

        # Ground / horizontal dimension labels.
        ground_y = world_y(0)
        svg += (
            f'<line x1="{group_x}" y1="{ground_y}" '
            f'x2="{group_x + horizontal_dim + 2*overhang_allowance}" y2="{ground_y}" '
            f'stroke="#0f172a" stroke-width="2.5"/>'
        )
        svg += (
            f'<text x="{pallet_x + horizontal_dim/2}" '
            f'y="{ground_y + 48}" font-family="system-ui,sans-serif" '
            f'font-size="22" font-weight="800" fill="#334155" text-anchor="middle">'
            f'{axis_label}: {horizontal_dim:.0f} mm</text>'
        )

    draw_view(
        front_group_x,
        front_pallet_x,
        pallet_w,
        "front",
        "Front View — Pallet Width Axis",
        "Pallet Width",
    )

    draw_view(
        side_group_x,
        side_pallet_x,
        pallet_l,
        "side",
        "Side View — Pallet Length Axis",
        "Pallet Length",
    )

    # Shared vertical dimension indication.
    dim_x = 36.0
    svg += (
        f'<line x1="{dim_x}" y1="{world_y(max_total_height)}" '
        f'x2="{dim_x}" y2="{world_y(0)}" stroke="#334155" stroke-width="3"/>'
    )
    svg += (
        f'<text x="18" y="{top_title + max_total_height/2}" '
        f'font-family="system-ui,sans-serif" font-size="22" font-weight="800" '
        f'fill="#334155" text-anchor="middle" '
        f'transform="rotate(-90,18,{top_title + max_total_height/2})">'
        f'Height (mm)</text>'
    )

    svg += "</svg>"
    return svg


# =========================================================
# PLOTLY 3D — LIGHTWEIGHT INDUSTRIAL VIEW
# =========================================================
def cuboid_vertices_faces(cuboids):
    xs, ys, zs = [], [], []
    ii, jj, kk = [], [], []

    faces = [
        (0, 2, 1), (0, 3, 2),
        (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4),
        (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6),
        (3, 0, 4), (3, 4, 7),
    ]

    for cuboid in cuboids:
        x = cuboid["x"]
        y = cuboid["y"]
        z = cuboid["z"]
        dx = cuboid["dx"]
        dy = cuboid["dy"]
        dz = cuboid["dz"]

        base = len(xs)

        vertices = [
            (x, y, z),
            (x + dx, y, z),
            (x + dx, y + dy, z),
            (x, y + dy, z),
            (x, y, z + dz),
            (x + dx, y, z + dz),
            (x + dx, y + dy, z + dz),
            (x, y + dy, z + dz),
        ]

        for vx, vy, vz in vertices:
            xs.append(vx)
            ys.append(vy)
            zs.append(vz)

        for a, b, c in faces:
            ii.append(base + a)
            jj.append(base + b)
            kk.append(base + c)

    return xs, ys, zs, ii, jj, kk


def cuboid_edge_arrays(cuboids):
    ex, ey, ez = [], [], []

    edge_pairs = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]

    for cuboid in cuboids:
        x = cuboid["x"]
        y = cuboid["y"]
        z = cuboid["z"]
        dx = cuboid["dx"]
        dy = cuboid["dy"]
        dz = cuboid["dz"]

        vertices = [
            (x, y, z),
            (x + dx, y, z),
            (x + dx, y + dy, z),
            (x, y + dy, z),
            (x, y, z + dz),
            (x + dx, y, z + dz),
            (x + dx, y + dy, z + dz),
            (x, y + dy, z + dz),
        ]

        for a, b in edge_pairs:
            ex.extend([vertices[a][0], vertices[b][0], None])
            ey.extend([vertices[a][1], vertices[b][1], None])
            ez.extend([vertices[a][2], vertices[b][2], None])

    return ex, ey, ez


def add_cuboid_group(
    fig,
    cuboids,
    fill_color,
    edge_color,
    name,
    edge_width=2.0,
    opacity=0.98,
):
    if not cuboids:
        return

    xs, ys, zs, ii, jj, kk = cuboid_vertices_faces(cuboids)

    fig.add_trace(
        go.Mesh3d(
            x=xs,
            y=ys,
            z=zs,
            i=ii,
            j=jj,
            k=kk,
            color=fill_color,
            opacity=opacity,
            flatshading=True,
            name=name,
            showlegend=False,
            hoverinfo="skip",
            lighting=dict(
                ambient=0.72,
                diffuse=0.58,
                specular=0.04,
                roughness=0.95,
                fresnel=0.02,
            ),
            lightposition=dict(x=1000, y=-1200, z=2200),
        )
    )

    ex, ey, ez = cuboid_edge_arrays(cuboids)

    fig.add_trace(
        go.Scatter3d(
            x=ex,
            y=ey,
            z=ez,
            mode="lines",
            line=dict(
                color=edge_color,
                width=edge_width,
            ),
            hoverinfo="skip",
            showlegend=False,
            name=f"{name} edges",
        )
    )


def generate_plotly_3d(
    layout,
    carton_count,
    box_vertical_h,
):
    if carton_count <= 0:
        return None

    fig = go.Figure()

    # Neutral industrial palette: carton tones are deliberately separated
    # from red securing straps and gray protection accessories.
    carton_palette = {
        "A": "#d8b982",
        "B": "#c7b48e",
    }
    carton_edge = "#3f3f46"
    pallet_fill = "#aeb7c2"
    pallet_edge = "#4b5563"
    strap_color = "#b91c1c"
    guard_color = "#6b7280"

    pallet_cuboid = [
        {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "dx": pallet_w,
            "dy": pallet_l,
            "dz": pallet_h,
        }
    ]

    add_cuboid_group(
        fig,
        pallet_cuboid,
        pallet_fill,
        pallet_edge,
        "Pallet",
        edge_width=2.5,
    )

    layers = build_display_stack(
        layout,
        carton_count,
    )

    carton_groups = {
        "A": [],
        "B": [],
    }

    for layer_idx, layer_positions in enumerate(layers):
        z = pallet_h + layer_idx * box_vertical_h

        for p in layer_positions:
            carton_groups[p["ROT"]].append(
                {
                    "x": p["x"],
                    "y": p["y"],
                    "z": z,
                    "dx": p["w"],
                    "dy": p["l"],
                    "dz": box_vertical_h,
                }
            )

    for rot in ("A", "B"):
        add_cuboid_group(
            fig,
            carton_groups[rot],
            carton_palette[rot],
            carton_edge,
            f"Cartons {rot}",
            edge_width=1.65,
        )

    cargo_top_z = (
        pallet_h + len(layers) * box_vertical_h
        if layers
        else pallet_h
    )

    bounds = placement_bounds(layout["PLACEMENTS"])

    if layout["PLACEMENTS"]:
        min_x = bounds["MIN_X"]
        min_y = bounds["MIN_Y"]
        max_x = bounds["MAX_X"]
        max_y = bounds["MAX_Y"]

        used_w = max_x - min_x
        used_l = max_y - min_y

        if show_corner_guards and cargo_top_z > pallet_h:
            gx, gy, gz = [], [], []

            # Four vertical corner guards.
            for cx, cy in [
                (min_x, min_y),
                (max_x, min_y),
                (max_x, max_y),
                (min_x, max_y),
            ]:
                gx.extend([cx, cx, None])
                gy.extend([cy, cy, None])
                gz.extend([pallet_h, cargo_top_z, None])

            # Top perimeter / edge guards.
            top_points = [
                (min_x, min_y, cargo_top_z),
                (max_x, min_y, cargo_top_z),
                (max_x, max_y, cargo_top_z),
                (min_x, max_y, cargo_top_z),
                (min_x, min_y, cargo_top_z),
            ]

            gx.extend([p[0] for p in top_points])
            gy.extend([p[1] for p in top_points])
            gz.extend([p[2] for p in top_points])

            fig.add_trace(
                go.Scatter3d(
                    x=gx,
                    y=gy,
                    z=gz,
                    mode="lines",
                    line=dict(
                        color=guard_color,
                        width=8,
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                    name="Corner / edge guards",
                )
            )

        if show_straps and cargo_top_z > pallet_h:
            sx, sy, sz = [], [], []

            # Two straps around the Y direction.
            for x_pos in [
                min_x + used_w * 0.30,
                min_x + used_w * 0.70,
            ]:
                path = [
                    (x_pos, min_y, pallet_h),
                    (x_pos, min_y, cargo_top_z + 10),
                    (x_pos, max_y, cargo_top_z + 10),
                    (x_pos, max_y, pallet_h),
                ]
                sx.extend([p[0] for p in path] + [None])
                sy.extend([p[1] for p in path] + [None])
                sz.extend([p[2] for p in path] + [None])

            # Two straps around the X direction.
            for y_pos in [
                min_y + used_l * 0.30,
                min_y + used_l * 0.70,
            ]:
                path = [
                    (min_x, y_pos, pallet_h),
                    (max_x, y_pos, pallet_h),
                    (max_x, y_pos, cargo_top_z + 10),
                    (min_x, y_pos, cargo_top_z + 10),
                ]
                sx.extend([p[0] for p in path] + [None])
                sy.extend([p[1] for p in path] + [None])
                sz.extend([p[2] for p in path] + [None])

            fig.add_trace(
                go.Scatter3d(
                    x=sx,
                    y=sy,
                    z=sz,
                    mode="lines",
                    line=dict(
                        color=strap_color,
                        width=5,
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                    name="Securing straps",
                )
            )

    if show_height_plane:
        fig.add_trace(
            go.Mesh3d(
                x=[0, pallet_w, pallet_w, 0],
                y=[0, 0, pallet_l, pallet_l],
                z=[max_total_height] * 4,
                i=[0, 0],
                j=[1, 2],
                k=[2, 3],
                color="#dc2626",
                opacity=0.055,
                hoverinfo="skip",
                showscale=False,
                showlegend=False,
                name="Height limit",
            )
        )

    x_span = pallet_w + 2 * overhang_allowance
    y_span = pallet_l + 2 * overhang_allowance
    z_span = max_total_height
    base_max = max(x_span, y_span, z_span)

    margin = max(80.0, overhang_allowance + 45.0)

    fig.update_layout(
        scene=dict(
            xaxis=dict(
                title="Width (mm)",
                range=[-margin, pallet_w + margin],
                gridcolor="rgba(148,163,184,.22)",
                zeroline=False,
                showbackground=False,
                nticks=6,
            ),
            yaxis=dict(
                title="Length (mm)",
                range=[-margin, pallet_l + margin],
                gridcolor="rgba(148,163,184,.22)",
                zeroline=False,
                showbackground=False,
                nticks=6,
            ),
            zaxis=dict(
                title="Height (mm)",
                range=[0, max_total_height + 100],
                gridcolor="rgba(148,163,184,.22)",
                zeroline=False,
                showbackground=False,
                nticks=7,
            ),
            aspectmode="manual",
            aspectratio=dict(
                x=x_span / base_max,
                y=y_span / base_max,
                z=z_span / base_max,
            ),
            camera=dict(
                projection=dict(type="orthographic"),
                eye=dict(x=1.55, y=1.45, z=1.15),
                up=dict(x=0, y=0, z=1),
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(r=5, l=5, b=5, t=28),
        showlegend=False,
        height=650,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
        uirevision="v021-industrial-orthographic",
    )

    return fig


# =========================================================
# DISPLAY HELPERS
# =========================================================
def orientation_name(scenario):
    group = scenario["GROUP"]

    if group["NORMAL"]:
        return "Normal H-Up"

    return (
        f"{group['UP_AXIS']} Up — "
        "Non-normal"
    )


def status_chip(scenario):
    group = scenario["GROUP"]

    if group["ALLOWED"]:
        if group["NORMAL"]:
            return (
                '<span class="chip ok-chip">'
                '✅ H-Up Allowed'
                '</span>'
            )

        return (
            '<span class="chip warn-chip">'
            f'⚠️ {group["UP_AXIS"]}-Up Allowed'
            '</span>'
        )

    return (
        '<span class="chip locked-chip">'
        f'🔒 {group["UP_AXIS"]}-Up Locked'
        '</span>'
    )


def view_selection(
    scenario,
    key_prefix,
):
    geometry = scenario[
        "GEOMETRY_BEST"
    ]

    practical = scenario[
        "PRACTICAL_BEST"
    ]

    same_layout = (
        normalized_layout_key(
            geometry["PLACEMENTS"]
        )
        == normalized_layout_key(
            practical["PLACEMENTS"]
        )
    )

    if (
        same_layout
        and geometry["GEOMETRY_TOTAL"]
        == practical["SAFE_TOTAL"]
    ):
        return (
            practical,
            practical["SAFE_TOTAL"],
            "Recommended / Geometry",
        )

    default_index = 1

    choice = st.radio(
        "Layout View",
        [
            "Geometry Maximum",
            "Recommended Safe Load",
        ],
        index=default_index,
        horizontal=True,
        key=f"{key_prefix}_view",
    )

    if choice == "Geometry Maximum":
        return (
            geometry,
            geometry["GEOMETRY_TOTAL"],
            choice,
        )

    return (
        practical,
        practical["SAFE_TOTAL"],
        choice,
    )


def render_scenario(
    scenario,
    title,
    border_color,
    key_prefix,
):
    geometry = scenario[
        "GEOMETRY_BEST"
    ]

    practical = scenario[
        "PRACTICAL_BEST"
    ]

    st.subheader(title)

    chips = (
        f'<span class="chip">'
        f'Geometry Strategy: '
        f'{geometry["STRATEGY"]}'
        f'</span>'
        f'<span class="chip">'
        f'Complexity: '
        f'{geometry["COMPLEXITY"]}'
        f'</span>'
        f'{status_chip(scenario)}'
    )

    if (
        normalized_layout_key(
            geometry["PLACEMENTS"]
        )
        != normalized_layout_key(
            practical["PLACEMENTS"]
        )
    ):
        chips += (
            f'<span class="chip">'
            f'Safe Strategy: '
            f'{practical["STRATEGY"]}'
            f'</span>'
        )

    st.markdown(
        chips,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Geometry Best / Layer",
            f'{geometry["COUNT"]} ใบ',
        )

    with c2:
        st.metric(
            "Height-fit Layers",
            f'{geometry["HEIGHT_LAYERS"]} ชั้น',
        )

    with c3:
        st.metric(
            "Geometry Capacity",
            f'{geometry["GEOMETRY_TOTAL"]} ใบ',
        )

    with c4:
        delta = (
            practical["SAFE_TOTAL"]
            - geometry["GEOMETRY_TOTAL"]
        )

        st.metric(
            "Recommended Safe Load",
            f'{practical["SAFE_TOTAL"]} ใบ',
            delta=(
                f"{delta} from Geometry"
                if delta < 0
                else "ผ่าน Weight Limit"
            ),
        )

    if practical["SAFE_TOTAL"] <= 0:
        st.error(
            "❌ ไม่สามารถจัดวางกล่องได้ภายใต้ข้อจำกัดปัจจุบัน"
        )

    elif (
        geometry["GEOMETRY_GROSS_WEIGHT"]
        > max_pallet_gross_weight
    ):
        st.error(
            f"❌ Geometry Max "
            f"{geometry['GEOMETRY_TOTAL']} กล่อง "
            f"= {geometry['GEOMETRY_GROSS_WEIGHT']:,.1f} kg "
            f"ซึ่งเกิน Max Pallet Gross "
            f"{max_pallet_gross_weight:,.1f} kg"
        )

        st.warning(
            f"⚠️ Recommended Safe Load = "
            f"**{practical['SAFE_TOTAL']} กล่อง** "
            f"({practical['SAFE_GROSS_WEIGHT']:,.1f} kg) "
            f"ด้วย {practical['STRATEGY']}"
        )

    else:
        st.success(
            f"✅ Geometry Capacity "
            f"{geometry['GEOMETRY_TOTAL']} กล่อง "
            f"มี Gross Weight "
            f"{geometry['GEOMETRY_GROSS_WEIGHT']:,.1f} kg "
            f"และอยู่ใน Max Pallet Gross Weight"
        )

    display_layout, display_count, display_mode = (
        view_selection(
            scenario,
            key_prefix,
        )
    )

    d1, d2 = st.columns(2)

    with d1:
        st.metric(
            "Safe Gross Weight",
            f'{practical["SAFE_GROSS_WEIGHT"]:,.1f} kg',
        )

        st.metric(
            "Safe Total Height",
            f'{practical["SAFE_TOTAL_HEIGHT"]:,.0f} mm',
        )

        st.metric(
            "Carton Area Coverage",
            f'{display_layout["CARTON_AREA_COVERAGE"]:.1f}%',
        )

    with d2:
        st.metric(
            "Remaining Weight",
            f'{practical["REMAINING_WEIGHT_SAFE"]:,.1f} kg',
        )

        st.metric(
            "Remaining Height",
            f'{practical["REMAINING_HEIGHT_SAFE"]:,.0f} mm',
        )

        st.metric(
            "Primary Limiter",
            practical["PRIMARY_LIMITER"],
        )

    st.caption(
        f"Limiter detail: "
        f"{practical['LIMITER_DETAIL']}"
    )

    st.caption(
        f"Layout envelope span: "
        f"{display_layout['ENVELOPE_W']:.0f} × "
        f"{display_layout['ENVELOPE_L']:.0f} mm "
        f"({display_layout['ENVELOPE_COVERAGE']:.1f}% of pallet area) • "
        f"Actual carton area / allowed footprint: "
        f"{display_layout['ALLOWED_FOOTPRINT_UTIL']:.1f}%"
    )

    if overhang_allowance > 0:
        st.caption(
            "Actual overhang — "
            f"Left {display_layout['OVERHANG_LEFT']:.1f} mm • "
            f"Right {display_layout['OVERHANG_RIGHT']:.1f} mm • "
            f"Front {display_layout['OVERHANG_FRONT']:.1f} mm • "
            f"Back {display_layout['OVERHANG_BACK']:.1f} mm"
        )

    st.markdown(
        f"""
        <div class="smart-note">
            <b>{display_mode}</b> •
            Showing <b>{display_count} cartons</b> •
            Floor Strategy: <b>{display_layout["STRATEGY"]}</b> •
            Layer pattern: A {display_layout["A_COUNT"]} + B {display_layout["B_COUNT"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    visualization = st.radio(
        "Visualization",
        [
            "🔝 Smart Layer Pattern",
            "📐 Engineering Elevation",
            "🧊 Lightweight 3D",
        ],
        index=0,
        horizontal=True,
        key=f"{key_prefix}_visualization",
    )

    if visualization == "🔝 Smart Layer Pattern":
        st.markdown(
            generate_svg_layer(
                display_layout,
                border_color,
            ),
            unsafe_allow_html=True,
        )

        st.caption(
            f"สีส้ม = Rotation A ({scenario['GROUP']['A_NAME']}) • "
            f"สีฟ้า = Rotation B ({scenario['GROUP']['B_NAME']}) • "
            "ทั้งสองแบบยังคง Up Orientation เดียวกัน"
        )

    elif visualization == "📐 Engineering Elevation":
        st.markdown(
            generate_true_scale_elevation_svg(
                display_layout,
                display_count,
                scenario["GROUP"]["BOX_VERTICAL_H"],
            ),
            unsafe_allow_html=True,
        )

        st.caption(
            "Front / Side อยู่ใน SVG เดียวกันและใช้ physical scale เดียวกันทุกแกน • "
            "Hidden rear carton edges ถูกตัดออกจาก visible-face projection"
        )

        if (
            display_count
            % max(display_layout["COUNT"], 1)
            != 0
        ):
            st.caption(
                "Safe / displayed quantity มี Partial Top Layer; "
                "ตำแหน่งกล่องชั้นบนถูกเลือกให้ geometric centroid "
                "อยู่ใกล้กึ่งกลางพาเลท"
            )

    else:
        st.caption(
            "Orthographic industrial view • Kraft cartons + dark carton edges + red straps • "
            "3D จะถูกสร้างเฉพาะเมื่อเลือก View นี้เพื่อลดเวลา rerun"
        )

        fig = generate_plotly_3d(
            display_layout,
            display_count,
            scenario["GROUP"]["BOX_VERTICAL_H"],
        )

        if fig is not None:
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displaylogo": False,
                    "scrollZoom": True,
                },
            )

        st.caption(
            "Corner Guards / Straps เป็น 3D illustration เพื่อช่วยสื่อสารเท่านั้น "
            "ไม่ใช่ Packaging requirement recommendation"
        )


# =========================================================
# WORKING CONDITION SUMMARY
# =========================================================
st.markdown(
    "### 🧱 Palletizing Working Condition"
)

wc1, wc2, wc3, wc4 = st.columns(4)

with wc1:
    st.metric(
        "Carton",
        (
            f"{box_w:.0f} × "
            f"{box_l:.0f} × "
            f"{box_h:.0f} mm"
        ),
    )

with wc2:
    st.metric(
        "Pallet",
        (
            f"{pallet_w:.0f} × "
            f"{pallet_l:.0f} × "
            f"{pallet_h:.0f} mm"
        ),
    )

with wc3:
    st.metric(
        "Max Total Height",
        f"{max_total_height:,.0f} mm",
    )

with wc4:
    st.metric(
        "Max Pallet Gross",
        f"{max_pallet_gross_weight:,.1f} kg",
    )

st.caption(
    f"Carton gross weight: "
    f"{box_weight:,.2f} kg • "
    f"Pallet tare: "
    f"{pallet_tare_weight:,.1f} kg • "
    f"Gap: {box_tolerance:.1f} mm • "
    f"Allowed overhang: "
    f"{overhang_allowance:.1f} mm/side"
)

allowed_text = []

if allow_h_up:
    allowed_text.append("H-Up")

if allow_l_up:
    allowed_text.append("L-Up")

if allow_w_up:
    allowed_text.append("W-Up")

st.info(
    "Allowed Carton Orientation: "
    + ", ".join(allowed_text)
)

total_layouts = sum(
    s["LAYOUT_COUNT"]
    for s in scenarios
)

st.caption(
    f"V0.2.1 evaluated {total_layouts} unique floor layouts "
    "from Simple Grid, Mixed Rows, Mixed Columns"
    + (
        ", Residual L-Fill"
        if advanced_residual_search
        else ""
    )
    + " across H-Up / L-Up / W-Up scenarios."
)

st.divider()


# =========================================================
# ADAPTIVE RESULT UI
# =========================================================
if (
    normal_scenario is not None
    and best_alternative_scenario is not None
):
    normal_safe = (
        normal_scenario[
            "PRACTICAL_BEST"
        ]["SAFE_TOTAL"]
    )

    alternative_safe = (
        best_alternative_scenario[
            "PRACTICAL_BEST"
        ]["SAFE_TOTAL"]
    )

    if alternative_safe > normal_safe:
        extra = (
            alternative_safe
            - normal_safe
        )

        gain_pct = (
            extra
            / normal_safe
            * 100.0
            if normal_safe > 0
            else 0.0
        )

        st.warning(
            f"⚠️ Best Alternative "
            f"{best_alternative_scenario['GROUP']['UP_AXIS']}-Up "
            f"เพิ่ม Safe Capacity ได้ "
            f"**+{extra} กล่อง (+{gain_pct:.1f}%)** "
            "แต่ต้องใช้ Non-normal carton orientation"
        )

        left, right = st.columns(2)

        with left:
            render_scenario(
                normal_scenario,
                "✅ Normal H-Up Reference",
                "#16a34a",
                "normal_compare",
            )

        with right:
            render_scenario(
                best_alternative_scenario,
                "⚠️ Higher Capacity Alternative",
                "#2563eb",
                "alternative_compare",
            )

    elif alternative_safe == normal_safe:
        st.success(
            f"✅ Recommended: **Normal H-Up — {normal_safe} cartons/pallet**. "
            f"Alternative "
            f"{best_alternative_scenario['GROUP']['UP_AXIS']}-Up "
            "ให้ Safe Capacity เท่ากัน จึงไม่มี Capacity Benefit "
            "จากการเปลี่ยน Up Orientation"
        )

        render_scenario(
            normal_scenario,
            "✅ Best & Recommended — Normal H-Up",
            "#16a34a",
            "normal_single",
        )

        with st.expander(
            "🔄 View Best Alternative — Same Safe Capacity",
            expanded=False,
        ):
            render_scenario(
                best_alternative_scenario,
                (
                    "Alternative — "
                    f"{best_alternative_scenario['GROUP']['UP_AXIS']} Up"
                ),
                "#2563eb",
                "alternative_same",
            )

    else:
        diff = (
            normal_safe
            - alternative_safe
        )

        st.success(
            f"✅ Recommended: **Normal H-Up — {normal_safe} cartons/pallet**. "
            f"Best allowed Alternative ต่ำกว่า {diff} กล่อง/pallet"
        )

        render_scenario(
            normal_scenario,
            "✅ Best & Recommended — Normal H-Up",
            "#16a34a",
            "normal_best",
        )

        with st.expander(
            "🔎 View Best Allowed Alternative",
            expanded=False,
        ):
            render_scenario(
                best_alternative_scenario,
                (
                    "Alternative — "
                    f"{best_alternative_scenario['GROUP']['UP_AXIS']} Up"
                ),
                "#2563eb",
                "alternative_lower",
            )

elif normal_scenario is not None:
    normal_safe = (
        normal_scenario[
            "PRACTICAL_BEST"
        ]["SAFE_TOTAL"]
    )

    st.success(
        f"✅ Recommended: **Normal H-Up — {normal_safe} cartons/pallet**. "
        "Non-normal Up Orientations ยังไม่ได้รับอนุญาต "
        "จึงไม่ถูกนำมาใช้ในการ Recommendation"
    )

    render_scenario(
        normal_scenario,
        "✅ Best & Recommended — Normal H-Up",
        "#16a34a",
        "normal_only",
    )

else:
    chosen = best_overall_scenario
    chosen_safe = (
        chosen[
            "PRACTICAL_BEST"
        ]["SAFE_TOTAL"]
    )

    st.warning(
        f"⚠️ H-Up ไม่ได้ถูกอนุญาตในเงื่อนไขปัจจุบัน "
        f"Recommendation จึงใช้ "
        f"**{chosen['GROUP']['UP_AXIS']}-Up — "
        f"{chosen_safe} cartons/pallet**"
    )

    render_scenario(
        chosen,
        (
            "⚠️ Recommended Allowed Layout — "
            f"{chosen['GROUP']['UP_AXIS']} Up"
        ),
        "#2563eb",
        "alternative_only",
    )


# =========================================================
# RECOMMENDATION SUMMARY
# =========================================================
st.divider()
st.subheader("🧭 Recommendation Summary")

recommended_scenario = (
    best_overall_scenario
)

# Normal wins safe-capacity ties across Up Orientation.
if normal_scenario is not None:
    if (
        normal_scenario[
            "PRACTICAL_BEST"
        ]["SAFE_TOTAL"]
        == best_overall_scenario[
            "PRACTICAL_BEST"
        ]["SAFE_TOTAL"]
    ):
        recommended_scenario = (
            normal_scenario
        )

rec = recommended_scenario[
    "PRACTICAL_BEST"
]

geom_rec = recommended_scenario[
    "GEOMETRY_BEST"
]

r1, r2, r3, r4 = st.columns(4)

with r1:
    st.metric(
        "Recommended Safe",
        f'{rec["SAFE_TOTAL"]} cartons',
    )

with r2:
    st.metric(
        "Recommended / Layer",
        rec["COUNT"],
    )

with r3:
    st.metric(
        "Safe Layers Used",
        rec["SAFE_LAYERS_USED"],
    )

with r4:
    st.metric(
        "Recommended Orientation",
        orientation_name(
            recommended_scenario
        ),
    )

r5, r6, r7, r8 = st.columns(4)

with r5:
    st.metric(
        "Safe Gross Weight",
        f'{rec["SAFE_GROSS_WEIGHT"]:,.1f} kg',
    )

with r6:
    st.metric(
        "Safe Total Height",
        f'{rec["SAFE_TOTAL_HEIGHT"]:,.0f} mm',
    )

with r7:
    st.metric(
        "Carton Area Coverage",
        f'{rec["CARTON_AREA_COVERAGE"]:.1f}%',
    )

with r8:
    st.metric(
        "Primary Limiter",
        rec["PRIMARY_LIMITER"],
    )

st.caption(
    f"Recommended floor strategy: "
    f"{rec['STRATEGY']} • "
    f"Geometry-best strategy: "
    f"{geom_rec['STRATEGY']} • "
    f"{rec['LIMITER_DETAIL']}"
)

if (
    normalized_layout_key(
        rec["PLACEMENTS"]
    )
    != normalized_layout_key(
        geom_rec["PLACEMENTS"]
    )
):
    st.info(
        f"💡 Geometry Best = "
        f"{geom_rec['COUNT']} cartons/layer "
        f"ด้วย {geom_rec['STRATEGY']}, "
        f"แต่ Practical Safe Recommendation เลือก "
        f"{rec['STRATEGY']} เพราะให้ Safe Qty เท่ากัน "
        "ด้วยรูปแบบที่เรียบง่าย / practical กว่า"
    )

if not recommended_scenario[
    "GROUP"
]["NORMAL"]:
    st.warning(
        "⚠️ Recommended Capacity ต้องใช้ Non-normal carton orientation. "
        "ก่อนใช้จริงควรยืนยัน Product orientation, internal support, "
        "customer requirement, label orientation และ handling risk"
    )


# =========================================================
# UP-ORIENTATION SCENARIO EXPLORER
# =========================================================
st.divider()
st.subheader(
    "📊 Up-Orientation Scenario Explorer"
)

scenario_rows = []

for scenario in scenarios:
    group = scenario["GROUP"]
    geom = scenario["GEOMETRY_BEST"]
    practical = scenario["PRACTICAL_BEST"]

    if group["ALLOWED"]:
        status = "✅ Allowed"
    else:
        status = "🔒 Locked"

    note = []

    if group["NORMAL"]:
        note.append("Normal H-Up")
    else:
        note.append("Non-normal")

    if (
        scenario is recommended_scenario
    ):
        note.append("Recommended")

    if (
        geom["STRATEGY"]
        != practical["STRATEGY"]
    ):
        note.append(
            "Geometry/Safe strategy differ"
        )

    scenario_rows.append(
        {
            "Up Axis": group["UP_AXIS"],
            "Status": status,
            "Geometry Strategy": geom["STRATEGY"],
            "Geometry / Layer": geom["COUNT"],
            "Practical Strategy": practical["STRATEGY"],
            "Safe / Layer": practical["COUNT"],
            "Height Layers": geom["HEIGHT_LAYERS"],
            "Geometry Qty": geom["GEOMETRY_TOTAL"],
            "Safe Qty": practical["SAFE_TOTAL"],
            "Safe Height": f'{practical["SAFE_TOTAL_HEIGHT"]:.0f}',
            "Safe Gross kg": f'{practical["SAFE_GROSS_WEIGHT"]:.1f}',
            "Area Coverage %": f'{practical["CARTON_AREA_COVERAGE"]:.1f}',
            "Limiter": practical["PRIMARY_LIMITER"],
            "Layouts Tested": scenario["LAYOUT_COUNT"],
            "Note": " • ".join(note),
        }
    )

st.dataframe(
    scenario_rows,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# LAYOUT SEARCH EXPLORER
# =========================================================
with st.expander(
    f"🔎 Layouts evaluated by {APP_VERSION}",
    expanded=False,
):
    search_rows = []

    for scenario in scenarios:
        group = scenario["GROUP"]

        sorted_candidates = sorted(
            scenario["EVALUATED"],
            key=geometry_candidate_key,
            reverse=True,
        )

        for item in sorted_candidates:
            search_rows.append(
                {
                    "Up Axis": group["UP_AXIS"],
                    "Allowed": (
                        "Yes"
                        if group["ALLOWED"]
                        else "No"
                    ),
                    "Strategy": item["STRATEGY"],
                    "Complexity": item["COMPLEXITY"],
                    "A Count": item["A_COUNT"],
                    "B Count": item["B_COUNT"],
                    "Boxes / Layer": item["COUNT"],
                    "Height Layers": item["HEIGHT_LAYERS"],
                    "Geometry Qty": item["GEOMETRY_TOTAL"],
                    "Safe Qty": item["SAFE_TOTAL"],
                    "Safe Height": f'{item["SAFE_TOTAL_HEIGHT"]:.0f}',
                    "Safe Gross kg": f'{item["SAFE_GROSS_WEIGHT"]:.1f}',
                    "Area Coverage %": f'{item["CARTON_AREA_COVERAGE"]:.1f}',
                    "Envelope %": f'{item["ENVELOPE_COVERAGE"]:.1f}',
                    "Limiter": item["PRIMARY_LIMITER"],
                }
            )

    st.dataframe(
        search_rows,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# ENGINEERING NOTE
# =========================================================
with st.expander(
    "ℹ️ ขอบเขตการคำนวณ / Engineering Note",
    expanded=False,
):
    st.markdown(
        """
        **V0.2.1 Visualization & Performance Update**

        - **Smart Floor Solver ใช้ Logic เดิมจาก V0.2** และยังประเมิน Floor Pattern หลาย Strategy ภายใน Up Orientation เดียวกัน:
          **Simple Grid, Mixed Rows, Mixed Columns และ Residual L-Fill**.
        - Rotation A / B ใน Layer Pattern คือการหมุนกล่องบนพื้น 90° เท่านั้น
          และ **ไม่ได้เปลี่ยน H-Up / L-Up / W-Up**.
        - Up Orientation ที่ไม่ได้รับอนุญาตจะยังถูกคำนวณเพื่อ Reference ใน Explorer
          แต่ **ไม่ถูกใช้ใน Recommendation**.
        - Default คือ **H-Up only** เพื่อไม่ให้ App สมมติเองว่าสินค้าสามารถนอนตะแคงได้.
        - Geometry Capacity พิจารณา Floor Pattern + Height Limit.
        - Recommended Safe Load เพิ่มข้อจำกัด **Max Pallet Gross Weight**.
        - เมื่อ Weight Limit ทำให้ Safe Qty เท่ากันหลาย Layout,
          V0.2 สามารถเลือก Pattern ที่เรียบง่ายกว่าเป็น Practical Recommendation.
        - Partial Top Layer ใช้ geometric-balance selection เพื่อให้ centroid ของกล่องชั้นบน
          อยู่ใกล้กึ่งกลางพาเลท; นี่ **ไม่ใช่ Center-of-Gravity calculation**.
        - **Carton Area Coverage** = ผลรวมพื้นที่ footprint จริงของกล่องต่อชั้น / พื้นที่พาเลท.
        - **Layout Envelope** เป็น span ของ pattern รวมช่องว่าง และไม่ถูกใช้แทน Carton Area Coverage.
        - Allowed Overhang ถูกคิดแบบสมมาตรทั้ง 4 ด้าน.
        - Carton Area Coverage สามารถเกิน 100% ได้เมื่อเปิด Overhang; จึงมี
          Actual carton area / allowed footprint แสดงแยกในรายละเอียด.
        - Engineering Elevation ใช้ **True relative physical scale** สำหรับ W / L / H และใช้ visible-face projection เพื่อตัด hidden rear edges.
        - Lightweight 3D รวม carton meshes / edges เป็น grouped traces, ใช้ orthographic camera และ render เฉพาะเมื่อผู้ใช้เลือก 3D View.
        - 3D Corner Guards / Straps เป็น **Illustration only** ไม่ใช่ระบบคำนวณหรือ Recommendation.
        - V0.2 ยังไม่พิจารณา Compression Strength, Box Stacking Strength,
          Column-vs-Interlock structural performance, Slip Sheet, Stretch Film,
          Required Edge Margin, Forklift Handling, CG, Transport Dynamic Load
          หรือ Pallet Deck Strength.
        """
    )
