USE news_db;

CREATE TABLE articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(100),
    author VARCHAR(100),
    title VARCHAR(255),
    description TEXT,
    url VARCHAR(500) UNIQUE,
    urlToImage VARCHAR(500),
    publishedAt DATETIME,
    content LONGTEXT
);