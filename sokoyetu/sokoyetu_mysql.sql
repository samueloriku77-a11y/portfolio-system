-- SokoYetu Database Schema for MySQL
-- Created for XAMPP MySQL Integration
-- Run this file in phpMyAdmin or MySQL CLI

-- Create Database
CREATE DATABASE IF NOT EXISTS sokoyetu DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sokoyetu;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'CUSTOMER',
  phone VARCHAR(20),
  
  -- Driver specific
  student_id VARCHAR(100) UNIQUE,
  profile_photo_url VARCHAR(255),
  university VARCHAR(255),
  course_major VARCHAR(255),
  year_of_study VARCHAR(10),
  is_active_driver BOOLEAN DEFAULT TRUE,
  
  -- Community stats
  deliveries_completed INT DEFAULT 0,
  vendors_supported INT DEFAULT 0,
  
  -- Vendor specific
  business_name VARCHAR(255),
  location_address TEXT,
  location_lat FLOAT,
  location_lng FLOAT,
  is_verified_vendor BOOLEAN DEFAULT FALSE,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_email (email),
  INDEX idx_student_id (student_id),
  INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Products Table
CREATE TABLE IF NOT EXISTS products (
  id INT PRIMARY KEY AUTO_INCREMENT,
  vendor_id INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  price FLOAT NOT NULL,
  category VARCHAR(50),
  image_url VARCHAR(255),
  stock_qty INT DEFAULT 0,
  is_available BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (vendor_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_name (name),
  INDEX idx_vendor (vendor_id),
  INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Product Images Table
CREATE TABLE IF NOT EXISTS product_images (
  id INT PRIMARY KEY AUTO_INCREMENT,
  product_id INT NOT NULL,
  order_id INT,
  image_url VARCHAR(255) NOT NULL,
  side_name VARCHAR(50),
  uploaded_by_id INT NOT NULL,
  is_verified BOOLEAN DEFAULT FALSE,
  admin_notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
  FOREIGN KEY (uploaded_by_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_product (product_id),
  INDEX idx_order (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Orders Table
CREATE TABLE IF NOT EXISTS orders (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_ref VARCHAR(100) UNIQUE NOT NULL,
  customer_id INT NOT NULL,
  vendor_id INT NOT NULL,
  driver_id INT,
  
  total_amount FLOAT NOT NULL,
  delivery_fee FLOAT DEFAULT 50.0,
  driver_earnings FLOAT DEFAULT 40.0,
  platform_fee FLOAT DEFAULT 10.0,
  
  status VARCHAR(50) DEFAULT 'PENDING_VENDOR_APPROVAL',
  transaction_id VARCHAR(255),
  
  admin_id INT,
  admin_approved_at TIMESTAMP NULL,
  admin_notes TEXT,
  
  delivery_address TEXT,
  delivery_lat FLOAT,
  delivery_lng FLOAT,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  accepted_at TIMESTAMP NULL,
  delivered_at TIMESTAMP NULL,
  
  FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (vendor_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (driver_id) REFERENCES users(id) ON DELETE SET NULL,
  FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL,
  
  INDEX idx_order_ref (order_ref),
  INDEX idx_customer (customer_id),
  INDEX idx_vendor (vendor_id),
  INDEX idx_driver (driver_id),
  INDEX idx_status (status),
  INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT DEFAULT 1,
  unit_price FLOAT NOT NULL,
  
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  
  INDEX idx_order (order_id),
  INDEX idx_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ledgers Table (Escrow System)
CREATE TABLE IF NOT EXISTS ledgers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT UNIQUE NOT NULL,
  amount FLOAT NOT NULL,
  status VARCHAR(50) DEFAULT 'HOLDING',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  released_at TIMESTAMP NULL,
  
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Handshake Keys Table (QR Code System)
CREATE TABLE IF NOT EXISTS handshake_keys (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT UNIQUE NOT NULL,
  part_a_vendor VARCHAR(255),
  part_b_customer VARCHAR(255),
  mated BOOLEAN DEFAULT FALSE,
  mated_at TIMESTAMP NULL,
  mated_lat FLOAT,
  mated_lng FLOAT,
  
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Delivery Verifications Table
CREATE TABLE IF NOT EXISTS delivery_verifications (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  driver_photo_url VARCHAR(255) NOT NULL,
  gps_lat FLOAT NOT NULL,
  gps_lng FLOAT NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_no_show BOOLEAN DEFAULT FALSE,
  notes TEXT,
  
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  INDEX idx_order (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Driver Locations Table
CREATE TABLE IF NOT EXISTS driver_locations (
  id INT PRIMARY KEY AUTO_INCREMENT,
  driver_id INT UNIQUE NOT NULL,
  lat FLOAT NOT NULL,
  lng FLOAT NOT NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  FOREIGN KEY (driver_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_driver (driver_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Payments Table
CREATE TABLE IF NOT EXISTS payments (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT,
  user_id INT NOT NULL,
  amount FLOAT NOT NULL,
  status VARCHAR(50) DEFAULT 'PENDING',
  transaction_id VARCHAR(255) UNIQUE NOT NULL,
  phone_number VARCHAR(20),
  mpesa_receipt VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP NULL,
  
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  
  INDEX idx_transaction (transaction_id),
  INDEX idx_user (user_id),
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Wallets Table
CREATE TABLE IF NOT EXISTS wallets (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT UNIQUE NOT NULL,
  balance FLOAT NOT NULL DEFAULT 0.0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Wallet Transactions Table
CREATE TABLE IF NOT EXISTS wallet_transactions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  amount FLOAT NOT NULL,
  transaction_type VARCHAR(50) DEFAULT 'DEPOSIT',
  status VARCHAR(50) DEFAULT 'PENDING',
  phone_number VARCHAR(20),
  reference VARCHAR(100) UNIQUE NOT NULL,
  transaction_metadata LONGTEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user (user_id),
  INDEX idx_reference (reference),
  INDEX idx_status (status),
  INDEX idx_type (transaction_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Disputes Table
CREATE TABLE IF NOT EXISTS disputes (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  raised_by_id INT NOT NULL,
  reason TEXT NOT NULL,
  status VARCHAR(50) DEFAULT 'PENDING',
  evidence_url VARCHAR(255),
  resolution_notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  resolved_at TIMESTAMP NULL,
  
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (raised_by_id) REFERENCES users(id) ON DELETE CASCADE,
  
  INDEX idx_order (order_id),
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  order_id INT,
  notification_type VARCHAR(50),
  message TEXT,
  sent BOOLEAN DEFAULT FALSE,
  sent_at TIMESTAMP NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
  
  INDEX idx_user (user_id),
  INDEX idx_sent (sent)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert Test Users
INSERT INTO users (email, name, hashed_password, role, phone, student_id, university, course_major, year_of_study, business_name, location_address, location_lat, location_lng, is_verified_vendor)
VALUES
  ('customer1@test.com', 'John Customer', '$2b$12$aAeiOtXUSThkAdViQ.T3xO8Bqkpa94o6QUDjAyhhFt7lKtk2jOie2', 'CUSTOMER', '+254700000001', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE),
  ('vendor1@test.com', 'Sarah Vendor', '$2b$12$aAeiOtXUSThkAdViQ.T3xO8Bqkpa94o6QUDjAyhhFt7lKtk2jOie2', 'VENDOR', '+254700000002', NULL, 'University of Nairobi', NULL, NULL, 'Sarah\'s Cafe', '-1.2864,36.8172', -1.2864, 36.8172, TRUE),
  ('driver1@test.com', 'Mike Driver', '$2b$12$aAeiOtXUSThkAdViQ.T3xO8Bqkpa94o6QUDjAyhhFt7lKtk2jOie2', 'DRIVER', '+254700000003', 'STU001', 'Kenyatta University', 'Computer Science', '3rd', NULL, NULL, NULL, NULL, FALSE),
  ('admin@test.com', 'Admin Manager', '$2b$12$aAeiOtXUSThkAdViQ.T3xO8Bqkpa94o6QUDjAyhhFt7lKtk2jOie2', 'ADMIN', '+254700000099', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE),
  ('customer2@test.com', 'Jane Customer', '$2b$12$aAeiOtXUSThkAdViQ.T3xO8Bqkpa94o6QUDjAyhhFt7lKtk2jOie2', 'CUSTOMER', '+254700000004', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE),
  ('vendor2@test.com', 'Peter Restaurant', '$2b$12$aAeiOtXUSThkAdViQ.T3xO8Bqkpa94o6QUDjAyhhFt7lKtk2jOie2', 'VENDOR', '+254700000005', NULL, 'Strathmore University', NULL, NULL, 'Peter\'s Restaurant', '-1.3163,36.8172', -1.3163, 36.8172, TRUE),
  ('driver2@test.com', 'Alex Driver', '$2b$12$aAeiOtXUSThkAdViQ.T3xO8Bqkpa94o6QUDjAyhhFt7lKtk2jOie2', 'DRIVER', '+254700000006', 'STU002', 'JKUAT', 'Business', '2nd', NULL, NULL, NULL, NULL, FALSE);

-- Create wallets for test users
INSERT INTO wallets (user_id, balance) VALUES
  ((SELECT id FROM users WHERE email = 'customer1@test.com'), 5000.0),
  ((SELECT id FROM users WHERE email = 'vendor1@test.com'), 0.0),
  ((SELECT id FROM users WHERE email = 'driver1@test.com'), 0.0),
  ((SELECT id FROM users WHERE email = 'admin@test.com'), 0.0),
  ((SELECT id FROM users WHERE email = 'customer2@test.com'), 2000.0),
  ((SELECT id FROM users WHERE email = 'vendor2@test.com'), 0.0),
  ((SELECT id FROM users WHERE email = 'driver2@test.com'), 1500.0);

-- Verify installation
SELECT COUNT(*) as total_users FROM users;
SELECT COUNT(*) as total_tables FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'sokoyetu';
