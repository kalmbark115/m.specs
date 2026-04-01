
import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
import time
import os

# ==========================================
# 1. PAGE CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="Riyadh Solar Intelligence (Mobile)",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. STATE & LANGUAGE LOGIC
# ==========================================
if "points" not in st.session_state: st.session_state.points = []
if "area" not in st.session_state: st.session_state.area = 0
if "map_center" not in st.session_state: st.session_state.map_center = [24.7136, 46.6753]
if "map_zoom" not in st.session_state: st.session_state.map_zoom = 18
if "lang" not in st.session_state: st.session_state.lang = "en"
if "time_view" not in st.session_state: st.session_state.time_view = "Annual"

if "last_click" not in st.session_state: st.session_state.last_click = None

if "show_audit" not in st.session_state: st.session_state.show_audit = False
if "show_service" not in st.session_state: st.session_state.show_service = False
if "show_credits" not in st.session_state: st.session_state.show_credits = False
if "svc_stage" not in st.session_state: st.session_state.svc_stage = "idle"
if "show_alert" not in st.session_state: st.session_state.show_alert = False
if "selected_contractor" not in st.session_state: st.session_state.selected_contractor = ""

def toggle_language(): st.session_state.lang = "ar" if st.session_state.lang == "en" else "en"
def toggle_time(): st.session_state.time_view = "Monthly" if st.session_state.time_view == "Annual" else "Annual"

def toggle_audit():
    if st.session_state.area > 0:
        if st.session_state.show_audit:
            st.session_state.show_audit = False
        else:
            st.session_state.show_audit = True
            st.session_state.show_service = False
            st.session_state.show_credits = False
            st.session_state.show_alert = False
    else:
        st.session_state.show_alert = True
        st.session_state.show_service = False
        st.session_state.show_credits = False

def toggle_credits():
    if st.session_state.show_credits:
        st.session_state.show_credits = False
    else:
        st.session_state.show_credits = True
        st.session_state.show_audit = False
        st.session_state.show_service = False
        st.session_state.show_alert = False

def open_service():
    if st.session_state.area > 0:
        if st.session_state.show_service:
            st.session_state.show_service = False
            st.session_state.svc_stage = "idle"
        else:
            st.session_state.show_service = True
            st.session_state.show_audit = False
            st.session_state.show_credits = False
            st.session_state.show_alert = False
            st.session_state.svc_stage = "scanning"
    else:
        st.session_state.show_alert = True
        st.session_state.show_audit = False
        st.session_state.show_credits = False

def close_all_popups():
    st.session_state.show_audit = False; st.session_state.show_service = False; st.session_state.show_credits = False; st.session_state.svc_stage = "idle"

def reset_view():
    close_all_popups(); st.session_state.show_alert = False; st.session_state.points = []; st.session_state.area = 0

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1)/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1)/2.0)**2
    return R * (2 * np.arcsin(np.sqrt(a)))

t = {
    "en": {
        "btn_lang": "عربي", "btn_cred": "Team", "title_top": "RIYADH", "title_bot": "SOLAR AI", "load": "Building Scale Profile",
        "maint": "Maintenance Strategy", "tech": "Solar Panel Tech (W)", "reset": "RESET MAP BOUNDARY", "area": "Rooftop Area",
        "units": "Panel Units", "opt_loads": ["Small Villa", "Standard Villa", "Large Estate", "Palace"], "opt_maint": ["Weekly (Elite)", "Monthly (Standard)", "Lazy Owner"],
        "annual": "Annual", "monthly": "Monthly", "overview": "Overview", "audit": "Investment Audit", "service": "Book Service",
        "alert": "⚠️ Please select a roof area on the map first!", "audit_title": "FINANCIAL AUDIT", "cost": "Estimated Install Cost",
        "payback": "Payback Period", "years": "Years", "direct_a": "Annual Direct Savings", "direct_m": "Monthly Direct Savings",
        "export_a": "Annual Export Credits", "export_m": "Monthly Export Credits", "total_a": "Total Annual Benefit", "total_m": "Total Monthly Benefit",
        "service_title": "SERVICE DISPATCH", "scanning": "Pinging Local Grid...", "request": "SEND REQUEST",
        "receipt_title": "PROJECT SUMMARY", "confirm": "Confirm & Submit", "cancel": "Cancel", "selected": "Selected Contractor",
        "success": "DISPATCH SUCCESSFUL", "success_sub": "A technician from your selected contractor will contact you shortly.",
        "finalizing": "Finalizing Dispatch...", "team": "PROJECT TEAM", "khalid": "Khalid Moh. Almubarak", "albaraa": "Albaraa Moh. Yousef"
    },
    "ar": {
        "btn_lang": "EN", "btn_cred": "فريق", "title_top": "الرياض", "title_bot": "للذكاء الشمسي", "load": "حجم المبنى", "maint": "استراتيجية الصيانة",
        "tech": "قدرة اللوح الشمسي (واط)", "reset": "إعادة تعيين الخريطة", "area": "مساحة السطح", "units": "عدد الألواح",
        "opt_loads": ["فيلا صغيرة", "فيلا قياسية", "قصر صغير", "قصر كبير"], "opt_maint": ["أسبوعي (ممتاز)", "شهري (قياسي)", "بدون صيانة"],
        "annual": "سنوي", "monthly": "شهري", "overview": "المخطط العام", "audit": "التدقيق الاستثماري", "service": "حجز الخدمة",
        "alert": "⚠️ الرجاء تحديد مساحة السطح على الخريطة أولاً!", "audit_title": "التقرير المالي", "cost": "التكلفة التقديرية للتركيب",
        "payback": "فترة الاسترداد", "years": "سنوات", "direct_a": "التوفير المباشر السنوي", "direct_m": "التوفير المباشر الشهري",
        "export_a": "أرباح التصدير السنوية", "export_m": "أرباح التصدير الشهرية", "total_a": "إجمالي العائد السنوي", "total_m": "إجمالي العائد الشهري",
        "service_title": "مركز الخدمة", "scanning": "جاري البحث عن مقاولين...", "request": "إرسال طلب",
        "receipt_title": "ملخص المشروع", "confirm": "تأكيد وإرسال الطلب", "cancel": "إلغاء", "selected": "المقاول المختار",
        "success": "تم إرسال الطلب بنجاح", "success_sub": "سيتواصل معك فني متخصص قريباً.",
        "finalizing": "جاري تأكيد الإرسال...", "team": "فريق المشروع", "khalid": "خالد محمد المبارك", "albaraa": "البراء محمد يوسف"
    }
}
loc = t[st.session_state.lang]

def calculate_area(pts):
    if len(pts) < 3: return 0
    lats = np.array([p[0] for p in pts]) * 111111
    lngs = np.array([p[1] for p in pts]) * 111111 * np.cos(np.radians(24.7))
    return 0.5 * np.abs(np.dot(lats, np.roll(lngs, 1)) - np.dot(lngs, np.roll(lats, 1)))

# ==========================================
# 3. UNIFIED CSS INJECTION (PRE-LOADED)
# ==========================================
is_ar = st.session_state.lang == "ar"

# Pull dynamic labels up here so CSS can grab them directly
view_label = loc['monthly'] if st.session_state.time_view == 'Annual' else loc['annual']
lbl_o = "Home" if not is_ar else "رئيسية"
lbl_a = "Audit" if not is_ar else "تقرير"
lbl_b = "Book" if not is_ar else "حجز"

unified_css = f"""
<style>
    /* TYPOGRAPHY & APP BASE */
    :root {{
        --f-btn: {'2.8vw' if is_ar else '2.6vw'};
        --f-pri: {'3.5vw' if is_ar else '3.2vw'};
        --f-hud-lbl: {'2.2vw' if is_ar else '2.0vw'};
        --f-hud-val: {'4.5vw' if is_ar else '4.0vw'};
        --f-hud-val-dark: {'5.0vw' if is_ar else '4.5vw'};
    }}
   
    ::-webkit-scrollbar {{ width: 0px !important; height: 0px !important; background: transparent !important; display: none !important; }}
    html, body, [data-testid="stAppViewContainer"], .block-container {{ overflow: hidden !important; max-height: 100vh !important; }}
    [data-testid="stStatusWidget"], [data-testid="stDecoration"] {{ display: none !important; visibility: hidden !important; opacity: 0 !important; height: 0 !important; }}
    :root {{ color-scheme: dark; }}
    body, .stApp, [data-testid="stAppViewContainer"] {{ background-color: #0A0A0A !important; color: white !important; }}
    .block-container {{ padding: 0 !important; max-width: 100vw !important; overflow: hidden; }}
   
    iframe {{ position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; z-index: 0 !important; border: none !important; }}
    div[data-testid="stFolium"] {{ position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; z-index: 0 !important; }}

    .stButton > button {{ outline: none !important; }}
    .stButton > button:focus {{ outline: none !important; box-shadow: none !important; color: inherit !important; }}

    [data-testid="stHeader"] {{
        background-color: #0A0A0A !important; border-bottom: 2px solid #D4AF37 !important; height: 115px !important;
        position: fixed !important; top: 0 !important; left: 0 !important; right: 0 !important; z-index: 999 !important;
    }}
    [data-testid="stHeader"] > div {{ display: none !important; }}
    [data-testid="stHeader"]::before {{
        content: "{loc['title_top']}"; position: absolute; right: 4vw; top: 12px;
        color: #D4AF37 !important; font-family: 'Times New Roman', serif !important; font-weight: 300 !important; letter-spacing: 1vw !important; font-size: 6vw !important; line-height: 1 !important; pointer-events: none;
    }}
    [data-testid="stHeader"]::after {{
        content: "{loc['title_bot']}"; position: absolute; right: 4vw; top: 38px;
        color: #FFFFFF !important; font-family: 'Times New Roman', serif !important; font-weight: 300 !important; letter-spacing: 0.5vw !important; font-size: 4vw !important; line-height: 1 !important; pointer-events: none;
    }}

    /* =========================================================
       THE MATHEMATICAL TELEPORT MATRIX
       ========================================================= */

    /* Collapse the Streamlit wrapper completely */
    div[data-testid="stVerticalBlock"]:has(> div.element-container span#mobile-nav-anchor) {{
        height: 0px !important; margin: 0 !important; padding: 0 !important; overflow: visible !important;
    }}
    span[id$="-anchor"] {{ display: none !important; }}

    /* Teleport every specific button wrapper to fixed positioning */
    div.element-container:has(span[id$="-anchor"]) + div.element-container div[data-testid="stButton"] {{
        position: fixed !important; z-index: 99999 !important; margin: 0 !important; padding: 0 !important;
    }}

    /* Strip the button design to create the seamless blend */
    div.element-container:has(span[id$="-anchor"]) + div.element-container button[kind="secondary"] {{
        background: transparent !important; border: none !important; box-shadow: none !important; border-radius: 0 !important;
        height: 100% !important; width: 100% !important; margin: 0 !important; padding: 0 !important; outline: none !important;
        display: flex !important; flex-direction: column !important; justify-content: center !important; align-items: center !important;
    }}

    /* --- NUCLEAR ANTI-TWITCH: HIDE NATIVE STREAMLIT TEXT COMPLETELY --- */
    div.element-container:has(span[id$="-anchor"]) + div.element-container button[kind="secondary"] p,
    div.element-container:has(span[id$="-anchor"]) + div.element-container button[kind="secondary"] div[data-testid="stMarkdownContainer"] {{
        display: none !important; opacity: 0 !important; visibility: hidden !important; font-size: 0 !important;
    }}

    /* --- INJECT TEXT VIA CSS PSEUDO-ELEMENTS (IMMUNE TO REACT DOM TWITCHING) --- */
    div.element-container:has(span[id$="-anchor"]) + div.element-container button[kind="secondary"]::after {{
        display: flex !important; flex-direction: column !important; justify-content: center !important; align-items: center !important;
        width: 100% !important; text-align: center !important; white-space: pre-wrap !important; line-height: 1.2 !important;
        pointer-events: none !important;
    }}

    /* --- MATH COORDINATES: ROW 1 (Top Left) - Bigger & Spaced --- */
    div.element-container:has(span#btn-lang-anchor) + div.element-container div[data-testid="stButton"] {{ top: 12px !important; left: 3vw !important; width: 15vw !important; height: 42px !important; }}
    div.element-container:has(span#btn-time-anchor) + div.element-container div[data-testid="stButton"] {{ top: 12px !important; left: 22vw !important; width: 15vw !important; height: 42px !important; }}
    div.element-container:has(span#btn-cred-anchor) + div.element-container div[data-testid="stButton"] {{ top: 12px !important; left: 41vw !important; width: 15vw !important; height: 42px !important; }}

    /* Pseudo Text Injection for Row 1 */
    div.element-container:has(span#btn-lang-anchor) + div.element-container button::after {{ content: "🌐\\A {loc['btn_lang']}"; font-size: 3.5vw !important; color: #ccc !important; font-weight: normal !important; }}
    div.element-container:has(span#btn-time-anchor) + div.element-container button::after {{ content: "🔄\\A {view_label}"; font-size: 3.5vw !important; color: #ccc !important; font-weight: normal !important; }}
    div.element-container:has(span#btn-cred-anchor) + div.element-container button::after {{ content: "👥\\A {loc['btn_cred']}"; font-size: 3.5vw !important; color: #ccc !important; font-weight: normal !important; }}


    /* --- MATH COORDINATES: ROW 2 (Bottom Full Width) --- */
    div.element-container:has(span#btn-book-anchor) + div.element-container div[data-testid="stButton"] {{ top: 60px !important; left: 0vw !important; width: 33.333vw !important; height: 55px !important; }}
    div.element-container:has(span#btn-audit-anchor) + div.element-container div[data-testid="stButton"] {{ top: 60px !important; left: 33.333vw !important; width: 33.333vw !important; height: 55px !important; }}
    div.element-container:has(span#btn-home-anchor) + div.element-container div[data-testid="stButton"] {{ top: 60px !important; left: 66.666vw !important; width: 33.333vw !important; height: 55px !important; }}

    /* Pseudo Text Injection for Row 2 (Audit is now white) */
    div.element-container:has(span#btn-book-anchor) + div.element-container button::after {{ content: "🛠️\\A {lbl_b}"; font-size: 4.2vw !important; color: white !important; font-weight: bold !important; }}
    div.element-container:has(span#btn-audit-anchor) + div.element-container button::after {{ content: "📊\\A {lbl_a}"; font-size: 4.2vw !important; color: white !important; font-weight: bold !important; }}
    div.element-container:has(span#btn-home-anchor) + div.element-container button::after {{ content: "🏠\\A {lbl_o}"; font-size: 4.2vw !important; color: white !important; font-weight: bold !important; }}

    [data-testid="stSidebar"], [data-testid="collapsedControl"] {{ display: none !important; }}

    /* =========================================================
       THE FLAWLESS VECTOR COGWHEEL
       ========================================================= */
    div[data-testid="stVerticalBlock"]:has(> div.element-container span#settings-master) {{
        position: fixed !important; top: 125px !important; left: 3vw !important; width: 40vw !important; min-width: 130px !important; max-width: 180px !important; z-index: 99998 !important; background: transparent !important; padding: 0 !important; pointer-events: none !important;
    }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container span#settings-master) * {{ pointer-events: auto !important; }}
    div.element-container:has(span#settings-master) {{ display: none !important; }}
    div.element-container:has(span#settings-master) + div.element-container {{
        position: fixed !important; top: 125px !important; left: 3vw !important; z-index: 999999 !important; width: 45px !important; height: 45px !important;
    }}
    div.element-container:has(span#settings-master) + div.element-container label {{
        background: rgba(15, 15, 15, 0.95) !important; border: 2px solid #D4AF37 !important; border-radius: 50% !important;
        width: 45px !important; height: 45px !important; min-height: 45px !important;
        display: flex !important; justify-content: center !important; align-items: center !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.8) !important; backdrop-filter: blur(5px) !important; cursor: pointer !important; padding: 0 !important; margin: 0 !important; position: relative !important;
    }}
    div.element-container:has(span#settings-master) + div.element-container label > div,
    div.element-container:has(span#settings-master) + div.element-container label > span {{
        position: absolute !important; left: -9999px !important; opacity: 0 !important; width: 0 !important; height: 0 !important; overflow: hidden !important; pointer-events: none !important; display: none !important;
    }}
    div.element-container:has(span#settings-master) + div.element-container label::after {{
        content: "" !important; position: absolute !important; top: 0 !important; left: 0 !important; width: 100% !important; height: 100% !important;
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23D4AF37'><path d='M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.06-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.73,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.06,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.43-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.49-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z'/></svg>") !important;
        background-size: 24px 24px !important; background-repeat: no-repeat !important; background-position: center !important; transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important; pointer-events: none !important; transform-origin: center center !important;
    }}
    div.element-container:has(span#settings-master) + div.element-container:has(input[type="checkbox"]:checked) label::after {{ transform: rotate(180deg) !important; }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container span#settings-master) div[data-testid="stVerticalBlock"]:has(div#floating-controls) {{
        margin-top: 60px !important; width: 100% !important; background: transparent !important; padding: 0 !important; transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.3s ease !important; transform: translateX(-150%) !important; opacity: 0 !important; pointer-events: none !important;
    }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container span#settings-master):has(input[type="checkbox"]:checked) div[data-testid="stVerticalBlock"]:has(div#floating-controls) {{ transform: translateX(0) !important; opacity: 1 !important; pointer-events: auto !important; }}
    div[data-testid="stVerticalBlock"]:has(div#floating-controls) .stSelectbox {{ background-color: rgba(15, 15, 15, 0.9) !important; border: 2px solid #D4AF37 !important; border-radius: 12px !important; padding: 4px 8px !important; margin-bottom: 8px !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.8) !important; backdrop-filter: blur(5px); }}
    div[data-testid="stVerticalBlock"]:has(div#floating-controls) label {{ color: #D4AF37 !important; font-weight: bold; text-shadow: 1px 1px 3px black !important; margin-bottom: 2px !important; font-size: var(--f-hud-lbl) !important; }}
    div[data-baseweb="select"] > div {{ background-color: transparent !important; border: none !important; color: white !important; font-size: var(--f-btn) !important; height: auto !important; min-height: 34px !important; padding-top: 2px !important; padding-bottom: 2px !important; }}
    div[data-baseweb="select"] span {{ line-height: 1.2 !important; white-space: normal !important; }}
    div[data-testid="stVerticalBlock"]:has(div#floating-controls) button[kind="primary"] {{ background: rgba(15, 15, 15, 0.9) !important; color: #D4AF37 !important; border: 2px solid #D4AF37 !important; border-radius: 12px !important; width: 100% !important; height: 35px !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.8) !important; transition: 0.2s !important; display: flex !important; align-items: center !important; justify-content: center !important; outline: none !important; backdrop-filter: blur(5px); margin-top: 5px !important; }}
    div[data-testid="stVerticalBlock"]:has(div#floating-controls) button[kind="primary"] p {{ font-size: var(--f-btn) !important; font-weight: bold !important; margin: 0 !important; color: inherit !important; white-space: normal !important; text-align: center !important; line-height: 1.1 !important; }}

    /* =========================================================
       THE DASHBOARD GRID HUD & SMART ALERT
       ========================================================= */
    .smart-alert {{ position: fixed; top: 135px; left: 50%; transform: translateX(-50%); background: rgba(200, 50, 50, 0.95); border: 1px solid #ff4b4b; color: white; padding: 1vh 4vw; border-radius: 8px; text-align: center; font-size: 3vw; font-weight: bold; z-index: 999999; box-shadow: 0 4px 15px rgba(0,0,0,0.5); width: 90vw; }}
    .results-hud {{ position: fixed; bottom: 15px; left: 2vw; right: 2vw; z-index: 9999; display: grid; grid-template-columns: 1fr 1fr; gap: 2vw; padding-bottom: 10px; }}
    .hud-card {{ background-color: rgba(10, 10, 10, 0.95); border: 1px solid rgba(212, 175, 55, 0.4); border-radius: 12px; width: 100%; height: 8vh; min-height: 60px; box-shadow: 0px 5px 15px rgba(0,0,0,0.5); display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 0 1vw; }}
    .highlight-card {{ background-color: #D4AF37; border: 1px solid #FFFFFF; box-shadow: 0px 5px 20px rgba(212, 175, 55, 0.5); grid-column: span 2; height: 9vh; min-height: 70px; }}
    .hud-label {{ color: #D4AF37; font-size: var(--f-hud-lbl); font-weight: bold; text-transform: uppercase; margin-bottom: 1px; text-align: center; }}
    .hud-value {{ color: white; font-size: var(--f-hud-val); font-weight: bold; text-align: center; white-space: nowrap; line-height: 1; }}
    .hud-label-dark {{ color: black; font-size: var(--f-hud-lbl); font-weight: 900; text-transform: uppercase; margin-bottom: 1px; text-align: center; line-height: 1; }}
    .hud-value-dark {{ color: black; font-size: var(--f-hud-val-dark); font-weight: 900; text-align: center; white-space: nowrap; line-height: 1; }}

    /* =========================================================
       MODALS CSS
       ========================================================= */
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) {{
        position: fixed !important; top: 50% !important; left: 50% !important; transform: translate(-50%, -50%) !important; width: 90vw !important; background: rgba(15, 15, 15, 0.98) !important; border: 2px solid #D4AF37 !important; border-radius: 16px !important; padding: 4vh 4vw !important; z-index: 9999999 !important; box-shadow: 0px 20px 50px rgba(0,0,0,0.9) !important; max-height: 85vh !important; overflow-y: auto !important;
    }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) > div.element-container:has(> div.stButton > button[kind="secondary"]) {{ position: absolute !important; top: 2vh !important; right: 2vw !important; width: auto !important; z-index: 999999 !important; }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) > div.element-container:has(> div.stButton > button[kind="secondary"]) button[kind="secondary"] {{ background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important; height: auto !important; outline: none !important; color: #D4AF37 !important; }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) > div.element-container:has(> div.stButton > button[kind="secondary"]) button[kind="secondary"] p {{ font-size: 8vw !important; font-weight: 300 !important; line-height: 1 !important; margin: 0 !important; color: inherit !important; transition: 0.2s !important; }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) button[kind="tertiary"] {{ background: transparent !important; color: transparent !important; border: none !important; box-shadow: none !important; height: 12vh !important; width: 100% !important; margin-top: -14vh !important; margin-bottom: 2vh !important; position: relative !important; z-index: 9999 !important; cursor: pointer !important; display: block !important; outline: none !important; color: transparent !important; }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) div[data-testid="stHorizontalBlock"]:last-of-type {{ display: flex !important; flex-direction: row !important; justify-content: center !important; gap: 4vw !important; margin: 3vh 0 0 0 !important; width: 100% !important; padding: 0 !important; }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) div[data-testid="stHorizontalBlock"]:last-of-type > div[data-testid="column"] {{ width: 42% !important; min-width: 42% !important; max-width: 42% !important; flex: 0 0 42% !important; display: block !important; padding: 0 !important; margin: 0 !important; }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) div[data-testid="stHorizontalBlock"]:last-of-type button[kind="secondary"], div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) button[kind="primary"] {{ font-weight: bold !important; font-size: var(--f-pri) !important; border-radius: 10px !important; height: 6vh !important; min-height: 40px !important; width: 100% !important; display: flex !important; align-items: center !important; justify-content: center !important; outline: none !important; margin: 0 !important; box-sizing: border-box !important; }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) div[data-testid="stHorizontalBlock"]:last-of-type button p {{ white-space: nowrap !important; margin: 0 !important; }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) div[data-testid="stHorizontalBlock"]:last-of-type button[kind="secondary"] {{ background: #222 !important; color: white !important; border: 1px solid rgba(212,175,55,0.4) !important; }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) button[kind="primary"] {{ background-color: #D4AF37 !important; color: #0A0A0A !important; border: none !important; box-shadow: 0 4px 10px rgba(0,0,0,0.5) !important; }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container div#modal-marker) button[kind="primary"]:disabled {{ background-color: #333 !important; color: #777 !important; border: 1px solid #444 !important; box-shadow: none !important; }}

    /* CREDITS NATIVE GRID - FIX COLLAPSING IMAGES */
    div[data-testid="stVerticalBlock"]:has(> div.element-container span#credits-grid) div[data-testid="stHorizontalBlock"] {{ display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; align-items: center !important; gap: 3vw !important; margin-bottom: 1.5vh !important; background: rgba(255,255,255,0.05) !important; border-left: 3px solid #D4AF37 !important; border-radius: 10px !important; padding: 1vh 2vw !important; box-shadow: 0 4px 10px rgba(0,0,0,0.4) !important; }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container span#credits-grid) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) {{ width: 65px !important; min-width: 65px !important; max-width: 65px !important; flex: 0 0 65px !important; display: flex !important; align-items: center !important; justify-content: center !important; padding: 0 !important; margin: 0 !important; }}
    div[data-testid="stVerticalBlock"]:has(> div.element-container span#credits-grid) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) {{ width: calc(100% - 65px) !important; flex: 1 1 auto !important; display: flex !important; align-items: center !important; padding: 0 !important; margin: 0 !important; }}
   
    /* SAFEGUARD: Force Streamlit's inner div wrappers to respect dimensions so image doesn't vanish */
    div[data-testid="stVerticalBlock"]:has(> div.element-container span#credits-grid) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) div.element-container,
    div[data-testid="stVerticalBlock"]:has(> div.element-container span#credits-grid) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) div[data-testid="stImage"] {{
        width: 100% !important; display: flex !important; justify-content: center !important; align-items: center !important; flex-shrink: 0 !important;
    }}

    /* Sledgehammer sizing on the actual Image Tag */
    div[data-testid="stVerticalBlock"]:has(> div.element-container span#credits-grid) img {{
        width: 55px !important; height: 55px !important; min-width: 55px !important; min-height: 55px !important; max-width: 55px !important; max-height: 55px !important; border-radius: 50% !important; border: 2px solid #D4AF37 !important; object-fit: cover !important; display: block !important; visibility: visible !important; opacity: 1 !important;
    }}
   
    .scanner-ring {{ width: 15vw; height: 15vw; border: 3px solid #D4AF37; border-radius: 50%; margin: 5vh auto 3vh auto; animation: pulse 1.5s infinite; opacity: 0; }}
    @keyframes pulse {{ 0% {{ transform: scale(0.6); opacity: 0; }} 50% {{ opacity: 1; }} 100% {{ transform: scale(1.2); opacity: 0; }} }}
    .checkmark-circle {{ width: 18vw; height: 18vw; border: 3px solid #D4AF37; border-radius: 50%; margin: 3vh auto 2vh auto; display: flex; align-items: center; justify-content: center; animation: scale-in 0.5s ease-out; }}
    @keyframes scale-in {{ 0% {{ transform: scale(0); }} 100% {{ transform: scale(1); }} }}
</style>
"""
st.markdown(unified_css, unsafe_allow_html=True)


# ==========================================
# 4. EARLY STATE PROCESSING
# ==========================================
if "main_map" in st.session_state and st.session_state.main_map and st.session_state.main_map.get("last_clicked"):
    new_p = (st.session_state.main_map["last_clicked"]["lat"], st.session_state.main_map["last_clicked"]["lng"])
    if st.session_state.last_click != new_p:  
        st.session_state.last_click = new_p  
        st.session_state.points.append(new_p)

st.session_state.area = calculate_area(st.session_state.points)

# ==========================================
# 5. MOBILE PAGE ARCHITECTURE
# ==========================================

f_title = "6vw" if is_ar else "5vw"
f_lbl = "3vw" if is_ar else "2.8vw"
f_val = "4.5vw" if is_ar else "4vw"
f_big = "5.5vw" if is_ar else "5vw"
f_card_tit = "3.5vw" if is_ar else "3.2vw"
f_card_sub = "2.8vw" if is_ar else "2.6vw"
f_card_dsc = "2.5vw" if is_ar else "2.3vw"
f_succ_tit = "6vw" if is_ar else "5.5vw"
f_succ_sub = "3.5vw" if is_ar else "3vw"

# THE ABSOLUTE POSITIONING CONTAINER
with st.container():
    st.markdown("<span id='mobile-nav-anchor'></span>", unsafe_allow_html=True)
   
    # ROW 1 Anchors & Blank Buttons (Text injected via CSS)
    st.markdown("<span id='btn-lang-anchor'></span>", unsafe_allow_html=True)
    st.button(" ", on_click=toggle_language, type="secondary", use_container_width=True, key="h_lang")
   
    st.markdown("<span id='btn-time-anchor'></span>", unsafe_allow_html=True)
    st.button("  ", on_click=toggle_time, type="secondary", use_container_width=True, key="h_time")
   
    st.markdown("<span id='btn-cred-anchor'></span>", unsafe_allow_html=True)
    st.button("   ", on_click=toggle_credits, type="secondary", use_container_width=True, key="h_cred")
   
    # ROW 2 Anchors & Blank Buttons (Text injected via CSS)
    st.markdown("<span id='btn-book-anchor'></span>", unsafe_allow_html=True)
    st.button("    ", on_click=open_service, type="secondary", use_container_width=True, key="h_srv")
   
    st.markdown("<span id='btn-audit-anchor'></span>", unsafe_allow_html=True)
    st.button("     ", on_click=toggle_audit, type="secondary", use_container_width=True, key="h_aud")
   
    st.markdown("<span id='btn-home-anchor'></span>", unsafe_allow_html=True)
    st.button("      ", on_click=reset_view, type="secondary", use_container_width=True, key="h_ovv")

# THE COG COMPONENT
with st.container():
    st.markdown("<span id='settings-master'></span>", unsafe_allow_html=True)
    st.checkbox("invisible_text", key="cog_toggle", value=False)
   
    with st.container():
        st.markdown("<div id='floating-controls'></div>", unsafe_allow_html=True)
        load_choice = st.selectbox(loc["load"], loc["opt_loads"], key="f_load")
        maint_val = st.selectbox(loc["maint"], loc["opt_maint"], key="f_maint")
       
        m_multiplier = {"Weekly (Elite)": 0.95, "Monthly (Standard)": 0.75, "Lazy Owner": 0.60, "أسبوعي (ممتاز)": 0.95, "شهري (قياسي)": 0.75, "بدون صيانة": 0.60}[maint_val]
       
        panel_w = st.selectbox(loc["tech"], [350, 450, 550, 650], index=1, key="f_tech")
       
        btn_res = "RESET" if not is_ar else "مسح"
        st.button(btn_res, on_click=reset_view, type="primary", use_container_width=True, key="f_reset")

if st.session_state.show_alert:
    st.markdown(f'<div class="smart-alert">{loc["alert"]}</div>', unsafe_allow_html=True)

# ==========================================
# 6. THE MAP ENGINE
# ==========================================

m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom, tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', zoom_control=False, max_zoom=22)

fg = folium.FeatureGroup(name="Roof Markers")

if st.session_state.points:
    for p in st.session_state.points:
        folium.CircleMarker(p, radius=5, color='#D4AF37', fill=True, fill_color='white').add_to(fg)
    if len(st.session_state.points) >= 3:
        folium.Polygon(st.session_state.points, color="#D4AF37", fill=True, fill_opacity=0.3, weight=3).add_to(fg)

map_data = st_folium(
    m,
    height=1200,
    width="100%",
    key="main_map",
    feature_group_to_add=fg,
    returned_objects=["last_clicked"]
)

if st.session_state.area > 0:
    area = st.session_state.area
    units = int(area / 2.3)
    kwp = (units * panel_w) / 1000.0
    consumption_map = {"Small Villa": 45000, "فيلا صغيرة": 45000, "Standard Villa": 75000, "فيلا قياسية": 75000, "Large Estate": 120000, "قصر صغير": 120000, "Palace": 200000, "قصر كبير": 200000}
   
    annual_consumption = consumption_map[load_choice]
    annual_generation = kwp * 2200 * m_multiplier
   
    direct_kwh = min(annual_generation, annual_consumption)
    export_kwh = max(0, annual_generation - annual_consumption)
   
    direct_savings_ann = direct_kwh * 0.18
    export_credits_ann = export_kwh * 0.07
    total_benefit_ann = direct_savings_ann + export_credits_ann
   
    install_cost = 35000 + (kwp * 2100)
    payback = install_cost / total_benefit_ann if total_benefit_ann > 0 else 0
    divider = 1 if st.session_state.time_view == "Annual" else 12

    lbl_dir = loc["direct_a"] if st.session_state.time_view == "Annual" else loc["direct_m"]
    lbl_exp = loc["export_a"] if st.session_state.time_view == "Annual" else loc["export_m"]
    lbl_tot = loc["total_a"] if st.session_state.time_view == "Annual" else loc["total_m"]

    st.markdown(f"""
    <div class="results-hud">
        <div class="hud-card"><div class="hud-label">{loc["area"]}</div><div class="hud-value">{area:.1f} m²</div></div>
        <div class="hud-card"><div class="hud-label">{loc["units"]}</div><div class="hud-value">{units}</div></div>
        <div class="hud-card"><div class="hud-label">{lbl_dir}</div><div class="hud-value">{(direct_savings_ann/divider):,.0f}</div></div>
        <div class="hud-card"><div class="hud-label">{lbl_exp}</div><div class="hud-value">{(export_credits_ann/divider):,.0f}</div></div>
        <div class="hud-card highlight-card"><div class="hud-label-dark">{lbl_tot}</div><div class="hud-value-dark">{(total_benefit_ann/divider):,.0f} SAR</div></div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 7. POPUP MODAL GENERATION
# ==========================================

# --- THE NATIVE MOBILE CREDITS MODAL ---
if st.session_state.show_credits:
    with st.container():
        st.markdown("<div id='modal-marker'></div>", unsafe_allow_html=True)
        st.button("✖", key="cred_x", type="secondary", on_click=close_all_popups)
           
        st.markdown(f"<div style='color: white; font-size: {f_title}; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.5); margin-top: -1vh; text-align: center; margin-bottom: 3vh;'>{loc['team']}</div>", unsafe_allow_html=True)
       
        st.markdown("<span id='credits-grid'></span>", unsafe_allow_html=True)
       
        c1, c2 = st.columns([1, 3])
        with c1:
            # REMOVED use_container_width=True to stop Streamlit from squishing the image
            if os.path.exists("khalid.png"):
                st.image("khalid.png")
            else:
                st.image("https://via.placeholder.com/200/1C2128/D4AF37?text=KM")
        with c2:
            st.markdown(f"<div style='color: white; font-size: 3.6vw; font-weight: bold; line-height: 1.2;'>{loc['khalid']}</div>", unsafe_allow_html=True)
           
        c3, c4 = st.columns([1, 3])
        with c3:
            # REMOVED use_container_width=True
            if os.path.exists("albaraa.png"):
                st.image("albaraa.png")
            else:
                st.image("https://via.placeholder.com/200/1C2128/D4AF37?text=AY")
        with c4:
            st.markdown(f"<div style='color: white; font-size: 3.6vw; font-weight: bold; line-height: 1.2;'>{loc['albaraa']}</div>", unsafe_allow_html=True)


# --- EXISTING MODALS ---
if st.session_state.show_audit and st.session_state.area > 0:
    with st.container():
        st.markdown("<div id='modal-marker'></div>", unsafe_allow_html=True)
        st.button("✖", key="aud_x", type="secondary", on_click=close_all_popups)
           
        st.markdown(f"<div style='color: white; font-size: {f_title}; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.5); margin-top: -1vh; padding-right: 5vw;'>{loc['audit_title']}</div>", unsafe_allow_html=True)
        st.markdown(f"<hr style='border-color: #D4AF37; opacity: 0.3; margin: 2vh 0;'><div style='display:flex; justify-content:space-between;'><div><div style='color:#aaa; font-size:{f_lbl};'>{loc['cost']}</div><div style='color:white; font-size:{f_big}; font-weight:bold;'>{install_cost:,.0f} SAR</div></div><div><div style='color:#aaa; font-size:{f_lbl};'>{loc['payback']}</div><div style='color:white; font-size:{f_big}; font-weight:bold;'>{payback:.1f} {loc['years']}</div></div></div>", unsafe_allow_html=True)

if st.session_state.show_service:
    with st.container():
        st.markdown("<div id='modal-marker'></div>", unsafe_allow_html=True)

        if st.session_state.svc_stage == "scanning":
            st.button("✖", key="scn_x", type="secondary", on_click=close_all_popups)
            st.markdown(f"<div class='scanner-ring'></div><div style='text-align:center; color:#D4AF37; font-weight:bold; font-size:{f_val}; margin-top:3vh;'>{loc['scanning']}</div>", unsafe_allow_html=True)
            time.sleep(2); st.session_state.svc_stage = "list"; st.rerun()
           
        elif st.session_state.svc_stage == "list":
            st.button("✖", key="list_x", type="secondary", on_click=close_all_popups)
            st.markdown(f"<div style='color: white; font-size: {f_title}; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.5); margin-top: -1vh; margin-bottom: 2vh; padding-right: 5vw;'>{loc['service_title']}</div>", unsafe_allow_html=True)

            if st.session_state.points:
                my_lat, my_lon = st.session_state.points[0]
            else:
                my_lat, my_lon = st.session_state.map_center
               
            d_acwa = haversine(my_lat, my_lon, 24.72, 46.70)
            d_desert = haversine(my_lat, my_lon, 24.68, 46.65)
            d_alfanar = haversine(my_lat, my_lon, 24.75, 46.75)

            contractors = [
                ("ACWA Power Solar", "https://images.unsplash.com/photo-1508514177221-188b1cf16e9d?w=150&h=150&fit=crop", "⭐⭐⭐⭐ 4.9", "🏆 Govt Partner", d_acwa),
                ("Desert Technologies", "https://images.unsplash.com/photo-1521618755572-156ae0cdd74d?w=150&h=150&fit=crop", "⭐⭐⭐⭐ 4.8", "🇸🇦 Saudi Panels", d_desert),
                ("Alfanar Energy", "https://images.unsplash.com/photo-1497440001374-f26997328c1b?w=150&h=150&fit=crop", "⭐⭐⭐⭐ 4.7", "⚡ Smart Grid", d_alfanar)
            ]
           
            for name, img, stars, desc, dist in contractors:
                is_sel = (st.session_state.selected_contractor == name)
                bg = "rgba(45,45,45,0.95)" if is_sel else "rgba(30,30,30,0.6)"
                border = "2px solid #D4AF37" if is_sel else "1px solid rgba(255,255,255,0.2)"
                shadow = "0 4px 10px rgba(212,175,55,0.4)" if is_sel else "none"
               
                card = f"""
                <div style='min-height: 12vh; background: {bg}; border: {border}; box-shadow: {shadow}; border-radius: 10px; padding: 1.5vh 2vw; display: flex; align-items: center; box-sizing: border-box; transition: 0.2s;'>
                    <img src='{img}' style='width: 12vw; height: 12vw; border-radius: 6px; object-fit: cover; margin-right: 2vw; border: 1px solid #D4AF37;'>
                    <div style='flex-grow: 1; line-height: 1.2;'>
                        <div style='color: white; font-weight: bold; font-size: {f_card_tit};'>{name}</div>
                        <div style='color: #D4AF37; font-size: {f_card_sub};'>{stars}</div>
                        <div style='color: #aaa; font-size: {f_card_dsc}; margin-top: 0.5vh;'>{desc}</div>
                    </div>
                    <div style='color: white; font-weight: bold; font-size: {f_card_tit};'>{dist:.1f} km</div>
                </div>
                """
                st.markdown(card, unsafe_allow_html=True)
               
                if st.button(" ", key=f"btn_{name}", type="tertiary", use_container_width=True):
                    st.session_state.selected_contractor = name
                    st.rerun()

            st.write("")
            req_disabled = (st.session_state.selected_contractor == "")
            if st.button(loc['request'], type="primary", disabled=req_disabled, use_container_width=True, key="btn_req"):
                st.session_state.svc_stage = "receipt"
                st.rerun()

        elif st.session_state.svc_stage == "receipt":
            st.button("✖", key="rec_x", type="secondary", on_click=close_all_popups)
            st.markdown(f"<div style='color: white; font-size: {f_title}; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.5); text-align: center; margin-top: -1vh; margin-bottom: 2vh; padding-right: 5vw;'>{loc['receipt_title']}</div>", unsafe_allow_html=True)
           
            rec = f"<div style='background: rgba(255,255,255,0.05); border-radius: 10px; padding: 2vh 4vw; text-align: left; margin-bottom: 2vh; border-left: 3px solid #D4AF37;'><div style='color:#aaa; font-size:{f_lbl};'>{loc['selected']}</div><div style='color:#D4AF37; font-weight:bold; font-size: {f_val}; margin-bottom:1.5vh;'>{st.session_state.selected_contractor}</div><div style='color:#aaa; font-size:{f_lbl};'>{loc['area']}</div><div style='color:white; font-weight:bold; font-size: {f_val}; margin-bottom:1vh;'>{area:.1f} m²</div><div style='color:#aaa; font-size:{f_lbl};'>{loc['units']}</div><div style='color:white; font-weight:bold; font-size: {f_val}; margin-bottom:1vh;'>{units} ({panel_w}W)</div><div style='color:#aaa; font-size:{f_lbl};'>{loc['cost']}</div><div style='color:#D4AF37; font-size:{f_big}; font-weight:bold;'>{install_cost:,.0f} SAR</div></div>"
            st.markdown(rec, unsafe_allow_html=True)
           
            b1, b2 = st.columns(2)
            with b1:
                if st.button(loc['cancel'], type="secondary", use_container_width=True, key="btn_cancel"):
                    st.session_state.svc_stage = "list"
                    st.rerun()
            with b2:
                if st.button(loc['confirm'], type="primary", use_container_width=True, key="btn_confirm"):
                    st.session_state.svc_stage = "submitting"
                    st.rerun()

        elif st.session_state.svc_stage == "submitting":
            st.button("✖", key="sub_x", type="secondary", on_click=close_all_popups)
            st.markdown(f"<div class='scanner-ring'></div><div style='text-align:center; color:#D4AF37; font-size:{f_val}; font-weight:bold; margin-top:3vh;'>{loc['finalizing']}</div>", unsafe_allow_html=True)
            time.sleep(1.5); st.session_state.svc_stage = "success"; st.rerun()

        elif st.session_state.svc_stage == "success":
            st.button("✖", key="suc_x", type="secondary", on_click=close_all_popups)
            st.markdown(f"<div class='checkmark-circle'><div style='color:#D4AF37; font-size:8vw; font-weight:bold;'>✔</div></div><div style='text-align:center; color:#D4AF37; font-size:{f_succ_tit}; font-weight:bold; margin-top: 1.5vh;'>{loc['success']}</div><div style='text-align:center; color:white; font-size:{f_succ_sub}; margin-top:1.5vh; line-height: 1.4; margin-bottom: 2vh;'>{loc['success_sub']}<br><span style='color:#aaa; font-size: {f_lbl};'>ID: #RYD-{int(time.time() % 10000)}</span></div>", unsafe_allow_html=True)
