import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from streamlit_calendar import calendar
from streamlit_gsheets import GSheetsConnection

# --- 核心連接設定 ---
# 這是根據截圖 提取的專屬 ID
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1xwTYj3hmrXnhPpmDEyq_NVTqvNd1884-Fqk3Q2YsciY/edit#gid=0"

ADMIN_PASSWORD = "tfboys0921"
FIXED_SLOTS = ["14:00", "16:00", "18:00"]

st.set_page_config(page_title="專業雲端預約系統", layout="wide")

# 初始化 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

def load_gsheet(sheet_name):
    # ttl=0 確保每次都讀取最新資料而不使用快取
    return conn.read(spreadsheet=GSHEET_URL, worksheet=sheet_name, ttl=0).astype(str)

def save_gsheet(df, sheet_name):
    conn.update(spreadsheet=GSHEET_URL, worksheet=sheet_name, data=df)
    st.cache_data.clear()

# 嘗試讀取雲端資料
try:
    df = load_gsheet("appointments")
    config_df = load_gsheet("config")
    off_df = load_gsheet("off_slots")
except:
    st.error("❌ 無法連接 Google Sheets。請確認表格權限已設為『知道連結的任何人都能編輯』")
    st.stop()

# --- CSS 樣式 ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    .stButton>button { height: 3.5rem; font-weight: bold; border-radius: 15px; background-color: #FF69B4; color: white; border: none; width: 100%; }
    .selected-date-box { font-size: 1.8rem; color: #D44E7D; font-weight: bold; text-align: center; background: #FFF0F5; padding: 20px; border-radius: 15px; border: 4px solid #FFB6C1; margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.title("🎀 系統功能")
mode = st.sidebar.radio("模式切換", ["👤 客戶預約", "🔐 店家管理"])

if mode == "👤 客戶預約":
    st.markdown("<h1 style='text-align:center; color:#D44E7D;'>🌸 歡迎線上預約 🌸</h1>", unsafe_allow_html=True)
    
    # 計算預約狀況
    active_df = df[df["狀態"] != "已取消"] if not df.empty else pd.DataFrame()
    event_list = []
    for i in range(0, 45):
        d = date.today() + timedelta(days=i)
        d_str = str(d)
        booked = active_df[active_df["日期"] == d_str]["開始時段"].tolist() if not active_df.empty else []
        closed = off_df[off_df["日期"] == d_str]["關閉時段"].tolist() if not off_df.empty else []
        if len(set(booked + closed)) < len(FIXED_SLOTS):
            event_list.append({"title": "● 有空檔", "start": d_str, "allDay": True, "color": "#D4EFDF", "textColor": "#1D8348"})
        else:
            event_list.append({"title": "已滿", "start": d_str, "allDay": True, "color": "#FADBD8", "textColor": "#943126"})

    res = calendar(events=event_list, options={"locale": "zh-tw", "height": 550, "timeZone": "UTC"}, key="cloud_cal")

    # 日期選擇邏輯
    sel_date_str = str(date.today())
    if res.get("callback") in ["dateClick", "select"]:
        cb = res.get("dateClick") or res.get("select")
        sel_date_str = (cb.get("date") or cb.get("start")).split("T")[0][:10]

    st.markdown(f"<div class='selected-date-box'>📅 選中日期：{sel_date_str}</div>", unsafe_allow_html=True)
    
    booked_now = df[(df["日期"] == sel_date_str) & (df["狀態"] != "已取消")]["開始時段"].tolist() if not df.empty else []
    closed_now = off_df[off_df["日期"] == sel_date_str]["關閉時段"].tolist() if not off_df.empty else []
    available_slots = [s for s in FIXED_SLOTS if s not in booked_now and s not in closed_now]

    if not available_slots:
        st.warning("當天已無名額。")
    else:
        with st.form("booking_form", clear_on_submit=True):
            c1, c2 = st.columns([1, 2])
            with c1:
                sel_time = st.radio("開始時間", available_slots, horizontal=True)
            with c2:
                name = st.text_input("姓名*")
                phone = st.text_input("電話*")
            
            items = config_df["項目名稱"].tolist() if not config_df.empty else []
            sel_items = st.multiselect("施作項目 (每項 2 小時)*", items)
            
            total_p = sum([int(config_df[config_df["項目名稱"] == i]["價格"].values[0]) for i in sel_items]) if sel_items else 0
            st.write(f"💰 **總金額預估：${total_p}**")
            
            if st.form_submit_button("🚀 確認預約"):
                if name and phone and sel_items:
                    start_dt = datetime.strptime(sel_time, "%H:%M")
                    end_t = (start_dt + timedelta(hours=len(sel_items)*2)).strftime("%H:%M")
                    new_rec = pd.DataFrame([[sel_date_str, sel_time, end_t, name, "女", " + ".join(sel_items), phone, str(total_p), "預約成功", ""]], columns=df.columns)
                    save_gsheet(pd.concat([df, new_rec]), "appointments")
                    st.success("✅ 預約成功！資料已同步至雲端表格。")
                    st.balloons()
                else:
                    st.error("請填寫姓名、電話與項目。")

else:
    # --- 後台管理 ---
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        t1, t2, t3 = st.tabs(["📊 排程看板", "🛠️ 管理設定", "📋 資料總表"])
        with t1:
            events = []
            if not df.empty:
                for _, r in df.iterrows():
                    if r["狀態"] != "已取消":
                        events.append({"title": f"{r['開始時段']} {r['客人姓名']} ({r['項目']})", "start": r["日期"], "color": "#FF69B4"})
            calendar(events=events, options={"locale": "zh-tw", "height": 600})
        with t2:
            st.subheader("項目價格設定")
            new_conf = st.data_editor(config_df, num_rows="dynamic", use_container_width=True)
            if st.button("更新項目"): save_gsheet(new_conf, "config")
            st.divider()
            st.subheader("店休管理")
            new_off = st.data_editor(off_df, num_rows="dynamic", use_container_width=True)
            if st.button("更新店休"): save_gsheet(new_off, "off_slots")
        with t3:
            st.subheader("雲端資料總表")
            new_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("同步資料變更"): save_gsheet(new_df, "appointments")
    elif pwd != "":
        st.error("密碼錯誤")
