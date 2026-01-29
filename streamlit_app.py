import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_calendar import calendar
import os

# --- 基礎設定 ---
DATA_FILE = "appointments_v7.csv"
CONFIG_FILE = "shop_config_v7.csv"
OFF_FILE = "off_slots_v7.csv" 
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

# --- 網頁配置：設為寬版 ---
st.set_page_config(page_title="專業美業預約系統", layout="wide")

# 自定義 CSS 讓介面更大、更直觀
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3rem; font-size: 1.2rem; }
    h1 { text-align: center; color: #FF69B4; }
    </style>
    """, unsafe_allow_html=True)

df = load_data(DATA_FILE)
config_df = load_data(CONFIG_FILE)
off_df = load_data(OFF_FILE)

st.sidebar.title("🎀 選單")
mode = st.sidebar.radio("模式", ["👤 客戶預約", "🔐 店家管理"])

if mode == "👤 客戶預約":
    st.title("✨ 歡迎預約 (請點擊日期) ✨")
    
    # 建立月曆事件 (不顯示數字，只顯示顏色與簡短文字)
    active_df = df[df["狀態"] != "已取消"]
    event_list = []
    for i in range(0, 60): # 顯示未來 60 天
        d = date.today() + pd.Timedelta(days=i)
        d_str = str(d)
        booked_slots = active_df[active_df["日期"] == d_str]["時段"].tolist()
        closed_slots = off_df[off_df["日期"] == d_str]["關閉時段"].tolist()
        total_unavailable = len(set(booked_slots + closed_slots))
        
        if total_unavailable < len(FIXED_SLOTS):
            event_list.append({
                "title": "● 可預約", 
                "start": d_str, 
                "allDay": True, 
                "color": "#D4EFDF", # 淺綠色背景
                "textColor": "#1D8348"
            })
        else:
            event_list.append({
                "title": "已額滿", 
                "start": d_str, 
                "allDay": True, 
                "color": "#FADBD8", # 淺紅色背景
                "textColor": "#943126"
            })

    # 月曆顯示介面
    cal_options = {
        "locale": "zh-tw",
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "today"},
        "selectable": True,
        "height": 600, # 加大月曆高度
        "contentHeight": 600,
    }
    
    # 月曆佔據上方大區塊
    state = calendar(events=event_list, options=cal_options, key="customer_cal")

    # 下方填寫區
    st.divider()
    sel_date_str = str(date.today())
    if state.get("callback") in ["dateClick", "select"]:
        sel_date_str = (state.get("dateClick") or state.get("select"))["date" if "date" in state.get("dateClick", {}) else "start"].split("T")[0]
    
    st.subheader(f"📍 您選擇的日期：{sel_date_str}")
    
    # 獲取可用時段
    booked = df[(df["日期"] == sel_date_str) & (df["狀態"] != "已取消")]["時段"].tolist()
    closed = off_df[off_df["日期"] == sel_date_str]["關閉時段"].tolist()
    available_slots = [s for s in FIXED_SLOTS if s not in booked and s not in closed]

    if not available_slots:
        st.warning("⚠️ 該日期已無可用時段，請選擇月曆上有綠色標記的其他日期。")
    else:
        with st.form("booking_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                sel_time = st.selectbox("選擇時段", available_slots)
                name = st.text_input("姓名*")
            with c2:
                gender = st.radio("性別", ["女", "男"], horizontal=True)
                phone = st.text_input("聯絡電話*")
            with c3:
                service = st.selectbox("服務項目", config_df["項目名稱"].tolist() if not config_df.empty else ["預設項目"])
                st.write(" ") # 墊高對齊
                submit = st.form_submit_button("🚀 確認預約")

            if submit and name and phone:
                price = config_df[config_df["項目名稱"] == service]["價格"].values[0] if not config_df.empty else "0"
                new_row = [sel_date_str, sel_time, name, gender, service, phone, str(price), "預約中", ""]
                pd.concat([load_data(DATA_FILE), pd.DataFrame([new_row], columns=df.columns)]).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.success(f"🎊 預約提交成功！{sel_date_str} {sel_time} 見！")
                st.balloons()

else:
    # --- 店家管理後台 ---
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        t1, t2, t3, t4 = st.tabs(["📅 排程表", "🚫 關閉時段/店休", "🛠️ 項目設定", "📋 總資料庫"])
        
        with t1:
            admin_events = []
            for _, r in df.iterrows():
                if r["狀態"] != "已取消":
                    admin_events.append({"title": f"{r['時段']} {r['客人姓名']}", "start": r["日期"], "color": "#FF69B4" if r["性別"] == "女" else "#4169E1"})
            for _, r in off_df.iterrows():
                admin_events.append({"title": f"❌ 已關閉 {r['關閉時段']}", "start": r["日期"], "color": "#95a5a6"})
            calendar(events=admin_events, options={"locale": "zh-tw", "height": 600})

        with t2:
            st.subheader("設定店休或特定不開放時間")
            col_a, col_b = st.columns(2)
            with col_a:
                off_d = st.date_input("選擇日期")
                off_ts = st.multiselect("選擇要關閉的時段", FIXED_SLOTS)
                if st.button("確認關閉"):
                    new_offs = pd.DataFrame({"日期": [str(off_d)]*len(off_ts), "關閉時段": off_ts})
                    pd.concat([load_data(OFF_FILE), new_offs]).to_csv(OFF_FILE, index=False, encoding="utf-8-sig")
                    st.rerun()
            with col_b:
                st.write("目前關閉清單：")
                curr_off = load_data(OFF_FILE)
                edited_off = st.data_editor(curr_off, num_rows="dynamic")
                if st.button("儲存修改/刪除"):
                    edited_off.to_csv(OFF_FILE, index=False, encoding="utf-8-sig")
                    st.rerun()

        with t3:
            new_conf = st.data_editor(config_df, num_rows="dynamic", use_container_width=True)
            if st.button("儲存服務項目"):
                new_conf.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")

        with t4:
            updated_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("儲存資料庫變更"):
                updated_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
    elif pwd != "":
        st.error("密碼錯誤")
