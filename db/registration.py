import pandas as pd


# DB에 있는 연월 목록
def get_available_yms():
    stat_ym = ["202509", "202510", "202511", "202512",
           "202601", "202602", "202603", "202604",
           "202605", "202606", "202607", "202608"]
    # 리스트 return
    return stat_ym

# 시도 이름 목록
def get_regions():
    region_name = ["서울", "부산", "전북", "전남", "대구", "인천", "광주"]

    # 리스트 return
    return region_name

# 성별 이름 목록
def get_genders():
    gender_name = ["남성", "여성"]
    # 리스트 return
    return gender_name


# 연령대 이름 목록
def get_age_groups():
    age_name = ["10대", "20대", "30대", "40대", "50대", "60대", "70대", "80대"]

    # 리스트 return
    return age_name

# 신규등록 조회
def get_new_registration(start_ym, end_ym, region=None, gender=None, age_group=None):
    df = pd.DataFrame({
        "stat_ym":     ["202608", "202608", "202608", "202607"],
        "region_name": ["서울",   "서울",   "부산",   "서울"],
        "gender_name": ["여성",   "남성",   "여성",   "여성"],
        "age_name":    ["20대",   "20대",   "30대",   "20대"],
        "reg_count":   [126,      210,      95,       110],
    })

    # 가짜 DataFrame return
    return df