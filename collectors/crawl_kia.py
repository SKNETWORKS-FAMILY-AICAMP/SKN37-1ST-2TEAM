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

    driver = webdriver.Chrome(
        options=options
    )

    return driver


def find_category_button(
    driver,
    category_name
):

    xpath_list = [

        f"//button[normalize-space()='{category_name}']",

        f"//a[normalize-space()='{category_name}']",

        f"//*[@role='tab' and normalize-space()='{category_name}']",

        f"//button[contains(normalize-space(.), '{category_name}')]",

        f"//a[contains(normalize-space(.), '{category_name}')]"
    ]


    for xpath in xpath_list:

        try:

            element = WebDriverWait(
                driver,
                3
            ).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        xpath
                    )
                )
            )

            return element


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


    category_names = [
        "차량 구매",
        "차량 정비",
        "홈페이지",
        "기아멤버스",
        "Pleos 계정"
    ]


    for selector in selectors:

        elements = driver.find_elements(
            By.CSS_SELECTOR,
            selector
        )

        question_items = []


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
                )


                if question_like:

                    question_items.append(
                        element
                    )


            except StaleElementReferenceException:

                continue


            except Exception:

                continue


        if len(question_items) > 0:

            return question_items


    return []

def get_question_text(item):

    try:

        return item.text.strip()

    except Exception:

        return ""


def click_question(
    driver,
    item
):

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


def get_answer_text(
    item,
    question
):

    xpath_list = [

        "./ancestor::li[1]",

        "./ancestor::*[contains(@class,'accordion')][1]",

        "./ancestor::*[contains(@class,'faq')][1]",

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


            if answer.startswith("A"):
                answer = answer[1:].strip()


            if answer:

                return answer


        except Exception:

            continue


    return ""


def crawl_kia_faq():

    driver = create_driver()

    faq_list = []


    try:

        driver.get(
            FAQ_URL
        )


        time.sleep(5)


        for site_category, db_category in CATEGORY_MAP.items():

            print()
            print(
                f"[{site_category}] FAQ 수집 시작..."
            )


            category_button = find_category_button(
                driver,
                site_category
            )


            if category_button is None:

                print(
                    f"카테고리를 찾지 못했습니다: {site_category}"
                )

                continue


            try:

                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    category_button
                )

                time.sleep(0.3)


                driver.execute_script(
                    "arguments[0].click();",
                    category_button
                )

                time.sleep(2)


            except Exception as e:

                print(
                    f"카테고리 클릭 실패: {e}"
                )

                continue



            items = get_question_items(
                driver
            )


            print(
                f"FAQ 목록: {len(items)}건"
            )


            for index in range(
                len(items)
            ):

                try:

                    items = get_question_items(
                        driver
                    )


                    if index >= len(items):

                        continue


                    item = items[index]



                    question = get_question_text(
                        item
                    )


                    if not question:
                        continue


                    click_question(
                        driver,
                        item
                    )


                    items = get_question_items(
                        driver
                    )


                    if index >= len(items):

                        continue


                    item = items[index]



                    answer = get_answer_text(
                        item,
                        question
                    )


                    if not answer:

                        print(
                            f"  답변 없음: {question}"
                        )

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


                    print(
                        f"  [{db_category}] {question}"
                    )


                except StaleElementReferenceException:

                    print(
                        f"  FAQ {index + 1}: 요소 변경됨"
                    )

                    continue


                except Exception as e:

                    print(
                        f"  FAQ {index + 1} 수집 실패: {e}"
                    )

                    continue


        unique_faq = []

        seen = set()


        for faq in faq_list:

            key = (
                faq["category"],
                faq["question"]
            )


            if key in seen:
                continue


            seen.add(
                key
            )


            unique_faq.append(
                faq
            )


        return unique_faq


    finally:

        driver.quit()



if __name__ == "__main__":

    data = crawl_kia_faq()


    print()
    print("=" * 80)
    print("기아 FAQ 크롤링 완료")
    print("=" * 80)

    print(
        f"총 수집 FAQ: {len(data)}건"
    )


    for item in data:

        print()
        print(
            "회사:",
            item["company"]
        )

        print(
            "카테고리:",
            item["category"]
        )

        print(
            "질문:",
            item["question"]
        )

        print(
            "답변:",
            item["answer"]
        )

        print(
            "URL:",
            item["source_url"]
        )

        print(
            "-" * 80
        )

    print()
    print("=" * 80)
    print("카테고리별 FAQ 개수")
    print("=" * 80)


    categories = [
        "차량구매",
        "차량정비",
        "홈페이지",
        "멤버스",
        "Pleos 계정"
    ]


    for category in categories:

        count = sum(
            1
            for item in data
            if item["category"] == category
        )


        print(
            category,
            ":",
            count,
            "개"
        )
