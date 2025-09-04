CREATE TABLE books (
    id SERIAL PRIMARY KEY, 
    title VARCHAR(50) NOT NULL, 
    author VARCHAR(50) NOT NULL, 
    genre VARCHAR(50) NOT NULL, 
    published_year INT NOT NULL, 
    status VARCHAR(15) NOT NULL,
    user_id INT REFERENCES users(id),
    UNIQUE (title, author, published_year)
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(50) NOT NULL,
    email VARCHAR(150) UNIQUE,
);

CREATE TABLE reviews( 
    id SERIAL PRIMARY KEY,
    book_id INT REFERENCES books(id),
    user_id INT REFERENCES users(id), 
    rating INT NOT NULL CHECK (RATING BETWEEN 1 and 5),
    comment TEXT,
    review_date TIMESTAMP
);

