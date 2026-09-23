import html

import pandas as pd
import streamlit as st

from db.faq import get_categories, get_companies, search_faq

ALL = "전체"
PAGE_SIZE = 20
DB_ERROR_MSG = "데이터를 불러오지 못했어요. 잠시 후 다시 시도해주세요."

# 카테고리별 배지 색 (Streamlit 지원 색: blue, green, orange, red, violet, gray)
CATEGORY_COLOR = {
    "차량구매": "blue",
    "차량정비": "orange",
    "홈페이지": "green",
    "멤버스": "violet",
    "Pleos 계정": "red",
}


def category_badge(name: str) -> str:
    """카테고리명 → ':orange-background[차량정비]' 형태의 컬러 배지 마크다운"""
    color = CATEGORY_COLOR.get(name, "gray")
    return f":{color}-background[{name}]"


# 페이지 배경 · 검색창 · 펼침 목록 꾸미기 (CSS 주입)
st.markdown("""
<style>
/* 메인 영역 배경: 위쪽만 살짝 푸른 그라데이션 · 글자색도 함께 고정 (다크 테마 대비) */
.stApp {
    background: linear-gradient(180deg, #EAF3FB 0%, #FFFFFF 280px);
}
.stApp, .stApp p, .stApp li, .stApp label,
.stApp h1, .stApp h2, .stApp h3,
.stApp [data-testid="stMarkdownContainer"] {
    color: #16232E;
}
/* 흐린 안내 글자(캡션)는 회색으로 */
.stApp [data-testid="stCaptionContainer"], .stApp small {
    color: #556474;
}
/* 사이드바 배경 + 글자색 */
section[data-testid="stSidebar"] {
    background-color: #F0F5FA;
}
section[data-testid="stSidebar"] * {
    color: #16232E;
}
/* 펼침 목록: 둥근 모서리 + 옅은 테두리 + 흰 배경 */
div[data-testid="stExpander"] {
    background: #FFFFFF;
    border: 1px solid #D8E2EC;
    border-radius: 10px;
    margin-bottom: 6px;
}
div[data-testid="stExpander"] summary, div[data-testid="stExpander"] summary * {
    color: #16232E;
}
/* 답변 영역 */
.faq-answer {
    line-height: 1.7;
    margin-bottom: 0.6rem;
}
/* 검색창: 둥글게 + 흰 배경 + 진한 글자 */
div[data-testid="stTextInput"] input {
    border-radius: 10px;
    background-color: #FFFFFF;
    color: #16232E;
}
div[data-testid="stTextInput"] input::placeholder {
    color: #8A98A6;
}
/* 선택 상자(카테고리)도 흰 배경 + 진한 글자 */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background-color: #FFFFFF;
    color: #16232E;
}
</style>
""", unsafe_allow_html=True)


def to_param(value: str) -> str | None:
    return None if value == ALL else value


# 선택 목록은 캐싱 (한 번 불러온 목록은 1시간 동안 재사용)
@st.cache_data(ttl=3600)
def load_companies() -> list[str]:
    return get_companies()


@st.cache_data(ttl=3600)
def load_categories(company: str) -> list[str]:
    return get_categories(company)


# ──────────────────────────────────────────────
# 사이드바 (요소 1, 2)
# ──────────────────────────────────────────────
try:
    companies = load_companies()
except Exception:
    st.error(DB_ERROR_MSG)
    st.stop()

if not companies:
    st.info("아직 수집된 FAQ 데이터가 없어요.")
    st.stop()

with st.sidebar:
    st.header("조회 조건")
    # 1 · 기본값 첫 기업(기아) · 기업이 4개 이상이면 선택 상자로
    if len(companies) >= 4:
        company = st.selectbox("기업 선택", companies, index=0)
    else:
        company = st.radio("기업 선택", companies, index=0)

    try:
        categories = [ALL] + load_categories(company)  # 선택한 기업에 실제로 있는 카테고리
    except Exception:
        st.error(DB_ERROR_MSG)
        st.stop()

    # 2 · key에 기업명을 넣어 기업이 바뀌면 새 위젯이 되어 "전체"로 초기화됨
    category = st.selectbox("카테고리", categories, index=0, key=f"category_{company}")

# ──────────────────────────────────────────────
# 메인 (요소 3~7)
# ──────────────────────────────────────────────
st.title("기업 FAQ 조회")  # 3

# 4 키워드 검색창 · 엔터 → 재실행(검색) · 앞뒤 공백 제거
keyword_raw = st.text_input(
    "키워드 검색",
    placeholder="궁금한 내용을 입력하세요 (예: 정비 예약)",
    label_visibility="collapsed",
)
keyword = keyword_raw.strip() or None

# 조건이 바뀌면 "더 보기" 개수 초기화
query_key = (company, category, keyword)
if st.session_state.get("faq_query_key") != query_key:
    st.session_state.faq_query_key = query_key
    st.session_state.faq_limit = PAGE_SIZE

try:
    with st.spinner("조회 중..."):
        df = search_faq(company, to_param(category), keyword)
except Exception:
    st.error(DB_ERROR_MSG)
    st.stop()

# 5 결과 요약
st.caption(
    f"{company} · {'전체 카테고리' if category == ALL else category} · {len(df):,}건"
)

if df.empty:
    st.info("검색 결과가 없어요. 다른 키워드를 입력해보세요.")
    st.stop()

# 6 질문 목록 · 처음엔 모두 접힘 · 20개씩 표시
limit = st.session_state.faq_limit
for row in df.head(limit).itertuples(index=False):
    with st.expander(f"**Q. {row.question}** · {category_badge(row.category_name)}", expanded=False):
        # 7 답변 영역: 답변 전문 + 원본 보기 링크 + 수집일
        # 답변은 원문 글자 그대로 + 줄바꿈 유지 (마크다운으로 해석하지 않음 · 기획 "줄바꿈 유지")
        answer_html = html.escape(str(row.answer)).replace("\n", "<br>")
        st.markdown(f'<div class="faq-answer">{answer_html}</div>', unsafe_allow_html=True)
        collected = str(row.collected_at)[:10].replace("-", ".")  # 2026-09-21 → 2026.09.21
        if pd.notna(row.source_url) and row.source_url:  # 원본 주소 없으면(None, NaN, 빈 값) 링크 숨김
            st.caption(f"[원본 보기 ↗]({row.source_url}) · 수집일 {collected}")
        else:
            st.caption(f"수집일 {collected}")

# 더 보기 버튼
if limit < len(df):
    remaining = len(df) - limit
    if st.button(f"더 보기 ({min(PAGE_SIZE, remaining)}개 더)"):
        st.session_state.faq_limit = limit + PAGE_SIZE
        st.rerun()
