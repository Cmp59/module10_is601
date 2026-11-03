DELETE FROM calculations
WHERE id = 2;

SELECT * FROM calculations;

-- Optional bonus: ON DELETE CASCADE demo (deleting bob also removes his calculations)
-- DELETE FROM users WHERE id = 2;
-- SELECT * FROM users;
-- SELECT * FROM calculations;
