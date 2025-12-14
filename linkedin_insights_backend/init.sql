-- Initialize LinkedIn Insights Database

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS linkedin_insights;
USE linkedin_insights;

-- Pages table
CREATE TABLE IF NOT EXISTS pages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    page_id VARCHAR(255) UNIQUE NOT NULL,
    linkedin_id VARCHAR(255) UNIQUE,
    name VARCHAR(500) NOT NULL,
    url VARCHAR(1000),
    profile_picture_url VARCHAR(1000),
    profile_picture_s3_url VARCHAR(1000),
    description TEXT,
    tagline VARCHAR(500),
    website VARCHAR(500),
    industry VARCHAR(255),
    company_size VARCHAR(100),
    headquarters VARCHAR(500),
    founded_year INT,
    company_type VARCHAR(100),
    follower_count INT DEFAULT 0,
    employee_count INT DEFAULT 0,
    specialties JSON,
    locations JSON,
    extra_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    last_scraped_at TIMESTAMP NULL,
    INDEX idx_page_id (page_id),
    INDEX idx_industry (industry),
    INDEX idx_follower_count (follower_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Posts table
CREATE TABLE IF NOT EXISTS posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id VARCHAR(255) UNIQUE NOT NULL,
    page_id INT NOT NULL,
    text TEXT,
    content_type VARCHAR(50),
    media_url VARCHAR(1000),
    media_s3_url VARCHAR(1000),
    media_type VARCHAR(50),
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    share_count INT DEFAULT 0,
    view_count INT DEFAULT 0,
    posted_at TIMESTAMP NULL,
    author_name VARCHAR(255),
    author_title VARCHAR(500),
    hashtags JSON,
    mentions JSON,
    extra_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE,
    INDEX idx_post_id (post_id),
    INDEX idx_page_id (page_id),
    INDEX idx_posted_at (posted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Comments table
CREATE TABLE IF NOT EXISTS comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    comment_id VARCHAR(255) UNIQUE NOT NULL,
    post_id INT NOT NULL,
    text TEXT,
    author_id VARCHAR(255),
    author_name VARCHAR(255),
    author_title VARCHAR(500),
    author_profile_url VARCHAR(1000),
    author_profile_picture VARCHAR(1000),
    like_count INT DEFAULT 0,
    reply_count INT DEFAULT 0,
    parent_comment_id INT NULL,
    commented_at TIMESTAMP NULL,
    extra_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_comment_id) REFERENCES comments(id) ON DELETE SET NULL,
    INDEX idx_comment_id (comment_id),
    INDEX idx_post_id (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Employees table
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    linkedin_id VARCHAR(255) UNIQUE NOT NULL,
    page_id INT NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    full_name VARCHAR(500),
    headline VARCHAR(500),
    profile_url VARCHAR(1000),
    profile_picture_url VARCHAR(1000),
    profile_picture_s3_url VARCHAR(1000),
    current_title VARCHAR(500),
    current_company VARCHAR(500),
    location VARCHAR(500),
    country VARCHAR(100),
    industry VARCHAR(255),
    connections_count INT,
    is_following BOOLEAN DEFAULT FALSE,
    is_follower BOOLEAN DEFAULT FALSE,
    is_employee BOOLEAN DEFAULT TRUE,
    experience_summary JSON,
    education_summary JSON,
    skills JSON,
    extra_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE,
    INDEX idx_linkedin_id (linkedin_id),
    INDEX idx_page_id (page_id),
    INDEX idx_full_name (full_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add some helpful views
CREATE OR REPLACE VIEW page_stats AS
SELECT 
    p.id,
    p.page_id,
    p.name,
    p.follower_count,
    COUNT(DISTINCT posts.id) as total_posts,
    COALESCE(AVG(posts.like_count), 0) as avg_likes,
    COALESCE(AVG(posts.comment_count), 0) as avg_comments,
    COUNT(DISTINCT e.id) as total_employees
FROM pages p
LEFT JOIN posts ON posts.page_id = p.id
LEFT JOIN employees e ON e.page_id = p.id
GROUP BY p.id;
