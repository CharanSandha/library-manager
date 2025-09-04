import get_info
from tabulate import tabulate



def get_genre_year(title, author):
        genre, year = get_info.determine_genre_and_year(title, author)
        return genre, year


def insert_book(title, author, status, genre, year, cur, conn, user_id=1,):
    cur.execute("""
        INSERT INTO books (title, author, genre, published_year, status, user_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (title, author, genre, year, status, user_id))
    conn.commit()
    print(f"Added '{title}' by {author} with status '{status}'.")


def update_book_status(new_status, title, author, cur, conn, user_id = 1):
     cur.execute(
    "UPDATE books SET status = %s WHERE user_id = %s AND title = %s AND author = %s",
    (new_status, user_id, title, author)
    )
     print(f"Updated the status for '{title}' by {author}")
     conn.commit()

def view_books(cur, user_id = 1):
    cur.execute(
    "SELECT * FROM books WHERE user_id = %s" , (user_id,)
    )
    rows = cur.fetchall()
    headers = [desc[0] for desc in cur.description]  # get column names
    print(tabulate(rows, headers=headers, tablefmt="grid"))

def view_reviews(cur, user_id = 1, title = '', author = ''):
    if title != '':
        cur.execute("SELECT reviews.rating, reviews.comment, reviews.review_date FROM reviews JOIN books ON reviews.book_id = books.id WHERE reviews.user_id = %s AND books.title = %s AND books.author = %s", (user_id, title, author))
    else:
        cur.execute(
        "SELECT books.title, books.author, rating, comment, review_date FROM reviews JOIN books ON books.id = reviews.book_id WHERE reviews.user_id = %s" , (user_id,)
        )
    rows = cur.fetchall()
    headers = [desc[0] for desc in cur.description]  # get column names
    print(tabulate(rows, headers=headers, tablefmt="grid"))

def enter_review(cur, conn, title, author, rating, comment, user_id = 1):
    cur.execute("SELECT id FROM books WHERE title = %s AND author = %s", (title, author))
    result = cur.fetchone()  # fetch one row
    if result is not None:
     book_id = result[0]  # first column of the row
    else:
        book_id = None
        print("Book not found.")
    
    cur.execute(
          "INSERT INTO reviews (book_id, user_id, rating, comment, review_date)" 
          "VALUES (%s, %s, %s, %s, NOW())", (book_id, user_id, rating, comment)
     )
    print("Your review was added.\n")
    conn.commit()

     