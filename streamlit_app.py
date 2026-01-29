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

# --- 網頁配置 ---
st.set_page_config(page_title="專業美業雲端預約系統", layout="wide")

# 加強版 CSS：包含「點選高亮」邏輯
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    
    /* 讓選中的日期格子變色 (高亮功能) */
    .fc-daygrid-day.fc-day-today { background-color: #FFF0F5 !important; } /* 今日顏色 */
    .fc-highlight { background: #FFB6C1 !important; opacity: 0.6 !important; } /* 點擊選中顏色 */
    
    /* 標題與按鈕 */
    h1 { color: #D44E7D !important; text-align: center; }
    .stButton>button { 
        height: 3.8rem; font-weight: bold; font-size: 1.2rem; border-radius: 20px; 
        background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%); 
        color: white; border: none; box-shadow: 0 4px 15px rgba(255, 105, 180, 0.3);
    }
    
    /* 選中日期的大盒子 */
    .selected-date-box { 
        font-size: 1.8rem; color: #D44E7D; font-weight: bold; text-align: center; 
        background: #FFFFFF; padding: 20px; border-radius: 20px; 
        border: 4px solid #FF69B4; margin: 20px 0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    
    .price-card {
        background: #FFF9FA; padding: 15px; border-radius: 15px; 
        border: 2px dashed #FF69B4; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 載入資料
@st.cache_data(ttl=5)
def load_all_data():
    try:
        app_df = pd.read_csv(get_gs_url("appointments")).astype(str)
        conf_df = pd.read_csv(get_gs_url("config")).astype(str)
        off_df = pd.read_csv(get_gs_url("off_slots")).astype(str)
        return app_df, conf_df, off_df
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df, config_df, off_df = load_all_data()

st.sidebar.markdown("## 🎀 選單")
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

    # 月曆配置：開啟 selectable 並設定高亮
    cal_res = calendar(
        events=event_list, 
        options={
            "locale": "zh-tw", 
            "selectable": True,  # 開啟選取功能
            "unselectAuto": False, # 點擊旁邊不自動取消選取
            "selectMirror": True,
            "height": 580, 
            "timeZone": "UTC"
        }, 
        key="pretty_cal_v2"
    )

    # 抓取選取日期
    sel_date = str(date.today())
    if cal_res.get("callback") in ["dateClick", "select"]:
        cb = cal_res.get("dateClick") or cal_res.get("select")
        sel_date = cb.get("date", cb.get("start")).split("T")[0][:10]

    st.markdown(f"<div class='selected-date-box'>📍 您選中的日期：{sel_date}</div>", unsafe_allow_html=True)

    # 預約時段邏輯
    booked_now = df[(df["日期"] == sel_date) & (df["狀態"] != "已取消")]["開始時段"].tolist() if not df.empty else []
    closed_now = off_df[off_df["日期"] == sel_date]["關閉時段"].tolist() if not off_df.empty else []
    available = [s for s in FIXED_SLOTS if s not in booked_now and s not in closed_now]

    if not available:
        st.error(f"💔 抱歉，{sel_date} 已經被約滿了！")
    else:
        with st.form("booking_form"):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown("### 🕒 開始時間")
                sel_time = st.radio("", available, horizontal=True)
            with c2:
                st.markdown("### 👤 聯絡資料")
                sc1, sc2 = st.columns(2)
                name = sc1.text_input("您的姓名*")
                phone = sc2.text_input("手機號碼*")
            
            st.divider()
            item_names = config_df["項目名稱"].tolist() if not config_df.empty else []
            sel_items = st.multiselect("施作項目 (可多選，每項 2 小時)*", item_names)
            
            total_price = 0
            if sel_items:
                for i in sel_items:
                    p = config_df[config_df["項目名稱"] == i]["價格"].values[0]
                    total_price += int(p)
            
            st.markdown(f"""
                <div class='price-card'>
                    <span style='color:#555;'>總金額預估：</span><br>
                    <span style='font-size:1.8rem; color:#E74C3C; font-weight:bold;'>$ {total_price}</span>
                </div>
            """, unsafe_allow_html=True)
            
            if st.form_submit_button("🚀 確定預約"):
                if name and phone and sel_items:
                    st.success(f"🎊 預約請求已發送！請截圖告知店家。")
                    st.balloons()
                else:
                    st.error("請填寫完整姓名、電話與項目。")
else:
    # 後台管理... (維持原樣)
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        st.dataframe(df)
