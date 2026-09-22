-- 03_seed.sql
-- 기준 데이터. 모두가 같은 값으로 시작하도록 함께 실행
-- 여러 번 실행해도 중복이 들어가지 않음
-- (신규등록 기준 데이터는 이미 있으면 api_code만 새 값으로 수정)

USE car_faq;
-- api_code = 공공데이터포털 신규등록정보 API 요청 변수에 넣는 값 (기술문서 코드표 기준)

-- 시도 17개 (api_code = 요청 변수 registGrcCode 값)
INSERT INTO region (region_name, api_code) VALUES
  ('서울', '1'),
  ('부산', '2'),
  ('대구', '3'),
  ('인천', '4'),
  ('광주', '5'),
  ('대전', '6'),
  ('울산', '7'),
  ('세종', '8'),
  ('경기', '9'),
  ('강원', '10'),
  ('충북', '11'),
  ('충남', '12'),
  ('전북', '13'),
  ('전남', '14'),
  ('경북', '15'),
  ('경남', '16'),
  ('제주', '17')
ON DUPLICATE KEY UPDATE api_code = VALUES(api_code);

-- 성별
INSERT INTO gender (gender_name, api_code) VALUES
  ('남성', '남자'), 
  ('여성', '여자')
ON DUPLICATE KEY UPDATE api_code = VALUES(api_code);

-- 연령대 (API 기준 10대 ~ 80대)
INSERT INTO age_group (age_name, api_code) VALUES
  ('10대', '1'), 
  ('20대', '2'), 
  ('30대', '3'), 
  ('40대', '4'), 
  ('50대', '5'), 
  ('60대', '6'), 
  ('70대', '7'), 
  ('80대', '8')
ON DUPLICATE KEY UPDATE api_code = VALUES(api_code);  

-- 코드표 확인 후 이렇게 채우기 (값은 예시가 아니라 빈칸)
-- UPDATE region    SET api_code = '__' WHERE region_name = '서울';
-- UPDATE gender    SET api_code = '__' WHERE gender_name = '남성';
-- UPDATE age_group SET api_code = '__' WHERE age_name    = '20대';


-- 기업: 시간이 남으면 기업을 더 추가, 한 줄만 추가하면 됨. 예: ('제네시스')
INSERT IGNORE INTO company (company_name) VALUES
  ('기아'), ('현대');

-- FAQ 카테고리: 팀 공통 카테고리 5개 (기아, 현대 공동 사용)
-- 기업별 원래 탭 → 공통 카테고리 (두 기업 공통 주제만 수집)
--   차량구매   ← 기아 '차량 구매'   / 현대 '차량구매'
--   차량정비   ← 기아 '차량 정비'   / 현대 '차량정비'
--   홈페이지   ← 기아 '홈페이지'    / 현대 '홈페이지'
--   멤버스     ← 기아 '기아멤버스'  / 현대 '블루멤버스'
--   Pleos 계정 ← 기아 'Pleos 계정' / 현대 'Pleos 계정'
--   수집 안 함: 기아 TOP 10, PBV, Kia App, 기타 / 현대 블루링크, 시승, 빌트인캠, 현대 디지털 키, 기타
-- 기업을 추가하면 그 기업의 탭도 이 5개 중 하나로 맞추기, 안 맞는 탭은 수집하지 않음
INSERT IGNORE INTO faq_category (category_name) VALUES
  ('차량구매'), ('차량정비'), ('홈페이지'), ('멤버스'), ('Pleos 계정');
