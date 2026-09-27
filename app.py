import streamlit as st
from styles import card_image, hero, info_box, inject_style, sidebar_footer

st.set_page_config(
    page_title="전국 자동차 신규등록 현황 및 기업 FAQ 조회",
    page_icon="assets/logo.png",
    layout="wide",
)

REG_PAGE = "pages/1_자동차_등록_현황.py"
FAQ_PAGE = "pages/2_기업_FAQ_조회.py"


def home():
    st.session_state["current_page"] = "home" 
    
    # 공통 스타일 주입 / 페이지 맨 위에서 1회 호출
    inject_style()
 
    # 상단 배너 출력 / 이미지 위에 제목과 설명 표시
    hero(
        "전국 자동차 신규등록 현황 및 기업 FAQ 조회",
        "누가, 언제, 어디서 새 차를 등록했을까요?",
    )
 
    # 기능 카드 2개 배치 / 좌: 신규등록 현황, 우: 기업 FAQ
    left, right = st.columns(2, gap="medium")
 
    with left:
        with st.container(border=True, key="homecard_reg"):
            card_image("assets/card_registration.png")
            st.subheader("자동차 신규등록 현황")
            st.write("연월, 시도, 성별, 연령대별 신규등록 대수 조회")
            st.page_link(REG_PAGE, label="조회하기 →")
 
    with right:
        with st.container(border=True, key="homecard_faq"):
            card_image("assets/card_faq.png")
            st.subheader("기업 FAQ 조회")
            st.write("기아, 현대 FAQ 검색")
            st.page_link(FAQ_PAGE, label="조회하기 →")
 
    # 조회 가능한 항목 안내 / 카드 아래 배치
    info_box("이런 정보를 조회할 수 있어요!", [
        "2016년 9월부터 10년(120개월)간의 자동차 신규등록 데이터",
        "17개 시도 · 성별 · 8개 연령대별 상세 조회와 차트",
        "기아 · 현대 고객센터 FAQ 통합 검색",
    ])

    # 데이터 출처 표시 / 화면 맨 아래 1줄
    st.caption(
        "데이터 출처: 공공데이터포털 (한국교통안전공단 자동차 신규등록정보) · "
        "기아, 현대 고객센터 FAQ"
    )


# 1 사이드바 메뉴 (메뉴 이름 = 파일 이름 · 현재 페이지 자동 강조)
nav = st.navigation([
    st.Page(home, title="홈", icon=":material/home:", default=True),
    st.Page(REG_PAGE, title="자동차 등록 현황", icon=":material/directions_car:"),
    st.Page(FAQ_PAGE, title="기업 FAQ 조회", icon=":material/apartment:"),
])

st.logo("assets/logo.png", size="large")
nav.run()
sidebar_footer() 

