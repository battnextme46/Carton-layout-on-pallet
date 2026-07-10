import streamlit as st
import math
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="Industrial Palletizing Optimizer V7.1", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📦 Carton Palletizing Layout Optimizer (Version 7.1)")
st.write("เครื่องมือจำลองการจัดวางระดับอุตสาหกรรม (แก้ไข Bug พิกัดฉากกระดาษและล็อกสเกลเรขาคณิตเรียบร้อย)")

# --- SIDEBAR INPUTS ---
st.sidebar.header("1. ข้อมูลกล่องสินค้า (mm)")
box_w = st.sidebar.number_input("ความกว้างกล่อง (Width - W)", value=370.0, step=10.0)
box_l = st.sidebar.number_input("ความยาวกล่อง (Length - L)", value=250.0, step=10.0)
box_h = st.sidebar.number_input("ความสูงกล่อง (Height - H)", value=125.0, step=10.0)

st.sidebar.header("2. ข้อมูลพาเลทและข้อจำกัด (mm)")
pallet_w = st.sidebar.number_input("ความกว้างพาเลท (Pallet W)", value=1200.0, step=50.0)
pallet_l = st.sidebar.number_input("ความยาวพาเลท (Pallet L)", value=800.0, step=50.0)
pallet_h = st.sidebar.number_input("ความหนาของพาเลท (Pallet H)", value=150.0, step=10.0)
max_air_height = st.sidebar.number_input("จำกัดความสูงรวมพาเลท", value=1500.0, step=50.0)

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
        "AREA_EFFICIENCY": area_efficiency,
        "USED_W": used_w, "USED_L": used_l
    }

# ประมวลผลลัพธ์ 6 ทิศทาง
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

# --- SVG VISUALIZATION ENGINE (2D Top View) ---
def generate_svg_pallet_layer(params, color_theme):
    if params["TOTAL_BOXES"] == 0:
        return f'<svg width="100%" height="auto" viewBox="0 0 1000 800" xmlns="http://www.w3.org/2000/svg"><rect width="1000" height="800" fill="#f8fafc" stroke="#ef4444" stroke-width="4"/><text x="500" y="400" font-size="40" fill="#ef4444" text-anchor="middle">ไม่สามารถจัดวางได้</text></svg>'
        
    sw, sl, bw, bl = params["SLOTS_W"], params["SLOTS_L"], params["BW_USED"], params["BL_USED"]
    pad = 150
    view_w, view_h = pallet_w + (pad * 2), pallet_l + (pad * 2)
    svg = f'<svg width="100%" height="auto" viewBox="0 0 {view_w} {view_h}" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff; border: 2px solid #e2e8f0; border-radius: 12px;">'
    svg += f'<rect x="{pad}" y="{pad}" width="{pallet_w}" height="{pallet_l}" fill="#fcfbf7" stroke="{color_theme}" stroke-width="6" rx="8" />'
    
    svg += f'<text x="{pad + (pallet_w/2)}" y="{view_h - 25}" font-size="30" font-weight="bold" fill="#475569" text-anchor="middle">W: {int(pallet_w)} mm</text>'
    svg += f'<text x="25" y="{pad + (pallet_l/2)}" font-size="30" font-weight="bold" fill="#475569" text-anchor="middle" transform="rotate(-90, 25, {pad + (pallet_l/2)})">L: {int(pallet_l)} mm</text>'
    
    ox, oy = pad + (pallet_w - params["USED_W"]) / 2, pad + (pallet_l - params["USED_L"]) / 2
    
    for i in range(sw):
        for j in range(sl):
            x, y = ox + i * (bw + box_tolerance), oy + j * (bl + box_tolerance)
            svg += f'<rect x="{x}" y="{y}" width="{bw}" height="{bl}" fill="#ffedd5" stroke="#ea580c" stroke-width="2" rx="4" />'
            svg += f'<text x="{x + bw/2}" y="{y + 25}" font-size="16" font-weight="bold" fill="#c2410c" text-anchor="middle">{int(bw)}</text>'
            svg += f'<text x="{x + bw - 12}" y="{y + bl/2}" font-size="16" font-weight="bold" fill="#475569" text-anchor="middle" transform="rotate(-90, {x + bw - 12}, {y + bl/2})">{int(bl)}</text>'
            
    svg += '</svg>'
    return svg

# --- 2D SIDE VIEW ENGINE ---
def generate_2d_side_views(params, color_theme, view_type='front'):
    fig, ax = plt.subplots(figsize=(8, 5))
    layers = params["MAX_LAYERS"]
    bh = params["BH_USED"]
    
    if view_type == 'front':
        total_dim = pallet_w
        slots = params["SLOTS_W"]
        bw = params["BW_USED"]
        ox = (pallet_w - params["USED_W"]) / 2
        ax.set_title("Front View (Pallet Width W Axis)", fontsize=12, weight='bold')
        ax.set_xlabel("Width (mm)")
    else:
        total_dim = pallet_l
        slots = params["SLOTS_L"]
        bw = params["BL_USED"]
        ox = (pallet_l - params["USED_L"]) / 2
        ax.set_title("Side View (Pallet Length L Axis)", fontsize=12, weight='bold')
        ax.set_xlabel("Length (mm)")
        
    ax.add_patch(plt.Rectangle((0, 0), total_dim, pallet_h, color='#cbd5e1', edgecolor='#475569', lw=1.5))
    ax.text(total_dim/2, pallet_h/2, f"Pallet H: {int(pallet_h)} mm", ha='center', va='center', color='#334155', weight='bold', fontsize=9)
    
    for k in range(layers):
        gz = pallet_h + (k * bh)
        for i in range(slots):
            gx = ox + i * (bw + box_tolerance)
            ax.add_patch(plt.Rectangle((gx, gz), bw, bh, facecolor='#ffedd5', edgecolor='#ea580c', lw=1.2))
            
    ax.axhline(y=max_air_height, color='#ef4444', linestyle='--', linewidth=2, label=f"Limit Cargo ({int(max_air_height)} mm)")
    ax.axhline(y=params["TOTAL_HEIGHT"], color=color_theme, linestyle='-', linewidth=2, label=f"Product Height ({int(params['TOTAL_HEIGHT'])} mm)")
    
    ax.set_xlim(-50, total_dim + 50)
    ax.set_ylim(0, max_air_height + 150)
    ax.set_ylabel("Height (mm)")
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    return fig

# --- PLOTLY 3D ENGINE (INDUSTRIAL MODE) ---
def draw_plotly_cube(fig, x, y, z, dx, dy, dz, color, line_color, opacity=1.0):
    fig.add_trace(go.Mesh3d(
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
        lighting=dict(ambient=1.0, diffuse=0.0, specular=0.0, roughness=1.0, fresnel=0.0),
        lightposition=dict(x=0, y=0, z=0)
    ))
    
    if opacity == 1.0:
        for edge in [
            ([x, x+dx], [y, y], [z, z]), ([x, x], [y, y+dy], [z, z]), ([x+dx, x+dx], [y, y+dy], [z, z]), ([x, x+dx], [y+dy, y+dy], [z, z]),
            ([x, x+dx], [y, y], [z+dz, z+dz]), ([x, x], [y, y+dy], [z+dz, z+dz]), ([x+dx, x+dx], [y, y+dy], [z+dz, z+dz]), ([x, x+dx], [y+dy, y+dy], [z+dz, z+dz]),
            ([x, x], [y, y], [z, z+dz]), ([x+dx, x+dx], [y, y], [z, z+dz]), ([x, x], [y+dy, y+dy], [z, z+dz]), ([x+dx, x+dx], [y+dy, y+dy], [z, z+dz])
        ]:
            fig.add_trace(go.Scatter3d(x=edge[0], y=edge[1], z=edge[2], mode='lines', line=dict(color=line_color, width=2), showlegend=False))

def generate_plotly_3d(params, color_theme, edge_theme):
    if params["TOTAL_BOXES"] == 0:
        return None
    fig = go.Figure()
    sw, sl, layers = params["SLOTS_W"], params["SLOTS_L"], params["MAX_LAYERS"]
    bw, bl, bh = params["BW_USED"], params["BL_USED"], params["BH_USED"]
    
    ox, oy = (pallet_w - params["USED_W"]) / 2, (pallet_l - params["USED_L"]) / 2
    cargo_top_z = pallet_h + (layers * bh)
    
    # 1. วาดพาเลทฐานล่าง
    draw_plotly_cube(fig, 0, 0, 0, pallet_w, pallet_l, pallet_h, '#cbd5e1', '#475569')
    
    # 2. วาดกองกล่องสินค้า
    for k in range(layers):
        gz = pallet_h + (k * bh)
        for j in range(sl):
            gy = oy + j * (bl + box_tolerance)
            for i in range(sw):
                gx = ox + i * (bw + box_tolerance)
                draw_plotly_cube(fig, gx, gy, gz, bw, bl, bh, color_theme, edge_theme)
                
    # 3. 🛡️ วาด PAPER CORNER GUARDS (ฉากกระดาษป้องกันมุม 4 มุมหลัก)
    g_sz = 40  # ความกว้างปีกฉากกระดาษมุม 40mm
    g_th = 6   # ความหนาฉากกระดาษ 6mm
    g_h = cargo_top_z - pallet_h  # ความสูงฉากเท่ากับกองสินค้า
    c_guard = '#94a3b8'  # สีฉากกระดาษเทาอ่อนมาตรฐาน
    c_line = '#475569'   # สีเส้นขอบฉาก
    
    # มุมที่ 1: หน้าซ้าย
    draw_plotly_cube(fig, ox - g_th, oy - g_th, pallet_h, g_sz, g_th, g_h, c_guard, c_line)
    draw_plotly_cube(fig, ox - g_th, oy, pallet_h, g_th, g_sz, g_h, c_guard, c_line)
    # มุมที่ 2: หน้าขวา
    draw_plotly_cube(fig, ox + params["USED_W"] - g_sz + g_th, oy - g_th, pallet_h, g_sz, g_th, g_h, c_guard, c_line)
    draw_plotly_cube(fig, ox + params["USED_W"], oy, pallet_h, g_th, g_sz, g_h, c_guard, c_line)
    # มุมที่ 3: หลังซ้าย
    draw_plotly_cube(fig, ox - g_th, oy + params["USED_L"], pallet_h, g_sz, g_th, g_h, c_guard, c_line)
    draw_plotly_cube(fig, ox - g_th, oy + params["USED_L"] - g_sz, pallet_h, g_th, g_sz, g_h, c_guard, c_line)
    # มุมที่ 4: หลังขวา
    draw_plotly_cube(fig, ox + params["USED_W"] - g_sz + g_th, oy + params["USED_L"], pallet_h, g_sz, g_th, g_h, c_guard, c_line)
    draw_plotly_cube(fig, ox + params["USED_W"], oy + params["USED_L"] - g_sz, pallet_h, g_th, g_sz, g_h, c_guard, c_line)
    
    # 4. 🔲 วาด TOP EDGE GUARDS (กรอบฉากกระดาษป้องกันรัดมุมด้านบนสุด 4 ด้าน)
    draw_plotly_cube(fig, ox, oy - g_th, cargo_top_z, params["USED_W"], g_th, g_th, '#e2e8f0', c_line)
    draw_plotly_cube(fig, ox, oy + params["USED_L"], cargo_top_z, params["USED_W"], g_th, g_th, '#e2e8f0', c_line)
    draw_plotly_cube(fig, ox - g_th, oy, cargo_top_z, g_th, params["USED_L"], g_th, '#e2e8f0', c_line)
    draw_plotly_cube(fig, ox + params["USED_W"], oy, cargo_top_z, g_th, params["USED_L"], g_th, '#e2e8f0', c_line)

    # 5. 🧵 วาด STRAPS (สายรัดพลาสติกสีกรมท่าเข้ม รัดรอบกองสินค้าแนวตั้งแกนละ 2 เส้น)
    strap_color = '#1e3a8a'
    s_w = 4.0
    
    # รัดแนวแกน X (ตัดผ่านหน้ากว้างของกองกล่อง 2 เส้นที่ระยะ 25% และ 75%)
    x_positions = [ox + (params["USED_W"] * 0.25), ox + (params["USED_W"] * 0.75)]
    for sx in x_positions:
        fig.add_trace(go.Scatter3d(
            x=[sx, sx, sx, sx, sx],
            y=[oy - g_th, oy - g_th, oy + params["USED_L"] + g_th, oy + params["USED_L"] + g_th, oy - g_th],
            z=[pallet_h, cargo_top_z + g_th, cargo_top_z + g_th, pallet_h, pallet_h],
            mode='lines', line=dict(color=strap_color, width=s_w), showlegend=False
        ))
        
    # รัดแนวแกน Y (ตัดผ่านหน้ายาวของกองกล่อง 2 เส้นที่ระยะ 25% และ 75%)
    y_positions = [oy + (params["USED_L"] * 0.25), oy + (params["USED_L"] * 0.75)]
    for sy in y_positions:
        fig.add_trace(go.Scatter3d(
            x=[ox - g_th, ox + params["USED_W"] + g_th, ox + params["USED_W"] + g_th, ox - g_th, ox - g_th],
            y=[sy, sy, sy, sy, sy],
            z=[pallet_h, pallet_h, cargo_top_z + g_th, cargo_top_z + g_th, pallet_h],
            mode='lines', line=dict(color=strap_color, width=s_w), showlegend=False
        ))

    # วาดระนาบเพดานสูงสุด Limit แดงโปร่งแสง
    fig.add_trace(go.Mesh3d(
        x=[0, pallet_w, pallet_w, 0], y=[0, 0, pallet_l, pallet_l], z=[max_air_height]*4,
        color='#ef4444', opacity=0.08, name='Limit Height'
    ))
    
    # ล็อกมิติตามสเกลเรขาคณิตจริง
    base_max = max(pallet_w, pallet_l)
    fig.update_layout(
        scene=dict(
            xaxis=dict(title='Width (mm)', range=[-100, pallet_w + 100]),
            yaxis=dict(title='Length (mm)', range=[-100, pallet_l + 100]),
            zaxis=dict(title='Height (mm)', range=[0, max_air_height + 100]),
            aspectmode='manual',
            aspectratio=dict(
                x=pallet_w / base_max,
                y=pallet_l / base_max,
                z=max_air_height / base_max
            )
        ),
        margin=dict(r=0, l=0, b=0, t=30),
        showlegend=False,
        height=650
    )
    return fig

# --- PRESENTATION SYSTEM ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🟢 แบบที่ 1: การจัดเรียงปกติ (H ขึ้น)")
    res1 = normal_cases[0]
    st.metric("จำนวนรวม", f"{res1['TOTAL_BOXES']} ใบ", f"สูงรวม {res1['TOTAL_HEIGHT']} mm")
    
    t1, t2, t3 = st.tabs(["🔝 Top View (SVG)", "📐 2D Side Views", "🌐 Industrial 3D"])
    with t1:
        st.write(generate_svg_pallet_layer(res1, "#16a34a"), unsafe_allow_html=True)
    with t2:
        st.pyplot(generate_2d_side_views(res1, "#16a34a", 'front'))
        st.pyplot(generate_2d_side_views(res1, "#16a34a", 'side'))
    with t3:
        p_fig1 = generate_plotly_3d(res1, '#ffedd5', '#ea580c')
        if p_fig1: st.plotly_chart(p_fig1, use_container_width=True)

with col2:
    st.subheader("🔵 แบบที่ 2: ทางเลือกอื่นๆ (Alternative)")
    res2 = alt_cases[0]
    st.metric("จำนวนรวม", f"{res2['TOTAL_BOXES']} ใบ", f"สูงรวม {res2['TOTAL_HEIGHT']} mm")
    
    t4, t5, t6 = st.tabs(["🔝 Top View (SVG)", "📐 2D Side Views", "🌐 Industrial 3D"])
    with t4:
        st.write(generate_svg_pallet_layer(res2, "#2563eb"), unsafe_allow_html=True)
    with t5:
        st.pyplot(generate_2d_side_views(res2, "#2563eb", 'front'))
        st.pyplot(generate_2d_side_views(res2, "#2563eb", 'side'))
    with t6:
        p_fig2 = generate_plotly_3d(res2, '#dbeafe', '#2563eb')
        if p_fig2: st.plotly_chart(p_fig2, use_container_width=True)

st.write("---")
st.subheader("📊 ตารางสรุป 6 ทิศทาง")
st.dataframe(all_ordered_cases, use_container_width=True)
