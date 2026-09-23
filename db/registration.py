from db.connection import fetch_df


# DB에 있는 연월 목록
def get_available_yms():
    df = fetch_df("SELECT DISTINCT stat_ym FROM new_registration_stat ORDER BY stat_ym")
    # 리스트 return
    return df["stat_ym"].tolist()

# 시도 이름 목록
def get_regions():
    df = fetch_df("SELECT region_name FROM region ORDER BY region_id")
    # 리스트 return
    return df["region_name"].tolist()

# 성별 이름 목록
def get_genders():
    df = fetch_df("SELECT gender_name FROM gender ORDER BY gender_id")
    # 리스트 return
    return df["gender_name"].tolist()


# 연령대 이름 목록
def get_age_groups():
    df = fetch_df("SELECT age_name FROM age_group ORDER BY age_id")
    # 리스트 return
    return df["age_name"].tolist()

# 신규등록 조회
def get_new_registration(start_ym, end_ym, region=None, gender=None, age_group=None):
    sql = """
        SELECT s.stat_ym, r.region_name, g.gender_name, a.age_name, s.reg_count
        FROM new_registration_stat s
        JOIN region r    ON s.region_id = r.region_id
        JOIN gender g    ON s.gender_id = g.gender_id
        JOIN age_group a ON s.age_id    = a.age_id
        WHERE s.stat_ym BETWEEN %s AND %s
    """
    params = [start_ym, end_ym]

    # 전체가 아니라면 선택 옵션 조건 추가
    # 지역
    if region is not None:
        sql += " AND r.region_name = %s"
        params.append(region)

    # 성별
    if gender is not None:
        sql += " AND g.gender_name = %s"
        params.append(gender)

    # 연령대
    if age_group is not None:
        sql += " AND a.age_name = %s"
        params.append(age_group)

    sql += " ORDER BY s.stat_ym DESC, r.region_id, g.gender_id, a.age_id"

    return fetch_df(sql, params)