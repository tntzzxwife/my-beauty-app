import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_calendar import calendar
import os

# --- 基礎設定 ---
DATA_FILE = "appointments_v9.csv"
CONFIG_FILE = "shop_config_v9.csv"
OFF_FILE = "off_slots_v9.csv" 
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
        return pd.read_csv(file, encoding="utf-8-sig").astype(str)
    return pd.DataFrame()

# --- 網頁配置 ---
st.set_page_config(page_title="專業美業預約系統", layout="wide")

# 自定義 CSS
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    .main .block-container { padding-top: 1rem; }
    .stButton>button { height: 3.5rem; font-weight: bold; font-size: 1.1rem; border-radius: 12px; background-color: #FF69B4; color: white; border: none; }
    .stButton>button:hover { background-color: #FF1493; color: white; }
    .selected-date-text { font-size: 1.5rem; color: #D44E7D; font-weight: bold; text-align: center; background: #FFF0F5; padding: 15px; border-radius: 12px; border: 2px dashed #FFB6C1; margin-bottom: 20px; }
    .fc-event { cursor: pointer; }
    </style>
    """, unsafe_allow_html=True)

df = load_data(DATA_FILE)
config_df = load_data(CONFIG_FILE)
off_df = load_data(OFF_FILE)

st.sidebar.title("🎀 系統功能")
mode = st.sidebar.radio("模式切換", ["👤 客戶預約介面", "🔐 店家管理後台"])

if mode == "👤 客戶預約介面":
    st.markdown("<h1 style='text-align:center; color: #D44E7D;'>🌸 歡迎預約 🌸</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>請在月曆點選日期，並在下方填寫預約資料</p>", unsafe_allow_html=True)
    
    # 建立事件清單
    active_df = df[df["狀態"] != "已取消"] if not df.empty else pd.DataFrame()
    event_list = []
    for i in range(0, 45):
        d = date.today() + pd.Timedelta(days=i)
        d_str = str(d)
        
        booked = active_df[active_df["日期"] == d_str]["時段"].tolist() if not active_df.empty else []
        closed = off_df[off_df["日期"] == d_str]["關閉時段"].tolist() if not off_df.empty else []
        total_blocked = len(set(booked + closed))
        
        if total_blocked < len(FIXED_SLOTS):
            event_list.append({"title": "● 可預約", "start": d_str, "allDay": True, "color": "#D4EFDF", "textColor": "#1D8348"})
        else:
            event_list.append({"title": "已額滿", "start": d_str, "allDay": True, "color": "#FADBD8", "textColor": "#943126"})

    cal_options = {
        "locale": "zh-tw",
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "today"},
        "selectable": True,
        "height": 550,
    }
    
    state = calendar(events=event_list, options=cal_options, key="cust_cal_v9")

    # --- 修正日期抓取邏輯 (YYYY-MM-DD 精準截取) ---
    sel_date_str = str(date.today())
    if state.get("callback") in ["dateClick", "select"]:
        cb = state.get("dateClick") or state.get("select")
        raw_val = cb.get("date") or cb.get("start")
        if raw_val:
            sel_date_str = raw_val[:10] 

    st.markdown(f"<div class='selected-date-text'>📍 您已選中預約日期：{sel_date_str}</div>", unsafe_allow_html=True)
    
    # 檢查該日剩餘時段
    booked_now = df[(df["日期"] == sel_date_str) & (df["狀態"] != "已取消")]["時段"].tolist() if not df.empty else []
    closed_now = off_df[off_df["日期"] == sel_date_str]["關閉時段"].tolist() if not off_df.empty else []
    available_slots = [s for s in FIXED_SLOTS if s not in booked_now and s not in closed_now]

    if not available_slots:
        st.error("😭 抱歉，這天目前已無時段可選，請挑選其他綠色標記的日期。")
    else:
        with st.form("booking_form", clear_on_submit=True):
            col_t, col_p = st.columns([1, 2])
            with col_t:
                st.write("🕒 **選擇時段**")
                sel_time = st.radio("時段：", available_slots, horizontal=True)
            with col_p:
                st.write("👤 **基本資料**")
                sc1, sc2 = st.columns(2)
                name = sc1.text_input("姓名*")
                phone = sc2.text_input("聯絡電話*")
            
            sc3, sc4 = st.columns(2)
            service = sc3.selectbox("施作項目", config_df["項目名稱"].tolist() if not config_df.empty else ["美甲設計"])
            gender = sc4.radio("性別", ["女", "男"], horizontal=True)
            
            note = st.text_area("備註 (是否有卸甲需求或其他備註)")
            
            if st.form_submit_button("🚀 確認提交預約"):
                if not name or not phone:
                    st.warning("請完整填寫姓名與電話喔！")
                else:
                    price = config_df[config_df["項目名稱"] == service]["價格"].values[0] if not config_df.empty else "0"
                    new_rec = [sel_date_str, sel_time, name, gender, service, phone, str(price), "預約中", note]
                    new_df = pd.DataFrame([new_rec], columns=["日期", "時段", "客人姓名", "性別", "項目", "電話", "金額", "狀態", "備註"])
                    pd.concat([load_data(DATA_FILE), new_df]).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                    st.success(f"🎊 預約提交成功！預約日期：{sel_date_str} {sel_time}")
                    st.balloons()

else:
    # --- 店家管理後台 ---
    pwd = st.sidebar.text_input("請輸入管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        t1, t2, t3, t4 = st.tabs(["📊 行事曆管理", "🚫 店休/關閉設定", "🛠️ 項目價格設定", "📋 資料庫總表"])
        
        with t1:
            st.subheader("美容師排程表")
            admin_events = []
            if not df.empty:
                for _, r in df.iterrows():
                    if r["狀態"] != "已取消":
                        admin_events.append({"title": f"{r['時段']} {r['客人姓名']}-{r['項目']}", "start": r["日期"], "color": "#FF69B4" if r["性別"] == "女" else "#4169E1"})
            if not off_df.empty:
                for _, r in off_df.iterrows():
                    admin_events.append({"title": f"❌ 關閉 {r['關閉時段']}", "start": r["日期"], "color": "#95a5a6"})
            calendar(events=admin_events, options={"locale": "zh-tw", "height": 600})

        with t2:
            st.subheader("設定特定日期不開放時段")
            col_o1, col_o2 = st.columns(2)
            with col_o1:
                off_d = st.date_input("選擇日期", date.today())
                off_ts = st.multiselect("選擇要關閉的時段", FIXED_SLOTS)
                if st.button("確認執行關閉"):
                    new_off_rows = pd.DataFrame({"日期": [str(off_d)]*len(off_ts), "關閉時段": off_ts})
                    pd.concat([load_data(OFF_FILE), new_off_rows]).to_csv(OFF_FILE, index=False, encoding="utf-8-sig")
                    st.success("已成功關閉該時段！")
                    st.rerun()
            with col_o2:
                st.write("目前手動關閉清單：")
                cur_off = load_data(OFF_FILE)
                if not cur_off.empty:
                    ed_off = st.data_editor(cur_off, num_rows="dynamic")
                    if st.button("儲存店休清單修改"):
                        ed_off.to_csv(OFF_FILE, index=False, encoding="utf-8-sig")
                        st.rerun()

        with t3:
            st.subheader("服務項目與金額設定")
            cur_conf = load_data(CONFIG_FILE)
            ed_conf = st.data_editor(cur_conf, num_rows="dynamic", use_container_width=True)
            if st.button("儲存項目設定"):
                ed_conf.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")
                st.success("設定已更新！")

        with t4:
            st.subheader("預約訂單原始資料管理")
            cur_df = load_data(DATA_FILE)
            if not cur_df.empty:
                ed_df = st.data_editor(cur_df, num_rows="dynamic", use_container_width=True)
                if st.button("儲存資料庫變更"):
                    ed_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                    st.success("資料庫同步成功！")
            else:
                st.write("目前尚無預約資料。")
                
    elif pwd != "":
        st.error("密碼錯誤，請重新輸入。")
