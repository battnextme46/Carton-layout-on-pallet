
import math
from itertools import combinations

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================
APP_VERSION = "V0.1"
MODULE_NAME = "Module 02 — Carton Palletizing Optimizer"

st.set_page_config(
    page_title=f"Carton Palletizing Optimizer {APP_VERSION}",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 2rem;
        }

        .result-banner {
            padding: 0.9rem 1rem;
            border-radius: 0.65rem;
            margin: 0.35rem 0 1rem 0;
            border: 1px solid rgba(148,163,184,.25);
            background: rgba(15,23,42,.35);
        }

        .result-banner strong {
            font-size: 1rem;
        }

        .small-note {
            font-size: .84rem;
            opacity: .78;
        }

        .chip {
            display: inline-block;
            padding: .18rem .48rem;
            margin-right: .3rem;
            margin-bottom: .25rem;
            border: 1px solid rgba(148,163,184,.45);
            border-radius: 999px;
            font-size: .76rem;
        }

        .warn-chip {
            border-color: rgba(245,158,11,.65);
        }

        .ok-chip {
            border-color: rgba(34,197,94,.65);
        }

        .locked-chip {
            border-color: rgba(239,68,68,.55);
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
    "— Engineering Rebuild / Orientation-aware / Weight-aware / Adaptive Result UI"
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
# SIDEBAR — TOLERANCES
# =========================================================
st.sidebar.header("4. ระยะเผื่อ (Tolerances - mm)")

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

st.sidebar.caption(
    "V0.1 ใช้ Allowed Overhang แบบสมมาตรทั้ง 4 ด้าน "
    "และยังไม่รวม Required Edge Margin"
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
# VALIDATION
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


# =========================================================
# ORIENTATION DEFINITIONS
# =========================================================
# Up-axis determines which original carton dimension becomes vertical.
ORIENTATION_GROUPS = [
    {
        "up_axis": "H",
        "allowed": allow_h_up,
        "normal": True,
        "label": "H Up — Normal",
        "orientations": [
            ("W×L×H", box_w, box_l, box_h),
            ("L×W×H", box_l, box_w, box_h),
        ],
    },
    {
        "up_axis": "L",
        "allowed": allow_l_up,
        "normal": False,
        "label": "L Up — Side Orientation",
        "orientations": [
            ("W×H×L", box_w, box_h, box_l),
            ("H×W×L", box_h, box_w, box_l),
        ],
    },
    {
        "up_axis": "W",
        "allowed": allow_w_up,
        "normal": False,
        "label": "W Up — Side Orientation",
        "orientations": [
            ("L×H×W", box_l, box_h, box_w),
            ("H×L×W", box_h, box_l, box_w),
        ],
    },
]


# =========================================================
# CALCULATION ENGINE — V0.1 SIMPLE GRID
# =========================================================
def calculate_case(
    case_name,
    up_axis,
    floor_box_w,
    floor_box_l,
    box_vertical_h,
    is_normal,
    orientation_allowed,
):
    effective_box_w = floor_box_w + box_tolerance
    effective_box_l = floor_box_l + box_tolerance

    allowable_w = pallet_w + (2 * overhang_allowance)
    allowable_l = pallet_l + (2 * overhang_allowance)

    slots_w = int(math.floor(allowable_w / effective_box_w))
    slots_l = int(math.floor(allowable_l / effective_box_l))
    boxes_per_layer = max(slots_w, 0) * max(slots_l, 0)

    height_layers = (
        int(math.floor(available_cargo_height / box_vertical_h))
        if box_vertical_h > 0
        else 0
    )

    geometry_total = boxes_per_layer * height_layers

    available_weight_for_cartons = (
        max_pallet_gross_weight - pallet_tare_weight
    )

    weight_capacity = max(
        int(math.floor(available_weight_for_cartons / box_weight)),
        0,
    )

    safe_total = min(geometry_total, weight_capacity)

    safe_layers_used = (
        int(math.ceil(safe_total / boxes_per_layer))
        if safe_total > 0 and boxes_per_layer > 0
        else 0
    )

    full_safe_layers = (
        safe_total // boxes_per_layer
        if boxes_per_layer > 0
        else 0
    )

    partial_top_layer_qty = (
        safe_total % boxes_per_layer
        if boxes_per_layer > 0
        else 0
    )

    geometry_total_height = (
        pallet_h + (height_layers * box_vertical_h)
        if geometry_total > 0
        else pallet_h
    )

    safe_total_height = (
        pallet_h + (safe_layers_used * box_vertical_h)
        if safe_total > 0
        else pallet_h
    )

    geometry_gross_weight = (
        pallet_tare_weight + geometry_total * box_weight
    )

    safe_gross_weight = (
        pallet_tare_weight + safe_total * box_weight
    )

    used_w = (
        slots_w * effective_box_w - box_tolerance
        if slots_w > 0
        else 0.0
    )

    used_l = (
        slots_l * effective_box_l - box_tolerance
        if slots_l > 0
        else 0.0
    )

    pallet_area = pallet_w * pallet_l
    allowed_area = allowable_w * allowable_l
    used_area = used_w * used_l

    pallet_coverage = (
        used_area / pallet_area * 100.0
        if pallet_area > 0 and boxes_per_layer > 0
        else 0.0
    )

    allowed_footprint_util = (
        used_area / allowed_area * 100.0
        if allowed_area > 0 and boxes_per_layer > 0
        else 0.0
    )

    actual_overhang_w_each_side = max(
        (used_w - pallet_w) / 2.0,
        0.0,
    )

    actual_overhang_l_each_side = max(
        (used_l - pallet_l) / 2.0,
        0.0,
    )

    remaining_height_safe = max(
        max_total_height - safe_total_height,
        0.0,
    )

    remaining_weight_safe = max(
        max_pallet_gross_weight - safe_gross_weight,
        0.0,
    )

    if not orientation_allowed:
        primary_limiter = "Orientation Locked"
    elif boxes_per_layer <= 0:
        primary_limiter = "Floor Space"
    elif height_layers <= 0:
        primary_limiter = "Height"
    elif weight_capacity < geometry_total:
        primary_limiter = "Pallet Gross Weight"
    else:
        primary_limiter = "Geometry (Floor + Height)"

    return {
        "CASE_NAME": case_name,
        "UP_AXIS": up_axis,
        "NORMAL": is_normal,
        "ALLOWED": orientation_allowed,
        "FLOOR_BOX_W": floor_box_w,
        "FLOOR_BOX_L": floor_box_l,
        "BOX_VERTICAL_H": box_vertical_h,
        "SLOTS_W": slots_w,
        "SLOTS_L": slots_l,
        "BOXES_PER_LAYER": boxes_per_layer,
        "HEIGHT_LAYERS": height_layers,
        "GEOMETRY_TOTAL": geometry_total,
        "WEIGHT_CAPACITY": weight_capacity,
        "SAFE_TOTAL": safe_total,
        "SAFE_LAYERS_USED": safe_layers_used,
        "FULL_SAFE_LAYERS": full_safe_layers,
        "PARTIAL_TOP_LAYER_QTY": partial_top_layer_qty,
        "GEOMETRY_TOTAL_HEIGHT": geometry_total_height,
        "SAFE_TOTAL_HEIGHT": safe_total_height,
        "GEOMETRY_GROSS_WEIGHT": geometry_gross_weight,
        "SAFE_GROSS_WEIGHT": safe_gross_weight,
        "USED_W": used_w,
        "USED_L": used_l,
        "PALLET_COVERAGE": pallet_coverage,
        "ALLOWED_FOOTPRINT_UTIL": allowed_footprint_util,
        "ACTUAL_OVERHANG_W": actual_overhang_w_each_side,
        "ACTUAL_OVERHANG_L": actual_overhang_l_each_side,
        "REMAINING_HEIGHT_SAFE": remaining_height_safe,
        "REMAINING_WEIGHT_SAFE": remaining_weight_safe,
        "PRIMARY_LIMITER": primary_limiter,
        "LAYOUT_STRATEGY": "Simple Grid",
    }


all_cases = []

for group in ORIENTATION_GROUPS:
    for (
        case_name,
        floor_box_w,
        floor_box_l,
        box_vertical_h,
    ) in group["orientations"]:
        all_cases.append(
            calculate_case(
                case_name=case_name,
                up_axis=group["up_axis"],
                floor_box_w=floor_box_w,
                floor_box_l=floor_box_l,
                box_vertical_h=box_vertical_h,
                is_normal=group["normal"],
                orientation_allowed=group["allowed"],
            )
        )


# =========================================================
# CASE RANKING / RECOMMENDATION
# =========================================================
def recommendation_key(case):
    """
    Higher is better.

    V0.1 rule:
    1) Safe quantity first
    2) Prefer Normal H-Up when quantity ties
    3) Lower safe pallet height
    4) Higher allowed-footprint utilization
    5) Higher boxes/layer
    """
    return (
        case["SAFE_TOTAL"],
        1 if case["NORMAL"] else 0,
        -case["SAFE_TOTAL_HEIGHT"],
        case["ALLOWED_FOOTPRINT_UTIL"],
        case["BOXES_PER_LAYER"],
    )


allowed_cases = [
    c
    for c in all_cases
    if c["ALLOWED"]
]

allowed_cases.sort(
    key=recommendation_key,
    reverse=True,
)

best_overall = allowed_cases[0]

normal_allowed_cases = [
    c
    for c in allowed_cases
    if c["NORMAL"]
]

alternative_allowed_cases = [
    c
    for c in allowed_cases
    if not c["NORMAL"]
]

best_normal = (
    max(normal_allowed_cases, key=recommendation_key)
    if normal_allowed_cases
    else None
)

best_alternative = (
    max(alternative_allowed_cases, key=recommendation_key)
    if alternative_allowed_cases
    else None
)


# =========================================================
# LAYER PLACEMENT HELPERS
# =========================================================
def full_layer_positions(case):
    if case["BOXES_PER_LAYER"] <= 0:
        return []

    effective_box_w = case["FLOOR_BOX_W"] + box_tolerance
    effective_box_l = case["FLOOR_BOX_L"] + box_tolerance

    allowable_w = pallet_w + (2 * overhang_allowance)
    allowable_l = pallet_l + (2 * overhang_allowance)

    allowed_x0 = -overhang_allowance
    allowed_y0 = -overhang_allowance

    group_w = case["USED_W"]
    group_l = case["USED_L"]

    start_x = (
        allowed_x0
        + (allowable_w - group_w) / 2.0
    )

    start_y = (
        allowed_y0
        + (allowable_l - group_l) / 2.0
    )

    positions = []

    for i in range(case["SLOTS_W"]):
        for j in range(case["SLOTS_L"]):
            positions.append(
                {
                    "x": start_x + i * effective_box_w,
                    "y": start_y + j * effective_box_l,
                    "w": case["FLOOR_BOX_W"],
                    "l": case["FLOOR_BOX_L"],
                }
            )

    return positions


def centered_subset(positions, qty):
    if qty <= 0:
        return []

    if qty >= len(positions):
        return [p.copy() for p in positions]

    cx = pallet_w / 2.0
    cy = pallet_l / 2.0

    ranked = sorted(
        positions,
        key=lambda p: (
            (p["x"] + p["w"] / 2.0 - cx) ** 2
            + (p["y"] + p["l"] / 2.0 - cy) ** 2
        ),
    )

    return [p.copy() for p in ranked[:qty]]


def build_display_stack(case, carton_count):
    """
    Returns a list of layers.
    Every layer contains carton positions.

    Full layers use the complete Simple Grid pattern.
    A partial final layer uses cartons nearest the pallet center.
    """
    if carton_count <= 0 or case["BOXES_PER_LAYER"] <= 0:
        return []

    base_pattern = full_layer_positions(case)

    full_layers = carton_count // case["BOXES_PER_LAYER"]
    remainder = carton_count % case["BOXES_PER_LAYER"]

    layers = []

    for _ in range(full_layers):
        layers.append([p.copy() for p in base_pattern])

    if remainder > 0:
        layers.append(
            centered_subset(base_pattern, remainder)
        )

    return layers


# =========================================================
# SVG TOP VIEW — FULL LAYER PATTERN
# =========================================================
def generate_svg_pallet_layer(case, color_theme):
    pad = max(pallet_w, pallet_l) * 0.11
    view_w = pallet_w + (2 * overhang_allowance) + (2 * pad)
    view_h = pallet_l + (2 * overhang_allowance) + (2 * pad)

    origin_x = pad + overhang_allowance
    origin_y = pad + overhang_allowance

    svg = (
        f'<svg width="100%" height="auto" '
        f'viewBox="0 0 {view_w} {view_h}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="background:#ffffff;border:2px solid #cbd5e1;'
        f'border-radius:12px;">'
    )

    # Allowed footprint including overhang.
    if overhang_allowance > 0:
        svg += (
            f'<rect x="{pad}" y="{pad}" '
            f'width="{pallet_w + 2*overhang_allowance}" '
            f'height="{pallet_l + 2*overhang_allowance}" '
            f'fill="none" stroke="#94a3b8" stroke-width="3" '
            f'stroke-dasharray="10,8" rx="8"/>'
        )

    # Physical pallet.
    svg += (
        f'<rect x="{origin_x}" y="{origin_y}" '
        f'width="{pallet_w}" height="{pallet_l}" '
        f'fill="#f8fafc" stroke="{color_theme}" '
        f'stroke-width="6" rx="8"/>'
    )

    positions = full_layer_positions(case)

    for p in positions:
        x = origin_x + p["x"]
        y = origin_y + p["y"]

        svg += (
            f'<rect x="{x}" y="{y}" '
            f'width="{p["w"]}" height="{p["l"]}" '
            f'fill="#ffedd5" stroke="#ea580c" '
            f'stroke-width="2" rx="4"/>'
        )

        label_size = max(
            13,
            min(24, int(min(p["w"], p["l"]) * 0.09)),
        )

        svg += (
            f'<text x="{x + p["w"]/2}" '
            f'y="{y + p["l"]/2 + label_size/3}" '
            f'font-family="system-ui,sans-serif" '
            f'font-size="{label_size}" '
            f'font-weight="700" fill="#9a3412" '
            f'text-anchor="middle">'
            f'{int(p["w"])}×{int(p["l"])}'
            f'</text>'
        )

    # Dimensions.
    svg += (
        f'<text x="{origin_x + pallet_w/2}" '
        f'y="{view_h - 20}" '
        f'font-size="24" font-weight="700" '
        f'fill="#334155" text-anchor="middle">'
        f'Pallet W: {int(pallet_w)} mm'
        f'</text>'
    )

    svg += (
        f'<text x="25" '
        f'y="{origin_y + pallet_l/2}" '
        f'font-size="24" font-weight="700" '
        f'fill="#334155" text-anchor="middle" '
        f'transform="rotate(-90,25,{origin_y + pallet_l/2})">'
        f'Pallet L: {int(pallet_l)} mm'
        f'</text>'
    )

    svg += "</svg>"

    return svg


# =========================================================
# 2D SIDE VIEW
# =========================================================
def generate_2d_side_view(
    case,
    carton_count,
    color_theme,
    view_type="front",
):
    layers = build_display_stack(case, carton_count)

    fig, ax = plt.subplots(figsize=(8, 4.8))

    if view_type == "front":
        total_dim = pallet_w
        axis_label = "Width (mm)"
        title = "Front View — Pallet Width Axis"
        floor_dim = case["FLOOR_BOX_W"]
        coord_key = "x"
    else:
        total_dim = pallet_l
        axis_label = "Length (mm)"
        title = "Side View — Pallet Length Axis"
        floor_dim = case["FLOOR_BOX_L"]
        coord_key = "y"

    ax.add_patch(
        plt.Rectangle(
            (0, 0),
            total_dim,
            pallet_h,
            facecolor="#cbd5e1",
            edgecolor="#475569",
            linewidth=1.5,
        )
    )

    ax.text(
        total_dim / 2,
        pallet_h / 2,
        f"Pallet H: {int(pallet_h)} mm",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
    )

    for layer_idx, layer_positions in enumerate(layers):
        z = pallet_h + layer_idx * case["BOX_VERTICAL_H"]

        # Side view uses unique projected carton coordinates.
        projected = sorted(
            {
                round(p[coord_key], 6)
                for p in layer_positions
            }
        )

        for coord in projected:
            ax.add_patch(
                plt.Rectangle(
                    (coord, z),
                    floor_dim,
                    case["BOX_VERTICAL_H"],
                    facecolor="#ffedd5",
                    edgecolor="#ea580c",
                    linewidth=1.2,
                )
            )

    display_height = (
        pallet_h
        + len(layers) * case["BOX_VERTICAL_H"]
        if layers
        else pallet_h
    )

    ax.axhline(
        y=max_total_height,
        linestyle="--",
        linewidth=2,
        label=f"Height Limit ({int(max_total_height)} mm)",
    )

    ax.axhline(
        y=display_height,
        linewidth=2,
        label=f"Displayed Load Height ({int(display_height)} mm)",
    )

    ax.set_xlim(
        -max(50, overhang_allowance + 20),
        total_dim + max(50, overhang_allowance + 20),
    )

    ax.set_ylim(
        0,
        max_total_height + max(120, case["BOX_VERTICAL_H"] * 0.6),
    )

    ax.set_title(title)
    ax.set_xlabel(axis_label)
    ax.set_ylabel("Height (mm)")
    ax.grid(axis="y", linestyle=":", alpha=0.55)
    ax.legend(loc="upper right")
    plt.tight_layout()

    return fig


# =========================================================
# PLOTLY 3D
# =========================================================
def draw_plotly_cube(
    fig,
    x,
    y,
    z,
    dx,
    dy,
    dz,
    color,
    line_color,
    opacity=1.0,
):
    fig.add_trace(
        go.Mesh3d(
            x=[x, x+dx, x+dx, x, x, x+dx, x+dx, x],
            y=[y, y, y+dy, y+dy, y, y, y+dy, y+dy],
            z=[z, z, z, z, z+dz, z+dz, z+dz, z+dz],
            i=[7, 0, 0, 0, 4, 4, 3, 3, 0, 0, 1, 1],
            j=[3, 4, 1, 2, 5, 6, 2, 7, 5, 4, 2, 6],
            k=[0, 7, 2, 3, 6, 7, 1, 6, 1, 5, 6, 5],
            color=color,
            opacity=opacity,
            flatshading=True,
            showscale=False,
            hoverinfo="skip",
            lighting=dict(
                ambient=1.0,
                diffuse=0.0,
                specular=0.0,
                roughness=1.0,
                fresnel=0.0,
            ),
        )
    )

    if opacity >= 0.95:
        edges = [
            ([x, x+dx], [y, y], [z, z]),
            ([x, x], [y, y+dy], [z, z]),
            ([x+dx, x+dx], [y, y+dy], [z, z]),
            ([x, x+dx], [y+dy, y+dy], [z, z]),
            ([x, x+dx], [y, y], [z+dz, z+dz]),
            ([x, x], [y, y+dy], [z+dz, z+dz]),
            ([x+dx, x+dx], [y, y+dy], [z+dz, z+dz]),
            ([x, x+dx], [y+dy, y+dy], [z+dz, z+dz]),
            ([x, x], [y, y], [z, z+dz]),
            ([x+dx, x+dx], [y, y], [z, z+dz]),
            ([x, x], [y+dy, y+dy], [z, z+dz]),
            ([x+dx, x+dx], [y+dy, y+dy], [z, z+dz]),
        ]

        for edge in edges:
            fig.add_trace(
                go.Scatter3d(
                    x=edge[0],
                    y=edge[1],
                    z=edge[2],
                    mode="lines",
                    line=dict(
                        color=line_color,
                        width=2,
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )


def generate_plotly_3d(case, carton_count, color_theme, edge_theme):
    if carton_count <= 0:
        return None

    fig = go.Figure()

    # Pallet base.
    draw_plotly_cube(
        fig,
        0,
        0,
        0,
        pallet_w,
        pallet_l,
        pallet_h,
        "#cbd5e1",
        "#475569",
    )

    layers = build_display_stack(case, carton_count)

    for layer_idx, layer_positions in enumerate(layers):
        z = pallet_h + layer_idx * case["BOX_VERTICAL_H"]

        for p in layer_positions:
            draw_plotly_cube(
                fig,
                p["x"],
                p["y"],
                z,
                p["w"],
                p["l"],
                case["BOX_VERTICAL_H"],
                color_theme,
                edge_theme,
            )

    cargo_top_z = (
        pallet_h + len(layers) * case["BOX_VERTICAL_H"]
        if layers
        else pallet_h
    )

    # Approximate load envelope for accessory illustration.
    positions = full_layer_positions(case)

    if positions:
        min_x = min(p["x"] for p in positions)
        min_y = min(p["y"] for p in positions)
        max_x = max(p["x"] + p["w"] for p in positions)
        max_y = max(p["y"] + p["l"] for p in positions)

        used_w = max_x - min_x
        used_l = max_y - min_y

        g_sz = 40
        g_th = 6
        guard_color = "#94a3b8"
        guard_line = "#475569"

        if show_corner_guards and cargo_top_z > pallet_h:
            cargo_h = cargo_top_z - pallet_h

            # Vertical corner guards.
            corners = [
                (min_x, min_y),
                (max_x, min_y),
                (min_x, max_y),
                (max_x, max_y),
            ]

            for cx, cy in corners:
                # Compact L-shaped indication.
                draw_plotly_cube(
                    fig,
                    cx - g_th,
                    cy - g_th,
                    pallet_h,
                    g_sz,
                    g_th,
                    cargo_h,
                    guard_color,
                    guard_line,
                )

                draw_plotly_cube(
                    fig,
                    cx - g_th,
                    cy - g_th,
                    pallet_h,
                    g_th,
                    g_sz,
                    cargo_h,
                    guard_color,
                    guard_line,
                )

            # Top edge guard illustration.
            safe_offset = min(
                g_sz + 5,
                max(0, min(used_w, used_l) / 4),
            )

            if used_l > 2 * safe_offset:
                y_start = min_y + safe_offset
                y_len = used_l - 2 * safe_offset

                draw_plotly_cube(
                    fig,
                    min_x,
                    y_start,
                    cargo_top_z,
                    g_sz,
                    y_len,
                    g_th,
                    guard_color,
                    guard_line,
                )

                draw_plotly_cube(
                    fig,
                    max_x - g_sz,
                    y_start,
                    cargo_top_z,
                    g_sz,
                    y_len,
                    g_th,
                    guard_color,
                    guard_line,
                )

            if used_w > 2 * safe_offset:
                x_start = min_x + safe_offset
                x_len = used_w - 2 * safe_offset

                draw_plotly_cube(
                    fig,
                    x_start,
                    min_y,
                    cargo_top_z,
                    x_len,
                    g_sz,
                    g_th,
                    guard_color,
                    guard_line,
                )

                draw_plotly_cube(
                    fig,
                    x_start,
                    max_y - g_sz,
                    cargo_top_z,
                    x_len,
                    g_sz,
                    g_th,
                    guard_color,
                    guard_line,
                )

        if show_straps and cargo_top_z > pallet_h:
            strap_color = "#1e3a8a"

            x_positions = [
                min_x + used_w * 0.25,
                min_x + used_w * 0.75,
            ]

            for sx in x_positions:
                fig.add_trace(
                    go.Scatter3d(
                        x=[sx, sx, sx, sx, sx],
                        y=[
                            min_y,
                            min_y,
                            max_y,
                            max_y,
                            min_y,
                        ],
                        z=[
                            pallet_h,
                            cargo_top_z + 8,
                            cargo_top_z + 8,
                            pallet_h,
                            pallet_h,
                        ],
                        mode="lines",
                        line=dict(
                            color=strap_color,
                            width=4.5,
                        ),
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )

            y_positions = [
                min_y + used_l * 0.25,
                min_y + used_l * 0.75,
            ]

            for sy in y_positions:
                fig.add_trace(
                    go.Scatter3d(
                        x=[
                            min_x,
                            max_x,
                            max_x,
                            min_x,
                            min_x,
                        ],
                        y=[sy, sy, sy, sy, sy],
                        z=[
                            pallet_h,
                            pallet_h,
                            cargo_top_z + 8,
                            cargo_top_z + 8,
                            pallet_h,
                        ],
                        mode="lines",
                        line=dict(
                            color=strap_color,
                            width=4.5,
                        ),
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )

    if show_height_plane:
        fig.add_trace(
            go.Mesh3d(
                x=[0, pallet_w, pallet_w, 0],
                y=[0, 0, pallet_l, pallet_l],
                z=[max_total_height] * 4,
                color="#ef4444",
                opacity=0.08,
                hoverinfo="skip",
                showscale=False,
            )
        )

    base_max = max(
        pallet_w,
        pallet_l,
        max_total_height,
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(
                title="Width (mm)",
                range=[
                    -max(100, overhang_allowance + 50),
                    pallet_w + max(100, overhang_allowance + 50),
                ],
            ),
            yaxis=dict(
                title="Length (mm)",
                range=[
                    -max(100, overhang_allowance + 50),
                    pallet_l + max(100, overhang_allowance + 50),
                ],
            ),
            zaxis=dict(
                title="Height (mm)",
                range=[0, max_total_height + 150],
            ),
            aspectmode="manual",
            aspectratio=dict(
                x=pallet_w / base_max,
                y=pallet_l / base_max,
                z=max_total_height / base_max,
            ),
        ),
        margin=dict(
            r=0,
            l=0,
            b=0,
            t=30,
        ),
        showlegend=False,
        height=650,
    )

    return fig


# =========================================================
# METRIC / TEXT HELPERS
# =========================================================
def orientation_name(case):
    if case["NORMAL"]:
        return "Normal H-Up"

    return f"{case['UP_AXIS']} Up — Non-normal"


def orientation_status_chip(case):
    if case["ALLOWED"]:
        if case["NORMAL"]:
            return '<span class="chip ok-chip">✅ H-Up Allowed</span>'

        return (
            f'<span class="chip warn-chip">⚠️ '
            f'{case["UP_AXIS"]}-Up Allowed</span>'
        )

    return (
        f'<span class="chip locked-chip">🔒 '
        f'{case["UP_AXIS"]}-Up Locked</span>'
    )


def result_mode(case):
    if case["GEOMETRY_TOTAL"] != case["SAFE_TOTAL"]:
        return "Recommended Safe Load"

    return "Geometry Max = Safe Load"


def display_count_selector(case, key_prefix):
    if case["GEOMETRY_TOTAL"] == case["SAFE_TOTAL"]:
        return case["SAFE_TOTAL"], "Recommended / Geometry"

    mode = st.radio(
        "Layout View",
        [
            "Recommended Safe Load",
            "Geometry Maximum",
        ],
        horizontal=True,
        key=f"{key_prefix}_view",
    )

    if mode == "Geometry Maximum":
        return case["GEOMETRY_TOTAL"], mode

    return case["SAFE_TOTAL"], mode


def render_case(case, title, color_theme, key_prefix):
    st.subheader(title)

    st.markdown(
        (
            f'<span class="chip">Layout: {case["LAYOUT_STRATEGY"]}</span>'
            f'<span class="chip">Case: {case["CASE_NAME"]}</span>'
            f'{orientation_status_chip(case)}'
        ),
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Boxes / Layer",
            f'{case["BOXES_PER_LAYER"]} ใบ',
        )

    with c2:
        st.metric(
            "Geometry Layers",
            f'{case["HEIGHT_LAYERS"]} ชั้น',
        )

    with c3:
        st.metric(
            "Geometry Capacity",
            f'{case["GEOMETRY_TOTAL"]} ใบ',
        )

    with c4:
        delta = (
            case["SAFE_TOTAL"]
            - case["GEOMETRY_TOTAL"]
        )

        st.metric(
            "Recommended Safe Load",
            f'{case["SAFE_TOTAL"]} ใบ',
            delta=(
                f"{delta} from Geometry"
                if delta < 0
                else "ผ่าน Weight Limit"
            ),
        )

    if case["SAFE_TOTAL"] <= 0:
        st.error(
            "❌ ไม่สามารถจัดวางกล่องในเงื่อนไขนี้ได้"
        )
    elif case["SAFE_TOTAL"] < case["GEOMETRY_TOTAL"]:
        st.error(
            f"❌ Geometry รองรับ {case['GEOMETRY_TOTAL']} กล่อง "
            f"แต่จะมี Gross Weight {case['GEOMETRY_GROSS_WEIGHT']:,.1f} kg "
            f"เกิน Max Pallet Gross Weight {max_pallet_gross_weight:,.1f} kg"
        )

        st.warning(
            f"⚠️ Recommended Safe Load = "
            f"**{case['SAFE_TOTAL']} กล่อง** "
            f"({case['SAFE_GROSS_WEIGHT']:,.1f} kg)"
        )
    else:
        st.success(
            f"✅ Geometry Capacity {case['GEOMETRY_TOTAL']} กล่อง "
            f"มี Gross Weight {case['GEOMETRY_GROSS_WEIGHT']:,.1f} kg "
            f"และอยู่ใน Max Pallet Gross Weight"
        )

    m1, m2 = st.columns(2)

    with m1:
        st.metric(
            "Safe Gross Weight",
            f'{case["SAFE_GROSS_WEIGHT"]:,.1f} kg',
        )

        st.metric(
            "Safe Total Height",
            f'{case["SAFE_TOTAL_HEIGHT"]:,.0f} mm',
        )

        st.metric(
            "Pallet Coverage",
            f'{case["PALLET_COVERAGE"]:.1f}%',
        )

    with m2:
        st.metric(
            "Remaining Weight",
            f'{case["REMAINING_WEIGHT_SAFE"]:,.1f} kg',
        )

        st.metric(
            "Remaining Height",
            f'{case["REMAINING_HEIGHT_SAFE"]:,.0f} mm',
        )

        st.metric(
            "Primary Limiter",
            case["PRIMARY_LIMITER"],
        )

    if overhang_allowance > 0:
        st.caption(
            f"Allowed footprint utilization: "
            f"{case['ALLOWED_FOOTPRINT_UTIL']:.1f}% • "
            f"Actual overhang W: {case['ACTUAL_OVERHANG_W']:.1f} mm/side • "
            f"L: {case['ACTUAL_OVERHANG_L']:.1f} mm/side"
        )
    else:
        st.caption(
            f"Layer footprint used: "
            f"{case['USED_W']:.0f} × {case['USED_L']:.0f} mm • "
            f"Pallet coverage: {case['PALLET_COVERAGE']:.1f}%"
        )

    display_count, display_mode = display_count_selector(
        case,
        key_prefix,
    )

    st.caption(
        f"Showing {display_count} cartons • "
        f"{display_mode} • "
        f"{orientation_name(case)}"
    )

    top_tab, side_tab, industrial_tab = st.tabs(
        [
            "🔝 Layer Pattern",
            "📐 Height / Side View",
            "🌐 3D Packaging Preview",
        ]
    )

    with top_tab:
        st.markdown(
            generate_svg_pallet_layer(
                case,
                color_theme,
            ),
            unsafe_allow_html=True,
        )

        st.caption(
            "Top View แสดง Full-layer Pattern ของ Orientation นี้ "
            "เพื่อใช้พิจารณาการจัดวางต่อชั้น"
        )

    with side_tab:
        front_fig = generate_2d_side_view(
            case,
            display_count,
            color_theme,
            "front",
        )

        st.pyplot(front_fig)
        plt.close(front_fig)

        side_fig = generate_2d_side_view(
            case,
            display_count,
            color_theme,
            "side",
        )

        st.pyplot(side_fig)
        plt.close(side_fig)

        if (
            display_count > 0
            and case["PARTIAL_TOP_LAYER_QTY"] > 0
            and display_count == case["SAFE_TOTAL"]
        ):
            st.caption(
                f"Safe Load มี Partial Top Layer "
                f"{case['PARTIAL_TOP_LAYER_QTY']} กล่อง"
            )

    with industrial_tab:
        fig = generate_plotly_3d(
            case,
            display_count,
            "#ffedd5" if case["NORMAL"] else "#dbeafe",
            "#ea580c" if case["NORMAL"] else "#2563eb",
        )

        if fig is not None:
            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        st.caption(
            "Corner Guards / Straps เป็น 3D illustration "
            "เพื่อช่วยสื่อสารเท่านั้น ไม่ใช่ Packaging requirement recommendation"
        )


# =========================================================
# WORKING CONDITION SUMMARY
# =========================================================
st.markdown("### 🧱 Palletizing Working Condition")

wc1, wc2, wc3, wc4 = st.columns(4)

with wc1:
    st.metric(
        "Carton",
        f"{box_w:.0f} × {box_l:.0f} × {box_h:.0f} mm",
    )

with wc2:
    st.metric(
        "Pallet",
        f"{pallet_w:.0f} × {pallet_l:.0f} × {pallet_h:.0f} mm",
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
    f"Carton gross weight: {box_weight:,.2f} kg • "
    f"Pallet tare: {pallet_tare_weight:,.1f} kg • "
    f"Gap: {box_tolerance:.1f} mm • "
    f"Allowed overhang: {overhang_allowance:.1f} mm/side"
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

st.caption(
    f"V0.1 evaluated {len(all_cases)} orientation cases "
    f"({len(allowed_cases)} allowed / "
    f"{len(all_cases)-len(allowed_cases)} locked)"
)

st.divider()


# =========================================================
# ADAPTIVE RESULT UI
# =========================================================
# Case A: Normal exists and alternative improves safe capacity.
if (
    best_normal is not None
    and best_alternative is not None
    and best_alternative["SAFE_TOTAL"] > best_normal["SAFE_TOTAL"]
):
    extra = (
        best_alternative["SAFE_TOTAL"]
        - best_normal["SAFE_TOTAL"]
    )

    gain_pct = (
        extra / best_normal["SAFE_TOTAL"] * 100.0
        if best_normal["SAFE_TOTAL"] > 0
        else 0.0
    )

    st.warning(
        f"⚠️ Alternative Orientation เพิ่ม Safe Capacity ได้ "
        f"**+{extra} กล่อง (+{gain_pct:.1f}%)** "
        f"แต่ต้องใช้ {best_alternative['UP_AXIS']}-Up "
        f"ซึ่งเป็น Non-normal orientation"
    )

    left, right = st.columns(2)

    with left:
        render_case(
            best_normal,
            "✅ Normal H-Up Reference",
            "#16a34a",
            "normal_compare",
        )

    with right:
        render_case(
            best_alternative,
            "⚠️ Higher Capacity Alternative",
            "#2563eb",
            "alt_compare",
        )

# Case B: Normal exists and alternative ties — recommend normal, collapse alternative.
elif (
    best_normal is not None
    and best_alternative is not None
    and best_alternative["SAFE_TOTAL"] == best_normal["SAFE_TOTAL"]
):
    st.success(
        f"✅ Recommended: **Normal H-Up — {best_normal['SAFE_TOTAL']} cartons/pallet**. "
        f"Alternative {best_alternative['UP_AXIS']}-Up ให้จำนวนเท่ากัน "
        "จึงไม่มี Capacity Benefit จากการเปลี่ยนทิศทางกล่อง"
    )

    render_case(
        best_normal,
        "✅ Best & Recommended Layout — Normal H-Up",
        "#16a34a",
        "normal_single",
    )

    with st.expander(
        "🔄 View Alternative Layout — Same Capacity",
        expanded=False,
    ):
        st.info(
            f"Alternative {best_alternative['UP_AXIS']}-Up "
            f"ให้ Safe Load = {best_alternative['SAFE_TOTAL']} กล่องเท่ากัน "
            "แต่ต้องใช้ Non-normal carton orientation"
        )

        render_case(
            best_alternative,
            f"Alternative — {best_alternative['UP_AXIS']} Up",
            "#2563eb",
            "alt_same",
        )

# Case C: Normal is best and alternative is lower, or no alternative enabled.
elif best_normal is not None and best_overall["NORMAL"]:
    if best_alternative is None:
        st.success(
            f"✅ Recommended: **Normal H-Up — {best_normal['SAFE_TOTAL']} cartons/pallet**. "
            "Non-normal orientations ยังไม่ได้รับอนุญาต จึงไม่ถูกนำมาใช้ในการ Recommendation"
        )
    else:
        diff = (
            best_normal["SAFE_TOTAL"]
            - best_alternative["SAFE_TOTAL"]
        )

        st.success(
            f"✅ Recommended: **Normal H-Up — {best_normal['SAFE_TOTAL']} cartons/pallet**. "
            f"Best allowed Alternative ต่ำกว่า {diff} กล่อง/pallet"
        )

    render_case(
        best_normal,
        "✅ Best & Recommended Layout — Normal H-Up",
        "#16a34a",
        "normal_best",
    )

    if best_alternative is not None:
        with st.expander(
            "🔎 View Best Allowed Alternative",
            expanded=False,
        ):
            render_case(
                best_alternative,
                f"Alternative — {best_alternative['UP_AXIS']} Up",
                "#2563eb",
                "alt_lower",
            )

# Case D: H-Up unavailable; best result is an alternative.
else:
    st.warning(
        f"⚠️ H-Up ไม่ได้ถูกอนุญาตในเงื่อนไขปัจจุบัน "
        f"Recommendation จึงใช้ **{best_overall['UP_AXIS']}-Up** "
        f"ที่ {best_overall['SAFE_TOTAL']} cartons/pallet"
    )

    render_case(
        best_overall,
        f"⚠️ Recommended Allowed Layout — {best_overall['UP_AXIS']} Up",
        "#2563eb",
        "alt_only",
    )


# =========================================================
# RECOMMENDATION SUMMARY
# =========================================================
st.divider()
st.subheader("🧭 Recommendation Summary")

rec = best_overall

if (
    best_normal is not None
    and rec["SAFE_TOTAL"] == best_normal["SAFE_TOTAL"]
):
    # Tie rule prefers Normal H-Up.
    rec = best_normal

r1, r2, r3, r4 = st.columns(4)

with r1:
    st.metric(
        "Recommended Safe",
        f'{rec["SAFE_TOTAL"]} cartons',
    )

with r2:
    st.metric(
        "Boxes / Layer",
        rec["BOXES_PER_LAYER"],
    )

with r3:
    st.metric(
        "Safe Layers Used",
        rec["SAFE_LAYERS_USED"],
    )

with r4:
    st.metric(
        "Recommended Orientation",
        orientation_name(rec),
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
        "Pallet Coverage",
        f'{rec["PALLET_COVERAGE"]:.1f}%',
    )

with r8:
    st.metric(
        "Primary Limiter",
        rec["PRIMARY_LIMITER"],
    )

if not rec["NORMAL"]:
    st.warning(
        "⚠️ Recommended Capacity ต้องใช้ Non-normal carton orientation. "
        "ก่อนนำไปใช้จริงควรยืนยัน Product orientation, label, internal support, "
        "customer requirement และ handling risk"
    )


# =========================================================
# ORIENTATION SCENARIO EXPLORER
# =========================================================
st.divider()
st.subheader("📊 Orientation Scenario Explorer")

table_rows = []

for case in all_cases:
    if case["ALLOWED"]:
        status = "✅ Allowed"
    else:
        status = "🔒 Locked"

    if case["NORMAL"]:
        orientation_class = "Normal"
    else:
        orientation_class = "Alternative"

    note_parts = []

    if not case["ALLOWED"]:
        note_parts.append("Not included in recommendation")

    if not case["NORMAL"]:
        note_parts.append("Non-normal orientation")

    if case["SAFE_TOTAL"] < case["GEOMETRY_TOTAL"]:
        note_parts.append("Weight limited")

    if (
        case["SAFE_TOTAL"] == rec["SAFE_TOTAL"]
        and case["CASE_NAME"] == rec["CASE_NAME"]
    ):
        note_parts.append("Recommended")

    table_rows.append(
        {
            "Case": case["CASE_NAME"],
            "Orientation": orientation_class,
            "Status": status,
            "Up Axis": case["UP_AXIS"],
            "Floor Size": (
                f'{case["FLOOR_BOX_W"]:.0f}×'
                f'{case["FLOOR_BOX_L"]:.0f}'
            ),
            "Box H": f'{case["BOX_VERTICAL_H"]:.0f}',
            "Boxes / Layer": case["BOXES_PER_LAYER"],
            "Height Layers": case["HEIGHT_LAYERS"],
            "Geometry Qty": case["GEOMETRY_TOTAL"],
            "Weight-safe Qty": case["SAFE_TOTAL"],
            "Safe Height": f'{case["SAFE_TOTAL_HEIGHT"]:.0f}',
            "Safe Gross kg": f'{case["SAFE_GROSS_WEIGHT"]:.1f}',
            "Coverage %": f'{case["PALLET_COVERAGE"]:.1f}',
            "Limiter": case["PRIMARY_LIMITER"],
            "Note": " • ".join(note_parts),
        }
    )

st.dataframe(
    table_rows,
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
        **V0.1 Engineering Rebuild**

        - Floor layout engine ของ V0.1 ยังเป็น **Simple Grid per layer**.
        - ระบบประเมินครบ 6 orientation cases แต่จะใช้เฉพาะ orientation ที่ผู้ใช้อนุญาตในการ Recommendation.
        - Default คือ **H-Up only** เพื่อไม่ให้ App สมมติเองว่าสามารถนอนตะแคงสินค้าได้.
        - Geometry Capacity พิจารณา Floor Footprint + Height Limit.
        - Recommended Safe Load เพิ่มข้อจำกัด **Max Pallet Gross Weight**.
        - Safe Load สามารถจบด้วย **Partial Top Layer** ได้เมื่อ Weight Limit ตัดจำนวนลงกลางชั้น.
        - Allowed Overhang ถูกคิดแบบสมมาตรทั้ง 4 ด้าน.
        - `Pallet Coverage > 100%` สามารถเกิดขึ้นได้เมื่อเปิด Overhang; จึงแยก Allowed-footprint utilization ไว้ในรายละเอียด.
        - 3D Corner Guards / Straps เป็น **Illustration only** ไม่ใช่ระบบคำนวณหรือ Recommendation ว่าจำเป็นต้องใช้.
        - V0.1 ยังไม่พิจารณา Compression Strength, Box Stacking Strength, Interlock Pattern,
          Column Stack Stability, Slip Sheet, Stretch Film, Edge Margin, Forklift handling,
          Center of Gravity หรือ Transport Dynamic Load.
        - Smart Mixed Rows / Mixed Columns / Residual-space Floor Optimization จะเป็นงานของ Version ถัดไป.
        """
    )
