"""
styles.py / 화면 공통 스타일
 
사용
    from styles import inject_style, hero
    inject_style()                   # 페이지마다 맨 위에서 1회 호출
    hero(...)                        # 홈 화면 배너
 
색 변경 시 .streamlit/config.toml 과 함께 수정
"""
 
import base64
from pathlib import Path
 
import streamlit as st
 
# 색 팔레트 정의 / config.toml 과 동일 값 유지
INK = "#16232E"         # 기본 글자
MUTED = "#5B6B85"       # 흐린 글자
LINE = "#DDE5F2"        # 테두리
BRAND = "#2563EB"       # 강조 파랑
BRAND_DEEP = "#1E3A8A"  # 진한 파랑 (그라데이션 시작)
 
 
def inject_style():
    """페이지 공통 CSS 주입 / 페이지 맨 위에서 1회 호출"""
    st.markdown(
        f"""
        <style>
        /* 메인 영역 배경 생성 / 위쪽에 옅은 푸른 기운 추가 */
        .stApp {{
            background:
                radial-gradient(1200px 320px at 20% -10%, #E3EDFC 0%, rgba(227,237,252,0) 70%),
                #F4F7FD;
        }}
 
        /* 사이드바 배경 지정 / 오른쪽 경계선 추가 */
        section[data-testid="stSidebar"] {{
            background: #FFFFFF;
            border-right: 1px solid {LINE};
        }}
 
        /* 제목 자간 조정 */
        h1 {{ letter-spacing: -0.02em; }}
 
        /* 화면 위아래 여백 축소 / 한 화면에 더 많이 보이도록 */
        .stMainBlockContainer, div.block-container {{
            padding-top: 1.6rem;
            padding-bottom: 1.5rem;
            max-width: 1100px;
        }}
 
        /* 카드 모양 지정 / st.container(border=True) 대상 */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: #FFFFFF;
            border: 1px solid {LINE};
            border-radius: 14px;
            box-shadow: 0 1px 2px rgba(22,35,46,.04), 0 8px 24px rgba(30,58,138,.06);
        }}
 
 
 
        /* 카드 안 제목, 설명 여백 축소 */
        div[data-testid="stVerticalBlockBorderWrapper"] h3 {{
            font-size: 22px;
            margin: 0 0 2px;
        }}
 
        /* 카드 안쪽 여백 축소 */
        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            padding: 4px 2px;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] p {{
            margin-bottom: 4px;
        }}
 
        /* 표 모서리 둥글게 처리 / 테두리 통일 */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {LINE};
            border-radius: 12px;
            overflow: hidden;
        }}
 
        /* 버튼 모양 조정 */
        div.stButton > button {{
            border-radius: 10px;
            font-weight: 600;
            padding: 0.45rem 1.1rem;
        }}
 
        /* 캡션 글자색 지정 */
        div[data-testid="stCaptionContainer"] p {{ color: {MUTED}; }}
 
        /* 홈 히어로 배너 생성 / 배경 이미지는 hero() 에서 지정 */
        .hero {{
            position: relative;
            border-radius: 18px;
            overflow: hidden;
            min-height: 205px;
            display: flex;
            align-items: center;
            margin-bottom: 14px;
        }}
 
        /* 글자 가독성 확보 / 이미지 왼쪽에 짙은 층 추가 */
        .hero::before {{
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, rgba(15,27,58,.88) 0%, rgba(30,58,138,.72) 45%, rgba(30,58,138,.15) 100%);
        }}
 
        .hero-inner {{
            position: relative;
            padding: 28px 36px;
            max-width: 720px;
        }}
        .hero h1 {{
            font-size: 30px;
            line-height: 1.3;
            margin: 0 0 12px;
            color: #FFFFFF;
            text-wrap: balance;
        }}
        .hero p {{
            font-size: 16px;
            line-height: 1.6;
            margin: 0;
            color: #E8EFFD;
        }}
 
        /* 카드 일러스트 출력 / 가운데 정렬 */
        .card-illust {{
            display: flex;
            justify-content: center;
            margin: 0 0 10px;
        }}
        .card-illust img {{
            width: 100%;
            max-width: 320px;
            border-radius: 12px;
        }}
 
        /* 좁은 화면 대응 / 배너 여백과 글자 크기 축소 */
        @media (max-width: 640px) {{
            .hero {{ min-height: 180px; }}
            .hero-inner {{ padding: 26px 22px; }}
            .hero h1 {{ font-size: 24px; }}
            .hero p {{ font-size: 15px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
 
 
def _to_data_uri(image_path: str) -> str:
    """이미지 파일을 CSS에 넣을 수 있는 형태로 변환
    - CSS는 로컬 파일 경로를 읽지 못하므로 글자로 바꿔서 직접 삽입
    """
    data = Path(image_path).read_bytes()
    encoded = base64.b64encode(data).decode()
    return f"data:image/png;base64,{encoded}"
 
 
def hero(title: str, subtitle: str, image_path: str = "assets/hero_car.png"):
    """홈 화면 상단 배너 출력 / 이미지 위에 제목과 설명 표시
    - title      : 큰 제목
    - subtitle   : 한 줄 설명
    - image_path : 배경 이미지 경로 (없으면 색 배경으로 대체)
    - 주의: Streamlit은 태그 안 style="..." 을 지우므로 배경은 <style> 안에서 지정
    """
    try:
        background = f"url('{_to_data_uri(image_path)}') right center/cover no-repeat"
    except FileNotFoundError:
        background = f"linear-gradient(120deg, {BRAND_DEEP} 0%, {BRAND} 100%)"
 
    # 배경 이미지 CSS 주입 / 인라인 style 대신 <style> 사용
    st.markdown(
        f"<style>.hero {{ background: {background}; }}</style>",
        unsafe_allow_html=True,
    )
 
    # 배너 내용 출력
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-inner">
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
 
 
def card_image(image_path: str, width: int = 230):
    """카드 안 일러스트 출력 / 가운데 정렬
    - Streamlit이 <img> 태그를 지우므로 st.image 사용
    """
    left, mid, right = st.columns([1, 3, 1])
    with mid:
        st.image(image_path, width=width)