import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
from streamlit_calendar import calendar

# --- 1. 時區修正 (確保日期不偏移) ---
tz_taiwan = timezone(timedelta(hours=8))
now_tw = datetime.now(tz_taiwan)
today_tw = now_tw.date()

SHEET_ID = "1xwTYj3hmrXnhPpmDEyq_NVTqvNd1884-Fqk3Q2YsciY"
def get_gs_url(sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

ADMIN_PASSWORD = "tfboys0921"
# 這是你要求的固定時段
FIXED_SLOTS = ["14:00", "16:00", "18:00"]

st.set_page_config(page_title="專業雲端預約系統", layout="wide")

# --- CSS 樣式 ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    .fc .fc-highlight { background: rgba(255, 105, 180, 0.4) !important; }
    h1 { color: #D44E7D !important; text-align: center; }
    .selected-date-box { 
        font-size: 1.8rem; color: #D44E7D; font-weight: bold; text-align: center; 
        background: white; padding: 20px; border-radius: 20px; border: 4px solid #FF69B4; margin: 20px 0;
    }
    /* 讓時段選擇器更好看 */
    .stRadio [data-testid="stMarkdownContainer"] { font-size: 1.2rem; font-weight: bold; color: #D44E7D; }
    .stButton>button { 
        height: 3.8rem; font-weight: bold; border-radius: 20px; 
        background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%); color: white; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 資料讀取 (強化容錯) ---
@st.cache_data(ttl=2)
def load_all_data():
    try:
        def clean_df(url):
            raw = pd.read_csv(url)
            raw.columns = raw.columns.str.replace(r'[^\w]', '', regex=True).str.strip()
            return raw.astype(str)
        return clean_df(get_gs_url("appointments")), clean_df(get_gs_url("config")), clean_df(get_gs_url("off_slots"))
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df, config_df, off_df = load_all_data()

st.sidebar.title("🎀 選單")
mode = st.sidebar.radio("", ["👤 客戶線上預約", "🔐 店家管理後台"])

if mode == "👤 客戶線上預約":
    st.markdown("<h1>🌸 歡迎預約您的美麗時光 🌸</h1>", unsafe_allow_html=True)
    
    # 建立月曆事件 (計算空檔)
    event_list = []
    for i in range(0, 45):
        d = today_tw + timedelta(days=i)
        d_str = str(d)
        booked = df[df["日期"] == d_str]["開始時段"].tolist() if not df.empty and "日期" in df.columns else []
        closed = off_df[off_df["日期"] == d_str]["關閉時段"].tolist() if not off_df.empty and "日期" in off_df.columns else []
        
        # 只要預約 + 關閉的時段少於 3 個，就顯示有空檔
        if len(set(booked + closed)) < len(FIXED_SLOTS):
            event_list.append({"title": "● 可預約", "start": d_str, "allDay": True, "color": "#D4EFDF", "textColor": "#1D8348"})
        else:
            event_list.append({"title": "已滿", "start": d_str, "allDay": True, "color": "#FADBD8", "textColor": "#943126"})

    cal_res = calendar(events=event_list, options={"locale": "zh-tw", "selectable": True, "height": 550, "timeZone": "UTC"}, key="v18_final")

    # 抓取選中日期 (處理時區偏移)
    sel_date = str(today_tw)
    if cal_res.get("callback") in ["dateClick", "select"]:
        cb = cal_res.get("dateClick") or cal_res.get("select")
        sel_date = cb.get("date", cb.get("start")).split("T")[0][:10]

    st.markdown(f"<div class='selected-date-box'>📍 您選中的日期：{sel_date}</div>", unsafe_allow_html=True)

    # --- 關鍵：時段選擇邏輯 ---
    # 找出該日期已被佔用的時段
    booked_now = df[(df["日期"] == sel_date) & (df["狀態"] != "已取消")]["開始時段"].tolist() if not df.empty and "日期" in df.columns else []
    closed_now = off_df[off_df["日期"] == sel_date]["關閉時段"].tolist() if not off_df.empty and "日期" in off_df.columns else []
    
    # 過濾出還能選的時段
    available = [s for s in FIXED_SLOTS if s not in booked_now and s not in closed_now]

    if not available:
        st.error(f"💔 抱歉，{sel_date} 的 14:00、16:00、18:00 均已約滿！")
    else:
        with st.form("booking_form", clear_on_submit=True):
            st.markdown("### 🕒 選擇預約時段")
            # 讓這三個時段以按鈕形式橫向排開
            sel_time = st.radio("可預約時段：", available, horizontal=True)
            
            st.divider()
            st.markdown("### 👤 填寫資料")
            c1, c2 = st.columns(2)
            name = c1.text_input("您的姓名*")
            phone = c2.text_input("手機號碼*")
            
            # 項目選單
            col_name = [c for c in config_df.columns if "項目" in c]
            item_list = config_df[col_name[0]].tolist() if col_name else []
            sel_items = st.multiselect("施作項目 (多選)*", item_list)
            
            if st.form_submit_button("🚀 確定送出預約"):
                if name and phone and sel_items:
                    st.success(f"🎊 預約申請已送出！時段：{sel_date} {sel_time}")
                    st.info("請截圖此畫面並告知店家唷！")
                    st.balloons()
                else:
                    st.error("請完整填寫姓名、電話與項目。")
