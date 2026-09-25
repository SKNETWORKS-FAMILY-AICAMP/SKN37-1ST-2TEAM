"""
자동차 신규등록 현황 (2페이지)
화면: 신지호 · 데이터: 강유나
근거: 화면 기획서 v0.4 「2. 자동차 신규등록 현황」 요소 1~10, 동작, 호출 함수

규칙
- 이 파일은 db/registration.py 조회 함수 호출만 함. SQL 작성 금지
- 연월은 함수에 '202608' 형식으로 넘기고, 화면엔 '2026.08'로 표시
- 시도 · 성별 · 연령대 "전체" → None으로 바꿔서 함수에 전달
- DB 오류 → 고정 안내 문구만 표시, 원래 오류 메시지 노출 금지
- 조회 버튼: 기획서는 st.form이지만, form 안에서는 연도를 바꿔도 월 목록이
  갱신되지 않아 st.button + session_state로 구현 (누를 때만 조회하는 동작은 동일)
- 다른 페이지에 다녀오면 선택 조건 · 조회 결과 · 탭을 처음 상태로 초기화
- 시작 연월은 끝 연월까지만, 끝 연월은 시작 연월부터만 고를 수 있음
- 탭마다 사이드바 조회 조건이 바뀜 (st.tabs의 key 기능 · Streamlit 1.55 이상 필요)
  · 상세 데이터 탭: 시작 연월, 끝 연월, 시도, 성별, 연령대 + 조회 버튼
  · 그래프 탭: 시작 연월, 끝 연월, 시도 (고르면 바로 반영)
  · 탭을 오가도 각 탭에서 고른 조건은 그대로 유지
- 그래프 탭: 요약 수치 (총 신규등록 · 월평균 · 최근 달 전월 대비 · 최다 시도/연령대)
  + 연월별 추이 (선) · 연령대별 신규등록 (묶은 막대, 남녀 색 구분) · 성별 비중 (도넛)
- 상단 배너 · 공통 스타일은 styles.py 사용 (inject_style, page_banner)
- 상세 데이터 탭 아래에 CSV 내려받기 버튼
"""
import altair as alt
import pandas as pd
import streamlit as st

from styles import inject_style, page_banner

from db.registration import (
    get_age_groups,
    get_available_yms,
    get_genders,
    get_new_registration,
    get_regions,
)

ALL = "전체"
DB_ERROR_MSG = "데이터를 불러오지 못했어요. 잠시 후 다시 시도해주세요."
GENDER_COLORS = {"남성": "#2a78d6", "여성": "#eb6834"}  # 그래프 색 (남성 파랑 · 여성 주황)

TAB_TABLE = "상세 데이터"
TAB_CHART = "그래프"
TAB_KEY = "newreg_tab"            # 지금 열린 탭 이름이 저장되는 곳


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

# ──────────────────────────────────────────────
# 다른 페이지에서 들어왔으면 선택 조건 · 조회 결과 · 탭 초기화
# (이 페이지의 상태는 모두 "newreg_"로 시작하는 이름으로 저장)
# ──────────────────────────────────────────────
if st.session_state.get("current_page") != "newreg":
    for k in [k for k in st.session_state if str(k).startswith("newreg_")]:
        del st.session_state[k]
st.session_state["current_page"] = "newreg"  # 지금 보고 있는 페이지 기록

# 지금 열린 탭 (처음엔 상세 데이터)
active_tab = st.session_state.get(TAB_KEY) or TAB_TABLE

# ──────────────────────────────────────────────
# 탭을 오가도 조건 유지
# - Streamlit은 화면에서 사라진 선택 상자의 값을 지움 (다른 탭에 가면 사라짐)
# - 그래서 고른 값을 "newreg_saved"에 따로 적어두고, 다시 그릴 때 그 값으로 시작
# ──────────────────────────────────────────────
saved: dict = st.session_state.setdefault("newreg_saved", {})


def remembered_select(label: str, options: list, key: str, default, **kwargs):
    """선택 상자 + 마지막 선택 기억 (목록에 없는 값이면 기본값으로)"""
    fallback = default if default in options else options[-1]
    if key in st.session_state:
        # 목록이 줄어서 지금 값이 목록에 없으면 → 기본값으로 바꿔서 화면에도 바로 반영
        if st.session_state[key] not in options:
            st.session_state[key] = fallback
        value = st.selectbox(label, options, key=key, **kwargs)        # 값은 session_state에서
    else:
        current = saved.get(key, fallback)
        if current not in options:
            current = fallback
        value = st.selectbox(label, options, index=options.index(current), key=key, **kwargs)
    saved[key] = value
    return value


# 기본값: 끝 = 가장 최근 연월, 시작 = 끝의 11개월 전 (최근 12개월, 데이터 범위 안에서)
default_end = yms[-1]
default_start = yms[max(0, len(yms) - 12)]


def ym_now(key: str, default_ym: str) -> str:
    """지금 골라져 있는 연월을 선택 상자를 그리기 전에 미리 읽기 → '202608'"""
    year = st.session_state.get(f"newreg_{key}_year", saved.get(f"newreg_{key}_year", default_ym[:4]))
    if year not in months_by_year:
        year = default_ym[:4]
    months = months_by_year[year]
    month_key = f"newreg_{key}_month_{year}"
    month = st.session_state.get(month_key, saved.get(month_key))
    if month not in months:
        month = default_ym[4:] if default_ym[:4] == year and default_ym[4:] in months else months[-1]
    return year + month


def ym_selector(label: str, default_ym: str, key: str,
                min_ym: str | None = None, max_ym: str | None = None) -> str:
    """연/월 선택 상자 2개 → '202608' 형식 문자열
    min_ym ~ max_ym 사이만 고를 수 있음
    (시작은 끝 연월까지만, 끝은 시작 연월부터만 → 시작이 끝보다 늦어질 수 없음)"""
    allowed = [ym for ym in yms
               if (min_ym is None or ym >= min_ym) and (max_ym is None or ym <= max_ym)]
    year_options = sorted({ym[:4] for ym in allowed})
    c1, c2 = st.columns(2)
    with c1:
        year = remembered_select(
            f"{label} 연도", year_options, key=f"newreg_{key}_year", default=default_ym[:4],
            format_func=lambda y: f"{y}년",
        )
    months = [ym[4:] for ym in allowed if ym[:4] == year]    # 범위 끝 연도면 그 월까지만
    with c2:
        default_month = default_ym[4:] if default_ym[:4] == year else months[-1]
        month = remembered_select(
            f"{label} 월", months,
            key=f"newreg_{key}_month_{year}",  # 연도별 별도 위젯 → 연도 바꾸면 월 목록 새로 생성
            default=default_month,
            format_func=lambda m: f"{int(m)}월",
        )
    return year + month


# ──────────────────────────────────────────────
# 제목 + 탭
# ──────────────────────────────────────────────
inject_style()      # 공통 스타일 주입 · 배너 · 카드 · 사이드바 모양
page_banner(        # 7 상단 배너
    "자동차 신규등록 현황",
    "assets/banner_registration.png",
)

# 사이드바 잔상 없애기
# - 탭을 누르면 탭은 바로 바뀌지만, 사이드바는 다시 실행이 끝나야 바뀜 → 이전 조건이 잠깐 남아 보임
# - 그래서 누른 탭과 맞지 않는 사이드바 묶음은 CSS로 바로 숨김
#   (첫 번째 탭 = 상세 데이터, 두 번째 탭 = 그래프 · Streamlit 버전마다 탭 HTML이 달라서 공통 속성만 사용)
#   (칸을 감싸는 상자 stLayoutWrapper까지 숨김 · 상자가 남으면 그 간격만큼 새 조건이 아래에서 올라오듯 보임)
st.html("""
<style>
body:has([role="tab"]:nth-child(2 of [role="tab"])[aria-selected="true"]) .st-key-newreg_side_table,
body:has([role="tab"]:nth-child(2 of [role="tab"])[aria-selected="true"]) :has(> .st-key-newreg_side_table),
body:has([role="tab"]:nth-child(1 of [role="tab"])[aria-selected="true"]) .st-key-newreg_side_chart,
body:has([role="tab"]:nth-child(1 of [role="tab"])[aria-selected="true"]) :has(> .st-key-newreg_side_chart) {
    display: none;
}
</style>
""")

# key → 열린 탭 이름이 st.session_state["newreg_tab"]에 저장됨
# on_change="rerun" → 탭을 바꾸면 다시 실행돼서 사이드바 조건이 바뀜
tab_table, tab_chart = st.tabs([TAB_TABLE, TAB_CHART], key=TAB_KEY, on_change="rerun")

# 사이드바 묶음 2개를 항상 따로 만들어 둠 (첫 칸 = 상세 데이터 조건, 둘째 칸 = 그래프 조건)
# - 한 칸을 두 탭이 같이 쓰면, 바뀐 조건 아래에 이전 탭의 선택 상자가 잠깐 붙어 보임
# - 칸을 나눠 두면 이전 탭의 선택 상자는 자기 칸에 남고, 그 칸은 위 CSS로 숨겨져서 안 보임
side_table = st.sidebar.container(key="newreg_side_table")
side_chart = st.sidebar.container(key="newreg_side_chart")


# ══════════════════════════════════════════════
# 탭 1 · 상세 데이터 (요소 1~6, 8~10)
# ══════════════════════════════════════════════
def show_table_tab():
    # 사이드바 조회 조건 (첫째 칸)
    with side_table:
        st.header("조회 조건")
        # 시작은 끝 연월까지만 고를 수 있음 (끝을 먼저 읽어 둠)
        start_ym = ym_selector("시작", default_start, "start",
                               max_ym=ym_now("end", default_end))               # 1
        end_ym = ym_selector("끝", default_end, "end", min_ym=start_ym)         # 2
        region = remembered_select("시도", [ALL] + region_list, "newreg_region", ALL)      # 3
        gender = remembered_select("성별", [ALL] + gender_list, "newreg_gender", ALL)      # 4
        age_group = remembered_select("연령대", [ALL] + age_list, "newreg_age", ALL)       # 5
        clicked = st.button("조회", type="primary", width="stretch")          # 6 · 사이드바 폭 꽉 차게

    # 조회 시점
    # - 처음 들어올 때: 기본값(최근 12개월, 전체, 전체, 전체)으로 바로 조회
    # - 이후: 조회 버튼을 누를 때만 조회
    if "newreg_query" not in st.session_state:
        st.session_state.newreg_query = (default_start, default_end, ALL, ALL, ALL)

    with tab_table:
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
            return

        # 8 조회 조건 요약
        st.caption(
            f"{ym_to_label(q_start)} ~ {ym_to_label(q_end)} · "
            f"{'전체 시도' if q_region == ALL else q_region} · "
            f"{'전체 성별' if q_gender == ALL else q_gender} · "
            f"{'전체 연령대' if q_age == ALL else q_age} · "
            f"{len(df):,}건"
        )

        if df.empty:
            st.info("선택한 조건에 맞는 데이터가 없어요.")
            return

        # 9 정렬: 연월 최신순 → 시도 → 성별 → 연령대 (각 목록 순서 기준)
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

        st.dataframe(table, hide_index=True, width="stretch",
                     height=min(520, 38 * (len(table) + 1)))

        # 11 조회 결과 내려받기 · utf-8-sig 로 저장해야 엑셀에서 한글이 안 깨짐
        st.download_button(
            "CSV로 내려받기",
            data=table.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"신규등록_{q_start}_{q_end}.csv",
            mime="text/csv",
        )


# ══════════════════════════════════════════════
# 탭 2 · 그래프 (요약 수치 + 그래프 3개)
# - 사이드바의 기간 · 시도로 조회 (성별 · 연령대는 항상 전체) · 고르면 바로 반영
# - 요약 수치: 총 신규등록 · 월평균 · 최근 달(전월 대비) · 최다 시도(시도를 골랐으면 최다 연령대)
# - 그래프: 연월별 추이 · 연령대별 신규등록 · 성별 비중
# ══════════════════════════════════════════════
def top_share(df: pd.DataFrame, column: str) -> tuple[str, float]:
    """해당 항목에서 합계가 가장 큰 값과 그 비중(%)"""
    sums = df.groupby(column)["reg_count"].sum()
    return str(sums.idxmax()), sums.max() / sums.sum() * 100


def month_total(ym: str, region: str) -> int | None:
    """한 달의 신규등록 합계 (전월 대비 계산용 · 실패하면 None)"""
    try:
        prev = get_new_registration(ym, ym, to_param(region), None, None)
    except Exception:
        return None
    return int(prev["reg_count"].sum()) if not prev.empty else None


def show_metrics(src: pd.DataFrame, by_month: pd.Series, region: str):
    """요약 수치 · 기간 · 시도에 따라 칸 수가 바뀜 (2~4칸)"""
    total = int(by_month.sum())
    n_month = len(by_month)

    # 전월 대비: 기간 마지막 달 vs 그 전달 (전달이 기간 밖이면 따로 조회)
    last_ym = by_month.index[-1]
    last = int(by_month.iloc[-1])
    pos = yms.index(last_ym)
    prev = None
    if pos > 0:
        prev_ym = yms[pos - 1]
        prev = int(by_month[prev_ym]) if prev_ym in by_month.index else month_total(prev_ym, region)
    delta = f"{(last - prev) / prev * 100:+.1f}%" if prev else None

    metrics = []  # (라벨, 값, st.metric 추가 옵션)
    if n_month == 1:
        # 한 달이면 총 신규등록 = 그 달 대수 → 전월 대비를 총 신규등록에 붙임 (같은 숫자 두 번 안 보이게)
        metrics.append(("총 신규등록", f"{total:,}대",
                        dict(delta=delta, delta_description="전월 대비" if delta else None)))
    else:
        metrics.append(("총 신규등록", f"{total:,}대", {}))
        metrics.append(("월평균", f"{total // n_month:,}대", {}))
        metrics.append((f"최근 달 ({ym_to_label(last_ym)})", f"{last:,}대",
                        dict(delta=delta, delta_description="전월 대비" if delta else None)))

    # 시도 전체면 최다 시도, 시도를 골랐으면 최다 연령대
    if region == ALL:
        name, share = top_share(src, "region_name")
        label = "최다 시도"
    else:
        name, share = top_share(src, "age_name")
        label = "최다 연령대"
    metrics.append((label, name, dict(delta=f"전체의 {share:.1f}%", delta_color="off", delta_arrow="off")))

    for col, (label, value, opts) in zip(st.columns(len(metrics)), metrics):
        col.metric(label, value, border=True, height="stretch", **opts)   # 카드 높이 맞춤


def draw_trend(by_month: pd.Series):
    """연월별 추이 · 선 그래프 (성별 · 연령대 합계)
    가로축 글자는 기간 길이에 맞춰 줄임 (정확한 연월은 마우스를 올리면 보임)
    · 13개월 이하: 매달 '2025.09'   · 14~36개월: 3개월마다 '2025.09'   · 37개월 이상: 1년마다 '2025'"""
    n = len(by_month)
    if n < 2:
        return                      # 한 달이면 추이가 없으니 제목까지 통째로 안 그림
    st.markdown("**연월별 추이**")
    trend = by_month.rename("reg_count").reset_index()
    trend["연월"] = trend["stat_ym"].map(ym_to_label)
    trend["날짜"] = pd.to_datetime(trend["stat_ym"] + "01", format="%Y%m%d")   # 시간 축으로 쓰기 위해

    if n <= 13:
        ticks, label_format = {"interval": "month", "step": 1}, "%Y.%m"
    elif n <= 36:
        ticks, label_format = {"interval": "month", "step": 3}, "%Y.%m"
    else:
        ticks, label_format = {"interval": "year", "step": 1}, "%Y"

    chart = (
        alt.Chart(trend)
        .mark_line(color="#4C5D73", strokeWidth=2.5,
                   point=alt.OverlayMarkDef(color="#4C5D73", size=50 if n <= 36 else 18, filled=True))
        .encode(
            x=alt.X("날짜:T", title=None, scale=alt.Scale(padding=12),
                    axis=alt.Axis(format=label_format, tickCount=ticks,
                                  labelAngle=0, labelOverlap=False, grid=False)),
            y=alt.Y("reg_count:Q", title="신규등록 (대)", scale=alt.Scale(zero=False),
                    axis=alt.Axis(labelExpr="format(datum.value, ',')")),
            tooltip=[alt.Tooltip("연월:N"),
                     alt.Tooltip("reg_count:Q", title="신규등록 (대)", format=",")],
        )
        .properties(height=280)
    )
    st.altair_chart(chart, use_container_width=True)


def draw_age(src: pd.DataFrame):
    """연령대별 신규등록 · 묶은 막대 (가로 연령대 · 색 성별 · 세로 = 기간 합계 대수)"""
    st.markdown("**연령대별 신규등록**")
    by_age = src.groupby(["age_name", "gender_name"], as_index=False)["reg_count"].sum()
    ages_shown = [a for a in age_list if a in set(by_age["age_name"])] + \
        [a for a in by_age["age_name"].unique() if a not in age_list]
    genders_shown = [g for g in gender_list if g in set(by_age["gender_name"])]
    chart = (
        alt.Chart(by_age)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("age_name:N", sort=ages_shown, title=None,
                    axis=alt.Axis(labelAngle=0, labelOverlap=False)),
            xOffset=alt.XOffset("gender_name:N", sort=genders_shown),
            y=alt.Y("reg_count:Q", title="신규등록 (대 · 기간 합계)",   # 고른 기간 전체를 더한 값
                    axis=alt.Axis(labelExpr="format(datum.value, ',')")),
            color=alt.Color(
                "gender_name:N", title=None,
                scale=alt.Scale(domain=genders_shown,
                                range=[GENDER_COLORS.get(g, "#8A98A6") for g in genders_shown]),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("age_name:N", title="연령대"),
                alt.Tooltip("gender_name:N", title="성별"),
                alt.Tooltip("reg_count:Q", title="신규등록 (대)", format=","),
            ],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)


def draw_gender(src: pd.DataFrame):
    """성별 비중 · 도넛 (고리 안에 비율 표시 · 범례는 위쪽)"""
    st.markdown("**성별 비중**")
    by_gender = src.groupby("gender_name", as_index=False)["reg_count"].sum()
    genders_shown = [g for g in gender_list if g in set(by_gender["gender_name"])] + \
        [g for g in by_gender["gender_name"] if g not in gender_list]
    by_gender["order"] = by_gender["gender_name"].map(genders_shown.index)
    by_gender["비율"] = by_gender["reg_count"] / by_gender["reg_count"].sum()

    base = alt.Chart(by_gender).encode(
        theta=alt.Theta("reg_count:Q", stack=True),
        order=alt.Order("order:Q"),
        color=alt.Color(
            "gender_name:N", title=None, legend=alt.Legend(orient="top"),
            scale=alt.Scale(domain=genders_shown,
                            range=[GENDER_COLORS.get(g, "#8A98A6") for g in genders_shown]),
        ),
        tooltip=[alt.Tooltip("gender_name:N", title="성별"),
                 alt.Tooltip("reg_count:Q", title="신규등록 (대)", format=","),
                 alt.Tooltip("비율:Q", format=".1%")],
    )
    donut = base.mark_arc(innerRadius=55, outerRadius=110, stroke="#FFFFFF", strokeWidth=2)
    labels = base.mark_text(radius=82, fontSize=14, fontWeight="bold").encode(
        text=alt.Text("비율:Q", format=".1%"),
        color=alt.value("#FFFFFF"),          # 글자는 흰색 (조각 색을 따라가면 안 보임)
    )
    st.altair_chart((donut + labels).properties(height=320), use_container_width=True)


def show_chart_tab():
    # 사이드바 그래프 조건 (둘째 칸)
    with side_chart:
        st.header("그래프 조건")
        # 기본값은 표와 같음 (최근 12개월)
        c_start = ym_selector("시작", default_start, "chart_start",
                              max_ym=ym_now("chart_end", default_end))
        c_end = ym_selector("끝", default_end, "chart_end", min_ym=c_start)
        chart_region = remembered_select("시도", [ALL] + region_list, "newreg_chart_region", ALL)

    with tab_chart:
        if c_start > c_end:
            st.error("시작 연월이 끝 연월보다 늦어요. 기간을 다시 선택해주세요.")
            return

        try:
            with st.spinner("조회 중..."):
                src = get_new_registration(c_start, c_end, to_param(chart_region), None, None)
        except Exception:
            st.error(DB_ERROR_MSG)
            return

        # 조회 조건 요약 (한 달이면 '2026.08', 여러 달이면 '2025.09 ~ 2026.08')
        period_label = (ym_to_label(c_start) if c_start == c_end
                        else f"{ym_to_label(c_start)} ~ {ym_to_label(c_end)}")
        region_label = "전국" if chart_region == ALL else chart_region
        st.caption(f"{period_label} · {region_label} · 성별 · 연령대 전체")

        if src.empty:
            st.info("선택한 조건에 맞는 데이터가 없어요.")
            return

        src = src.assign(reg_count=src["reg_count"].astype(int))
        by_month = src.groupby("stat_ym")["reg_count"].sum().sort_index()   # 연월별 합계

        show_metrics(src, by_month, chart_region)

        draw_trend(by_month)
        left, right = st.columns([3, 2], gap="medium")
        with left:
            draw_age(src)
        with right:
            draw_gender(src)


# 열린 탭의 조건 · 내용만 그림 (안 열린 탭은 조회도 안 함)
if active_tab == TAB_CHART:
    show_chart_tab()
else:
    show_table_tab()
