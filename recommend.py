#what i need to do - create embeddings for all read books of user from users_books descriptions, then 
#create embeddings for all books in books table that the user hasn't read
#then compare the embeddings of the unread books to read books and find the one that matches it the mist
#add frontend feature that asks user if they would like a recommended book and then renders that on the webpage,
#the title and author of the description matching the read book descriptions the most

from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer('all-MiniLM-L6-v2')
books = []

with open("books.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

# First line = header, skip it
for line in lines[1:]:
    parts = [p.strip() for p in line.strip().split("|")]
    if len(parts) < 4:
        continue  # skip bad rows

    book_id, title, author, genre, desc = parts
    full_desc = f"{desc} Genre: {genre}. Author: {author}."

    books.append({
        "id": int(book_id),
        "title": title,
        "desc": full_desc
    })
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="books")

for book in books:
    embedding = model.encode(book["desc"]).tolist()
    collection.add(documents=[book["desc"]], ids=[str(book["id"])], embeddings=[embedding])

user_query = "science fiction"
query_embedding = model.encode(user_query).tolist()
results = collection.query(query_embeddings=[query_embedding], n_results=1)
print(results)