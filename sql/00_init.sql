-- 00_init.sql
-- DB 생성. 가장 먼저 한 번만 실행
-- 실행 순서: 00_init -> 01_registration -> 02_faq -> 03_seed

CREATE DATABASE IF NOT EXISTS car_faq
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
