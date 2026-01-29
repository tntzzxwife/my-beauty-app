import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from streamlit_calendar import calendar

SHEET_ID = "1xwTYj3hmrXnhPpmDEyq_NVTqvNd1884-Fqk3Q2YsciY"
def get_gs_url(sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

ADMIN_PASSWORD = "tfboys0921"
FIXED_SLOTS = ["14:00", "16:00", "18:00"]

st.set_page_config(page_title="專業雲端預約系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    /* 月曆點擊亮起功能 */
    .fc .fc-highlight { background: rgba(255, 105, 180, 0.4) !important; }
    .fc-daygrid-day.fc-day-today { background-color: #FFF0F5 !important; }
    h1 { color: #D44E7D !important; text-align: center; }
    .selected-date-box { 
        font-size: 1.8rem; color: #D44E7D; font-weight: bold; text-align: center; 
        background: white; padding: 20px; border-radius: 20px; border: 4px solid #FF69B4; 
    }
    .stButton>button { 
        height: 3.8rem; font-weight: bold; border-radius: 20px; 
        background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%); color: white; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=2)
def load_all_data():
    try:
        a = pd.read_csv(get_gs_url("appointments")).astype(str)
        c = pd.read_csv(get_gs_url("config")).astype(str)
        o = pd.read_csv(get_gs_url("off_slots")).astype(str)
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
    
    event_list = []
    # 建立月曆事件 (略...) 
    # (此處邏輯與前版一致，確保有 title 和 start)
    
    cal_res = calendar(events=event_list, options={"locale": "zh-tw", "selectable": True, "height": 550}, key="v15_cal")

    sel_date = str(date.today())
    if cal_res.get("callback") in ["dateClick", "select"]:
        cb = cal_res.get("dateClick") or cal_res.get("select")
        sel_date = cb.get("date", cb.get("start")).split("T")[0][:10]

    st.markdown(f"<div class='selected-date-box'>📍 您選中的日期：{sel_date}</div>", unsafe_allow_html=True)

    # 檢查欄位是否存在，避免 KeyError
    if "項目名稱" in config_df.columns:
        item_list = config_df["項目名稱"].tolist()
    else:
        item_list = ["請檢查 Google 表格 config 分頁的標題"]

    with st.form("booking_form"):
        # 時段選擇、姓名電話 (略...)
        sel_items = st.multiselect("選擇施作項目", item_list)
        if st.form_submit_button("🚀 確定預約"):
            st.success("測試成功！")
            st.balloons()
