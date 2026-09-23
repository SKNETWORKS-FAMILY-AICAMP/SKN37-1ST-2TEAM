import streamlit as st

st.set_page_config(
    page_title="전국 자동차 신규등록 현황 및 기업 FAQ 조회",
    layout="wide",
)

REG_PAGE = "pages/1_자동차_등록_현황.py"
FAQ_PAGE = "pages/2_기업_FAQ_조회.py"


def home():
    # 2 서비스 제목 (미정: 서비스 이름 → 제안값대로 프로젝트 이름 그대로)
    st.title("전국 자동차 신규등록 현황 및 기업 FAQ 조회")

    # 3 설명글
    st.write(
        "누가(성별·연령대) 어디서(시도) 새 차를 등록했는지와 "
        "자동차 기업 FAQ를 한 곳에서 조회하는 서비스예요."
    )

    st.divider()

    # 4, 5 바로가기 카드 (좌: 신규등록 현황 / 우: FAQ)
    left, right = st.columns(2)

    with left:
        with st.container(border=True):
            st.subheader("자동차 신규등록 현황")
            st.write("연월, 시도, 성별, 연령대별 신규등록 대수 조회")
            st.page_link(REG_PAGE, label="바로가기")

    with right:
        with st.container(border=True):
            st.subheader("기업 FAQ 조회")
            st.write("기아, 현대 FAQ 검색")
            st.page_link(FAQ_PAGE, label="바로가기")

    # 6 데이터 출처 (미정: 표시 여부 → 제안값대로 맨 아래 1줄 표시)
    st.caption(
        "데이터 출처: 공공데이터포털 (한국교통안전공단 자동차 신규등록정보) · "
        "기아, 현대 고객센터 FAQ"
    )


# 1 사이드바 메뉴 (메뉴 이름 = 파일 이름 · 현재 페이지 자동 강조)
nav = st.navigation([
    st.Page(home, title="홈", default=True),
    st.Page(REG_PAGE, title="자동차 등록 현황"),
    st.Page(FAQ_PAGE, title="기업 FAQ 조회"),
])
nav.run()
