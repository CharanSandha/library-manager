import numpy as np
import psycopg2
from sentence_transformers import SentenceTransformer

# Initialize model and DB connection globally for reuse
model = SentenceTransformer('all-MiniLM-L6-v2')

conn = psycopg2.connect(
    dbname="personal_library_manager",
    user="postgres",
    password="Supremo77!",
    host="localhost"
)

def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


def recommend_book(current_id, exclusions):
    cur = conn.cursor()

    # Fetch read books info for the user
    cur.execute("""
        SELECT b.id, b.title, b.author, b.genre, b.published_year
        FROM users_books ub
        JOIN books b ON ub.book_id = b.id
        WHERE ub.user_id = %s AND ub.status = 'finished'
    """, (current_id,))
    read_rows = cur.fetchall()

    # Add all excluded books to read_rows to exclude them from recommendations
    if exclusions:
        # Fetch details for all excluded books
        placeholders = ','.join(['%s'] * len(exclusions))
        sql = f"""SELECT b.id, b.title, b.author, b.genre, b.published_year
                  FROM books b WHERE b.id IN ({placeholders})"""
        cur.execute(sql, exclusions)
        excluded_books = cur.fetchall()
        read_rows.extend(excluded_books)

    if not read_rows:
        return None  # No read books, can't recommend

    # Prepare descriptions and embeddings for read books
    read_books = []
    for row in read_rows:
        desc = f" Genre: {row[3]}. Author: {row[2]}. Published in {row[4]}."
        read_books.append({"id": row[0], "desc": desc})

    read_embeddings = [model.encode(book['desc']) for book in read_books]
    avg_embedding = np.mean(read_embeddings, axis=0)

    # Fetch unread books excluding all read and excluded books
    exclusion_ids = [book['id'] for book in read_books]  # all books to exclude
    if exclusion_ids:
        placeholders = ','.join(['%s'] * len(exclusion_ids))
        sql = f"""
            SELECT b.id, b.title, b.author, b.genre, b.published_year
            FROM books b
            WHERE b.id NOT IN ({placeholders})
        """
        cur.execute(sql, exclusion_ids)
    else:
        cur.execute("""
            SELECT b.id, b.title, b.author, b.genre, b.published_year
            FROM books b
        """)

    unread_rows = cur.fetchall()
    if not unread_rows:
        return None

    best_score = -1
    best_book = None

    for row in unread_rows:
        full_desc = f" Genre: {row[3]}. Author: {row[2]}. Published in {row[4]}."
        embedding = model.encode(full_desc)
        score = cosine_similarity(avg_embedding, embedding)

        if score > best_score:
            best_score = score
            best_book = {
                "id": row[0],
                "title": row[1],
                "author": row[2]
            }
    return best_book
