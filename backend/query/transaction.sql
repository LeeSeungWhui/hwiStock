-- name: transaction.pingTestTable
SELECT 1
  FROM T_TEST_TRANSACTION
 LIMIT 1;

-- name: transaction.insertValue
INSERT INTO T_TEST_TRANSACTION
     (VALUE)
VALUES (:val);
