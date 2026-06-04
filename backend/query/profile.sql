-- name: profile.me
SELECT USER_NO AS USER_NO
     , USER_ID AS USER_ID
     , USER_NM AS USER_NM
     , USER_EML AS USER_EML
     , ROLE_CD AS ROLE_CD
  FROM T_USER
 WHERE USER_ID = :userId;

-- name: profile.updateMe
UPDATE T_USER
   SET USER_NM = :userNm
 WHERE USER_ID = :userId;
