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
    h1 { color: #D44E7D !important; text-align: center; font-weight: bold; }
    .selected-date-box { 
        font-size: 1.6rem; color: #D44E7D; font-weight: bold; text-align: center; 
        background: white; padding: 20px; border-radius: 20px; border: 4px solid #FF69B4; margin: 20px 0;
    }
    .stButton>button { 
        height: 3.8rem; font-weight: bold; border-radius: 20px; 
        background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%); color: white; border: none;
    }
    .stForm { background-color: white; padding: 25px; border-radius: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 資料讀取與洗淨 ---
@st.cache_data(ttl=2)
def load_all_data():
    try:
        def clean_df(url):
            raw = pd.read_csv(url)
            # 移除隱形編碼字元與空白
            raw.columns = raw.columns.str.replace(r'[^\w]', '', regex=True).str.strip()
            return raw.astype(str)
        return clean_df(get_gs_url("appointments")), clean_df(get_gs_url("config")), clean_df(get_gs_url("off_slots"))
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df, config_df, off_df = load_all_data()

st.sidebar.title("🎀 系統選單")
mode = st.sidebar.radio("", ["👤 客戶線上預約", "🔐 店家管理後台"])

if mode == "👤 客戶線上預約":
    st.markdown("<h1>🌸 專業美業預約系統 🌸</h1>", unsafe_allow_html=True)
    
    # 建立月曆事件 (計算空檔)
    event_list = []
    for i in range(0, 45):
        d = today_tw + timedelta(days=i)
        d_str = str(d)
        # 抓取表格中當天已經被約掉的時段
        booked = df[df["日期"] == d_str]["開始時段"].tolist() if not df.empty and "日期" in df.columns else []
        closed = off_df[off_df["日期"] == d_str]["關閉時段"].tolist() if not off_df.empty and "日期" in off_df.columns else []
        
        # 只要預約 + 關閉的時段少於 3 個，就顯示綠色「可預約」
        if len(set(booked + closed)) < len(FIXED_SLOTS):
            event_list.append({"title": "● 可預約", "start": d_str, "allDay": True, "color": "#D4EFDF", "textColor": "#1D8348"})
        else:
            event_list.append({"title": "已滿", "start": d_str, "allDay": True, "color": "#FADBD8", "textColor": "#943126"})

    cal_res = calendar(events=event_list, options={"locale": "zh-tw", "selectable": True, "height": 550, "timeZone": "UTC"}, key="v19_final")

    # 抓取選中日期
    sel_date = str(today_tw)
    if cal_res.get("callback") in ["dateClick", "select"]:
        cb = cal_res.get("dateClick") or cal_res.get("select")
        sel_date = cb.get("date", cb.get("start")).split("T")[0][:10]

    st.markdown(f"<div class='selected-date-box'>📍 您選中的日期：{sel_date}</div>", unsafe_allow_html=True)

    # --- 關鍵：時段自動消失邏輯 ---
    # 找出該日期已被佔用（且狀態不是已取消）的時段
    booked_now = df[(df["日期"] == sel_date) & (df["狀態"] != "已取消")]["開始時段"].tolist() if not df.empty and "日期" in df.columns else []
    closed_now = off_df[off_df["日期"] == sel_date]["關閉時段"].tolist() if not off_df.empty and "日期" in off_df.columns else []
    
    # 從 FIXED_SLOTS (14,16,18) 中移除已被佔用的時段
    available = [s for s in FIXED_SLOTS if s not in booked_now and s not in closed_now]

    if not available:
        st.error(f"💔 抱歉，{sel_date} 的 14:00、16:00、18:00 均已約滿，請選擇其他日期！")
    else:
        with st.form("booking_form", clear_on_submit=True):
            st.markdown("### 🕒 1. 選擇預約時段")
            sel_time = st.radio("可選擇時段：", available, horizontal=True)
            
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
            col_name = [c for c in config_df.columns if "項目" in c]
            item_list = config_df[col_name[0]].tolist() if col_name else []
            sel_items = st.multiselect("項目可多選 (每項約 2 小時)*", item_list)
            
            if st.form_submit_button("🚀 確定預約"):
                if name and phone and sel_items and line_name:
                    st.success(f"🎊 預約申請已送出！")
                    st.info(f"預約詳情：{sel_date} {sel_time}\n姓名：{name}\nLINE：{line_name}")
                    st.balloons()
                else:
                    st.error("請填寫姓名、LINE暱稱、電話並選擇項目。")
else:
    # 店家管理...
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        st.subheader("📊 預約資料總覽")
        st.dataframe(df, use_container_width=True)
