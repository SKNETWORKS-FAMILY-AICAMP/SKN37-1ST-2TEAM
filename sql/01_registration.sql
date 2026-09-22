-- 01_registration.sql
-- 자동차 등록 현황 영역 / 담당: 등록 현황 파트
-- 출처: 국토교통 통계누리 OPEN API, 자동차등록대수현황 시도별 (form_id=5498, style_num=2)
-- 조회 필터: 연월, 지역(시도), 차종

USE car_faq;

CREATE TABLE IF NOT EXISTS region (
  region_id   INT AUTO_INCREMENT PRIMARY KEY,
  region_name VARCHAR(20) NOT NULL UNIQUE          -- API의 '시도명' 그대로. 예: 서울, 경기, 전남광주
);

CREATE TABLE IF NOT EXISTS vehicle_type (
  type_id   INT AUTO_INCREMENT PRIMARY KEY,
  type_name VARCHAR(20) NOT NULL UNIQUE            -- 승용, 승합, 화물, 특수
);

CREATE TABLE IF NOT EXISTS registration_stat (
  stat_id   INT AUTO_INCREMENT PRIMARY KEY,
  stat_ym   CHAR(6) NOT NULL,                      -- API의 'date'. 예: '202608'
  region_id INT NOT NULL,
  type_id   INT NOT NULL,
  reg_count INT NOT NULL,                          -- API의 '<차종>>계' 값
  UNIQUE (stat_ym, region_id, type_id),            -- 년월, 시도, 차종 한 조합은 한 행
  FOREIGN KEY (region_id) REFERENCES region (region_id),
  FOREIGN KEY (type_id)   REFERENCES vehicle_type (type_id)
);

-- API 응답을 저장하는 규칙
-- 1) '시군구'가 '계'인 행만 저장, 시도 단위 합계라서 시군구 행을 따로 더하지 않아도 됨
-- 2) 한 행에서 '승용>계', '승합>계', '화물>계', '특수>계' 네 값을 꺼내 네 행으로 저장
--    가로로 펼쳐진 열을 세로로 바꾸는 작업 (pandas의 melt와 같은 개념)
-- 3) '총계>계'는 저장하지 않음, 네 차종을 더하면 같은 값이 나와서 SUM으로 계산
-- 4) 관용, 자가용, 영업용 열은 이번 범위(용도 필터 없음)에서는 쓰지 않음
-- 5) 시도명이 처음 보는 이름이면 region에 먼저 넣고 id를 찾아 사용
--    INSERT IGNORE INTO region (region_name) VALUES (%s);
-- 6) 최근 월은 잠정치라 값이 바뀔 수 있어서, 다시 받으면 새 값으로 덮어씌움
--    INSERT INTO registration_stat (stat_ym, region_id, type_id, reg_count)
--    VALUES (%s, %s, %s, %s)
--    ON DUPLICATE KEY UPDATE reg_count = VALUES(reg_count);

-- 화면 필터가 SQL 조건이 되는 예시 (Streamlit에서는 값을 %s로 넘김)

-- 부산, 2024년 1월 ~ 2026년 8월, 차종별 등록 대수
-- SELECT s.stat_ym, v.type_name, s.reg_count
-- FROM registration_stat s
-- JOIN region r       ON s.region_id = r.region_id
-- JOIN vehicle_type v ON s.type_id   = v.type_id
-- WHERE r.region_name = '부산'
--   AND s.stat_ym BETWEEN '202401' AND '202608'
-- ORDER BY s.stat_ym DESC, v.type_id;

-- 지역 '전체' 선택 시: 지역 조건 제외 → 전체 시도 행 표시 (합산 안 함)
-- SELECT s.stat_ym, r.region_name, v.type_name, s.reg_count
-- FROM registration_stat s
-- JOIN region r       ON s.region_id = r.region_id
-- JOIN vehicle_type v ON s.type_id   = v.type_id
-- WHERE s.stat_ym BETWEEN '202401' AND '202608'
-- ORDER BY s.stat_ym DESC, r.region_id, v.type_id;

-- 선택한 기간에 실제로 있는 시도만 목록으로 (지역 선택 상자 채우기)
-- SELECT DISTINCT r.region_id, r.region_name
-- FROM registration_stat s
-- JOIN region r ON s.region_id = r.region_id
-- WHERE s.stat_ym BETWEEN '202401' AND '202608'
-- ORDER BY r.region_id;
