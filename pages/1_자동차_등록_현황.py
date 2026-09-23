import pandas as pd
import streamlit as st

from db.registration import (
    get_age_groups,
    get_available_yms,
    get_genders,
    get_new_registration,
    get_regions,
)

ALL = "전체"
DB_ERROR_MSG = "데이터를 불러오지 못했어요. 잠시 후 다시 시도해주세요."


# ──────────────────────────────────────────────
# 도우미
# ──────────────────────────────────────────────
def ym_to_label(ym: str) -> str:
    """'202608' → '2026.08'"""
    return f"{ym[:4]}.{ym[4:]}"


def to_param(value: str) -> str | None:
    """화면의 '전체' → 함수 약속의 None"""
    return None if value == ALL else value


def order_by(series: pd.Series, order: list[str]) -> pd.Categorical:
    """목록 순서대로 정렬되게 만들기 · 목록에 없는 값은 맨 뒤로"""
    extra = [v for v in series.unique() if v not in order]
    return pd.Categorical(series, categories=list(order) + extra, ordered=True)


# 선택 목록은 캐싱 (한 번 불러온 목록은 1시간 동안 재사용)
@st.cache_data(ttl=3600)
def load_options():
    return (
        get_available_yms(),
        get_regions(),
        get_genders(),
        get_age_groups(),
    )


# ──────────────────────────────────────────────
# 선택 목록 불러오기 (실패 시 안내 후 중단)
# ──────────────────────────────────────────────
try:
    yms, region_list, gender_list, age_list = load_options()
except Exception:
    st.error(DB_ERROR_MSG)
    st.stop()

if not yms:
    st.info("아직 수집된 신규등록 데이터가 없어요.")
    st.stop()

yms = sorted(yms)
years = sorted({ym[:4] for ym in yms})
months_by_year: dict[str, list[str]] = {}
for ym in yms:
    months_by_year.setdefault(ym[:4], []).append(ym[4:])

# 기본값: 끝 = 가장 최근 연월, 시작 = 끝의 11개월 전 (최근 12개월, 데이터 범위 안에서)
default_end = yms[-1]
default_start = yms[max(0, len(yms) - 12)]


# ──────────────────────────────────────────────
# 사이드바 필터 (요소 1~6)
# ──────────────────────────────────────────────
def ym_selector(label: str, default_ym: str, key: str) -> str:
    """연/월 선택 상자 2개 → '202608' 형식 문자열"""
    c1, c2 = st.columns(2)
    with c1:
        year = st.selectbox(
            f"{label} 연도", years,
            index=years.index(default_ym[:4]),
            format_func=lambda y: f"{y}년",
            key=f"{key}_year",
        )
    months = months_by_year[year]
    with c2:
        default_month = default_ym[4:] if default_ym[:4] == year else months[-1]
        month = st.selectbox(
            f"{label} 월", months,
            index=months.index(default_month),
            format_func=lambda m: f"{int(m)}월",
            key=f"{key}_month_{year}",  # 연도별 별도 위젯 → 연도 바꾸면 월 목록 새로 생성
        )
    return year + month


with st.sidebar:
    st.header("조회 조건")
    st.caption("시작 연월")
    start_ym = ym_selector("시작", default_start, "start")                  # 1
    st.caption("끝 연월")
    end_ym = ym_selector("끝", default_end, "end")                          # 2
    region = st.selectbox("시도", [ALL] + region_list, index=0)             # 3
    gender = st.selectbox("성별", [ALL] + gender_list, index=0)             # 4
    age_group = st.selectbox("연령대", [ALL] + age_list, index=0)           # 5
    clicked = st.button("조회", type="primary")                             # 6

# ──────────────────────────────────────────────
# 조회 시점
# - 처음 들어올 때: 기본값(최근 12개월, 전체, 전체, 전체)으로 바로 조회
# - 이후: 조회 버튼을 누를 때만 조회
# ──────────────────────────────────────────────
if "newreg_query" not in st.session_state:
    st.session_state.newreg_query = (default_start, default_end, ALL, ALL, ALL)

st.title("자동차 신규등록 현황")  # 7

if clicked:
    if start_ym > end_ym:
        st.error("시작 연월이 끝 연월보다 늦어요. 기간을 다시 선택해주세요.")
    else:
        st.session_state.newreg_query = (start_ym, end_ym, region, gender, age_group)

q_start, q_end, q_region, q_gender, q_age = st.session_state.newreg_query

try:
    with st.spinner("조회 중..."):
        df = get_new_registration(
            q_start, q_end, to_param(q_region), to_param(q_gender), to_param(q_age)
        )
except Exception:
    st.error(DB_ERROR_MSG)
    st.stop()

# 8 조회 조건 요약 + 신규등록 안내
st.caption(
    f"{ym_to_label(q_start)} ~ {ym_to_label(q_end)} · "
    f"{'전체 시도' if q_region == ALL else q_region} · "
    f"{'전체 성별' if q_gender == ALL else q_gender} · "
    f"{'전체 연령대' if q_age == ALL else q_age} · "
    f"{len(df):,}건"
)
st.caption("신규등록 = 그 달에 새로 등록된 차 기준 · 개인 명의만 집계 (법인 제외)")

if df.empty:
    st.info("선택한 조건에 맞는 데이터가 없어요.")
    st.stop()

# 9 상세 데이터 표 · 정렬: 연월 최신순 → 시도 → 성별 → 연령대 (각 목록 순서 기준)
df = df.copy()
df["region_name"] = order_by(df["region_name"], region_list)
df["gender_name"] = order_by(df["gender_name"], gender_list)
df["age_name"] = order_by(df["age_name"], age_list)
df = df.sort_values(
    ["stat_ym", "region_name", "gender_name", "age_name"],
    ascending=[False, True, True, True],
).reset_index(drop=True)

# 10 합계 행 · 지금 표에 보이는 행의 합 · 화면에서 계산
total = int(df["reg_count"].sum())

table = pd.DataFrame({
    "연월": df["stat_ym"].map(ym_to_label),
    "시도": df["region_name"].astype(str),
    "성별": df["gender_name"].astype(str),
    "연령대": df["age_name"].astype(str),
    "신규등록 (대)": df["reg_count"].map(lambda n: f"{int(n):,}"),
})
table.loc[len(table)] = ["합계", "", "", "", f"{total:,}"]

st.subheader("상세 데이터")
st.dataframe(table, hide_index=True, height=min(520, 38 * (len(table) + 1)))
