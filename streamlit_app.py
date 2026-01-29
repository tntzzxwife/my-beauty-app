import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- 基礎設定 ---
DATA_FILE = "appointments.csv"
COLS = ["日期", "時段", "客人姓名", "電話", "施作項目", "金額", "狀態", "備註"]
ADMIN_PASSWORD = "666"  # 你可以改成你自己想要的後台密碼

# 初始化資料
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=COLS).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

def load_data():
    return pd.read_csv(DATA_FILE, encoding="utf-8-sig").astype(str)

# --- 介面開始 ---
st.set_page_config(page_title="專業美容預約系統", layout="centered")

# 使用側邊欄來切換模式
mode = st.sidebar.radio("模式切換", ["👤 顧客預約", "🔐 店家管理"])

df = load_data()

if mode == "👤 顧客預約":
    st.header("✨ 線上預約系統")
    st.info("歡迎預約！請選擇您想要的日期與時段。")

    with st.form("guest_form"):
        selected_date = st.date_input("1. 選擇日期", min_value=date.today())
        
        # --- 動態時段過濾邏輯 ---
        all_times = [f"{h:02d}:{m:02d}" for h in range(10, 21) for m in (0, 30)]
        # 找出該日期已被約走的時段
        booked_times = df[(df["日期"] == str(selected_date)) & (df["狀態"] != "已取消")]["時段"].tolist()
        # 排除已被約走的時段
        available_times = [t for t in all_times if t not in booked_times]
        
        selected_time = st.selectbox("2. 選擇可用時段", available_times if available_times else ["當日已滿"])
        
        name = st.text_input("3. 您的姓名")
        phone = st.text_input("4. 聯絡電話")
        service = st.selectbox("5. 施作項目", ["美甲設計", "接睫毛", "臉部護理", "半永久紋繡", "其他諮詢"])
        note = st.text_area("6. 其他備註 (選填)")
        
        if st.form_submit_button("送出預約"):
            if selected_time == "當日已滿":
                st.error("此日期已無空檔，請更換日期。")
            elif not name or not phone:
                st.warning("請填寫姓名與電話以便與您聯繫。")
            else:
                new_data = pd.DataFrame([[str(selected_date), selected_time, name, phone, service, "0", "預約中", note]], columns=COLS)
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.success(f"🎉 預約成功！{selected_date} {selected_time} 見！")
                st.balloons()

else:
    # --- 店家管理後台 ---
    st.header("🔐 店家管理後台")
    pwd = st.text_input("請輸入管理密碼", type="password")
    
    if pwd == ADMIN_PASSWORD:
        tab1, tab2, tab3 = st.tabs(["📅 月曆檢視", "📋 預約清單", "📊 統計報表"])
        
        with tab1:
            st.subheader("本月預約概覽")
            # 整理資料給日曆看
            df['日期_dt'] = pd.to_datetime(df['日期'])
            cal_df = df[df["狀態"] != "已取消"].copy()
            if not cal_df.empty:
                # 簡單的月曆呈現：顯示每天的預約人數
                daily_counts = cal_df.groupby('日期').size().reset_index(name='預約人數')
                st.write("點擊下方表格可查看具體日期：")
                st.dataframe(daily_counts, use_container_width=True)
                
                # 選擇日期查看當天詳情
                view_date = st.date_input("查看特定日期的預約詳情", date.today())
                day_detail = df[df["日期"] == str(view_date)]
                if not day_detail.empty:
                    st.table(day_detail[["時段", "客人姓名", "施作項目", "狀態"]])
                else:
                    st.write("當天暫無預約。")

        with tab2:
            st.subheader("所有原始資料")
            search = st.text_input("🔍 搜尋客人姓名或電話")
            if search:
                filtered_df = df[df["客人姓名"].str.contains(search) | df["電話"].str.contains(search)]
            else:
                filtered_df = df.sort_values(["日期", "時段"], ascending=False)
            
            st.dataframe(filtered_df, use_container_width=True)
            
            # 刪除與狀態更新功能
            st.divider()
            edit_idx = st.selectbox("選擇要操作的序號", filtered_df.index)
            c1, c2 = st.columns(2)
            if c1.button("✅ 標記為完成"):
                df.at[edit_idx, "狀態"] = "已完成"
                df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.rerun()
            if c2.button("🗑️ 刪除紀錄"):
                df = df.drop(edit_idx)
                df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.rerun()

        with tab3:
            st.subheader("營收統計")
            # 這裡可以計算已完成訂單的總金額
            df["金額"] = pd.to_numeric(df["金額"], errors='coerce').fillna(0)
            total = df[df["狀態"] == "已完成"]["金額"].sum()
            st.metric("累計已成交金額", f"${total}")

    elif pwd != "":
        st.error("密碼錯誤，請重新輸入。")
