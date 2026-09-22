-- 99_migrate_20260922.sql
-- 2026-09-22 기획 변경용. 이전 SQL(통계누리 차종별 등록 현황)을 이미 실행한 사람만 "한 번" 실행하세요.
-- 처음 세팅하는 사람은 실행하지 않아도 돼요.
--
-- 하는 일: 등록 현황 파트의 옛날 테이블 3개를 지워요.
--          FAQ 테이블(company, faq_category, faq)과 그 안의 데이터는 건드리지 않아요.
--
-- 실행 후 순서: 01_registration.sql → 03_seed.sql

USE car_faq;

DROP TABLE IF EXISTS registration_stat;   -- 옛 등록 통계 (region, vehicle_type을 참조해서 먼저 지워요)
DROP TABLE IF EXISTS vehicle_type;        -- 옛 차종 목록 (이번 기획에서 차종 필터 없음)
DROP TABLE IF EXISTS region;              -- 옛 시도 목록 (api_code 컬럼이 추가된 새 구조로 다시 만들어요)
