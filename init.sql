-- Create the main application database
CREATE DATABASE intacct_db;

-- Create the test database
CREATE DATABASE test_intacct_db;

-- Connect to test database and load test data
\c test_intacct_db;

-- Load the test data
\i /docker-entrypoint-initdb.d/reset_db.sql