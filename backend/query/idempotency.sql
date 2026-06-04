-- name: idempotency.ensureTable
CREATE TABLE IF NOT EXISTS T_REQUEST_IDEMPOTENCY (
       SCOPE_TP TEXT NOT NULL,
       IDEMPOTENCY_KEY TEXT NOT NULL,
       STATUS_CD TEXT NOT NULL,
       PAYLOAD_DIGEST TEXT NOT NULL,
       RESPONSE_JSON TEXT,
       EXPIRES_AT_MS BIGINT NOT NULL,
       REG_DT TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       UPD_DT TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       PRIMARY KEY (SCOPE_TP, IDEMPOTENCY_KEY)
);

-- name: idempotency.deleteExpired
DELETE
  FROM T_REQUEST_IDEMPOTENCY
 WHERE EXPIRES_AT_MS <= :nowMs;

-- name: idempotency.getEntry
SELECT SCOPE_TP AS "scopeTp"
     , IDEMPOTENCY_KEY AS "idempotencyKey"
     , STATUS_CD AS "statusCd"
     , PAYLOAD_DIGEST AS "payloadDigest"
     , RESPONSE_JSON AS "responseJson"
     , EXPIRES_AT_MS AS "expiresAtMs"
     , REG_DT AS "regDt"
     , UPD_DT AS "updDt"
  FROM T_REQUEST_IDEMPOTENCY
 WHERE SCOPE_TP = :scopeType
   AND IDEMPOTENCY_KEY = :idempotencyKey
 LIMIT 1;

-- name: idempotency.insertEntry
INSERT INTO T_REQUEST_IDEMPOTENCY (
       SCOPE_TP,
       IDEMPOTENCY_KEY,
       STATUS_CD,
       PAYLOAD_DIGEST,
       RESPONSE_JSON,
       EXPIRES_AT_MS
)
VALUES ( :scopeType,
         :idempotencyKey,
         :statusCd,
         :payloadDigest,
         :responseJson,
         :expiresAtMs
       );

-- name: idempotency.completeEntry
UPDATE T_REQUEST_IDEMPOTENCY
   SET STATUS_CD = :statusCd
     , RESPONSE_JSON = :responseJson
     , EXPIRES_AT_MS = :expiresAtMs
     , UPD_DT = CURRENT_TIMESTAMP
 WHERE SCOPE_TP = :scopeType
   AND IDEMPOTENCY_KEY = :idempotencyKey;
