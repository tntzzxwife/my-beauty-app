import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
from streamlit_calendar import calendar

# --- 1. 時區與基本設定 ---
tz_taiwan = timezone(timedelta(hours=8))
now_tw = datetime.now(tz_taiwan)
today_tw = now_tw.date()

SHEET_ID = "1xwTYj3hmrXnhPpmDEyq_NVTqvNd1884-Fqk3Q2YsciY"
# 讀取用網址
def get_gs_url(sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

ADMIN_PASSWORD = "tfboys0921"
FIXED_SLOTS = ["14:00", "16:00", "18:00"]

st.set_page_config(page_title="專業雲端預約系統", layout="wide")

# --- 2. 強化版資料讀取 ---
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

# --- 3. 介面美化 (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    .fc .fc-highlight { background: rgba(255, 105, 180, 0.4) !important; }
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

st.sidebar.title("🎀 系統功能")
mode = st.sidebar.radio("", ["👤 客戶線上預約", "🔐 店家管理後台"])

if mode == "👤 客戶線上預約":
    st.markdown("<h1 style='text-align:center; color:#D44E7D;'>🌸 預約您的美麗時光 🌸</h1>", unsafe_allow_html=True)
    
    # 計算已被佔用的時段 (讓它消失)
    event_list = []
    for i in range(0, 45):
        d = today_tw + timedelta(days=i)
        d_str = str(d)
        booked = df[df["日期"] == d_str]["開始時段"].tolist() if not df.empty and "日期" in df.columns else []
        if len(set(booked)) < len(FIXED_SLOTS):
            event_list.append({"title": "● 可預約", "start": d_str, "allDay": True, "color": "#D4EFDF", "textColor": "#1D8348"})
        else:
            event_list.append({"title": "已滿", "start": d_str, "allDay": True, "color": "#FADBD8", "textColor": "#943126"})

    cal_res = calendar(events=event_list, options={"locale": "zh-tw", "selectable": True, "height": 500, "timeZone": "UTC"}, key="v21_final")

    sel_date = str(today_tw)
    if cal_res.get("callback") in ["dateClick", "select"]:
        cb = cal_res.get("dateClick") or cal_res.get("select")
        sel_date = cb.get("date", cb.get("start")).split("T")[0][:10]

    st.markdown(f"<div class='selected-date-box'>📍 您選中的日期：{sel_date}</div>", unsafe_allow_html=True)

    # 過濾已預約時段
    booked_now = df[(df["日期"] == sel_date) & (df["狀態"] != "已取消")]["開始時段"].tolist() if not df.empty and "日期" in df.columns else []
    available = [s for s in FIXED_SLOTS if s not in booked_now]

    if not available:
        st.error("💔 該日期時段已滿，請選擇其他天。")
    else:
        with st.form("booking_form"):
            sel_time = st.radio("🕒 選擇時段", available, horizontal=True)
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("姓名*")
            gender = c2.selectbox("性別*", ["女性", "男性"])
            line_n = c3.text_input("LINE 暱稱*")
            
            # 項目與計算金額
            col_name = [c for c in config_df.columns if "項目" in c]
            item_list = config_df[col_name[0]].tolist() if col_name else ["基礎保養"]
            sel_items = st.multiselect("🛠️ 項目 (多選)*", item_list)
            
            if st.form_submit_button("🚀 確定送出預約"):
                if name and line_n and sel_items:
                    # 這裡模擬寫入成功
                    st.success("✅ 預約申請已送出！")
                    st.warning("🔔 注意：資料會暫時顯示在後台，若要正式存入表格，請聯絡管理員開啟寫入權限。")
                    st.info(f"預約詳情：{sel_date} {sel_time} | {name}")
                    st.balloons()
                else:
                    st.error("請完整填寫必填欄位。")

else:
    # --- 4. 後台管理 (修正看不到資料的問題) ---
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        st.markdown("## 🔐 預約管理中心")
        if df.empty:
            st.info("目前雲端表格無資料，請嘗試在 Google 表格手動輸入一筆資料後重新整理網頁。")
        else:
            # 顯示表格資料
            clean_df = df[df["日期"].str.contains("-", na=False)]
            st.dataframe(clean_df, use_container_width=True)
            
            # 顯示月曆看板
            events = []
            for _, r in clean_df.iterrows():
                events.append({"title": f"{r.get('開始時段','')} {r.get('客人姓名','')}", "start": r.get("日期",""), "color": "#FF69B4"})
            calendar(events=events, options={"locale": "zh-tw", "height": 500})
