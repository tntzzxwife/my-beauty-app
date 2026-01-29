import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_calendar import calendar
import os

# --- 基礎設定 ---
DATA_FILE = "appointments_v6.csv"
CONFIG_FILE = "shop_config_v6.csv"
OFF_FILE = "off_slots_v6.csv" # 儲存店家關閉的時段
ADMIN_PASSWORD = "tfboys0921"
FIXED_SLOTS = ["14:00", "16:00", "18:00"] 

# 初始化資料夾與檔案
for f, cols in zip([DATA_FILE, CONFIG_FILE, OFF_FILE], 
                   [["日期", "時段", "客人姓名", "性別", "項目", "電話", "金額", "狀態", "備註"],
                    ["項目名稱", "價格"],
                    ["日期", "關閉時段"]]):
    if not os.path.exists(f):
        pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8-sig")

def load_data(file):
    return pd.read_csv(file, encoding="utf-8-sig").astype(str)

# --- 介面開始 ---
st.set_page_config(page_title="專業美業預約系統 v6.0", layout="wide")
df = load_data(DATA_FILE)
config_df = load_data(CONFIG_FILE)
off_df = load_data(OFF_FILE)

st.sidebar.title("🎀 系統選單")
mode = st.sidebar.radio("切換模式", ["👤 客戶線上預約", "🔐 店家管理後台"])

if mode == "👤 客戶線上預約":
    st.title("📅 線上預約系統")
    st.info("點擊月曆查看空檔，綠色表示尚有名額。")

    col_cal, col_form = st.columns([2, 1])

    with col_cal:
        active_df = df[df["狀態"] != "已取消"]
        event_list = []
        for i in range(0, 45):
            d = date.today() + pd.Timedelta(days=i)
            d_str = str(d)
            
            # 計算該日被約走的 + 店家關閉的
            booked_slots = active_df[active_df["日期"] == d_str]["時段"].tolist()
            closed_slots = off_df[off_df["日期"] == d_str]["關閉時段"].tolist()
            total_unavailable = len(set(booked_slots + closed_slots))
            
            remaining = len(FIXED_SLOTS) - total_unavailable
            
            if remaining > 0:
                event_list.append({"title": f"🟢 餘 {remaining}", "start": d_str, "allDay": True, "color": "#2ECC71"})
            else:
                event_list.append({"title": "🔴 已滿/店休", "start": d_str, "allDay": True, "color": "#E74C3C"})

        state = calendar(events=event_list, options={"locale": "zh-tw", "selectable": True}, key="cust_cal")

    with col_form:
        sel_date_str = str(date.today())
        if state.get("callback") in ["dateClick", "select"]:
            sel_date_str = (state.get("dateClick") or state.get("select"))["date" if "date" in state.get("dateClick", {}) else "start"].split("T")[0]
            
        st.subheader(f"📅 預約日期：{sel_date_str}")
        
        # 過濾可用時段 (扣除已約與店家關閉)
        booked = df[(df["日期"] == sel_date_str) & (df["狀態"] != "已取消")]["時段"].tolist()
        closed = off_df[off_df["日期"] == sel_date_str]["關閉時段"].tolist()
        available_slots = [s for s in FIXED_SLOTS if s not in booked and s not in closed]

        with st.form("booking_form", clear_on_submit=True):
            if not available_slots:
                st.error("此日期目前無可用時段。")
                sel_time = None
            else:
                sel_time = st.selectbox("選擇時段", available_slots)
            
            name = st.text_input("客人姓名*")
            phone = st.text_input("聯絡電話*")
            gender = st.radio("性別", ["女", "男"], horizontal=True)
            service = st.selectbox("項目", config_df["項目名稱"].tolist() if not config_df.empty else ["請先設定項目"])
            
            submit = st.form_submit_button("送出預約")
            if submit and sel_time and name and phone:
                price = config_df[config_df["項目名稱"] == service]["價格"].values[0] if not config_df.empty else "0"
                new_row = [sel_date_str, sel_time, name, gender, service, phone, str(price), "預約中", ""]
                pd.concat([load_data(DATA_FILE), pd.DataFrame([new_row], columns=df.columns)]).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.success("預約成功！")
                st.balloons()

else:
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        tab1, tab2, tab3, tab4 = st.tabs(["📊 行事曆管理", "🚫 店休/關閉設定", "🛠️ 項目設定", "📑 資料庫"])
        
        with tab1:
            admin_events = []
            for _, r in df.iterrows():
                if r["狀態"] != "已取消":
                    admin_events.append({"title": f"{r['時段']} {r['客人姓名']}", "start": r["日期"], "color": "#FF69B4" if r["性別"] == "女" else "#4169E1"})
            # 把店休也顯示在後台月曆
            for _, r in off_df.iterrows():
                admin_events.append({"title": f"❌ 已關閉 {r['關閉時段']}", "start": r["日期"], "color": "#95a5a6"})
            calendar(events=admin_events, options={"locale": "zh-tw"})

        with tab2:
            st.subheader("設定特定日期不開放的時段")
            st.write("例如：2023-10-25 的 14:00 要休息，請在此新增。")
            
            with st.form("off_form"):
                off_d = st.date_input("選擇日期")
                off_t = st.multiselect("要關閉的時段", FIXED_SLOTS)
                if st.form_submit_button("確認關閉這些時段"):
                    new_offs = pd.DataFrame({"日期": [str(off_d)]*len(off_t), "關閉時段": off_t})
                    pd.concat([load_data(OFF_FILE), new_offs]).to_csv(OFF_FILE, index=False, encoding="utf-8-sig")
                    st.success("已成功關閉該時段，客人將無法預約。")
                    st.rerun()
            
            st.write("目前關閉清單：")
            curr_off = load_data(OFF_FILE)
            edited_off = st.data_editor(curr_off, num_rows="dynamic")
            if st.button("儲存/刪除店修清單"):
                edited_off.to_csv(OFF_FILE, index=False, encoding="utf-8-sig")
                st.rerun()

        with tab3:
            new_conf = st.data_editor(config_df, num_rows="dynamic")
            if st.button("儲存項目"):
                new_conf.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")

        with tab4:
            updated_df = st.data_editor(df, num_rows="dynamic")
            if st.button("儲存所有資料"):
                updated_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
    elif pwd != "":
        st.error("密碼錯誤")
