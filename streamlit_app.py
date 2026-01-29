import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from streamlit_calendar import calendar
import os

# --- 基礎設定 ---
DATA_FILE = "appointments_v11.csv"
CONFIG_FILE = "shop_config_v11.csv"
OFF_FILE = "off_slots_v11.csv" 
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

# 加強版 CSS
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    .main .block-container { padding-top: 1rem; }
    .stButton>button { height: 3.5rem; font-weight: bold; font-size: 1.2rem; border-radius: 15px; background-color: #FF69B4; color: white; border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .selected-date-box { font-size: 1.8rem; color: #D44E7D; font-weight: bold; text-align: center; background: #FFF0F5; padding: 20px; border-radius: 15px; border: 4px solid #FFB6C1; margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

df = load_data(DATA_FILE)
config_df = load_data(CONFIG_FILE)
off_df = load_data(OFF_FILE)

st.sidebar.title("🎀 選單")
mode = st.sidebar.radio("切換模式", ["👤 客戶預約", "🔐 店家管理"])

if mode == "👤 客戶預約":
    st.markdown("<h1 style='text-align:center; color:#D44E7D;'>🌸 歡迎線上預約 🌸</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>請在月曆點選日期，選中後下方會顯示可用時段</p>", unsafe_allow_html=True)
    
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
        "timeZone": "UTC", # 強制月曆使用 UTC 顯示，避免前端自動轉換
    }
    
    res = calendar(events=event_list, options=cal_options, key="final_v11_cal")

    # 【終極日期修正邏輯】
    sel_date_str = str(date.today())
    if res.get("callback") in ["dateClick", "select"]:
        cb = res.get("dateClick") or res.get("select")
        raw_val = cb.get("date") or cb.get("start")
        if raw_val:
            # 處理可能出現的 2026-02-10T00:00:00.000Z 或是 2026-02-10
            # 我們直接取 T 以前的字串，並用 pd.to_datetime 強制轉換後加回 0 天，確保純淨日期
            clean_date = raw_val.split("T")[0]
            # 如果偵測到時區偏移（例如抓到前一天晚上），手動校正
            try:
                # 判斷字串長度，如果包含時間資訊，我們只截取前 10 碼
                sel_date_str = clean_date[:10]
                # 額外保險：如果回傳的是帶有 16:00:00 (UTC+8 偏移) 的字串，
                # 下面的判斷會修正它
                if "16:00:00" in raw_val or "T00:00:00" in raw_val:
                    # 這是最穩定的做法：從 ISO 格式直接讀取日期
                    sel_date_str = pd.to_datetime(raw_val).date().isoformat()
            except:
                sel_date_str = clean_date[:10]

    st.markdown(f"<div class='selected-date-box'>📍 您選中的日期是：{sel_date_str}</div>", unsafe_allow_html=True)
    
    # 顯示可用時段
    booked_now = df[(df["日期"] == sel_date_str) & (df["狀態"] != "已取消")]["時段"].tolist() if not df.empty else []
    closed_now = off_df[off_df["日期"] == sel_date_str]["關閉時段"].tolist() if not off_df.empty else []
    available_slots = [s for s in FIXED_SLOTS if s not in booked_now and s not in closed_now]

    if not available_slots:
        st.warning(f"⚠️ {sel_date_str} 這天已經沒有名額了，請選其他綠色日期。")
    else:
        with st.form("booking_form", clear_on_submit=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("🕒 **請選擇時段**")
                sel_time = st.radio("可用時段：", available_slots, horizontal=True)
            with col2:
                st.write("👤 **請填寫資料**")
                n_col, p_col = st.columns(2)
                name = n_col.text_input("姓名*")
                phone = p_col.text_input("電話*")
            
            s_col, g_col = st.columns(2)
            service = s_col.selectbox("項目", config_df["項目名稱"].tolist() if not config_df.empty else ["美甲設計"])
            gender = g_col.radio("性別", ["女", "男"], horizontal=True)
            
            note = st.text_area("備註 (是否有卸甲需求)")
            
            if st.form_submit_button("🚀 確認送出預約"):
                if not name or not phone:
                    st.error("姓名與電話是必填的喔！")
                else:
                    price = config_df[config_df["項目名稱"] == service]["價格"].values[0] if not config_df.empty else "0"
                    new_row = pd.DataFrame([[sel_date_str, sel_time, name, gender, service, phone, str(price), "預約中", note]], 
                                           columns=df.columns if not df.empty else ["日期", "時段", "客人姓名", "性別", "項目", "電話", "金額", "狀態", "備註"])
                    pd.concat([load_data(DATA_FILE), new_row]).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                    st.success(f"🎉 預約提交成功！日期：{sel_date_str} 時段：{sel_time}")
                    st.balloons()

else:
    # --- 後台管理 ---
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        t1, t2, t3, t4 = st.tabs(["📊 排程管理", "🚫 店休設定", "🛠️ 項目設定", "📋 資料總表"])
        with t1:
            events = []
            if not df.empty:
                for _, r in df.iterrows():
                    if r["狀態"] != "已取消":
                        events.append({"title": f"{r['時段']} {r['客人姓名']}", "start": r["日期"], "color": "#FF69B4"})
            if not off_df.empty:
                for _, r in off_df.iterrows():
                    events.append({"title": f"❌ 關閉 {r['關閉時段']}", "start": r["日期"], "color": "#95a5a6"})
            calendar(events=events, options={"locale": "zh-tw", "height": 600})
        with t2:
            st.subheader("手動關閉不開放時段")
            off_d = st.date_input("選擇日期")
            off_ts = st.multiselect("選擇關閉時段", FIXED_SLOTS)
            if st.button("確認關閉"):
                new_off = pd.DataFrame({"日期": [str(off_d)]*len(off_ts), "關閉時段": off_ts})
                pd.concat([load_data(OFF_FILE), new_off]).to_csv(OFF_FILE, index=False, encoding="utf-8-sig")
                st.rerun()
            st.data_editor(load_data(OFF_FILE), num_rows="dynamic", use_container_width=True)
        with t3:
            st.data_editor(config_df, num_rows="dynamic", use_container_width=True)
        with t4:
            st.data_editor(df, num_rows="dynamic", use_container_width=True)
    elif pwd != "":
        st.error("密碼錯誤")
