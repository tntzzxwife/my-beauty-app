import streamlit as st

st.set_page_config(page_title="專業預約入口", layout="centered")

# 粉色美化
st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    .card {
        background: white; padding: 40px; border-radius: 30px;
        text-align: center; border: 3px solid #FF69B4;
        box-shadow: 0 10px 25px rgba(255,105,180,0.2);
    }
    .btn {
        background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%);
        color: white !important; padding: 18px 35px;
        text-decoration: none; border-radius: 50px;
        font-size: 22px; font-weight: bold; display: inline-block;
        margin-top: 25px; transition: 0.3s;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="card">
        <h1 style='color: #D44E7D;'>🌸 歡迎預約您的美麗時光 🌸</h1>
        <p style='color: #666; font-size: 18px;'>
            系統將自動過濾已預約時段<br>
            確保您的專屬時間不被重複預約
        </p>
        <br>
        <a href="這裡貼上你的_GOOGLE_表單連結" target="_blank" class="btn">✨ 立即查詢剩餘時段 ✨</a>
        <br><br>
        <p style='color: #999; font-size: 14px;'>✓ 預約成功後將由 LINE 或 Email 通知您</p>
    </div>
""", unsafe_allow_html=True)
