import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from streamlit_calendar import calendar
import os

# --- 基礎設定 ---
DATA_FILE = "appointments_v10.csv"
CONFIG_FILE = "shop_config_v10.csv"
OFF_FILE = "off_slots_v10.csv" 
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
    if os.path.exists(file):
        try:
            return pd.read_csv(file, encoding="utf-8-sig").astype(str)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# --- 網頁配置 ---
st.set_page_config(page_title="專業預約系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    .main .block-container { padding-top: 1rem; }
    .stButton>button { height: 3.5rem; font-weight: bold; font-size: 1.1rem; border-radius: 12px; background-color: #FF69B4; color: white; border: none; }
    .selected-date-text { font-size: 1.6rem; color: #D44E7D; font-weight: bold; text-align: center; background: #FFF0F5; padding: 15px; border-radius: 12px; border: 3px solid #FFB6C1; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

df = load_data(DATA_FILE)
config_df = load_data(CONFIG_FILE)
off_df = load_data(OFF_FILE)

st.sidebar.title("🎀 系統選單")
mode = st.sidebar.radio("模式", ["👤 客戶預約", "🔐 店家管理"])

if mode == "👤 客戶預約":
    st.markdown("<h1 style='text-align:center;'>🌸 預約您的美容時光 🌸</h1>", unsafe_allow_html=True)
    
    # 建立事件
    active_df = df[df["狀態"] != "已取消"] if not df.empty else pd.DataFrame()
    event_list = []
    for i in range(0, 45):
        d = date.today() + timedelta(days=i)
        d_str = str(d)
        booked = active_df[active_df["日期"] == d_str]["時段"].tolist() if not active_df.empty else []
        closed = off_df[off_df["日期"] == d_str]["關閉時段"].tolist() if not off_df.empty else []
        total = len(set(booked + closed))
        
        if total < len(FIXED_SLOTS):
            event_list.append({"title": "● 可預約", "start": d_str, "allDay": True, "color": "#D4EFDF", "textColor": "#1D8348"})
        else:
            event_list.append({"title": "已滿", "start": d_str, "allDay": True, "color": "#FADBD8", "textColor": "#943126"})

    cal_options = {
        "locale": "zh-tw",
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "today"},
        "selectable": True,
        "height": 580,
    }
    
    # 顯示月曆
    res = calendar(events=event_list, options=cal_options, key="final_cal")

    # 【核心修正點】：處理日期選取
    sel_date_str = str(date.today())
    if res.get("callback") in ["dateClick", "select"]:
        cb_data = res.get("dateClick") or res.get("select")
        raw_val = cb_data.get("date") or cb_data.get("start")
        if raw_val:
            # 只取字串前 10 碼，解決時區偏移 1 小時導致日期跳變的問題
            sel_date_str = raw_val[:10]

    st.markdown(f"<div class='selected-date-text'>📅 選中日期：{sel_date_str}</div>", unsafe_allow_html=True)
    
    # 過濾時段
    booked_now = df[(df["日期"] == sel_date_str) & (df["狀態"] != "已取消")]["時段"].tolist() if not df.empty else []
    closed_now = off_df[off_df["日期"] == sel_date_str]["關閉時段"].tolist() if not off_df.empty else []
    available_slots = [s for s in FIXED_SLOTS if s not in booked_now and s not in closed_now]

    if not available_slots:
        st.warning("⚠️ 此日期已滿，請點選其他有綠色標記的日期。")
    else:
        with st.form("booking_form", clear_on_submit=True):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("🕒 **時段**")
                sel_time = st.radio("選擇：", available_slots, horizontal=True)
            with c2:
                st.write("👤 **個人資料**")
                sc1, sc2 = st.columns(2)
                name = sc1.text_input("姓名*")
                phone = sc2.text_input("電話*")
            
            sc3, sc4 = st.columns(2)
            service = sc3.selectbox("項目", config_df["項目名稱"].tolist() if not config_df.empty else ["美甲設計"])
            gender = sc4.radio("性別", ["女", "男"], horizontal=True)
            
            note = st.text_area("備註 (是否有卸甲需求)")
            
            if st.form_submit_button("🚀 確認提交預約"):
                if not name or not phone:
                    st.error("請填妥姓名與電話！")
                else:
                    price = config_df[config_df["項目名稱"] == service]["價格"].values[0] if not config_df.empty else "0"
                    new_rec = pd.DataFrame([[sel_date_str, sel_time, name, gender, service, phone, str(price), "預約中", note]], 
                                           columns=["日期", "時段", "客人姓名", "性別", "項目", "電話", "金額", "狀態", "備註"])
                    pd.concat([load_data(DATA_FILE), new_rec]).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                    st.success(f"✅ 預約完成：{sel_date_str} {sel_time}")
                    st.balloons()

else:
    # --- 後台管理 ---
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        t1, t2, t3, t4 = st.tabs(["📊 排程", "🚫 店休設定", "🛠️ 項目設定", "📋 資料總表"])
        with t1:
            events = []
            if not df.empty:
                for _, r in df.iterrows():
                    if r["狀態"] != "已取消":
                        events.append({"title": f"{r['時段']} {r['客人姓名']}", "start": r["日期"], "color": "#FF69B4"})
            if not off_df.empty:
                for _, r in off_df.iterrows():
                    events.append({"title": f"❌ 關 {r['關閉時段']}", "start": r["日期"], "color": "#95a5a6"})
            calendar(events=events, options={"locale": "zh-tw", "height": 600})
        with t2:
            st.subheader("關閉特定日期時段")
            off_d = st.date_input("選擇日期")
            off_ts = st.multiselect("選擇關閉時段", FIXED_SLOTS)
            if st.button("執行關閉"):
                new_off = pd.DataFrame({"日期": [str(off_d)]*len(off_ts), "關閉時段": off_ts})
                pd.concat([load_data(OFF_FILE), new_off]).to_csv(OFF_FILE, index=False, encoding="utf-8-sig")
                st.rerun()
            st.data_editor(load_data(OFF_FILE), num_rows="dynamic")
        with t3:
            st.data_editor(config_df, num_rows="dynamic", use_container_width=True)
        with t4:
            st.data_editor(df, num_rows="dynamic", use_container_width=True)
    elif pwd != "":
        st.error("密碼錯誤")
