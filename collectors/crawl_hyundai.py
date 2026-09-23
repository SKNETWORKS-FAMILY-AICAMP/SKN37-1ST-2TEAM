import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


FAQ_URL = "https://www.hyundai.com/kr/ko/e/customer/center/faq"


CATEGORY_MAP = {
    "\uCC28\uB7C9\uAD6C\uB9E4": "\uCC28\uB7C9\uAD6C\uB9E4",
    "\uCC28\uB7C9\uC815\uBE44": "\uCC28\uB7C9\uC815\uBE44",
    "\uD648\uD398\uC774\uC9C0": "\uD648\uD398\uC774\uC9C0",
    "\uBE14\uB8E8\uBA64\uBC84\uC2A4": "\uBA64\uBC84\uC2A4",
    "Pleos \uACC4\uC815": "Pleos \uACC4\uC815",
}


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)


def crawl_hyundai_faq():

    driver = create_driver()
    faq_list = []

    try:
        driver.get(FAQ_URL)

        wait = WebDriverWait(driver, 10)

        time.sleep(3)

        for site_category, db_category in CATEGORY_MAP.items():

            print(f"\n[{site_category}] FAQ 수집 시작...")

            category_button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        f"//button[normalize-space()='{site_category}']"
                    )
                )
            )

            driver.execute_script(
                "arguments[0].click();",
                category_button
            )

            time.sleep(1)

            items = driver.find_elements(
                By.CSS_SELECTOR,
                ".list-wrap .list-item"
            )

            print(f"FAQ 목록: {len(items)}건")

            for index in range(len(items)):

                try:
                    items = driver.find_elements(
                        By.CSS_SELECTOR,
                        ".list-wrap .list-item"
                    )

                    if index >= len(items):
                        continue

                    item = items[index]

                    question_element = item.find_element(
                        By.CSS_SELECTOR,
                        ".list-content"
                    )

                    question = question_element.text.strip()

                    if not question:
                        continue

                    item_class = item.get_attribute("class")

                    if "active" not in item_class:

                        title_button = item.find_element(
                            By.CSS_SELECTOR,
                            ".list-title"
                        )

                        driver.execute_script(
                            "arguments[0].click();",
                            title_button
                        )

                        time.sleep(0.3)

                    items = driver.find_elements(
                        By.CSS_SELECTOR,
                        ".list-wrap .list-item"
                    )

                    if index >= len(items):
                        continue

                    item = items[index]

                    answer_element = item.find_element(
                        By.CSS_SELECTOR,
                        ".conts"
                    )

                    answer = answer_element.text.strip()

                    if not answer:
                        print(
                            f"  답변 없음: {question}"
                        )
                        continue

                    faq_list.append(
                        {
                            "category": db_category,
                            "question": question,
                            "answer": answer,
                            "source_url": FAQ_URL,
                        }
                    )

                    print(
                        f"  [{db_category}] {question}"
                    )

                except Exception as e:

                    print(
                        f"  FAQ {index + 1} 수집 실패: {e}"
                    )

        unique_faq = []
        seen = set()

        for faq in faq_list:

            question = faq["question"]

            if question in seen:
                continue

            seen.add(question)
            unique_faq.append(faq)

        print(
            f"\n총 수집 FAQ: {len(unique_faq)}건"
        )

        return unique_faq

    finally:
        driver.quit()


if __name__ == "__main__":

    data = crawl_hyundai_faq()

    print(
        f"\n최종 수집 건수: {len(data)}"
    )