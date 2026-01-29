import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from streamlit_calendar import calendar

# --- 核心連線設定 ---
SHEET_ID = "1xwTYj3hmrXnhPpmDEyq_NVTqvNd1884-Fqk3Q2YsciY"
def get_gs_url(sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

ADMIN_PASSWORD = "tfboys0921"
FIXED_SLOTS = ["14:00", "16:00", "18:00"]

st.set_page_config(page_title="專業雲端預約系統", layout="wide")

# --- 加強版 CSS：包含點選高亮功能 ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    /* 月曆點擊高亮 (Highlight) 顏色 */
    .fc .fc-highlight { background: rgba(255, 105, 180, 0.4) !important; }
    .fc-daygrid-day.fc-day-today { background-color: #FFF0F5 !important; }
    
    h1 { color: #D44E7D !important; text-align: center; }
    .selected-date-box { 
        font-size: 1.8rem; color: #D44E7D; font-weight: bold; text-align: center; 
        background: white; padding: 20px; border-radius: 20px; 
        border: 4px solid #FF69B4; margin: 20px 0;
    }
    .stButton>button { 
        height: 3.8rem; font-weight: bold; border-radius: 20px; 
        background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%); color: white; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 防呆資料讀取 ---
@st.cache_data(ttl=2)
def load_all_data():
    try:
        # 使用 header=0 並 strip() 移除空白
        a = pd.read_csv(get_gs_url("appointments"), header=0).astype(str)
        c = pd.read_csv(get_gs_url("config"), header=0).astype(str)
        o = pd.read_csv(get_gs_url("off_slots"), header=0).astype(str)
        a.columns = a.columns.str.strip()
        c.columns = c.columns.str.strip()
        o.columns = o.columns.str.strip()
        return a, c, o
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df, config_df, off_df = load_all_data()

st.sidebar.title("🎀 選單")
mode = st.sidebar.radio("", ["👤 客戶線上預約", "🔐 店家管理後台"])

if mode == "👤 客戶線上預約":
    st.markdown("<h1>🌸 歡迎預約您的美麗時光 🌸</h1>", unsafe_allow_html=True)
    
    # 建立月曆事件
    event_list = []
    for i in range(0, 45):
        d = date.today() + timedelta(days=i)
        d_str = str(d)
        booked = df[df["日期"] == d_str]["開始時段"].tolist() if not df.empty else []
        closed = off_df[off_df["日期"] == d_str]["關閉時段"].tolist() if not off_df.empty else []
        if len(set(booked + closed)) < len(FIXED_SLOTS):
            event_list.append({"title": "● 可預約", "start": d_str, "allDay": True, "color": "#D4EFDF", "textColor": "#1D8348"})
        else:
            event_list.append({"title": "已滿", "start": d_str, "allDay": True, "color": "#FADBD8", "textColor": "#943126"})

    # 月曆配置 (啟動 selectable)
    cal_res = calendar(
        events=event_list, 
        options={
            "locale": "zh-tw", 
            "selectable": True, 
            "height": 550,
            "unselectAuto": False 
        }, 
        key="pretty_cal_final"
    )

    # 抓取選中日期
    sel_date = str(date.today())
    if cal_res.get("callback") in ["dateClick", "select"]:
        cb = cal_res.get("dateClick") or cal_res.get("select")
        sel_date = cb.get("date", cb.get("start")).split("T")[0][:10]

    st.markdown(f"<div class='selected-date-box'>📍 您選中的日期：{sel_date}</div>", unsafe_allow_html=True)

    # 項目選單邏輯
    item_list = []
    if not config_df.empty and "項目名稱" in config_df.columns:
        item_list = config_df["項目名稱"].tolist()
    else:
        st.warning("⚠️ 讀取不到項目，請檢查 Google 表格標題是否為『項目名稱』")

    with st.form("booking_form", clear_on_submit=True):
        st.markdown("### 📝 填寫預約資訊")
        col1, col2 = st.columns(2)
        name = col1.text_input("姓名*")
        phone = col2.text_input("電話*")
        
        sel_items = st.multiselect("施作項目 (多選)*", item_list)
        
        # 動態計算金額
        total = 0
        if sel_items and "價格" in config_df.columns:
            for item in sel_items:
                price = config_df[config_df["項目名稱"] == item]["價格"].values[0]
                total += int(price)
        st.write(f"💰 預估金額：${total}")

        if st.form_submit_button("🚀 確定預約"):
            if name and phone and sel_items:
                st.success("✅ 預約已送出！請通知店家確認。")
                st.balloons()
            else:
                st.error("請完整填寫姓名、電話與項目。")
