import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from streamlit_calendar import calendar
import os

# --- 基礎設定 ---
DATA_FILE = "appointments_v12.csv"
CONFIG_FILE = "shop_config_v12.csv"
OFF_FILE = "off_slots_v12.csv" 
ADMIN_PASSWORD = "tfboys0921"
# 雖然維持這三個開始時間，但現在每個項目會佔用 2 小時
FIXED_SLOTS = ["14:00", "16:00", "18:00"] 

# 初始化檔案
for f, cols in zip([DATA_FILE, CONFIG_FILE, OFF_FILE], 
                   [["日期", "開始時段", "結束時段", "客人姓名", "性別", "項目", "電話", "總金額", "狀態", "備註"],
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
st.set_page_config(page_title="專業多功能預約系統", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    .main .block-container { padding-top: 1rem; }
    .stButton>button { height: 3.5rem; font-weight: bold; font-size: 1.2rem; border-radius: 15px; background-color: #FF69B4; color: white; border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .selected-date-box { font-size: 1.6rem; color: #D44E7D; font-weight: bold; text-align: center; background: #FFF0F5; padding: 15px; border-radius: 12px; border: 3px solid #FFB6C1; margin: 20px 0; }
    .price-tag { font-size: 1.4rem; color: #E74C3C; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

df = load_data(DATA_FILE)
config_df = load_data(CONFIG_FILE)
off_df = load_data(OFF_FILE)

st.sidebar.title("🎀 選單")
mode = st.sidebar.radio("切換模式", ["👤 客戶多項目預約", "🔐 店家管理後台"])

if mode == "👤 客戶多項目預約":
    st.markdown("<h1 style='text-align:center; color:#D44E7D;'>🌸 歡迎線上預約 🌸</h1>", unsafe_allow_html=True)
    
    # 建立事件（顯示空檔）
    active_df = df[df["狀態"] != "已取消"] if not df.empty else pd.DataFrame()
    event_list = []
    for i in range(0, 45):
        d = date.today() + timedelta(days=i)
        d_str = str(d)
        booked = active_df[active_df["日期"] == d_str]["開始時段"].tolist() if not active_df.empty else []
        closed = off_df[off_df["日期"] == d_str]["關閉時段"].tolist() if not off_df.empty else []
        total = len(set(booked + closed))
        
        if total < len(FIXED_SLOTS):
            event_list.append({"title": "● 可預約", "start": d_str, "allDay": True, "color": "#D4EFDF", "textColor": "#1D8348"})
        else:
            event_list.append({"title": "已滿", "start": d_str, "allDay": True, "color": "#FADBD8", "textColor": "#943126"})

    cal_options = {"locale": "zh-tw", "selectable": True, "height": 550, "timeZone": "UTC"}
    res = calendar(events=event_list, options=cal_options, key="multi_v12_cal")

    # 日期修正
    sel_date_str = str(date.today())
    if res.get("callback") in ["dateClick", "select"]:
        cb = res.get("dateClick") or res.get("select")
        raw_val = cb.get("date") or cb.get("start")
        if raw_val: sel_date_str = raw_val.split("T")[0][:10]

    st.markdown(f"<div class='selected-date-box'>📅 您選擇的日期：{sel_date_str}</div>", unsafe_allow_html=True)
    
    # 檢查該日已佔用時段
    booked_now = df[(df["日期"] == sel_date_str) & (df["狀態"] != "已取消")]["開始時段"].tolist() if not df.empty else []
    closed_now = off_df[off_df["日期"] == sel_date_str]["關閉時段"].tolist() if not off_df.empty else []
    available_slots = [s for s in FIXED_SLOTS if s not in booked_now and s not in closed_now]

    if not available_slots:
        st.warning(f"⚠️ {sel_date_str} 已經沒有空檔囉！")
    else:
        with st.form("multi_booking_form", clear_on_submit=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("🕒 **選擇開始時間**")
                sel_time = st.radio("開始時段：", available_slots, horizontal=True)
            with col2:
                st.write("👤 **填寫資料**")
                n_col, p_col = st.columns(2)
                name = n_col.text_input("姓名*")
                phone = p_col.text_input("電話*")
            
            # 多選項目
            service_list = config_df["項目名稱"].tolist() if not config_df.empty else ["基礎美甲"]
            selected_services = st.multiselect("施作項目 (可多選，每個項目預計 2 小時)*", service_list)
            
            # 即時計算金額與時間
            total_price = 0
            if selected_services:
                for s in selected_services:
                    p = config_df[config_df["項目名稱"] == s]["價格"].values[0]
                    total_price += int(p)
            
            st.markdown(f"<span class='price-tag'>💰 總計金額：${total_price}</span> (預計耗時: {len(selected_services)*2} 小時)", unsafe_allow_html=True)
            
            note = st.text_area("備註 (例如：是否有卸甲、指定款式等)")
            
            if st.form_submit_button("🚀 確定送出預約"):
                if not name or not phone or not selected_services:
                    st.error("姓名、電話跟項目都是必填的喔！")
                else:
                    # 計算結束時間
                    start_dt = datetime.strptime(sel_time, "%H:%M")
                    end_dt = start_dt + timedelta(hours=len(selected_services) * 2)
                    end_time_str = end_dt.strftime("%H:%M")
                    
                    services_str = " + ".join(selected_services)
                    new_rec = pd.DataFrame([[sel_date_str, sel_time, end_time_str, name, "女", services_str, phone, str(total_price), "預約中", note]], 
                                           columns=["日期", "開始時段", "結束時段", "客人姓名", "性別", "項目", "電話", "總金額", "狀態", "備註"])
                    pd.concat([load_data(DATA_FILE), new_rec]).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                    st.success(f"🎉 預約成功！{sel_date_str} {sel_time} 開始，預計完成時間 {end_time_str}")
                    st.balloons()

else:
    # --- 後台管理 ---
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        t1, t2, t3, t4 = st.tabs(["📊 排程看板", "🚫 店休設定", "🛠️ 服務項目", "📋 資料總表"])
        with t1:
            events = []
            if not df.empty:
                for _, r in df.iterrows():
                    if r["狀態"] != "已取消":
                        events.append({"title": f"{r['開始時段']} {r['客人姓名']} | {r['項目']}", "start": r["日期"], "color": "#FF69B4"})
            if not off_df.empty:
                for _, r in off_df.iterrows():
                    events.append({"title": f"❌ 關閉 {r['關閉時段']}", "start": r["日期"], "color": "#95a5a6"})
            calendar(events=events, options={"locale": "zh-tw", "height": 600})
        with t2:
            st.subheader("手動關閉不開放時段")
            off_d = st.date_input("選擇日期")
            off_ts = st.multiselect("選擇時段", FIXED_SLOTS)
            if st.button("確認執行"):
                new_off = pd.DataFrame({"日期": [str(off_d)]*len(off_ts), "關閉時段": off_ts})
                pd.concat([load_data(OFF_FILE), new_off]).to_csv(OFF_FILE, index=False, encoding="utf-8-sig")
                st.rerun()
            st.data_editor(load_data(OFF_FILE), num_rows="dynamic")
        with t3:
            st.subheader("設定服務項目與價格")
            new_conf = st.data_editor(config_df, num_rows="dynamic", use_container_width=True)
            if st.button("儲存項目"):
                new_conf.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")
        with t4:
            st.subheader("所有預約明細")
            new_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("儲存資料變更"):
                new_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
    elif pwd != "":
        st.error("密碼錯誤")
