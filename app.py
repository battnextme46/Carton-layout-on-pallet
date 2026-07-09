import streamlit as st
import math

# ตั้งค่าหน้าเว็บให้แสดงผลแบบกว้างและสวยงาม
st.set_page_config(
    page_title="Carton Palletizing Optimizer", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📦 Carton Palletizing Layout Optimizer (6-Way Analysis)")
st.write("เครื่องมือคำนวณและจำลองการจัดวางกล่องสินค้าบนพาเลทแบบปรับทิศทางได้ 6 รูปแบบเพื่อหาประสิทธิภาพสูงสุด")

# --- SIDEBAR INPUTS (แถบเมนูด้านซ้ายสำหรับรับค่า) ---
st.sidebar.header("1. ข้อมูลกล่องสินค้า (mm)")
box_w = st.sidebar.number_input("ความกว้างกล่อง (Width - W)", value=330.0, step=10.0)
box_l = st.sidebar.number_input("ความยาวกล่อง (Length - L)", value=303.0, step=10.0)
box_h = st.sidebar.number_input("ความสูงกล่อง (Height - H)", value=397.0, step=10.0)

st.sidebar.header("2. ข้อมูลพาเลทและข้อจำกัด (mm)")
pallet_w = st.sidebar.number_input("ความกว้างพาเลท (Pallet W)", value=1200.0, step=50.0)
pallet_l = st.sidebar.number_input("ความยาวพาเลท (Pallet L)", value=1000.0, step=50.0)
pallet_h = st.sidebar.number_input("ความหนาของพาเลท (Pallet H)", value=140.0, step=10.0)
max_air_height = st.sidebar.number_input("จำกัดความสูงรวมพาเลท", value=1600.0, step=50.0)

st.sidebar.header("3. ระยะเผื่อ (Tolerances - mm)")
box_tolerance = st.sidebar.slider("ระยะเผื่อระหว่างกล่อง", 0.0, 10.0, 2.0, step=0.5)
overhang_allowance = st.sidebar.slider("ระยะกล่องยื่นนอกขอบ", 0.0, 50.0, 0.0, step=5.0)

# --- CALCULATION ENGINE ---
def calculate_pallet_layout(bw_used, bl_used, bh_used, case_name, is_normal_case):
    effective_box_w = bw_used + box_tolerance
    effective_box_l = bl_used + box_tolerance
    max_allowable_w = pallet_w + (2 * overhang_allowance)
    max_allowable_l = pallet_l + (2 * overhang_allowance)
    
    slots_w = math.floor(max_allowable_w / effective_box_w)
    slots_l = math.floor(max_allowable_l / effective_box_l)
    boxes_per_layer = slots_w * slots_l
    
    available_cargo_height = max_air_height - pallet_h
    max_layers = math.floor(available_cargo_height / bh_used) if available_cargo_height > 0 else 0
    total_boxes = boxes_per_layer * max_layers
    total_height_with_pallet = pallet_h + (max_layers * bh_used) if total_boxes > 0 else pallet_h
    
    used_w = slots_w * effective_box_w - box_tolerance
    used_l = slots_l * effective_box_l - box_tolerance
    area_efficiency = (used_w * used_l) / (pallet_w * pallet_l) * 100 if total_boxes > 0 else 0
    
    return {
        "CASE_NAME": case_name,
        "TYPE": "ปกติ" if is_normal_case else "ทางเลือกอื่นๆ",
        "BW_USED": bw_used, "BL_USED": bl_used, "BH_USED": bh_used,
        "SLOTS_W": slots_w, "SLOTS_L": slots_l,
        "BOXES_PER_LAYER": boxes_per_layer,
        "MAX_LAYERS": max_layers,
        "TOTAL_BOXES": total_boxes,
        "TOTAL_HEIGHT": total_height_with_pallet,
        "AREA_EFFICIENCY": area_efficiency
    }

dims = [box_w, box_l, box_h]
dim_names = ['W', 'L', 'H']
normal_cases, alt_cases = [], []
case_idx = 1

for i in range(3):
    h_val, h_nm = dims[i], dim_names[i]
    is_normal = (h_nm == 'H')
    rem_dims = [dims[j] for j in range(3) if j != i]
    rem_nms = [dim_names[j] for j in range(3) if j != i]
    
    res1 = calculate_pallet_layout(rem_dims[0], rem_dims[1], h_val, f"Case {case_idx}: {rem_nms[0]}x{rem_nms[1]}x{h_nm}", is_normal)
    if is_normal: normal_cases.append(res1)
    else: alt_cases.append(res1)
    case_idx += 1
    
    res2 = calculate_pallet_layout(rem_dims[1], rem_dims[0], h_val, f"Case {case_idx}: {rem_nms[1]}x{rem_nms[0]}x{h_nm}", is_normal)
    if is_normal: normal_cases.append(res2)
    else: alt_cases.append(res2)
    case_idx += 1

normal_cases.sort(key=lambda x: (x['TOTAL_BOXES'], -x['TOTAL_HEIGHT']), reverse=True)
alt_cases.sort(key=lambda x: (x['TOTAL_BOXES'], -x['TOTAL_HEIGHT']), reverse=True)
all_ordered_cases = normal_cases + alt_cases

# --- SVG VISUALIZATION ENGINE ---
def generate_svg_pallet_layer(params, color_theme):
    if params["TOTAL_BOXES"] == 0:
        return f'<svg width="100%" height="auto" viewBox="0 0 1000 800" xmlns="http://www.w3.org/2000/svg"><rect width="1000" height="800" fill="#f8fafc" stroke="#ef4444" stroke-width="4"/><text x="500" y="400" font-size="40" fill="#ef4444" text-anchor="middle">ไม่สามารถจัดวางได้</text></svg>'
        
    sw, sl, bw, bl = params["SLOTS_W"], params["SLOTS_L"], params["BW_USED"], params["BL_USED"]
    pad = 150
    view_w, view_h = pallet_w + (pad * 2), pallet_l + (pad * 2)
    svg = f'<svg width="100%" height="auto" viewBox="0 0 {view_w} {view_h}" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff; border: 2px solid #e2e8f0; border-radius: 12px;">'
    svg += f'<rect x="{pad}" y="{pad}" width="{pallet_w}" height="{pallet_l}" fill="#fcfbf7" stroke="{color_theme}" stroke-width="6" rx="8" />'
    
    # วาดมิติพาเลท
    svg += f'<text x="{pad + (pallet_w/2)}" y="{view_h - 25}" font-size="30" font-weight="bold" fill="#475569" text-anchor="middle">ความกว้างพาเลท W: {int(pallet_w)} mm</text>'
    svg += f'<text x="25" y="{pad + (pallet_l/2)}" font-size="30" font-weight="bold" fill="#475569" text-anchor="middle" transform="rotate(-90, 25, {pad + (pallet_l/2)})">ความยาวพาเลท L: {int(pallet_l)} mm</text>'
    
    t_used_w = sw * (bw + box_tolerance) - box_tolerance
    t_used_l = sl * (bl + box_tolerance) - box_tolerance
    ox, oy = pad + (pallet_w - t_used_w) / 2, pad + (pallet_l - t_used_l) / 2
    
    for i in range(sw):
        for j in range(sl):
            x, y = ox + i * (bw + box_tolerance), oy + j * (bl + box_tolerance)
            svg += f'<rect x="{x}" y="{y}" width="{bw}" height="{bl}" fill="#ffedd5" stroke="#ea580c" stroke-width="2" rx="4" />'
            label_w = f"W:{int(bw)}" if (i==0 and j==0) else f"{int(bw)}"
            label_l = f"L:{int(bl)}" if (i==0 and j==0) else f"{int(bl)}"
            svg += f'<text x="{x + bw/2}" y="{y + bl/2 - 5}" font-size="18" font-weight="bold" fill="#9a3412" text-anchor="middle">{label_w}</text>'
            svg += f'<text x="{x + bw/2}" y="{y + bl/2 + 20}" font-size="18" font-weight="bold" fill="#9a3412" text-anchor="middle">{label_l}</text>'
    svg += '</svg>'
    return svg

# --- PRESENTATION & LAYOUT SYSTEM ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🟢 แบบที่ 1: จัดเรียงแบบปกติ (Normal Case - H ขึ้น)")
    res = normal_cases[0]
    m1, m2, m3 = st.columns(3)
    m1.metric("จำนวนกล่องทั้งหมด", f"{res['TOTAL_BOXES']} ใบ")
    m2.metric("จำนวนชั้น (Layers)", f"{res['MAX_LAYERS']} ชั้น")
    m3.metric("ความสูงรวมพาเลท", f"{res['TOTAL_HEIGHT']} mm")
    st.write(generate_svg_pallet_layer(res, "#16a34a"), unsafe_allow_html=True)

with col2:
    st.subheader("🔵 แบบที่ 2: ทางเลือกอื่นๆ (Alternative)")
    res = alt_cases[0]
    m4, m5, m6 = st.columns(3)
    m4.metric("จำนวนกล่องทั้งหมด", f"{res['TOTAL_BOXES']} ใบ")
    m5.metric("จำนวนชั้น (Layers)", f"{res['MAX_LAYERS']} ชั้น")
    m6.metric("ความสูงรวมพาเลท", f"{res['TOTAL_HEIGHT']} mm")
    st.write(generate_svg_pallet_layer(res, "#2563eb"), unsafe_allow_html=True)

if alt_cases[0]["TOTAL_BOXES"] > normal_cases[0]["TOTAL_BOXES"]:
    st.success(f"🔥 **แนะนำทางเลือกอื่นๆ (Alternative):** สามารถเพิ่มจำนวนกล่องได้อีก **{alt_cases[0]['TOTAL_BOXES'] - normal_cases[0]['TOTAL_BOXES']} ใบ** ต่อพาเลท!")
else:
    st.info("💡 **แนะนำแบบจัดเรียงปกติ (Normal Case):** ได้ปริมาณกล่องสูงสุดและจัดเรียงได้ง่ายที่สุดครับ")

st.write("---")
st.subheader("📊 ตารางสรุป 6 ทิศทาง")
st.dataframe(all_ordered_cases, use_container_width=True)
