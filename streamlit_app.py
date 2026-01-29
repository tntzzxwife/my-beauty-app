import streamlit as st
from datetime import datetime, timedelta
import urllib.parse

# 1. 基本設定
st.set_page_config(page_title="預約通知系統", layout="centered")

# 2. 粉嫩介面樣式
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    h1 { color: #D44E7D; text-align: center; }
    .booking-card { background: white; padding: 30px; border-radius: 20px; border: 2px solid #FF69B4; }
    .stButton>button { 
        background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%); 
        color: white; border-radius: 50px; height: 3.5rem; width: 100%; border: none; font-size: 1.2rem; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>🌸 歡迎預約您的美麗時光 🌸</h1>", unsafe_allow_html=True)

# 3. 預約內容填寫
with st.container():
    st.markdown("<div class='booking-card'>", unsafe_allow_html=True)
    
    d = st.date_input("📅 選擇日期")
    t = st.selectbox("🕒 選擇時段", ["14:00", "16:00", "18:00"])
    
    st.divider()
    
    name = st.text_input("客人姓名*")
    line_n = st.text_input("LINE 暱稱*")
    phone = st.text_input("手機號碼*")
    items = st.multiselect("施作項目*", ["美甲", "美睫", "皮膚保養", "霧眉設計"])
    
    if st.button("🚀 送出預約並通知店家"):
        if name and line_n and phone and items:
            # 整理預約內容文字
            msg = (
                f"【新預約申請】\n"
                f"📅 日期：{d}\n"
                f"🕒 時段：{t}\n"
                f"👤 姓名：{name}\n"
                f"🆔 LINE：{line_n}\n"
                f"📱 電話：{phone}\n"
                f"🛠️ 項目：{', '.join(items)}\n"
                f"--- \n"
                f"請與我確認預約，謝謝！"
            )
            
            # 轉換為 LINE 連結格式
            encoded_msg = urllib.parse.quote(msg)
            # 這裡可以換成你的 LINE ID 連結，例如 https://line.me/ti/p/你的ID
            line_url = f"https://line.me/R/msg/text/?{encoded_msg}"
            
            st.success("✅ 預約資訊已準備好！")
            st.balloons()
            
            # 顯示跳轉按鈕
            st.markdown(f"""
                <a href="{line_url}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #00B900; color: white; padding: 15px; text-align: center; border-radius: 15px; font-weight: bold; font-size: 1.2rem;">
                        💬 點我傳送 LINE 預約通知
                    </div>
                </a>
            """, unsafe_allow_html=True)
            st.info("💡 點擊上方綠色按鈕，將預約訊息傳送給店家，預約才算正式開始喔！")
            
        else:
            st.error("❌ 請完整填寫所有欄位喔！")
    
    st.markdown("</div>", unsafe_allow_html=True)
