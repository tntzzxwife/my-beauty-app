import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
from streamlit_calendar import calendar

# --- 1. 時區修正 (台北時間 UTC+8) ---
tz_taiwan = timezone(timedelta(hours=8))
now_tw = datetime.now(tz_taiwan)
today_tw = now_tw.date()

SHEET_ID = "1xwTYj3hmrXnhPpmDEyq_NVTqvNd1884-Fqk3Q2YsciY"
def get_gs_url(sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

ADMIN_PASSWORD = "tfboys0921"
FIXED_SLOTS = ["14:00", "16:00", "18:00"]

st.set_page_config(page_title="專業雲端預約系統", layout="wide")

# --- CSS 樣式 ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    .fc .fc-highlight { background: rgba(255, 105, 180, 0.4) !important; }
    h1 { color: #D44E7D !important; text-align: center; }
    .selected-date-box { 
        font-size: 1.6rem; color: #D44E7D; font-weight: bold; text-align: center; 
        background: white; padding: 20px; border-radius: 20px; border: 4px solid #FF69B4; margin: 20px 0;
    }
    .stButton>button { 
        height: 3.8rem; font-weight: bold; border-radius: 20px; 
        background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%); color: white; border: none; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 資料讀取 (強化防錯) ---
@st.cache_data(ttl=1)
def load_all_data():
    def clean_df(url):
        try:
            raw = pd.read_csv(url)
            raw.columns = raw.columns.str.replace(r'[^\w]', '', regex=True).str.strip()
            return raw.astype(str)
        except:
            return pd.DataFrame()
    return clean_df(get_gs_url("appointments")), clean_df(get_gs_url("config")), clean_df(get_gs_url("off_slots"))

df, config_df, off_df = load_all_data()

st.sidebar.title("🎀 選單")
mode = st.sidebar.radio("", ["👤 客戶線上預約", "🔐 店家管理後台"])

if mode == "👤 客戶線上預約":
    st.markdown("<h1>🌸 預約您的美麗時光 🌸</h1>", unsafe_allow_html=True)
    
    # --- 月曆事件計算 ---
    event_list = []
    for i in range(0, 45):
        d = today_tw + timedelta(days=i)
        d_str = str(d)
        event_list.append({"title": "● 可預約", "start": d_str, "allDay": True, "color": "#D4EFDF", "textColor": "#1D8348"})

    cal_res = calendar(events=event_list, options={"locale": "zh-tw", "selectable": True, "height": 500, "timeZone": "UTC"}, key="v20_fix")

    # 抓取選中日期
    sel_date = str(today_tw)
    if cal_res.get("callback") in ["dateClick", "select"]:
        cb = cal_res.get("dateClick") or cal_res.get("select")
        sel_date = cb.get("date", cb.get("start")).split("T")[0][:10]

    st.markdown(f"<div class='selected-date-box'>📍 您選中的日期：{sel_date}</div>", unsafe_allow_html=True)

    # --- 強制顯示 14, 16, 18 時段 (不論表格是否有資料) ---
    with st.form("booking_form"):
        st.markdown("### 🕒 1. 選擇預約時段")
        # 即使表格是空的，也讓這三個出現
        sel_time = st.radio("可選擇時段：", FIXED_SLOTS, horizontal=True)
        
        st.divider()
        st.markdown("### 👤 2. 填寫基本資料")
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("客人姓名*")
        gender = c2.selectbox("性別*", ["女性", "男性", "其他"])
        line_name = c3.text_input("LINE 暱稱*")
        
        c4, c5 = st.columns(2)
        phone = c4.text_input("手機號碼*")
        referral = c5.text_input("推薦人 (選填)")

        st.divider()
        st.markdown("### 🛠️ 3. 選擇施作項目")
        # 抓取項目
        item_list = []
        if not config_df.empty:
            col_name = [c for c in config_df.columns if "項目" in c]
            if col_name: item_list = config_df[col_name[0]].tolist()
        
        if not item_list: item_list = ["基礎保養", "精緻美甲", "美睫設計"] # 防呆選項
        
        sel_items = st.multiselect("項目可多選*", item_list)
        
        if st.form_submit_button("🚀 確定送出預約"):
            if name and phone and sel_items:
                st.success(f"✅ 預約申請已送出！請通知店家。")
                st.info(f"日期：{sel_date} | 時段：{sel_time}")
                st.balloons()
            else:
                st.error("請完整填寫姓名、電話與項目。")
else:
    # --- 後台管理 ---
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        st.markdown("## 🔐 預約管理中心")
        st.dataframe(df, use_container_width=True)
    elif pwd != "":
        st.error("密碼錯誤")
