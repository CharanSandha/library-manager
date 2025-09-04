import books
import getpass
import psycopg2

password = getpass.getpass("Enter your PostgreSQL password: ")
conn = psycopg2.connect(dbname = "personal_library_manager", user = "postgres", password = password)
cur = conn.cursor()

while True:
    display_message = ("Hi library user! Select an option from the list (1-4)\n"
    "1. Add a book to my list\n"
    "2. Update the status of a book in my list\n"
    "3. View my book information\n"
    "4. Enter a book review\n"
    "5. View my past reviews\n"
    "6. Exit\n")

    input_selection = int(input(display_message))
    if (input_selection == 1):
        title = input("Enter the title of the book you're adding: ")
        author = input("Enter the author's name: ")
        status = input("Enter the status 'Want to read', 'Reading', or 'Read': ")
        status = status.strip().title()
        genre, year = books.get_genre_year(title, author)
        books.insert_book(title, author, status, genre, year, cur, conn)
    elif (input_selection == 2):
        title = input("Title of book you'd like to update: ")
        author = input("Author of book you'd like to update: ")
        status = input("Enter the new status 'Want to read', 'Reading', or 'Read': ")
        new_status = status.strip().title()
        books.update_book_status(new_status, title, author, cur, conn)
    elif(input_selection == 3):
        books.view_books(cur)
    elif (input_selection == 4):
        title = input("What is the title of the book you want to review: ")
        author = input("Who is the author of the book you want to review: ")
        rating = int(input("Rate the book 1-5: "))
        comment = input("Leave a comment about the book: ")

        books.enter_review(cur, conn, title, author, rating, comment)
    elif (input_selection == 5):
       title = input("Enter the title of the book review you want to view (press enter if you wanna view all): ")
       if title != '':
           author = input("What is the author's name: ")
       else:
           author = ''
       books.view_reviews(cur, 1, title, author) 


    elif(input_selection == 6):
        print("Okay, see you later! :)")
        cur.close()
        conn.close()
        break
    



