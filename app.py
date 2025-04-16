import os
import tempfile

import speech_recognition as sr
import re

# ▶ 추가: 로그인/회원가입 함수를 import해 사용
from backend.auth import register, login

# ▶ 기존 코드 유지
from backend.chatbot import generate_response
from backend.db import init_db, save_message
from inference import predict_emotion_from_text
from log_emotion import log_emotion
from reports.generate_report import generate_html_report
from reports.emotion_trend_plot import plot_emotion_trend

import streamlit as st

# ▶ 페이지 설정
st.set_page_config(page_title="WEAKEND 감정 챗봇", layout="centered")
st.markdown("""
    <style>
        .block-container {
            max-width: 450px;
            min-height: 2000px;
            margin: 40px auto;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 20px;
            padding: 30px 20px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
        }
        body {
            background-color: #f1f3f6;
        }
        h1 { font-size: 28px !important; text-align: center; }
        h3 { font-size: 18px !important; text-align: center; }
        button { font-size: 16px !important; }
            
        .chat-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-top: 20px;
        }

        .user-bubble {
            align-self: flex-end;
            background-color: #A8E6CF;
            color: #000;
            padding: 12px 16px;
            border-radius: 18px 18px 0px 18px;
            max-width: 75%;
            word-wrap: break-word;
        }

        .bot-bubble {
            align-self: flex-start;
            background-color: #ECECEC;
            color: #000;
            padding: 12px 16px;
            border-radius: 18px 18px 18px 0px;
            max-width: 75%;
            word-wrap: break-word;
        }
    </style>
""", unsafe_allow_html=True)

# ▶ 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
init_db()

# ─────────────────────────────────────────────────────────────────────────────
# 1) 로그인/회원가입 페이지 함수
# ─────────────────────────────────────────────────────────────────────────────
def show_login_page():
    st.markdown("<h1 style='text-align: center; font-size: 30px;'>☀️ WEAKEND ☀️</h1>", unsafe_allow_html=True)
    st.image("mainimage.png", use_container_width=True)

    # 로그인/회원가입 이동 버튼
    if st.button("🔐 로그인", use_container_width=True):
        st.session_state.auth_page = "로그인"

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    if st.button("📝 회원가입", use_container_width=True):
        st.session_state.auth_page = "회원가입"

    # 실제 로그인/회원가입 폼
    if st.session_state.get("auth_page") == "로그인":
        st.subheader("로그인")
        user = st.text_input("아이디")
        passwd = st.text_input("비밀번호", type="password")
        if st.button("로그인 확인"):
            if login(user, passwd):
                st.session_state["logged_in"] = True
                st.session_state["username"] = user
                st.success("로그인 성공! 🎉")
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

    elif st.session_state.get("auth_page") == "회원가입":
        st.subheader("회원가입")
        new_user = st.text_input("아이디")
        new_pass = st.text_input("비밀번호", type="password")
        if st.button("회원가입 확인"):
            if register(new_user, new_pass):
                st.success("회원가입 완료! 로그인 해주세요.")
                st.session_state["auth_page"] = "로그인"
            else:
                st.error("이미 가입된 아이디입니다.")

# ─────────────────────────────────────────────────────────────────────────────
# 2) 메인 (챗봇/리포트) 페이지 함수
#    (기존 3개 탭: 내 감정 입력하기, 감정 리포트, 리포트 다운로드)
# ─────────────────────────────────────────────────────────────────────────────
def show_main_page():
    page = st.sidebar.radio("탭 선택", ["내 감정 입력하기", "감정 리포트", "리포트 다운로드"])
    username = st.session_state["username"]

    # ──────────────────────────────
    # 1️⃣ 감정 입력 탭 (기존 코드 유지)
    # ──────────────────────────────
    if page == "내 감정 입력하기":
        st.title("☀️WEAKEND 감정 상담 챗봇")

        audio_file = st.file_uploader("🎤 음성 파일을 업로드하세요 (WAV)", type=["wav","mp3"])
        user_input = ""

        if audio_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_file.read())
                recognizer = sr.Recognizer()
                with sr.AudioFile(tmp_file.name) as source:
                    audio_data = recognizer.record(source)
                    try:
                        user_input = recognizer.recognize_google(audio_data, language="ko-KR")
                        st.success(f"📝 변환된 텍스트: {user_input}")
                    except:
                        st.warning("음성 인식 실패. 텍스트로 입력해주세요.")

        if not user_input:
            user_input = st.text_input("✏️ 감정을 표현해보세요")

        if user_input:
            # 1. 챗봇 응답
            bot_reply = generate_response(user_input)

            # 2. DB 저장
            save_message("user", user_input)
            save_message("bot", bot_reply)

            # 3. 대화 히스토리 저장
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("bot", bot_reply))

        # 말풍선 출력
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for sender, msg in st.session_state.chat_history:
            if sender == "user":
                st.markdown(f'<div class="user-bubble">{msg}</div>', unsafe_allow_html=True)
            elif sender == "bot":
                st.markdown(f'<div class="bot-bubble">{msg}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)



    # ──────────────────────────────
    # 2️⃣ 감정 리포트 탭 (기존 코드 유지)
    # ──────────────────────────────
    elif page == "감정 리포트":
        st.title("📈 감정 변화 리포트")
        fig = plot_emotion_trend(username)
        st.pyplot(fig)

    # ──────────────────────────────
    # 3️⃣ 리포트 다운로드 탭 (기존 코드 유지)
    # ──────────────────────────────
    elif page == "리포트 다운로드":
        st.title("📄 감정 리포트 PDF 다운로드")
        if st.button("📥 PDF 저장하기"):
            pdf_path = generate_html_report(username)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📩 리포트 다운로드",
                    data=f,
                    file_name=f"{username}_감정리포트.pdf",
                    mime="application/pdf"
                )

    # 로그아웃 버튼
    if st.sidebar.button("로그아웃"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["chat_history"] = []
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 3) 최종 실행 로직
#    (로그인 여부 확인해서 페이지 보여주기)
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state["logged_in"]:
    # 로그인 안 된 상태 => 로그인 페이지
    show_login_page()
else:
    # 로그인 성공 상태 => 메인 페이지
    show_main_page()
