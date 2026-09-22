# 불러오기 (os, requests, BeautifulSoup, load_dotenv)
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# .env 읽기
load_dotenv()

# url, API 키를 변수에 담기
url = "https://apis.data.go.kr/B553881/newRegistlnfoService_02/getnewRegistlnfoService02"
API_KEY = os.getenv("MOLIT_API_KEY")

def get_count(year, month, region_code, gender_code, age_code):
    # 1) params 딕셔너리 만들기 (매개변수 사용)
    params = {
        "serviceKey": API_KEY,
        "registYy": year,
        "registMt": month,
        "registGrcCode": region_code,
        "sexdstn": gender_code,
        "agrde": age_code
    }
    # 2) requests.get으로 요청
    response = requests.get(url, params=params)

    # 3) BeautifulSoup으로 resultcode 확인
    soup = BeautifulSoup(response.text, "html.parser")
    result_code = soup.find("resultcode").text

    #    "00"이 아니면? → 일단 print로 알려 주기
    if result_code != "00":
        print("에러:", result_code)
        return None
    
    # 4) dtaco 꺼내서 int로 바꾸고 return
    count = int(soup.find("dtaco").text)
    return count



