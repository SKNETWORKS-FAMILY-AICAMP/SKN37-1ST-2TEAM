-- 00_init.sql
-- DB 생성. 가장 먼저 한 번만 실행하세요.
-- 실행 순서: 00_init -> 01_registration -> 02_faq -> 03_seed
-- 01_registration은 "자동차 신규등록 현황" 테이블이에요. (2026-09-22 기획 변경)

CREATE DATABASE IF NOT EXISTS car_faq
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
