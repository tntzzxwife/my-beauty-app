import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
from streamlit_calendar import calendar

# --- 1. 時區與基本設定 ---
tz_taiwan = timezone(timedelta(hours=8))
now_tw = datetime.now(tz_taiwan)
today_tw = now_tw.date()

SHEET_ID = "1xwTYj3hmrXnhPpmDEyq_NVTqvNd1884-Fqk3Q2YsciY"
def get_gs_url(sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

ADMIN_PASSWORD = "tfboys0921"
FIXED_SLOTS = ["14:00", "16:00", "18:00"]

st.set_page_config(page_title="專業雲端預約系統", layout="wide")

# --- 2. 資料讀取 (強化防錯版) ---
@st.cache_data(ttl=2)
def load_all_data():
    def clean_df(url):
        try:
            raw = pd.read_csv(url)
            # 清除所有標題的隱形字元與空格
            raw.columns = raw.columns.str.replace(r'[^\w]', '', regex=True).str.strip()
            return raw.astype(str)
        except:
            return pd.DataFrame()
    
    return clean_df(get_gs_url("appointments")), clean_df(get_gs_url("config")), clean_df(get_gs_url("off_slots"))

df, config_df, off_df = load_all_data()

# --- 3. 介面美化 ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    h1 { color: #D44E7D !important; text-align: center; }
    .stButton>button { border-radius: 20px; background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%); color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.title("🎀 系統功能")
mode = st.sidebar.radio("", ["👤 客戶線上預約", "🔐 店家管理後台"])

if mode == "👤 客戶線上預約":
    st.markdown("<h1>🌸 歡迎預約您的美麗時光 🌸</h1>", unsafe_allow_html=True)
    
    # 月曆顯示邏輯 (略，與前版相同)
    event_list = []
    # (此處程式碼會根據 df 內的日期與時段自動隱藏已被預約的時段)
    
    # --- 顯示選取日期與表單 ---
    # ... (此處代碼同前一版，包含性別、LINE暱稱、推薦人等欄位)
    st.info("請填寫預約表單...")

else:
    # --- 4. 後台管理 (修正看不到資料的問題) ---
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        st.markdown("## 🔐 雲端管理中心")
        
        if df.empty:
            st.warning("⚠️ 目前雲端表格是空的，或連線異常。請確認 Google 表格權限。")
        else:
            t1, t2 = st.tabs(["📊 預約看板", "📋 完整清單"])
            with t1:
                events = []
                # 遍歷 df，將資料轉為月曆事件
                for _, r in df.iterrows():
                    # 確保必要的欄位存在才顯示
                    d = r.get("日期", "")
                    t = r.get("開始時段", "")
                    n = r.get("客人姓名", "未知")
                    s = r.get("狀態", "")
                    
                    if d and d != "nan" and s != "已取消":
                        events.append({"title": f"{t} {n}", "start": d, "color": "#FF69B4"})
                
                calendar(events=events, options={"locale": "zh-tw", "height": 600})
            
            with t2:
                st.write("### 所有的預約紀錄：")
                # 移除重複的標題行並顯示
                clean_display = df[df["日期"] != "日期"]
                st.dataframe(clean_display, use_container_width=True)
                
    elif pwd != "":
        st.error("密碼錯誤")
