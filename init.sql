-- init.sql

-- Create database
CREATE DATABASE IF NOT EXISTS btcdb;

-- Use the database
USE btcdb;

-- Create table for storing addresses
CREATE TABLE IF NOT EXISTS public_addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    address VARCHAR(255) NOT NULL,
    private_key VARCHAR(255) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create application user
CREATE USER IF NOT EXISTS 'btcuser'@'%' IDENTIFIED BY 'btcpass';

-- Give privileges to the user
GRANT ALL PRIVILEGES ON btcdb.* TO 'btcuser'@'%';

-- Apply changes
FLUSH PRIVILEGES;
