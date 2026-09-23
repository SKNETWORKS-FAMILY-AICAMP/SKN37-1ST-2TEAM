import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from db.connection import fetch_df, execute_many

# .env 읽기
load_dotenv()

# 요청 주소와 API 키
url = "https://apis.data.go.kr/B553881/newRegistlnfoService_02/getnewRegistlnfoService02"
API_KEY = os.getenv("MOLIT_API_KEY")


# 조건 1조합의 신규등록 대수를 돌려주기
def get_count(year, month, region_code, gender_code, age_code):
    params = {
        "serviceKey": API_KEY,
        "registYy": year,
        "registMt": month,
        "registGrcCode": region_code,
        "sexdstn": gender_code,
        "agrde": age_code
    }
    response = requests.get(url, params=params, timeout=10)

    soup = BeautifulSoup(response.text, "html.parser")

    tag = soup.find("resultcode")
    if tag is None:
        print("예상 못한 응답:", response.text[:200])
        return None

    result_code = tag.text

    # 03 = NODATA_ERROR : 그 조건에 등록된 차가 없음 → 0
    if result_code == "03":
        return 0
    
    if result_code != "00":
        print("에러:", result_code)
        return None

    count = int(soup.find("dtaco").text)
    return count



# 수집할 연월 만들기 (2021.09 ~ 2026.08)
START_YM = "202109"
END_YM = "202608"

YMS = []
for year in range(2021, 2027):
    for month in range(1, 13):
        ym = f"{year}{month:02d}"
        if START_YM <= ym <= END_YM:
            YMS.append(ym)

if __name__ == "__main__":
    # 저장용 id + API용 코드 꺼내기
    regions = fetch_df("SELECT region_id, api_code FROM region ORDER BY region_id")
    genders = fetch_df("SELECT gender_id, api_code FROM gender ORDER BY gender_id")
    ages = fetch_df("SELECT age_id, api_code FROM age_group ORDER BY age_id")

    # 수집
    MAX_CALLS = 2900          # 하루 3,000번 제한 · 여유 100번
    SLEEP_SEC = 0.2
    SAVE_EVERY = 500
    call_count = 0
    rows = []

    # 이미 저장된 조합 가져오기
    done = fetch_df("SELECT stat_ym, region_id, gender_id, age_id FROM new_registration_stat")

    done_set = set()
    for _, row in done.iterrows():
        done_set.add((row["stat_ym"], row["region_id"], row["gender_id"], row["age_id"]))

    print("이미 저장된 조합:", len(done_set))

    # 모은 값을 한 번에 저장
    sql = """
        INSERT INTO new_registration_stat (stat_ym, region_id, gender_id, age_id, reg_count)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE reg_count = VALUES(reg_count)
    """

    stop = False

    for ym in YMS:
        if stop:
            break
        for _, region in regions.iterrows():
            if stop:
                break
            for _, gender in genders.iterrows():
                if stop:
                    break
                for _, age in ages.iterrows():
                    if call_count >= MAX_CALLS:
                        stop = True
                        break
                    key = (ym, region["region_id"], gender["gender_id"], age["age_id"])
                    if key in done_set:
                        continue

                    count = get_count(ym[:4], ym[4:], region["api_code"],
                                    gender["api_code"], age["api_code"])
                    if count is None:
                        print("응답 오류로 중단합니다. call_count:", call_count)
                        stop = True
                        break
                    rows.append((ym, region["region_id"], gender["gender_id"],
                                age["age_id"], count))
                    call_count += 1
                    # 진행률 확인
                    if call_count % 100 == 0:
                        print(f"진행: {call_count} / {MAX_CALLS}")

                    time.sleep(SLEEP_SEC)
                    if len(rows) >= SAVE_EVERY:
                        execute_many(sql, rows)
                        print("중간 저장:", call_count, "번째")
                        rows = []          # 저장했으니 비우기

    # 반복 끝난 뒤 저장
    execute_many(sql, rows)
    print("저장 완료:", len(rows), "행")
