import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from streamlit_calendar import calendar

# --- 核心連線設定 (直接讀取，不報錯) ---
SHEET_ID = "1xwTYj3hmrXnhPpmDEyq_NVTqvNd1884-Fqk3Q2YsciY"

def get_gs_url(sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

ADMIN_PASSWORD = "tfboys0921"
FIXED_SLOTS = ["14:00", "16:00", "18:00"]

# --- 網頁配置 ---
st.set_page_config(page_title="專業美業雲端預約系統", layout="wide")

# 加強版粉色系 CSS
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    .main .block-container { padding-top: 2rem; }
    
    /* 標題與文字顏色 */
    h1, h2, h3 { color: #D44E7D !important; font-family: 'Microsoft JhengHei', sans-serif; }
    
    /* 按鈕樣式 */
    .stButton>button { 
        height: 3.8rem; font-weight: bold; font-size: 1.2rem; border-radius: 20px; 
        background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%); 
        color: white; border: none; box-shadow: 0 4px 15px rgba(255, 105, 180, 0.3);
        transition: all 0.3s; width: 100%;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255, 105, 180, 0.5); }
    
    /* 選中日期外框 */
    .selected-date-box { 
        font-size: 1.8rem; color: #D44E7D; font-weight: bold; text-align: center; 
        background: #FFF0F5; padding: 25px; border-radius: 20px; 
        border: 4px solid #FFB6C1; margin: 25px 0; box-shadow: inset 0 0 10px rgba(255, 182, 193, 0.5);
    }
    
    /* 價格標籤 */
    .price-card {
        background: #FFFFFF; padding: 15px; border-radius: 15px; border-left: 10px solid #FF69B4;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-top: 10px;
    }
    
    /* 表單區塊 */
    .stForm { background-color: white; padding: 30px; border-radius: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid #FFE4E1; }
    </style>
    """, unsafe_allow_html=True)

# 讀取雲端資料 (加載中顯示美美的訊息)
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

st.sidebar.markdown("<h2 style='text-align:center;'>🎀 系統功能</h2>", unsafe_allow_html=True)
mode = st.sidebar.radio("", ["👤 客戶線上預約", "🔐 店家管理後台"])

if mode == "👤 客戶線上預約":
    st.markdown("<h1 style='text-align:center;'>🌸 歡迎預約您的美麗時光 🌸</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888;'>請先在月曆選取日期，再選擇時段與項目</p>", unsafe_allow_html=True)

    # 建立月曆事件 (有空位顯示綠色)
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

    cal_res = calendar(events=event_list, options={"locale": "zh-tw", "height": 580, "timeZone": "UTC"}, key="pretty_cal")

    # 抓取選中日期
    sel_date = str(date.today())
    if cal_res.get("callback") in ["dateClick", "select"]:
        cb = cal_res.get("dateClick") or cal_res.get("select")
        sel_date = cb.get("date", cb.get("start")).split("T")[0][:10]

    st.markdown(f"<div class='selected-date-box'>📅 您選中的日期：{sel_date}</div>", unsafe_allow_html=True)

    # 過濾時段
    booked_now = df[(df["日期"] == sel_date) & (df["狀態"] != "已取消")]["開始時段"].tolist() if not df.empty else []
    closed_now = off_df[off_df["日期"] == sel_date]["關閉時段"].tolist() if not off_df.empty else []
    available = [s for s in FIXED_SLOTS if s not in booked_now and s not in closed_now]

    if not available:
        st.error(f"💔 抱歉，{sel_date} 已經被約滿了，換一天試試看吧！")
    else:
        with st.form("pretty_booking_form"):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown("### 🕒 選擇時間")
                sel_time = st.radio("", available, horizontal=True)
            with c2:
                st.markdown("### 👤 聯絡資料")
                sc1, sc2 = st.columns(2)
                name = sc1.text_input("您的姓名*", placeholder="王小美")
                phone = sc2.text_input("手機號碼*", placeholder="0912-345-678")
            
            st.divider()
            st.markdown("### 🛠️ 選擇施作項目 (每項約 2 小時)")
            item_names = config_df["項目名稱"].tolist() if not config_df.empty else ["基礎保養"]
            sel_items = st.multiselect("可多選項目：", item_names)
            
            # 即時算錢
            total_price = 0
            if sel_items:
                for i in sel_items:
                    p = config_df[config_df["項目名稱"] == i]["價格"].values[0]
                    total_price += int(p)
            
            st.markdown(f"""
                <div class='price-card'>
                    <span style='color:#555;'>預計總金額：</span><br>
                    <span style='font-size:1.8rem; color:#E74C3C;'>$ {total_price}</span>
                    <span style='color:#888; margin-left:10px;'>(預計耗時 {len(sel_items)*2} 小時)</span>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            if st.form_submit_button("🚀 確定預約"):
                if name and phone and sel_items:
                    # 提示客人
                    st.success(f"🎊 預約請求已準備好！請截圖此畫面並傳送給店家確認。")
                    st.info(f"預約內容：{sel_date} {sel_time} | {', '.join(sel_items)}")
                    st.balloons()
                else:
                    st.error("填寫完整姓名、電話並勾選項目，我們才能為您服務喔！")

else:
    # --- 後台管理 ---
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        st.markdown("## 🔐 雲端管理中心")
        t1, t2 = st.tabs(["📊 今日排程", "📋 雲端資料總覽"])
        with t1:
            events = []
            if not df.empty:
                for _, r in df.iterrows():
                    events.append({"title": f"{r['開始時段']} {r['客人姓名']} ({r['項目']})", "start": r["日期"], "color": "#FF69B4"})
            calendar(events=events, options={"locale": "zh-tw", "height": 600})
        with t2:
            st.dataframe(df, use_container_width=True)
            st.info("💡 欲修改資料或項目，請直接前往您的 Google Sheet 進行編輯，網頁會自動同步。")
    elif pwd != "":
        st.error("密碼錯誤")
