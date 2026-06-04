-- name: sampleBootstrap.createConfigTable
CREATE TABLE IF NOT EXISTS T_SAMPLE_CONFIG (
       CONFIG_KEY TEXT PRIMARY KEY,
       CONFIG_JSON TEXT NOT NULL,
       REG_DT TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       UPD_DT TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- name: sampleBootstrap.createTaskTable
CREATE TABLE IF NOT EXISTS T_SAMPLE_TASK (
       TASK_NO BIGSERIAL PRIMARY KEY,
       DATA_NM TEXT NOT NULL,
       DATA_DESC TEXT,
       OWNER_NM TEXT,
       STAT_CD TEXT NOT NULL,
       AMT REAL,
       ATTACH_NM TEXT,
       REG_DT TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- name: sampleBootstrap.createFormTable
CREATE TABLE IF NOT EXISTS T_SAMPLE_FORM_SUBMIT (
       FORM_NO BIGSERIAL PRIMARY KEY,
       USER_NM TEXT NOT NULL,
       USER_EML TEXT NOT NULL,
       PHONE_TXT TEXT NOT NULL,
       CATEGORY_CD TEXT NOT NULL,
       START_DT TEXT NOT NULL,
       END_DT TEXT NOT NULL,
       BUDGET_RANGE_TXT TEXT NOT NULL,
       REQUIREMENT_TXT TEXT,
       FEATURE_JSON TEXT,
       REF_URL TEXT,
       ATTACH_NM TEXT,
       REG_DT TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- name: sampleBootstrap.createAdminUserTable
CREATE TABLE IF NOT EXISTS T_SAMPLE_ADMIN_USER (
       USER_NO BIGSERIAL PRIMARY KEY,
       USER_NM TEXT NOT NULL,
       USER_EML TEXT NOT NULL UNIQUE,
       ROLE_CD TEXT NOT NULL,
       STAT_CD TEXT NOT NULL,
       NOTIFY_EMAIL INTEGER NOT NULL DEFAULT 0,
       NOTIFY_SMS INTEGER NOT NULL DEFAULT 0,
       NOTIFY_PUSH INTEGER NOT NULL DEFAULT 0,
       PROFILE_IMG_URL TEXT,
       REG_DT TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- name: sampleBootstrap.seedTasks
INSERT INTO T_SAMPLE_TASK (
       DATA_NM,
       DATA_DESC,
       OWNER_NM,
       STAT_CD,
       AMT,
       ATTACH_NM,
       REG_DT
)
VALUES ( '랜딩 페이지 시안 확정', '랜딩 IA 및 카피 확정', '기획팀', 'done', 1200000, 'landing_spec.pdf', '2026-02-10' ),
       ( '회원가입 폼 검증 규칙 반영', '필수값/형식/비밀번호 확인 검증', '프론트', 'running', 800000, 'signup_flow.fig', '2026-02-12' ),
       ( '로그 마스킹 정책 적용', '민감정보 마스킹 규칙 점검', '백엔드', 'pending', 950000, 'log_policy.md', '2026-02-14' ),
       ( '샘플 페이지 QA', '랜딩/샘플 플로우 수동 점검', 'QA', 'ready', 500000, '', '2026-02-16' ),
       ( '대시보드 통계 API 점검', '상태 집계/금액 합계 검증', '백엔드', 'running', 670000, 'dashboard_api.postman_collection.json', '2026-02-17' ),
       ( '공개 GNB 모바일 드로어 개선', '모바일 햄버거 메뉴 접근성 개선', '프론트', 'done', 420000, 'gnb_mobile.png', '2026-02-17' ),
       ( '포트폴리오 섹션 리뉴얼', '히어로/아키텍처/샘플 섹션 개편', '디자인', 'pending', 730000, 'portfolio_wireframe.fig', '2026-02-18' ),
       ( '회원가입 중복 이메일 처리', '409 AUTH_409_USER_EXISTS 매핑', '백엔드', 'done', 390000, '', '2026-02-18' ),
       ( '프로필 설정 화면 구성', '내 프로필/시스템 설정 탭 구현', '프론트', 'running', 610000, 'settings_ui.fig', '2026-02-19' ),
       ( 'T_DATA 샘플 데이터 정리', '초기 샘플 레코드/상태코드 정리', 'DBA', 'ready', 250000, 'seed_data.sql', '2026-02-20' ),
       ( '미들웨어 공개 경로 점검', '공개/보호 경로 리다이렉트 테스트', '백엔드', 'done', 540000, 'middleware_test.log', '2026-02-21' ),
       ( '숨고/크몽 샘플 시나리오 작성', '랜딩→샘플 허브→상세 샘플 퍼널 스크립트', '기획팀', 'pending', 460000, 'demo_script.docx', '2026-02-22' );

-- name: sampleBootstrap.seedAdminUsers
INSERT INTO T_SAMPLE_ADMIN_USER (
       USER_NM,
       USER_EML,
       ROLE_CD,
       STAT_CD,
       NOTIFY_EMAIL,
       NOTIFY_SMS,
       NOTIFY_PUSH,
       PROFILE_IMG_URL,
       REG_DT
)
VALUES ( '김관리', 'admin@demo.demo', 'admin', 'active', 1, 0, 1, '', '2026-01-15' ),
       ( '박에디터', 'editor@demo.demo', 'editor', 'active', 1, 1, 0, '', '2026-01-20' ),
       ( '이사용자', 'user@demo.demo', 'user', 'inactive', 0, 0, 0, '', '2026-02-03' );

-- name: sample.overview
SELECT ( SELECT COUNT(*)
           FROM T_SAMPLE_TASK
       ) AS "taskCount"
     , ( SELECT COUNT(*)
           FROM T_SAMPLE_ADMIN_USER
       ) AS "adminUserCount"
     , ( SELECT COUNT(*)
           FROM T_SAMPLE_FORM_SUBMIT
       ) AS "formSubmissionCount";

-- name: sample.dashboardStatusSummary
SELECT STAT_CD AS "statCd"
     , COUNT(*) AS "count"
     , COALESCE(SUM(AMT), 0) AS "amountSum"
  FROM T_SAMPLE_TASK
 GROUP BY STAT_CD;

-- name: sample.dashboardMonthlyTrend
SELECT TO_CHAR(REG_DT, 'YYYY-MM') AS "monthKey"
     , COUNT(*) AS "count"
     , COALESCE(SUM(AMT), 0) AS "amountSum"
  FROM T_SAMPLE_TASK
 GROUP BY TO_CHAR(REG_DT, 'YYYY-MM')
 ORDER BY "monthKey" ASC;

-- name: sample.dashboardRecent
SELECT TASK_NO AS "taskNo"
     , DATA_NM AS "dataNm"
     , DATA_DESC AS "dataDesc"
     , OWNER_NM AS "ownerNm"
     , STAT_CD AS "statCd"
     , AMT AS "amt"
     , ATTACH_NM AS "attachNm"
     , REG_DT AS "regDt"
  FROM T_SAMPLE_TASK
 ORDER BY REG_DT DESC,
       TASK_NO DESC
 LIMIT 5;

-- name: sample.taskList
SELECT TASK_NO AS "taskNo"
     , DATA_NM AS "dataNm"
     , DATA_DESC AS "dataDesc"
     , OWNER_NM AS "ownerNm"
     , STAT_CD AS "statCd"
     , AMT AS "amt"
     , ATTACH_NM AS "attachNm"
     , REG_DT AS "regDt"
  FROM T_SAMPLE_TASK
 WHERE ( :q = ''
         OR LOWER(DATA_NM) LIKE LOWER(:qLike)
         OR LOWER(COALESCE(DATA_DESC, '')) LIKE LOWER(:qLike)
         OR LOWER(COALESCE(OWNER_NM, '')) LIKE LOWER(:qLike)
       )
   AND ( :status = ''
         OR STAT_CD = :status
       )
   AND REG_DT >= :fromDate
   AND REG_DT < :toDateExclusive
 ORDER BY REG_DT DESC,
       TASK_NO DESC
 LIMIT :limit
OFFSET :offset;

-- name: sample.taskListCount
SELECT COUNT(*) AS "totalCount"
  FROM T_SAMPLE_TASK
 WHERE ( :q = ''
         OR LOWER(DATA_NM) LIKE LOWER(:qLike)
         OR LOWER(COALESCE(DATA_DESC, '')) LIKE LOWER(:qLike)
         OR LOWER(COALESCE(OWNER_NM, '')) LIKE LOWER(:qLike)
       )
   AND ( :status = ''
         OR STAT_CD = :status
       )
   AND REG_DT >= :fromDate
   AND REG_DT < :toDateExclusive;

-- name: sample.taskDetail
SELECT TASK_NO AS "taskNo"
     , DATA_NM AS "dataNm"
     , DATA_DESC AS "dataDesc"
     , OWNER_NM AS "ownerNm"
     , STAT_CD AS "statCd"
     , AMT AS "amt"
     , ATTACH_NM AS "attachNm"
     , REG_DT AS "regDt"
  FROM T_SAMPLE_TASK
 WHERE TASK_NO = :id;

-- name: sample.taskCreate
INSERT INTO T_SAMPLE_TASK (
       DATA_NM,
       DATA_DESC,
       OWNER_NM,
       STAT_CD,
       AMT,
       ATTACH_NM
)
VALUES ( :title,
         :description,
         :owner,
         :status,
         :amount,
         :attachmentName
       );

-- name: sample.taskFindCreatedCandidate
SELECT TASK_NO AS "taskNo"
     , DATA_NM AS "dataNm"
     , DATA_DESC AS "dataDesc"
     , OWNER_NM AS "ownerNm"
     , STAT_CD AS "statCd"
     , AMT AS "amt"
     , ATTACH_NM AS "attachNm"
     , REG_DT AS "regDt"
  FROM T_SAMPLE_TASK
 WHERE DATA_NM = :title
   AND COALESCE(DATA_DESC, '') = COALESCE(:description, '')
   AND COALESCE(OWNER_NM, '') = COALESCE(:owner, '')
   AND STAT_CD = :status
   AND COALESCE(AMT, 0) = COALESCE(:amount, 0)
   AND COALESCE(ATTACH_NM, '') = COALESCE(:attachmentName, '')
 ORDER BY TASK_NO DESC
 LIMIT 1;

-- name: sample.taskUpdate
UPDATE T_SAMPLE_TASK
   SET DATA_NM = :title,
       DATA_DESC = :description,
       OWNER_NM = :owner,
       STAT_CD = :status,
       AMT = :amount,
       ATTACH_NM = :attachmentName
 WHERE TASK_NO = :id;

-- name: sample.taskDelete
DELETE
  FROM T_SAMPLE_TASK
 WHERE TASK_NO = :id;

-- name: sample.formSubmitCreate
INSERT INTO T_SAMPLE_FORM_SUBMIT (
       USER_NM,
       USER_EML,
       PHONE_TXT,
       CATEGORY_CD,
       START_DT,
       END_DT,
       BUDGET_RANGE_TXT,
       REQUIREMENT_TXT,
       FEATURE_JSON,
       REF_URL,
       ATTACH_NM
)
VALUES ( :name,
         :email,
         :phone,
         :category,
         :startDate,
         :endDate,
         :budgetRange,
         :requirement,
         :selectedFeatures,
         :referenceUrl,
         :attachmentName
       );

-- name: sample.formSubmitLatest
SELECT FORM_NO AS "formNo"
     , USER_NM AS "userNm"
     , USER_EML AS "userEml"
     , PHONE_TXT AS "phoneTxt"
     , CATEGORY_CD AS "categoryCd"
     , START_DT AS "startDt"
     , END_DT AS "endDt"
     , BUDGET_RANGE_TXT AS "budgetRangeTxt"
     , REQUIREMENT_TXT AS "requirementTxt"
     , FEATURE_JSON AS "featureJson"
     , REF_URL AS "refUrl"
     , ATTACH_NM AS "attachNm"
     , REG_DT AS "regDt"
  FROM T_SAMPLE_FORM_SUBMIT
 ORDER BY FORM_NO DESC
 LIMIT 1;

-- name: sample.formSubmitCount
SELECT COUNT(*) AS "totalCount"
  FROM T_SAMPLE_FORM_SUBMIT;

-- name: sample.adminUserList
SELECT USER_NO AS "userNo"
     , USER_NM AS "userNm"
     , USER_EML AS "userEml"
     , ROLE_CD AS "roleCd"
     , STAT_CD AS "statCd"
     , NOTIFY_EMAIL AS "notifyEmail"
     , NOTIFY_SMS AS "notifySms"
     , NOTIFY_PUSH AS "notifyPush"
     , PROFILE_IMG_URL AS "profileImgUrl"
     , REG_DT AS "regDt"
  FROM T_SAMPLE_ADMIN_USER
 ORDER BY USER_NO DESC
 LIMIT :limit
OFFSET :offset;

-- name: sample.adminUserListCount
SELECT COUNT(*) AS "totalCount"
  FROM T_SAMPLE_ADMIN_USER;

-- name: sample.adminUserDetail
SELECT USER_NO AS "userNo"
     , USER_NM AS "userNm"
     , USER_EML AS "userEml"
     , ROLE_CD AS "roleCd"
     , STAT_CD AS "statCd"
     , NOTIFY_EMAIL AS "notifyEmail"
     , NOTIFY_SMS AS "notifySms"
     , NOTIFY_PUSH AS "notifyPush"
     , PROFILE_IMG_URL AS "profileImgUrl"
     , REG_DT AS "regDt"
  FROM T_SAMPLE_ADMIN_USER
 WHERE USER_NO = :id;

-- name: sample.adminUserExistsByEmail
SELECT USER_NO AS "userNo"
  FROM T_SAMPLE_ADMIN_USER
 WHERE LOWER(USER_EML) = LOWER(:email)
 LIMIT 1;

-- name: sample.adminUserCreate
INSERT INTO T_SAMPLE_ADMIN_USER (
       USER_NM,
       USER_EML,
       ROLE_CD,
       STAT_CD,
       NOTIFY_EMAIL,
       NOTIFY_SMS,
       NOTIFY_PUSH,
       PROFILE_IMG_URL
)
VALUES ( :name,
         :email,
         :role,
         :status,
         :notifyEmail,
         :notifySms,
         :notifyPush,
         :profileImageUrl
       );

-- name: sample.adminUserFindCreatedCandidate
SELECT USER_NO AS "userNo"
     , USER_NM AS "userNm"
     , USER_EML AS "userEml"
     , ROLE_CD AS "roleCd"
     , STAT_CD AS "statCd"
     , NOTIFY_EMAIL AS "notifyEmail"
     , NOTIFY_SMS AS "notifySms"
     , NOTIFY_PUSH AS "notifyPush"
     , PROFILE_IMG_URL AS "profileImgUrl"
     , REG_DT AS "regDt"
  FROM T_SAMPLE_ADMIN_USER
 WHERE LOWER(USER_EML) = LOWER(:email)
 LIMIT 1;

-- name: sample.adminUserUpdate
UPDATE T_SAMPLE_ADMIN_USER
   SET USER_NM = :name,
       ROLE_CD = :role,
       STAT_CD = :status,
       NOTIFY_EMAIL = :notifyEmail,
       NOTIFY_SMS = :notifySms,
       NOTIFY_PUSH = :notifyPush,
       PROFILE_IMG_URL = :profileImageUrl
 WHERE USER_NO = :id;

-- name: sample.configByKey
SELECT CONFIG_KEY AS "configKey"
     , CONFIG_JSON AS "configJson"
     , REG_DT AS "regDt"
     , UPD_DT AS "updDt"
  FROM T_SAMPLE_CONFIG
 WHERE CONFIG_KEY = :configKey;

-- name: sample.configInsert
INSERT INTO T_SAMPLE_CONFIG (
       CONFIG_KEY,
       CONFIG_JSON
)
VALUES ( :configKey,
         :configJson
       );

-- name: sample.configUpdate
UPDATE T_SAMPLE_CONFIG
   SET CONFIG_JSON = :configJson,
       UPD_DT = CURRENT_TIMESTAMP
 WHERE CONFIG_KEY = :configKey;
