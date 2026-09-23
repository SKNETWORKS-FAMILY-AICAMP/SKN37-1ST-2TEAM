"""
collectors/load_faq_csv.py / 크롤링 결과 CSV를 faq 테이블에 적재

사용
    python -m collectors.load_faq_csv dumps/hyundai_faq_data.csv 현대
    python -m collectors.load_faq_csv dumps/kia_faq_data.csv 기아

- 열 이름은 자동으로 찾음 (question / 질문 / Q 등)
- company, faq_category에 없는 값은 새로 추가
- 같은 질문이 이미 있으면 답변만 갱신 (중복 행 생기지 않음)
"""

import sys
from datetime import date

import pandas as pd

from db.connection import execute_many, fetch_df

# 열 이름 후보 / 앞에서부터 찾아서 처음 맞는 것 사용
COLUMN_CANDIDATES = {
    "question": ["question", "질문", "q", "title", "faq_question"],
    "answer": ["answer", "답변", "a", "content", "faq_answer"],
    "category": ["category", "category_name", "카테고리", "분류", "category_id"],
    "source_url": ["source_url", "url", "link", "링크", "출처"],
    "collected_at": ["collected_at", "수집일", "date", "crawled_at"],
    "company": ["company", "company_name", "기업", "제조사"],
}

DEFAULT_URL = {
    "현대": "https://www.hyundai.com/kr/ko/e/customer/center/faq",
    "기아": "https://www.kia.com/kr/customer-service/center/faq",
}


def find_column(df, key):
    """후보 목록에서 실제 존재하는 열 이름 찾기 / 없으면 None"""
    lowered = {str(c).strip().lower(): c for c in df.columns}
    for name in COLUMN_CANDIDATES[key]:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def read_csv(path):
    """CSV 읽기 / 한글 인코딩 자동 시도"""
    for encoding in ["utf-8-sig", "cp949", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("CSV 인코딩을 읽지 못했습니다. 원아님께 UTF-8로 다시 요청하세요.")


def get_id_map(table, id_column, name_column, names):
    """이름 목록을 받아 없는 것은 추가한 뒤 {이름: 번호} 반환"""
    rows = [(n,) for n in sorted(set(names)) if str(n).strip() != ""]
    if rows:
        execute_many(
            f"INSERT IGNORE INTO {table} ({name_column}) VALUES (%s)", rows
        )
    df = fetch_df(f"SELECT {id_column}, {name_column} FROM {table}")
    return dict(zip(df[name_column], df[id_column]))


def main(csv_path, company_name):
    df = read_csv(csv_path)
    print(f"CSV 읽기 완료 · {len(df):,}행")
    print("열 목록:", list(df.columns))

    # 1 열 이름 확인
    found = {key: find_column(df, key) for key in COLUMN_CANDIDATES}
    print("\n[열 연결 결과]")
    for key, column in found.items():
        print(f"  {key:12} ← {column if column else '(없음)'}")

    if not found["question"] or not found["answer"]:
        print("\n질문 또는 답변 열을 찾지 못했습니다. COLUMN_CANDIDATES에 실제 열 이름을 추가하세요.")
        return

    # 2 기업 · 카테고리 번호 확보
    companies = df[found["company"]] if found["company"] else [company_name] * len(df)
    categories = df[found["category"]] if found["category"] else ["기타"] * len(df)

    company_map = get_id_map("company", "company_id", "company_name", companies)
    category_map = get_id_map("faq_category", "category_id", "category_name", categories)
    print(f"\n기업 {len(company_map)}개 · 카테고리 {len(category_map)}개 확인")

    # 3 저장할 행 만들기
    today = date.today()
    rows = []
    skipped = 0
    for _, row in df.iterrows():
        question = str(row[found["question"]]).strip()
        answer = str(row[found["answer"]]).strip()
        if question == "" or question.lower() == "nan":
            skipped += 1
            continue

        company = str(row[found["company"]]).strip() if found["company"] else company_name
        category = str(row[found["category"]]).strip() if found["category"] else "기타"
        url = str(row[found["source_url"]]).strip() if found["source_url"] else DEFAULT_URL.get(company, "")
        collected = row[found["collected_at"]] if found["collected_at"] else today

        rows.append((
            company_map[company],
            category_map[category],
            question[:500],          # 테이블 정의가 VARCHAR(500)
            answer,
            url[:500],
            pd.to_datetime(collected).date() if found["collected_at"] else today,
        ))

    print(f"저장할 행: {len(rows):,}개 (빈 질문 {skipped}개 제외)")

    # 4 적재 / 같은 질문은 답변만 갱신
    sql = """
        INSERT INTO faq (company_id, category_id, question, answer, source_url, collected_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            answer       = VALUES(answer),
            category_id  = VALUES(category_id),
            source_url   = VALUES(source_url),
            collected_at = VALUES(collected_at)
    """
    execute_many(sql, rows)

    # 5 결과 확인
    check = fetch_df("""
        SELECT c.company_name, fc.category_name, COUNT(*) AS 건수
        FROM faq f
        JOIN company c       ON f.company_id  = c.company_id
        JOIN faq_category fc ON f.category_id = fc.category_id
        GROUP BY c.company_name, fc.category_name
        ORDER BY c.company_name, fc.category_name
    """)
    print("\n[적재 결과]")
    print(check.to_string(index=False))


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "dumps/hyundai_faq_data.csv"
    company = sys.argv[2] if len(sys.argv) > 2 else "현대"
    main(path, company)
