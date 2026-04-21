-- SokoYetu Hyperlocal Delivery Platform - MySQL Database Schema
-- Created: 2024-04-12
-- Database for escrow-protected hyperlocal marketplace with GPS handshake verification

-- ─────────────────────────────────────────────────────────────────────────────
-- CREATE DATABASE
-- ─────────────────────────────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS sokoyetu DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sokoyetu;

-- ─────────────────────────────────────────────────────────────────────────────
-- USERS TABLE - Core user management (CUSTOMER, VENDOR, DRIVER roles)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('CUSTOMER', 'VENDOR', 'DRIVER') DEFAULT 'CUSTOMER' NOT NULL,
    phone VARCHAR(20),
    
    -- Driver specific fields
    student_id VARCHAR(50) UNIQUE,
    profile_photo_url VARCHAR(500),
    university VARCHAR(255),
    course_major VARCHAR(255),
    year_of_study VARCHAR(10),
    is_active_driver BOOLEAN DEFAULT TRUE,
    
    -- Community stats
    deliveries_completed INT DEFAULT 0,
    vendors_supported INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_student_id (student_id),
    INDEX idx_role (role),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- PRODUCTS TABLE - Vendor products/recipes
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    vendor_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'LOCAL_MARKET' or 'RESTAURANT'
    image_url VARCHAR(500),
    stock_qty INT DEFAULT 0,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (vendor_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_vendor_id (vendor_id),
    INDEX idx_category (category),
    INDEX idx_is_available (is_available)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- ORDERS TABLE - Main order management with escrow tracking
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_ref VARCHAR(50) UNIQUE NOT NULL, -- Human-readable e.g. SKY-2024-00001
    customer_id INT NOT NULL,
    vendor_id INT NOT NULL,
    driver_id INT,
    
    total_amount DECIMAL(10, 2) NOT NULL,
    delivery_fee DECIMAL(10, 2) DEFAULT 50.0,
    driver_earnings DECIMAL(10, 2) DEFAULT 40.0, -- Part of delivery fee
    platform_fee DECIMAL(10, 2) DEFAULT 10.0,    -- Platform cut
    
    status ENUM('PENDING_PAYMENT', 'PENDING_VENDOR_APPROVAL', 'ACCEPTED_BY_VENDOR', 
                'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED_BY_USER', 
                'DISPUTE', 'FAILED') DEFAULT 'PENDING_PAYMENT' NOT NULL,
    transaction_id VARCHAR(255),
    
    -- Delivery address
    delivery_address TEXT,
    delivery_lat DECIMAL(10, 8),
    delivery_lng DECIMAL(10, 8),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP NULL,
    delivered_at TIMESTAMP NULL,
    
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (vendor_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_order_ref (order_ref),
    INDEX idx_customer_id (customer_id),
    INDEX idx_vendor_id (vendor_id),
    INDEX idx_driver_id (driver_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- ORDER_ITEMS TABLE - Items within an order
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE order_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT DEFAULT 1 NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- LEDGERS TABLE - Escrow ledger for payment holding
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE ledgers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT UNIQUE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status ENUM('HOLDING', 'RELEASED', 'REFUNDED') DEFAULT 'HOLDING' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    released_at TIMESTAMP NULL,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- HANDSHAKE_KEYS TABLE - Double-blind GPS verification system
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE handshake_keys (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT UNIQUE NOT NULL,
    part_a_vendor VARCHAR(255) NOT NULL, -- Sent to vendor on order placed
    part_b_customer VARCHAR(255) NOT NULL, -- Encoded in QR code for customer
    mated BOOLEAN DEFAULT FALSE,
    mated_at TIMESTAMP NULL,
    mated_lat DECIMAL(10, 8),
    mated_lng DECIMAL(10, 8),
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id),
    INDEX idx_mated (mated)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- DELIVERY_VERIFICATIONS TABLE - GPS location verification during delivery
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE delivery_verifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    driver_photo_url VARCHAR(500) NOT NULL,
    gps_lat DECIMAL(10, 8) NOT NULL,
    gps_lng DECIMAL(10, 8) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_no_show BOOLEAN DEFAULT FALSE,
    notes TEXT,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- DRIVER_LOCATIONS TABLE - Real-time driver GPS tracking
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE driver_locations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    driver_id INT UNIQUE NOT NULL,
    lat DECIMAL(10, 8) NOT NULL,
    lng DECIMAL(10, 8) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (driver_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_driver_id (driver_id),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- PAYMENTS TABLE - M-Pesa payment processing
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE payments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    user_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status ENUM('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED') DEFAULT 'PENDING' NOT NULL,
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    mpesa_receipt VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id),
    INDEX idx_user_id (user_id),
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- DISPUTES TABLE - Handle disputes and conflicts
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE disputes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    raised_by_id INT NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('PENDING', 'VERIFIED', 'FAILED', 'DISPUTED') DEFAULT 'PENDING' NOT NULL,
    evidence_url VARCHAR(500),
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (raised_by_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id),
    INDEX idx_raised_by_id (raised_by_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- NOTIFICATIONS TABLE - Multi-channel notifications (email, SMS, WhatsApp)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    order_id INT,
    notification_type VARCHAR(50) NOT NULL, -- 'email', 'sms', 'whatsapp'
    message TEXT NOT NULL,
    sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_order_id (order_id),
    INDEX idx_notification_type (notification_type),
    INDEX idx_sent (sent)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────────────────────
-- SAMPLE DATA FOR TESTING
-- ─────────────────────────────────────────────────────────────────────────────

-- Sample Users
INSERT INTO users (email, name, hashed_password, role, phone, student_id, is_active_driver, deliveries_completed) VALUES
('customer1@test.com', 'John Customer', '$2b$12$KIX0bW9H2Y2F5KqZZ9z8MuV.WEnfINJkNb8z3X9YqMF5jA7h3vIFu', 'CUSTOMER', '+254700000001', NULL, NULL, 0),
('vendor1@test.com', 'Sarah Vendor', '$2b$12$KIX0bW9H2Y2F5KqZZ9z8MuV.WEnfINJkNb8z3X9YqMF5jA7h3vIFu', 'VENDOR', '+254700000002', 'STU001', NULL, 0),
('driver1@test.com', 'Mike Driver', '$2b$12$KIX0bW9H2Y2F5KqZZ9z8MuV.WEnfINJkNb8z3X9YqMF5jA7h3vIFu', 'DRIVER', '+254700000003', 'STU002', TRUE, 15),
('customer2@test.com', 'Jane Smith', '$2b$12$KIX0bW9H2Y2F5KqZZ9z8MuV.WEnfINJkNb8z3X9YqMF5jA7h3vIFu', 'CUSTOMER', '+254700000004', NULL, NULL, 0),
('vendor2@test.com', 'Tom Restaurant', '$2b$12$KIX0bW9H2Y2F5KqZZ9z8MuV.WEnfINJkNb8z3X9YqMF5jA7h3vIFu', 'VENDOR', '+254700000005', 'STU003', NULL, 0),
('driver2@test.com', 'James Delivery', '$2b$12$KIX0bW9H2Y2F5KqZZ9z8MuV.WEnfINJkNb8z3X9YqMF5jA7h3vIFu', 'DRIVER', '+254700000006', 'STU004', TRUE, 23);

-- Sample Products
INSERT INTO products (vendor_id, name, description, price, category, stock_qty, is_available) VALUES
(2, 'Chicken Chapati', 'Crispy chapati with grilled chicken', 150.00, 'LOCAL_MARKET', 50, TRUE),
(2, 'Githeri', 'Corn and beans mix', 80.00, 'LOCAL_MARKET', 40, TRUE),
(2, 'Mandazi', 'Sweet fried dough', 30.00, 'LOCAL_MARKET', 100, TRUE),
(5, 'Nyama Choma', 'Grilled meat with ugali', 250.00, 'RESTAURANT', 25, TRUE),
(5, 'Samosa (6 pieces)', 'Vegetable samosas', 50.00, 'RESTAURANT', 60, TRUE),
(5, 'Biryani', 'Fragrant rice with meat', 200.00, 'RESTAURANT', 15, TRUE);

-- Sample Orders
INSERT INTO orders (order_ref, customer_id, vendor_id, driver_id, total_amount, delivery_fee, driver_earnings, platform_fee, status, created_at) VALUES
('SKY-2024-00001', 1, 2, 3, 280.00, 50.00, 40.00, 10.00, 'DELIVERED', '2024-04-10 10:30:00'),
('SKY-2024-00002', 4, 5, 3, 350.00, 50.00, 40.00, 10.00, 'OUT_FOR_DELIVERY', '2024-04-12 09:15:00'),
('SKY-2024-00003', 1, 5, NULL, 150.00, 50.00, 40.00, 10.00, 'PENDING_PAYMENT', '2024-04-12 14:22:00');

-- Sample Order Items
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 2, 150.00), -- 2x Chicken Chapati
(1, 2, 1, 80.00),  -- 1x Githeri
(2, 4, 1, 250.00), -- 1x Nyama Choma
(2, 5, 2, 50.00),  -- 2x Samosa
(3, 6, 1, 200.00); -- 1x Biryani

-- Sample Ledgers (Escrow)
INSERT INTO ledgers (order_id, amount, status, created_at) VALUES
(1, 280.00, 'RELEASED', '2024-04-10 10:30:00'),
(2, 350.00, 'HOLDING', '2024-04-12 09:15:00'),
(3, 150.00, 'HOLDING', '2024-04-12 14:22:00');

-- Sample Handshake Keys
INSERT INTO handshake_keys (order_id, part_a_vendor, part_b_customer, mated, mated_at, mated_lat, mated_lng) VALUES
(1, 'VENDOR_KEY_ABC123', 'CUSTOMER_QR_XYZ789', TRUE, '2024-04-10 11:15:00', -1.2921, 36.8219),
(2, 'VENDOR_KEY_DEF456', 'CUSTOMER_QR_UVW456', FALSE, NULL, NULL, NULL),
(3, 'VENDOR_KEY_GHI789', 'CUSTOMER_QR_RST123', FALSE, NULL, NULL, NULL);

-- Sample Driver Locations
INSERT INTO driver_locations (driver_id, lat, lng, updated_at) VALUES
(3, -1.2850, 36.8300, CURRENT_TIMESTAMP),
(6, -1.2950, 36.8150, CURRENT_TIMESTAMP);

-- Sample Payments
INSERT INTO payments (order_id, user_id, amount, status, transaction_id, phone_number, mpesa_receipt, completed_at) VALUES
(1, 1, 280.00, 'COMPLETED', 'TXN-2024-001', '+254700000001', 'MPG001', '2024-04-10 10:35:00'),
(2, 4, 350.00, 'COMPLETED', 'TXN-2024-002', '+254700000004', 'MPG002', '2024-04-12 09:20:00'),
(3, 1, 150.00, 'PENDING', 'TXN-2024-003', '+254700000001', NULL, NULL);

-- Sample Notifications
INSERT INTO notifications (user_id, order_id, notification_type, message, sent, sent_at) VALUES
(1, 1, 'sms', 'Your order SKY-2024-00001 has been delivered!', TRUE, '2024-04-10 11:45:00'),
(2, 1, 'sms', 'New order SKY-2024-00001 from John Customer', TRUE, '2024-04-10 10:31:00'),
(3, 1, 'sms', 'Order SKY-2024-00001 is ready for pickup', TRUE, '2024-04-10 11:00:00'),
(4, 2, 'sms', 'Your order SKY-2024-00002 is on the way!', TRUE, '2024-04-12 09:30:00'),
(5, 2, 'sms', 'New order SKY-2024-00002 from Jane Smith', TRUE, '2024-04-12 09:16:00'),
(3, 2, 'sms', 'Pickup order SKY-2024-00002 - Tom Restaurant', TRUE, '2024-04-12 09:25:00');

-- ─────────────────────────────────────────────────────────────────────────────
-- VERIFICATION
-- ─────────────────────────────────────────────────────────────────────────────

SHOW TABLES;
SELECT COUNT(*) as total_users FROM users;
SELECT COUNT(*) as total_orders FROM orders;
SELECT COUNT(*) as total_products FROM products;

-- ─────────────────────────────────────────────────────────────────────────────
-- NOTE: Password hash above is for "password123"
-- Use this for testing logins
-- ─────────────────────────────────────────────────────────────────────────────
