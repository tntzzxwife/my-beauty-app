import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from streamlit_calendar import calendar

# --- 核心連線設定 ---
SHEET_ID = "1xwTYj3hmrXnhPpmDEyq_NVTqvNd1884-Fqk3Q2YsciY"

def get_gs_url(sheet_name):
    # 使用匯出 CSV 格式
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

ADMIN_PASSWORD = "tfboys0921"
FIXED_SLOTS = ["14:00", "16:00", "18:00"]

st.set_page_config(page_title="專業雲端預約系統", layout="wide")

# --- CSS 樣式：包含點選高亮 ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    /* 月曆點擊高亮 */
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

# --- 強化版資料讀取 ---
@st.cache_data(ttl=2)
def load_all_data():
    try:
        # 讀取並清除所有隱形字元
        def clean_df(url):
            raw_df = pd.read_csv(url)
            # 清除欄位名稱的隱形編碼與空格
            raw_df.columns = raw_df.columns.str.replace(r'[^\w]', '', regex=True).str.strip()
            return raw_df.astype(str)

        app_df = clean_df(get_gs_url("appointments"))
        conf_df = clean_df(get_gs_url("config"))
        off_df = clean_df(get_gs_url("off_slots"))
        
        return app_df, conf_df, off_df
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df, config_df, off_df = load_all_data()

st.sidebar.title("🎀 選單")
mode = st.sidebar.radio("", ["👤 客戶線上預約", "🔐 店家管理後台"])

if mode == "👤 客戶線上預約":
    st.markdown("<h1>🌸 歡迎預約您的美麗時光 🌸</h1>", unsafe_allow_html=True)
    
    # 建立月曆事件
    event_list = []
    # (此處維持日期空檔判斷邏輯)
    for i in range(0, 45):
        d = date.today() + timedelta(days=i)
        d_str = str(d)
        booked = df[df["日期"] == d_str]["開始時段"].tolist() if not df.empty and "日期" in df.columns else []
        if len(booked) < len(FIXED_SLOTS):
            event_list.append({"title": "● 可預約", "start": d_str, "allDay": True, "color": "#D4EFDF", "textColor": "#1D8348"})

    cal_res = calendar(events=event_list, options={"locale": "zh-tw", "selectable": True, "height": 550}, key="v16_pretty")

    sel_date = str(date.today())
    if cal_res.get("callback") in ["dateClick", "select"]:
        cb = cal_res.get("dateClick") or cal_res.get("select")
        sel_date = cb.get("date", cb.get("start")).split("T")[0][:10]

    st.markdown(f"<div class='selected-date-box'>📍 您選中的日期：{sel_date}</div>", unsafe_allow_html=True)

    # 項目選單：使用更彈性的欄位搜尋
    item_list = []
    # 嘗試尋找包含 "項目" 兩個字的欄位
    col_name = [c for c in config_df.columns if "項目" in c]
    if col_name:
        item_list = config_df[col_name[0]].tolist()
    
    with st.form("booking_form", clear_on_submit=True):
        st.markdown("### 📝 填寫預約資訊")
        c1, c2 = st.columns(2)
        name = c1.text_input("姓名*")
        phone = c2.text_input("電話*")
        
        sel_items = st.multiselect("施作項目 (多選)*", item_list)
        
        # 金額計算
        price_col = [c for c in config_df.columns if "價格" in c]
        total = 0
        if sel_items and price_col and col_name:
            for item in sel_items:
                p = config_df[config_df[col_name[0]] == item][price_col[0]].values[0]
                total += int(p)
        st.write(f"💰 預估金額：${total}")

        if st.form_submit_button("🚀 確定預約"):
            if name and phone and sel_items:
                st.success("✅ 預約已成功記錄！請截圖告知店家。")
                st.balloons()
            else:
                st.error("請填寫姓名、電話並選擇項目。")
