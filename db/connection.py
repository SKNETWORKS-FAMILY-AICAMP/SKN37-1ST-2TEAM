import os                       # 환경변수 (.env 값)를 읽을 때 사용
import pymysql                  # 파이썬에서 MySQL에 접속하는 라이브러리
import pandas as pd             # 조회 겨로가를 표로 만들 때 사용
from dotenv import load_dotenv  # .env 파일 내용을 환경변수로 불러오는 함수

# .env 파일 내용 읽어오기
load_dotenv()

# MySQL과 연결
def get_connection():
    connection = pymysql.connect (
        # .env 파일에서 읽어오기
        host = os.getenv("DB_HOST"),
        port = int(os.getenv("DB_PORT", "3306")),
        user = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"),
        database = os.getenv("DB_NAME"),
        charset = "utf8mb4"
    )
    return connection

# SELECT 결과를 DataFrame으로 돌려주기
def fetch_df(sql, params=None):
    connection = get_connection()
    try:
        # SQL 실행하기
        cursor = connection.cursor()
        cursor.execute(sql, params)

        # 결과 행 모두 가져오기99_migrate → 01_registration → 03_seed 순서로 실행
        rows = cursor.fetchall()

        # 컬럼 이름만 모으기
        columns = []
        for col in cursor.description:
            columns.append(col[0])

        # 행과 컬럼 이름을 합쳐서 표로 돌려주기
        return pd.DataFrame(rows, columns=columns)
    finally:
        # 연결 닫기 (성공, 실패 상관없이 실행)
        connection.close()

# 여러 행을 한 번에 INSERT 하기
def execute_many(sql, rows):
    connection = get_connection()
    try:
        # 여러 행 INSERT 실행하기
        cursor = connection.cursor()
        cursor.executemany(sql, rows)

        # 저장 확정하기
        connection.commit()
    except Exception:
        # 에러가 나면 넣은 것 모두 취소하기
        connection.rollback()
        raise
    finally:
        # 연결 닫기 (성공, 실패 상관없이 실행)
        connection.close()



