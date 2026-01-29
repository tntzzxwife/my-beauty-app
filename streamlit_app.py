import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_calendar import calendar
import os

# --- 基礎設定 ---
DATA_FILE = "appointments_v8.csv"
CONFIG_FILE = "shop_config_v8.csv"
OFF_FILE = "off_slots_v8.csv" 
ADMIN_PASSWORD = "tfboys0921"
FIXED_SLOTS = ["14:00", "16:00", "18:00"] 

# 初始化檔案
for f, cols in zip([DATA_FILE, CONFIG_FILE, OFF_FILE], 
                   [["日期", "時段", "客人姓名", "性別", "項目", "電話", "金額", "狀態", "備註"],
                    ["項目名稱", "價格"],
                    ["日期", "關閉時段"]]):
    if not os.path.exists(f):
        pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8-sig")

def load_data(file):
    return pd.read_csv(file, encoding="utf-8-sig").astype(str)

# --- 網頁配置 ---
st.set_page_config(page_title="專業預約系統", layout="wide")

# 自定義 CSS：強化選中效果與按鈕樣式
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    .main .block-container { padding-top: 1rem; }
    /* 讓選擇的日期格子亮起來 (FullCalendar 自定義) */
    .fc-day-selected { background-color: #FFD1DC !important; border: 2px solid #FF69B4 !important; }
    .stButton>button { height: 4rem; font-weight: bold; font-size: 1.1rem; }
    .selected-date-text { font-size: 1.5rem; color: #D44E7D; font-weight: bold; text-align: center; background: #FFF0F5; padding: 10px; border-radius: 10px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

df = load_data(DATA_FILE)
config_df = load_data(CONFIG_FILE)
off_df = load_data(OFF_FILE)

st.sidebar.title("🎀 選單")
mode = st.sidebar.radio("切換模式", ["👤 客戶預約", "🔐 店家管理"])

if mode == "👤 客戶預約":
    st.markdown("<h1>🌸 歡迎預約 🌸</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>請點選日期，並於下方選擇時段填寫資料</p>", unsafe_allow_html=True)
    
    # 建立事件清單
    active_df = df[df["狀態"] != "已取消"]
    event_list = []
    for i in range(0, 45):
        d = date.today() + pd.Timedelta(days=i)
        d_str = str(d)
        booked = active_df[active_df["日期"] == d_str]["時段"].tolist()
        closed = off_df[off_df["日期"] == d_str]["關閉時段"].tolist()
        total_blocked = len(set(booked + closed))
        
        if total_blocked < len(FIXED_SLOTS):
            event_list.append({"title": "● 可預約", "start": d_str, "allDay": True, "color": "#D4EFDF", "textColor": "#1D8348"})
        else:
            event_list.append({"title": "已額滿", "start": d_str, "allDay": True, "color": "#FADBD8", "textColor": "#943126"})

    # 月曆配置：加入選中高亮邏輯
    cal_options = {
        "locale": "zh-tw",
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "today"},
        "selectable": True,
        "height": 550,
        "unselectAuto": False, # 點擊其他地方不取消選取
        "selectMirror": True,
    }
    
    state = calendar(events=event_list, options=cal_options, key="cust_cal")

    # --- 處理選取日期 ---
    sel_date_str = str(date.today()) # 預設今天
    if state.get("callback") in ["dateClick", "select"]:
        # 抓取選中日期
        sel_date_str = (state.get("dateClick") or state.get("select"))["date" if "date" in state.get("dateClick", {}) else "start"].split("T")[0]

    # 顯示「選中提示區」
    st.markdown(f"<div class='selected-date-text'>📍 您已選中：{sel_date_str}</div>", unsafe_allow_html=True)
    
    # 獲取該日可用時段
    booked_now = df[(df["日期"] == sel_date_str) & (df["狀態"] != "已取消")]["時段"].tolist()
    closed_now = off_df[off_df["日期"] == sel_date_str]["關閉時段"].tolist()
    available_slots = [s for s in FIXED_SLOTS if s not in booked_now and s not in closed_now]

    if not available_slots:
        st.error("😭 抱歉，這天已經沒有時段可以預約了，請點選月曆上其他的日期。")
    else:
        with st.form("booking_form", clear_on_submit=True):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("🕒 **選擇時段**")
                sel_time = st.radio("可用時段：", available_slots, horizontal=True)
            with c2:
                st.write("👤 **基本資料**")
                sub_c1, sub_c2 = st.columns(2)
                name = sub_c1.text_input("姓名*")
                phone = sub_c2.text_input("電話*")
                
            service = st.selectbox("施作項目", config_df["項目名稱"].tolist() if not config_df.empty else ["無服務"])
            note = st.text_area("備註 (卸甲或其他需求)")
            
            submit = st.form_submit_button("🚀 確定送出預約")
            
            if submit:
                if not name or not phone:
                    st.warning("請填寫姓名與電話喔！")
                else:
                    price = config_df[config_df["項目名稱"] == service]["價格"].values[0] if not config_df.empty else "0"
                    new_data = [sel_date_str, sel_time, name, "女", service, phone, str(price), "預約中", note]
                    pd.concat([load_data(DATA_FILE), pd.DataFrame([new_data], columns=df.columns)]).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                    st.success(f"🎊 預約提交成功！期待在 {sel_date_str} {sel_time} 見到您！")
                    st.balloons()

else:
    # --- 店家管理後台 ---
    pwd = st.sidebar.text_input("後台密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        t1, t2, t3, t4 = st.tabs(["📊 行事曆管理", "🚫 關閉時段/店休", "🛠️ 項目設定", "📋 總資料庫"])
        
        with t1:
            admin_events = []
            for _, r in df.iterrows():
                if r["狀態"] != "已取消":
                    admin_events.append({"title": f"{r['時段']} {r['客人姓名']}", "start": r["日期"], "color": "#FF69B4"})
            for _, r in off_df.iterrows():
                admin_events.append({"title": f"❌ 關閉 {r['關閉時段']}", "start": r["日期"], "color": "#95a5a6"})
            calendar(events=admin_events, options={"locale": "zh-tw", "height": 600})

        with t2:
            st.subheader("手動關閉不開放時段")
            col_off_1, col_off_2 = st.columns(2)
            with col_off_1:
                off_date = st.date_input("選擇日期")
                off_times = st.multiselect("選擇關閉時段", FIXED_SLOTS)
                if st.button("確認關閉"):
                    new_offs = pd.DataFrame({"日期": [str(off_date)]*len(off_times), "關閉時段": off_times})
                    pd.concat([load_data(OFF_FILE), new_offs]).to_csv(OFF_FILE, index=False, encoding="utf-8-sig")
                    st.rerun()
            with col_off_2:
                curr_off = load_data(OFF_FILE)
                edited_off = st.data_editor(curr_off, num_rows="dynamic")
                if st.button("更新關閉清單"):
                    edited_off.to_csv(OFF_FILE, index=False, encoding="utf-8-sig")
                    st.rerun()

        with t3:
            new_conf = st.data_editor(config_df, num_rows="dynamic", use_container_width=True)
            if st.button("儲存項目設定"):
                new_conf.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")

        with t4:
            updated_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("儲存資料庫"):
                updated_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
    elif pwd != "":
        st.error("密碼錯誤")
