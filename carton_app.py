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
st.sidebar.header("1. ขนาดกล่องสินค้า (Carton Dimensions - mm)")
box_w = st.sidebar.number_input("ความกว้างกล่อง (Width - W)", value=330.0, step=10.0)
box_l = st.sidebar.number_input("ความยาวกล่อง (Length - L)", value=303.0, step=10.0)
box_h = st.sidebar.number_input("ความสูงกล่อง (Height - H)", value=397.0, step=10.0)

st.sidebar.header("2. ขนาดพาเลทและข้อจำกัดขนส่ง (mm)")
pallet_w = st.sidebar.number_input("ความกว้างพาเลท (Pallet W)", value=1200.0, step=50.0)
pallet_l = st.sidebar.number_input("ความยาวพาเลท (Pallet L)", value=1000.0, step=50.0)
pallet_h = st.sidebar.number_input("ความหนาของพาเลท (Pallet H)", value=140.0, step=10.0)
max_air_height = st.sidebar.number_input("จำกัดความสูงรวมพาเลท (Max Cargo Height)", value=1600.0, step=50.0)

st.sidebar.header("3. ค่าเผื่อเชิงวิศวกรรม (Tolerances - mm)")
box_tolerance = st.sidebar.slider("ระยะเผื่อระหว่างกล่อง (Box Tolerance)", 0.0, 10.0, 2.0, step=0.5)
overhang_allowance = st.sidebar.slider("ระยะกล่องยื่นนอกขอบพาเลท (Overhang)", 0.0, 50.0, 0.0, step=5.0)

# --- CALCULATION ENGINE (ระบบคำนวณหลัก) ---
def calculate_pallet_layout(bw_used, bl_used, bh_used, case_name, is_normal_case):
    effective_box_w = bw_used + box_tolerance
    effective_box_l = bl_used + box_tolerance
    
    max_allowable_w = pallet_w + (2 * overhang_allowance)
    max_allowable_l = pallet_l + (2 * overhang_allowance)
    
    # 1. จำนวนกล่องในระนาบ 2D (แต่ละชั้น)
    slots_w = math.floor(max_allowable_w / effective_box_w)
    slots_l = math.floor(max_allowable_l / effective_box_l)
    boxes_per_layer = slots_w * slots_l
    
    # 2. จำนวนชั้นในแนวตั้ง (Z-Axis)
    available_cargo_height = max_air_height - pallet_h
    max_layers = math.floor(available_cargo_height / bh_used)
    
    if max_layers < 0: 
        max_layers = 0
        
    total_boxes = boxes_per_layer * max_layers
    total_height_with_pallet = pallet_h + (max_layers * bh_used) if total_boxes > 0 else pallet_h
    
    used_w = slots_w * effective_box_w - box_tolerance
    used_l = slots_l * effective_box_l - box_tolerance
    area_efficiency = (used_w * used_l) / (pallet_w * pallet_l) * 100 if total_boxes > 0 else 0
    
    return {
        "CASE_NAME": case_name,
        "TYPE": "ปกติ (เอาด้านสูงขึ้น)" if is_normal_case else "ทางเลือก (ตะแคง/นอนกล่อง)",
        "BW_USED": bw_used, "BL_USED": bl_used, "BH_USED": bh_used,
        "SLOTS_W": slots_w, "SLOTS_L": slots_l,
        "BOXES_PER_LAYER": boxes_per_layer,
        "MAX_LAYERS": max_layers,
        "TOTAL_BOXES": total_boxes,
        "TOTAL_HEIGHT": total_height_with_pallet,
        "AREA_EFFICIENCY": area_efficiency
    }

# ประมวลผลแบบหมุน 6 ทิศทาง (6-Way Generation)
dims = [box_w, box_l, box_h]
dim_names = ['W', 'L', 'H']

normal_cases = []
alt_cases = []
case_idx = 1

for i in range(3):
    h_val = dims[i]
    h_nm = dim_names[i]
    is_normal = (h_nm == 'H')
    
    rem_dims = [dims[j] for j in range(3) if j != i]
    rem_nms = [dim_names[j] for j in range(3) if j != i]
    
    # ทิศทางย่อยที่ 1
    name_1 = f"Case {case_idx}: {rem_nms[0]}x{rem_nms[1]}x{h_nm}"
    res_1 = calculate_pallet_layout(rem_dims[0], rem_dims[1], h_val, name_1, is_normal)
    if is_normal: normal_cases.append(res_1)
    else: alt_cases.append(res_1)
    case_idx += 1
    
    # ทิศทางย่อยที่ 2 (หมุนฐาน 90 องศา)
    name_2 = f"Case {case_idx}: {rem_nms[1]}x{rem_nms[0]}x{h_nm}"
    res_2 = calculate_pallet_layout(rem_dims[1], rem_dims[0], h_val, name_2, is_normal)
    if is_normal: normal_cases.append(res_2)
    else: alt_cases.append(res_2)
    case_idx += 1

# เรียงลำดับหาเคสที่ดีที่สุด (เน้นจำนวนกล่องมากที่สุด ถ้าเท่ากันเลือกเคสที่ความสูงต่ำกว่า)
normal_cases.sort(key=lambda x: (x['TOTAL_BOXES'], -x['TOTAL_HEIGHT']), reverse=True)
alt_cases.sort(key=lambda x: (x['TOTAL_BOXES'], -x['TOTAL_HEIGHT']), reverse=True)
all_ordered_cases = normal_cases + alt_cases

# --- SVG VISUALIZATION ENGINE (เครื่องมือวาดรูปแบบเวกเตอร์ประสิทธิภาพสูง) ---
def generate_svg_pallet_layer(params, title_prefix, color_theme):
    if params["TOTAL_BOXES"] == 0:
        # กรณีวางไม่ได้เลย
        return f"""
        <svg width="100%" height="auto" viewBox="0 0 1400 1200" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="1400" height="1200" fill="#f8fafc" stroke="#ef4444" stroke-width="4" rx="10" />
            <text x="700" y="600" font-family="system-ui, sans-serif" font-size="45" font-weight="bold" fill="#ef4444" text-anchor="middle">
                ไม่สามารถจัดวางได้ (เกินข้อจำกัดระบบ)
            </text>
        </svg>
        """
        
    sw, sl = params["SLOTS_W"], params["SLOTS_L"]
    bw, bl = params["BW_USED"], params["BL_USED"]
    
    # ออกแบบขอบเขตภาพให้มีพื้นที่บอกมิติรอบข้าง (Padding)
    pad_left, pad_top = 150, 150
    view_w = pallet_w + (pad_left * 2)
    view_h = pallet_l + (pad_top * 2)
    
    svg = f'<svg width="100%" height="auto" viewBox="0 0 {view_w} {view_h}" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff; border: 2px solid #e2e8f0; border-radius: 12px;">'
    
    # 1. วาดขอบเขตพาเลทหลัก (Pallet Outline)
    svg += f'<rect x="{pad_left}" y="{pad_top}" width="{pallet_w}" height="{pallet_l}" fill="#fcfbf7" stroke="{color_theme}" stroke-width="6" rx="8" />'
    
    # 2. เส้นระบุมิติและขนาดของพาเลท (Pallet Dimensions)
    # ขนาดด้านกว้าง (W) ด้านล่าง
    svg += f'<line x1="{pad_left}" y1="{view_h - 60}" x2="{pad_left + pallet_w}" y2="{view_h - 60}" stroke="#475569" stroke-width="3" />'
    svg += f'<polygon points="{pad_left},{view_h - 60} {pad_left+20},{view_h-70} {pad_left+20},{view_h-50}" fill="#475569" />'
    svg += f'<polygon points="{pad_left + pallet_w},{view_h - 60} {pad_left+pallet_w-20},{view_h-70} {pad_left+pallet_w-20},{view_h-50}" fill="#475569" />'
    svg += f'<text x="{pad_left + (pallet_w/2)}" y="{view_h - 25}" font-family="system-ui, sans-serif" font-size="30" font-weight="bold" fill="#475569" text-anchor="middle">ความกว้างพาเลท W: {int(pallet_w)} mm</text>'
    
    # ขนาดด้านยาว (L) ด้านซ้าย
    svg += f'<line x1="60" y1="{pad_top}" x2="60" y2="{pad_top + pallet_l}" stroke="#475569" stroke-width="3" />'
    svg += f'<polygon points="60,{pad_top} 50,{pad_top+20} 70,{pad_top+20}" fill="#475569" />'
    svg += f'<polygon points="60,{pad_top+pallet_l} 50,{pad_top+pallet_l-20} 70,{pad_top+pallet_l-20}" fill="#475569" />'
    svg += f'<text x="25" y="{pad_top + (pallet_l/2)}" font-family="system-ui, sans-serif" font-size="30" font-weight="bold" fill="#475569" text-anchor="middle" transform="rotate(-90, 25, {pad_top + (pallet_l/2)})">ความยาวพาเลท L: {int(pallet_l)} mm</text>'
    
    # 3. จัดกล่องให้อยู่ตรงกลางพื้นที่พาเลท (Centering Logic)
    total_used_w = sw * (bw + box_tolerance) - box_tolerance
    total_used_l = sl * (bl + box_tolerance) - box_tolerance
    offset_x = pad_left + (pallet_w - total_used_w) / 2
    offset_y = pad_top + (pallet_l - total_used_l) / 2
    
    # 4. วาดกล่องทีละกล่องพร้อมกำกับมิติแบบ CAD
    for i in range(sw):
        for j in range(sl):
            x = offset_x + i * (bw + box_tolerance)
            y = offset_y + j * (bl + box_tolerance)
            
            # วาดตัวกล่องสินค้า (สีส้มพาสเทล ขอบเข้มสวยงาม)
            svg += f'<rect x="{x}" y="{y}" width="{bw}" height="{bl}" fill="#ffedd5" stroke="#ea580c" stroke-width="2" rx="4" />'
            
            # ระบุข้อความขนาดกล่องด้านในแบบคมชัด
            label_w = f"W:{int(bw)}" if (i==0 and j==0) else f"{int(bw)}"
            label_l = f"L:{int(bl)}" if (i==0 and j==0) else f"{int(bl)}"
            
            # แสดงขนาดด้านกว้าง (แนวนอน)
            svg += f'<text x="{x + bw/2}" y="{y + bl/2 - 5}" font-family="system-ui, sans-serif" font-size="18" font-weight="bold" fill="#9a3412" text-anchor="middle">{label_w}</text>'
            # แสดงขนาดด้านยาว (แนวตั้ง)
            svg += f'<text x="{x + bw/2}" y="{y + bl/2 + 20}" font-family="system-ui, sans-serif" font-size="18" font-weight="bold" fill="#9a3412" text-anchor="middle">{label_l}</text>'
            
    svg += '</svg>'
    return svg

# --- PRESENTATION & LAYOUT SYSTEM ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🟢 แบบที่ 1: จัดเรียงแบบปกติ (Normal Case - H ขึ้น)")
    normal_best = normal_cases[0]
    
    # แสดงตัวชี้วัด
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("จำนวนกล่องทั้งหมด", f"{normal_best['TOTAL_BOXES']} ใบ")
    metric_col2.metric("จำนวนชั้น (Layers)", f"{normal_best['MAX_LAYERS']} ชั้น")
    metric_col3.metric("ความสูงรวมพาเลท", f"{normal_best['TOTAL_HEIGHT']} mm")
    
    st.write(f"**รูปแบบการจัดเรียง:** {normal_best['CASE_NAME']} | **ประสิทธิภาพพื้นที่คลัง:** {normal_best['AREA_EFFICIENCY']:.1f}%")
    # วาดภาพรูปแบบที่ 1
    st.write(generate_svg_pallet_layer(normal_best, "Normal Case", "#16a34a"), unsafe_allow_html=True)

with col2:
    st.subheader("🔵 แบบที่ 2: ทางเลือกที่ดีที่สุด (Best Alternative)")
    alt_best = alt_cases[0]
    
    # แสดงตัวชี้วัด
    metric_col4, metric_col5, metric_col6 = st.columns(3)
    metric_col4.metric("จำนวนกล่องทั้งหมด", f"{alt_best['TOTAL_BOXES']} ใบ")
    metric_col5.metric("จำนวนชั้น (Layers)", f"{alt_best['MAX_LAYERS']} ชั้น")
    metric_col6.metric("ความสูงรวมพาเลท", f"{alt_best['TOTAL_HEIGHT']} mm")
    
    st.write(f"**รูปแบบการจัดเรียง:** {alt_best['CASE_NAME']} | **ประสิทธิภาพพื้นที่คลัง:** {alt_best['AREA_EFFICIENCY']:.1f}%")
    # วาดภาพรูปแบบที่ 2
    st.write(generate_svg_pallet_layer(alt_best, "Alternative Best Case", "#2563eb"), unsafe_allow_html=True)

# แนะนำทางเลือกที่ดีที่สุดผ่าน Alert Box
if alt_best["TOTAL_BOXES"] > normal_best["TOTAL_BOXES"]:
    st.success(f"🔥 **แนะนำทางเลือกที่ 2 (แบบผสม/ตะแคงกล่อง):** เพราะสามารถเพิ่มจำนวนกล่องขึ้นพาเลทได้อีก **{alt_best['TOTAL_BOXES'] - normal_best['TOTAL_BOXES']} ใบ** ต่อพาเลท!")
else:
    st.info("💡 **แนะนำแบบจัดเรียงปกติ (Normal Case):** เนื่องจากได้ปริมาณกล่องสูงสุดและจัดเรียงได้ง่ายตามหลักสรีระศาสตร์ของกล่องสินค้าครับ")

# --- SUMMARY DATA TABLE (ตารางสรุปผล 6 ทิศทาง) ---
st.write("---")
st.subheader("📊 ตารางเปรียบเทียบรูปแบบการจัดวางทั้ง 6 ทิศทาง (6-Way Configuration Summary)")

# เตรียมข้อมูลเพื่อนำมาพล็อตตารางตารางของ Streamlit
summary_data = []
for idx, c in enumerate(all_ordered_cases):
    summary_data.append({
        "สัญลักษณ์": "⭐ แนะนำ" if (c == normal_best or c == alt_best) and c['TOTAL_BOXES'] > 0 else "ทางเลือก",
        "ชื่อเคสการคำนวณ": c['CASE_NAME'],
        "ประเภทการจัดวาง": c['TYPE'],
        "ด้านกล่องที่วางบนพาเลท (mm)": f"{int(c['BW_USED'])} x {int(c['BL_USED'])}",
        "จำนวน/ชั้น (Pcs)": c['BOXES_PER_LAYER'],
        "จำนวนชั้นสูงสุด (Layers)": c['MAX_LAYERS'],
        "จำนวนกล่องรวม (Pcs)": c['TOTAL_BOXES'],
        "ความสูงรวมพาเลท (mm)": c['TOTAL_HEIGHT'],
        "ประสิทธิภาพระนาบ": f"{c['AREA_EFFICIENCY']:.1f}%"
    })

st.dataframe(summary_data, use_container_width=True)
```
eof

---

### 🧠 สรุปทบทวน: สเต็ปการเปิดสร้าง Web Interface ใหม่ตั้งแต่ศูนย์ 

เพื่อเป็นการทบทวนความเข้าใจและช่วยให้พี่ทำโปรเจกต์ต่อๆ ไปได้ด้วยตัวเองอย่างมั่นใจ นี่คือ **3 ขั้นตอนหลัก** ในการเปลี่ยน Python Code บนกระดาษ ให้กลายเป็นหน้าเว็บแอปสุดสวยครับ:

```
[ขั้นตอนที่ 1: GitHub]           [ขั้นตอนที่ 2: GitHub]          [ขั้นตอนที่ 3: Streamlit]
สร้างคลังเก็บไฟล์ (Repo)  --->  อัปโหลดไฟล์ (app.py + reqs) --->  กดปุ่มเปิดตัว (Deploy App)
```

#### 📂 ขั้นตอนที่ 1: เปิด "บ้าน" บน GitHub (Create Repository)
1. เข้าเว็บ **GitHub.com** แล้วกดปุ่มสีเขียว **New** (หรือ Create repository)
2. **Repository name:** ตั้งชื่อภาษาอังกฤษ (ห้ามเคาะเว้นวรรค ให้ใช้ขีดกลางแทน เช่น `carton-pallet-optimizer`)
3. **Choose visibility:** เลือกเป็น **Public** (เพื่อให้ Streamlit หลังบ้านเข้ามาหยิบไฟล์ไปเปิดตัวหน้าเว็บได้ฟรี)
4. **Add README file:** ติ๊กช่องนี้เป็น **On (เปิดสีเขียว)** เพื่อช่วยให้สร้างไฟล์งานง่ายขึ้น
5. เลื่อนลงไปกดปุ่มสีเขียว **Create repository**

#### 📝 ขั้นตอนที่ 2: เขียน "สูตรสร้างโปรแกรม" (Create Code Files)
ในคลังไฟล์ใหม่ที่เพิ่งสร้าง ให้สร้างไฟล์ขึ้นมา **2 ไฟล์คู่กัน** เสมอ:

* **ไฟล์ที่ 1: `app.py` (ไฟล์โค้ดหลัก)**
  1. กดปุ่ม **Add file** -> เลือก **Create new file**
  2. ตั้งชื่อไฟล์ว่า `app.py`
  3. คัดลอกโค้ดกล่องสีดำด้านบนทั้งหมดของผมไปวางลงไป
  4. เลื่อนลงมากดปุ่มสีเขียว **Commit changes...** และกดยืนยันปุ่มสีฟ้าอีกครั้ง *(จำกฎเหล็ก "กดปุ่มเซฟ 2 รอบ" ไว้ให้แม่นนะครับ)*

* **ไฟล์ที่ 2: `requirements.txt` (ไฟล์ลงทะเบียนโปรแกรมเสริม)**
  1. กดปุ่ม **Add file** -> เลือก **Create new file**
  2. ตั้งชื่อไฟล์ว่า `requirements.txt` *(ตัวพิมพ์เล็กทั้งหมด)*
  3. พิมพ์ตัวหนังสือลงไปเพียงบรรทัดเดียวถ้วน:
     ```text
     streamlit
