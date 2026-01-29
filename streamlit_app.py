import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from streamlit_calendar import calendar

# --- 直接連線設定 (跳過 Secrets) ---
SHEET_ID = "1xwTYj3hmrXnhPpmDEyq_NVTqvNd1884-Fqk3Q2YsciY"
# 這是 Google Sheets 的匯出格式網址
def get_gsheet_url(sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

ADMIN_PASSWORD = "tfboys0921"
FIXED_SLOTS = ["14:00", "16:00", "18:00"]

st.set_page_config(page_title="專業雲端預約系統", layout="wide")

# 加載資料
@st.cache_data(ttl=10) # 每 10 秒自動刷新
def load_data(sheet_name):
    url = get_gsheet_url(sheet_name)
    return pd.read_csv(url).astype(str)

try:
    df = load_data("appointments")
    config_df = load_data("config")
    off_df = load_data("off_slots")
except Exception as e:
    st.error(f"❌ 讀取失敗，請確認 Google 表格右上方『共用』已設為『知道連結的任何人都能編輯』")
    st.info("目前的錯誤訊息：" + str(e))
    st.stop()

# --- CSS 樣式 ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    .stButton>button { height: 3.5rem; font-weight: bold; border-radius: 15px; background-color: #FF69B4; color: white; border: none; }
    .selected-date-box { font-size: 1.8rem; color: #D44E7D; font-weight: bold; text-align: center; background: #FFF0F5; padding: 20px; border-radius: 15px; border: 4px solid #FFB6C1; margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.title("🎀 預約選單")
mode = st.sidebar.radio("切換模式", ["👤 客戶預約", "🔐 店家管理"])

if mode == "👤 客戶預約":
    st.markdown("<h1 style='text-align:center; color:#D44E7D;'>🌸 歡迎預約美容時光 🌸</h1>", unsafe_allow_html=True)
    
    # 計算月曆 (僅顯示 45 天內)
    event_list = []
    for i in range(0, 45):
        d = date.today() + timedelta(days=i)
        d_str = str(d)
        booked = df[df["日期"] == d_str]["開始時段"].tolist() if not df.empty else []
        closed = off_df[off_df["日期"] == d_str]["關閉時段"].tolist() if not off_df.empty else []
        if len(set(booked + closed)) < len(FIXED_SLOTS):
            event_list.append({"title": "● 有空檔", "start": d_str, "allDay": True, "color": "#D4EFDF", "textColor": "#1D8348"})
        else:
            event_list.append({"title": "已滿", "start": d_str, "allDay": True, "color": "#FADBD8", "textColor": "#943126"})

    res = calendar(events=event_list, options={"locale": "zh-tw", "height": 550, "timeZone": "UTC"}, key="v14_cal")

    sel_date_str = str(date.today())
    if res.get("callback") in ["dateClick", "select"]:
        cb = res.get("dateClick") or res.get("select")
        sel_date_str = (cb.get("date") or cb.get("start")).split("T")[0][:10]

    st.markdown(f"<div class='selected-date-box'>📅 您選中的日期：{sel_date_str}</div>", unsafe_allow_html=True)
    
    booked_now = df[(df["日期"] == sel_date_str) & (df["狀態"] != "已取消")]["開始時段"].tolist() if not df.empty else []
    closed_now = off_df[off_df["日期"] == sel_date_str]["關閉時段"].tolist() if not off_df.empty else []
    available_slots = [s for s in FIXED_SLOTS if s not in booked_now and s not in closed_now]

    if not available_slots:
        st.warning("⚠️ 此日期已滿，請選擇其他日期。")
    else:
        with st.form("booking_form"):
            c1, c2 = st.columns([1, 2])
            with c1:
                sel_time = st.radio("開始時間", available_slots, horizontal=True)
            with c2:
                name = st.text_input("姓名*")
                phone = st.text_input("電話*")
            
            items = config_df["項目名稱"].tolist() if not config_df.empty else []
            sel_items = st.multiselect("施作項目 (每項 2 小時)", items)
            
            if st.form_submit_button("🚀 確認送出預約"):
                if name and phone and sel_items:
                    # 提示：由於這版是直接讀取，寫入功能會引導至 Google Form 或保持讀取
                    st.success(f"🎉 測試成功！預約資料已準備好。")
                    st.info("備註：由於 Streamlit 的寫入限制，如需全自動寫入 Google 表格，請點擊右側選單聯絡管理員。")
                else:
                    st.error("請填寫姓名、電話與項目。")

else:
    # --- 後台管理 ---
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        st.subheader("📊 雲端排程同步中")
        events = [{"title": f"{r['開始時段']} {r['客人姓名']}", "start": r["日期"], "color": "#FF69B4"} for _, r in df.iterrows()]
        calendar(events=events, options={"locale": "zh-tw", "height": 600})
        st.dataframe(df, use_container_width=True)
