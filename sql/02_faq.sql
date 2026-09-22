-- 02_faq.sql
-- 기업 FAQ 영역 (웹크롤링으로 수집) / 담당: FAQ 파트 (기아, 현대)
-- 기아와 현대가 같은 테이블을 함께 써요. 정의는 한 곳에서만 고치세요.

USE car_faq;

CREATE TABLE IF NOT EXISTS company (
  company_id   INT AUTO_INCREMENT PRIMARY KEY,
  company_name VARCHAR(50) NOT NULL UNIQUE         -- 예: 기아, 현대
);

CREATE TABLE IF NOT EXISTS faq_category (
  category_id   INT AUTO_INCREMENT PRIMARY KEY,
  category_name VARCHAR(50) NOT NULL UNIQUE        -- 팀 공통 카테고리: 차량구매, 차량정비, 홈페이지, 멤버스, Pleos 계정
);

CREATE TABLE IF NOT EXISTS faq (
  faq_id       INT AUTO_INCREMENT PRIMARY KEY,
  company_id   INT NOT NULL,
  category_id  INT NOT NULL,
  question     VARCHAR(500) NOT NULL,
  answer       TEXT NOT NULL,
  source_url   VARCHAR(500),                       -- 원본 페이지 주소
  collected_at DATE NOT NULL,                      -- 수집일
  UNIQUE (company_id, question),                   -- 재크롤링해도 중복이 들어가지 않게
  FOREIGN KEY (company_id)  REFERENCES company (company_id),
  FOREIGN KEY (category_id) REFERENCES faq_category (category_id)
);

-- 화면 필터가 SQL 조건이 되는 예시
-- 기아 FAQ 중 '차량정비' 카테고리, 질문에 '예약'이 들어간 것
-- SELECT f.question, f.answer, f.source_url, f.collected_at
-- FROM faq f
-- JOIN company c      ON f.company_id  = c.company_id
-- JOIN faq_category k ON f.category_id = k.category_id
-- WHERE c.company_name  = '기아'
--   AND k.category_name = '차량정비'
--   AND f.question LIKE '%예약%';
