# collectors/crawl_kia.py

import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException
)


FAQ_URL = "https://www.kia.com/kr/customer-service/center/faq"

MAX_PER_CATEGORY = 15


CATEGORY_MAP = {
    "차량 구매": "차량구매",
    "차량 정비": "차량정비",
    "홈페이지": "홈페이지",
    "기아멤버스": "멤버스",
    "Pleos 계정": "Pleos 계정"
}


def create_driver():

    options = Options()

    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    return webdriver.Chrome(options=options)



def find_category_button(driver, category_name):

    xpath_list = [
        f"//button[normalize-space()='{category_name}']",
        f"//a[normalize-space()='{category_name}']",
        f"//*[@role='tab' and normalize-space()='{category_name}']",
        f"//button[contains(normalize-space(.), '{category_name}')]",
        f"//a[contains(normalize-space(.), '{category_name}')]"
    ]

    for xpath in xpath_list:

        try:

            return WebDriverWait(driver,3).until(EC.element_to_be_clickable((By.XPATH, xpath)))

        except TimeoutException:
            continue

    return None


def get_question_items(driver):

    selectors = [
        "button[aria-expanded]",
        "[role='button'][aria-expanded]",
        ".faq button",
        ".accordion button",
        "[class*='faq'] button",
        "[class*='accordion'] button",
        "li button"
    ]

    category_names = list(CATEGORY_MAP.keys())

    question_items = []

    for selector in selectors:

        elements = driver.find_elements(
            By.CSS_SELECTOR,
            selector
        )

        for element in elements:

            try:

                if not element.is_displayed():
                    continue

                text = element.text.strip()

                if not text:
                    continue

                if text in category_names:
                    continue

                if len(text) > 500:
                    continue

                question_like = (
                    "?" in text
                    or "나요" in text
                    or "까요" in text
                    or "무엇" in text
                    or "어떻게" in text
                    or "인가요" in text
                    or "되나요" in text
                    or "있나요" in text
                )

                if question_like:
                    question_items.append(element)

            except Exception:
                continue


    # 질문 텍스트 기준 중복 제거
    unique_items = []
    seen_text = set()

    for item in question_items:

        try:
            text = item.text.strip()
        except Exception:
            continue

        if text in seen_text:
            continue

        seen_text.add(text)
        unique_items.append(item)

    return unique_items



def get_question_text(item):

    try:
        return item.text.strip()

    except Exception:
        return ""


def click_question(driver, item):

    try:

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            item
        )

        time.sleep(0.2)

        driver.execute_script(
            "arguments[0].click();",
            item
        )

        time.sleep(0.5)

        return True

    except Exception:
        return False

def get_answer_text(item, question):

    xpath_list = [
        "./ancestor::li[1]",
        "./ancestor::*[contains(@class,'accordion')][1]",
        "./ancestor::*[contains(@class,'faq')][1]",
        "./ancestor::*[contains(@class,'item')][1]",
        "./parent::*"
    ]

    for xpath in xpath_list:

        try:

            container = item.find_element(
                By.XPATH,
                xpath
            )

            full_text = container.text.strip()

            if not full_text:
                continue

            answer = full_text.replace(
                question,
                "",
                1
            ).strip()

            if answer.startswith("A."):
                answer = answer[2:].strip()

            elif answer.startswith("A"):
                answer = answer[1:].strip()

            if answer:
                return answer

        except Exception:
            continue

    return ""


def category_count(faq_list, category):

    return sum(
        1
        for faq in faq_list
        if faq["category"] == category
    )


def collect_current_page(
    driver,
    db_category,
    faq_list
):

    items = get_question_items(driver)

    print(f"  현재 페이지 FAQ 후보: {len(items)}건")

    for index in range(len(items)):

        # 최대 수집량 도달
        if category_count(faq_list,db_category) >= MAX_PER_CATEGORY:

            print(f"  [{db_category}] "f"최대 {MAX_PER_CATEGORY}건 수집 완료")

            return True


        try:

            items = get_question_items(driver)

            if index >= len(items):
                continue

            item = items[index]

            question = get_question_text(item)

            if not question:
                continue


            # 중복 질문 제외
            already_exists = any(
                faq["category"] == db_category
                and faq["question"] == question
                for faq in faq_list
            )

            if already_exists:
                continue


            # 질문 클릭
            click_question(
                driver,
                item
            )


            items = get_question_items(driver)

            if index >= len(items):
                continue

            item = items[index]


            answer = get_answer_text(
                item,
                question
            )


            if not answer:

                print(f"    답변 없음: {question}")

                continue


            faq_list.append(
                {
                    "company": "기아",
                    "category": db_category,
                    "question": question,
                    "answer": answer,
                    "source_url": FAQ_URL
                }
            )


            current_count = category_count(faq_list,db_category)


            print(
                f"    [{db_category}] "
                f"{current_count}/{MAX_PER_CATEGORY} "
                f"{question}"
            )


        except StaleElementReferenceException:

            continue


        except Exception as e:

            print(f"    FAQ {index + 1} 수집 실패: {e}")

    return False

def go_to_next_page(
    driver,
    current_page
):

    next_page = current_page + 1

    xpath_list = [
        f"//button[normalize-space()='{next_page}']",
        f"//a[normalize-space()='{next_page}']",
        f"//*[@role='button' and normalize-space()='{next_page}']"
    ]

    for xpath in xpath_list:

        buttons = driver.find_elements(
            By.XPATH,
            xpath
        )

        for button in buttons:

            try:

                if not button.is_displayed():
                    continue

                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    button
                )

                time.sleep(0.2)

                driver.execute_script(
                    "arguments[0].click();",
                    button
                )

                time.sleep(1)

                return True

            except Exception:
                continue

    return False

def collect_category(
    driver,
    site_category,
    db_category,
    faq_list
):

    print()
    print("=" * 70)
    print(f"[{site_category}] FAQ 수집 시작")
    print("=" * 70)


    category_button = find_category_button(
        driver,
        site_category
    )

    if category_button is None:

        print(f"카테고리를 찾지 못했습니다: {site_category}")

        return


    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        category_button
    )

    time.sleep(0.3)

    driver.execute_script("arguments[0].click();",category_button)

    time.sleep(2)


    page = 1


    while True:

        print(f"  {page}페이지 수집 중...")


        limit_reached = collect_current_page(driver,db_category,faq_list)


        # 15건 다 모으면 다음 페이지 안 감
        if limit_reached:
            break


        # 현재까지 이미 15건이면 종료
        if category_count(faq_list,db_category) >= MAX_PER_CATEGORY:

            break


        moved = go_to_next_page(
            driver,
            page
        )


        if not moved:
            break


        page += 1


        # 무한 반복 방지
        if page > 30:
            break


    print(
        f"[{db_category}] 최종 수집: "
        f"{category_count(faq_list, db_category)}건"
    )


def crawl_kia_faq():

    driver = create_driver()

    faq_list = []


    try:

        driver.get(FAQ_URL)

        print("기아 FAQ 페이지 접속 중...")

        time.sleep(5)


        for site_category, db_category in CATEGORY_MAP.items():

            try:

                collect_category(
                    driver,
                    site_category,
                    db_category,
                    faq_list
                )

            except Exception as e:

                print(
                    f"[{site_category}] 수집 오류: {e}"
                )


        # 최종 중복 제거
        unique_faq = []
        seen = set()

        for faq in faq_list:

            key = (
                faq["category"],
                faq["question"]
            )

            if key in seen:
                continue

            seen.add(key)
            unique_faq.append(faq)


        return unique_faq


    finally:

        driver.quit()


if __name__ == "__main__":

    data = crawl_kia_faq()


    print()
    print("=" * 80)
    print("기아 FAQ 크롤링 완료")
    print("=" * 80)

    print(f"총 수집 FAQ: {len(data)}건")


    categories = ["차량구매","차량정비","홈페이지","멤버스","Pleos 계정"]


    print()
    print("=" * 80)
    print("카테고리별 FAQ 개수")
    print("=" * 80)


    for category in categories:

        count = sum(
            1
            for item in data
            if item["category"] == category
        )

        print(category,":",count,"개")
