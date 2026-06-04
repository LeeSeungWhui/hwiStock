-- name: auth.userByUsername
SELECT USER_NO AS "userNo"
     , USER_ID AS "userId"
     , USER_PW AS "userPw"
     , USER_NM AS "userNm"
     , USER_EML AS "userEml"
     , ROLE_CD AS "roleCd"
  FROM T_USER
 WHERE USER_ID = :u;

-- name: auth.insertUser
INSERT INTO T_USER
     ( USER_ID
     , USER_PW
     , USER_NM
     , USER_EML
     , ROLE_CD
     )
VALUES ( :userId
       , :userPw
       , :userNm
       , :userEml
       , :roleCd
       );

-- name: auth.updateUserSeed
UPDATE T_USER
   SET USER_PW = :userPw
     , USER_NM = :userNm
     , USER_EML = :userEml
     , ROLE_CD = :roleCd
 WHERE USER_ID = :userId;

-- name: auth.deleteExpiredTokenState
DELETE FROM T_TOKEN
 WHERE EXPIRES_AT_MS <= :nowMs;

-- name: auth.ensureTokenStateTable
CREATE TABLE IF NOT EXISTS T_TOKEN (
    STATE_TP VARCHAR(32) NOT NULL
  , TOKEN_JTI VARCHAR(191) NOT NULL
  , EXPIRES_AT_MS BIGINT NOT NULL
  , TOKEN_PAYLOAD_JSON TEXT
  , PRIMARY KEY (STATE_TP, TOKEN_JTI)
);

-- name: auth.getTokenState
SELECT STATE_TP AS "stateTp"
     , TOKEN_JTI AS "tokenJti"
     , EXPIRES_AT_MS AS "expiresAtMs"
     , TOKEN_PAYLOAD_JSON AS "tokenPayloadJson"
  FROM T_TOKEN
 WHERE STATE_TP = :stateType
   AND TOKEN_JTI = :tokenJti
 LIMIT 1;

-- name: auth.updateTokenState
UPDATE T_TOKEN
   SET EXPIRES_AT_MS = :expiresAtMs
     , TOKEN_PAYLOAD_JSON = :tokenPayloadJson
 WHERE STATE_TP = :stateType
   AND TOKEN_JTI = :tokenJti;

-- name: auth.insertTokenState
INSERT INTO T_TOKEN
     ( STATE_TP
     , TOKEN_JTI
     , EXPIRES_AT_MS
     , TOKEN_PAYLOAD_JSON
     )
VALUES ( :stateType
       , :tokenJti
       , :expiresAtMs
       , :tokenPayloadJson
       );

-- name: auth.deleteTokenState
DELETE FROM T_TOKEN
 WHERE STATE_TP = :stateType
   AND TOKEN_JTI = :tokenJti;
