-- 01_registration.sql
-- 자동차 신규등록 현황 영역
-- 출처: 공공데이터포털 OPEN API
--       한국교통안전공단_자동차종합정보 신규등록정보 서비스
--       GET https://apis.data.go.kr/B553881/newRegistlnfoService_02/getnewRegistlnfoService02
-- 조회 필터: 연월, 시도, 성별, 연령대
-- ※ "신규" 등록 대수, 그 달에 새로 등록된 차만. (전체 보유 대수 아님)

USE car_faq;

-- ※ 이전 기획(통계누리 차종별) SQL을 이미 실행한 사람은
--    99_migrate_20260922.sql 을 먼저 한 번 실행한 뒤 이 파일을 실행

-- 시도
-- region_name : 화면에 보여 줄 이름 (예: 서울)
-- api_code    : API 요청 변수 registGrcCode에 넣을 값 (기술문서 코드표 확인 후 입력)
CREATE TABLE IF NOT EXISTS region (
  region_id   INT AUTO_INCREMENT PRIMARY KEY,
  region_name VARCHAR(20) NOT NULL UNIQUE,
  api_code    VARCHAR(10) UNIQUE
);

-- 성별
-- api_code : API 요청 변수 sexdstn에 넣을 값
CREATE TABLE IF NOT EXISTS gender (
  gender_id   INT AUTO_INCREMENT PRIMARY KEY,
  gender_name VARCHAR(10) NOT NULL UNIQUE,         -- 남성, 여성
  api_code    VARCHAR(10) UNIQUE
);

-- 연령대
-- api_code : API 요청 변수 agrde에 넣을 값
CREATE TABLE IF NOT EXISTS age_group (
  age_id   INT AUTO_INCREMENT PRIMARY KEY,
  age_name VARCHAR(10) NOT NULL UNIQUE,            -- 10대 ~ 80대
  api_code VARCHAR(10) UNIQUE
);

-- 신규등록 통계
-- 연월 + 시도 + 성별 + 연령대 1조합 = 1행
-- 한 달 = 17개 시도 × 2개 성별 × 8개 연령대 = 272행 (= API 호출 272번)
CREATE TABLE IF NOT EXISTS new_registration_stat (
  stat_id   INT AUTO_INCREMENT PRIMARY KEY,
  stat_ym   CHAR(6) NOT NULL,                      -- registYy + registMt. 예: '202608'
  region_id INT NOT NULL,
  gender_id INT NOT NULL,
  age_id    INT NOT NULL,
  reg_count INT NOT NULL,                          -- API 응답의 dtaCo 값
  UNIQUE (stat_ym, region_id, gender_id, age_id),  -- 한 조합은 한 행
  FOREIGN KEY (region_id) REFERENCES region (region_id),
  FOREIGN KEY (gender_id) REFERENCES gender (gender_id),
  FOREIGN KEY (age_id)    REFERENCES age_group (age_id)
);

-- API 응답을 저장하는 규칙
-- 1) 요청 1번 = 숫자 1개. 응답 <body><dtaCo>숫자</dtaCo></body> 의 dtaCo가 reg_count.
-- 2) 연월 × 시도 × 성별 × 연령대 조합마다 반복 호출
--    요청 변수: serviceKey, registYy(YYYY), registMt(MM, 두 자리), registGrcCode, sexdstn, agrde
-- 3) 코드 값은 region, gender, age_group 테이블의 api_code에서 꺼내 사용
-- 4) 응답 형식은 XML. (요청에 _type=json 을 붙여 JSON이 오는지 먼저 확인해 보기)
-- 5) 다시 받으면 새 값으로 덮어씌움.
--    INSERT INTO new_registration_stat (stat_ym, region_id, gender_id, age_id, reg_count)
--    VALUES (%s, %s, %s, %s, %s)
--    ON DUPLICATE KEY UPDATE reg_count = VALUES(reg_count);
-- 6) 개발 계정은 하루 3,000번까지 호출 가능, 12개월 = 3,264번이라 이틀에 나눠 받음

-- 시도 수집이 불가능하다고 결정되면 (예비안)
-- region 테이블과 region_id 컬럼을 빼고, UNIQUE (stat_ym, gender_id, age_id) 로 바꾸기

-- 화면 필터가 SQL 조건이 되는 예시 (Streamlit에서는 값을 %s로 넘김)

-- 부산, 20대, 여성, 2025년 9월 ~ 2026년 8월
-- SELECT s.stat_ym, r.region_name, g.gender_name, a.age_name, s.reg_count
-- FROM new_registration_stat s
-- JOIN region r    ON s.region_id = r.region_id
-- JOIN gender g    ON s.gender_id = g.gender_id
-- JOIN age_group a ON s.age_id    = a.age_id
-- WHERE s.stat_ym BETWEEN '202509' AND '202608'
--   AND r.region_name = '부산'
--   AND g.gender_name = '여성'
--   AND a.age_name    = '20대'
-- ORDER BY s.stat_ym DESC;

-- 시도, 성별, 연령대 '전체' 선택 시: 그 조건만 빼기 → 해당 행을 모두 표시 (합산 안 함)
-- SELECT s.stat_ym, r.region_name, g.gender_name, a.age_name, s.reg_count
-- FROM new_registration_stat s
-- JOIN region r    ON s.region_id = r.region_id
-- JOIN gender g    ON s.gender_id = g.gender_id
-- JOIN age_group a ON s.age_id    = a.age_id
-- WHERE s.stat_ym BETWEEN '202509' AND '202608'
-- ORDER BY s.stat_ym DESC, r.region_id, g.gender_id, a.age_id;
