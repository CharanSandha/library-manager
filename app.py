from flask import Flask, render_template, url_for, redirect, request, flash
import psycopg2
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from recommendation_engine import recommend_book

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
app.config['SECRET_KEY'] = 'thisisasecretkey'

bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError("That username already exists. Please choose a different one")

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('books_home'))
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/')
def home():
    return render_template('home2.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# PostgreSQL connection
conn = psycopg2.connect(
    dbname="personal_library_manager",
    user="postgres",
    password="Supremo77!",
    host="localhost"
)

@app.route('/home')
@login_required
def books_home():
    status_filter = request.args.get('status', 'all')  # default to 'all'
    cur = conn.cursor()

    if status_filter == 'all':
        cur.execute("""
            SELECT b.id, b.title, b.author, ub.status, ub.current_page, ub.total_pages, reviews.rating
FROM users_books ub
JOIN books b ON ub.book_id = b.id
JOIN users u ON ub.user_id = u.id
LEFT JOIN reviews ON reviews.book_id = ub.book_id AND reviews.user_id = u.id
WHERE u.id = %s
        """, (current_user.id,))
    else:
        cur.execute("""
            SELECT b.id, b.title, b.author, ub.status, ub.current_page, ub.total_pages, reviews.rating
            FROM users_books ub
            JOIN books b ON ub.book_id = b.id
            JOIN users u ON ub.user_id = u.id
            LEFT JOIN reviews ON reviews.book_id = ub.book_id AND reviews.user_id = u.id
            WHERE ub.user_id = %s AND ub.status = %s
        """, (current_user.id, status_filter))

    books = cur.fetchall()
    cur.execute("""
        SELECT book_id FROM fav_and_wish WHERE user_id = %s AND type = 'fav'
    """, (current_user.id,))
    favorite_book_ids = {row[0] for row in cur.fetchall()}
    conn.commit()
    cur.close()
    return render_template("home.html", books=books, current_filter=status_filter, favorite_book_ids=favorite_book_ids)

@app.route("/wishlist")
def my_wishes():
    cur = conn.cursor()
    cur.execute("""
        SELECT b.title, b.author, b.genre, b.published_year 
        FROM books b 
        JOIN fav_and_wish ON b.id = fav_and_wish.book_id 
        JOIN users ON users.id = fav_and_wish.user_id
        WHERE fav_and_wish.type = 'wish' AND users.username = %s
    """, (current_user.username,))
    books = cur.fetchall()
    cur.close()
    return render_template("wishlist.html", books=books)

@app.route("/fav")
def my_favs():
    cur = conn.cursor()
    cur.execute("""
        SELECT b.title, b.author, b.genre, b.published_year 
        FROM books b 
        JOIN fav_and_wish ON b.id = fav_and_wish.book_id 
        JOIN users ON users.id = fav_and_wish.user_id
        WHERE fav_and_wish.type = 'fav' AND users.username = %s
        """, (current_user.username,))
    books = cur.fetchall()
    cur.close()
    return render_template("fav.html", books=books)

@app.route('/add_to_favs/<int:book_id>', methods=['POST'])
@login_required
def add_to_favs(book_id):
   cur = conn.cursor()
   cur.execute("""
                SELECT * FROM fav_and_wish
                WHERE user_id = %s AND book_id = %s AND type = 'fav'
            """, (current_user.id, book_id))
   result = cur.fetchone()

   if result:
                # If already a favorite, remove it (toggle off)
                cur.execute("""
                    DELETE FROM fav_and_wish
                    WHERE user_id = %s AND book_id = %s AND type = 'fav'
                """, (current_user.id, book_id))
   else:
                # If not, add to favorites (toggle on)
                cur.execute("""
                    INSERT INTO fav_and_wish (book_id, user_id, type, added_at)
                    VALUES (%s, %s, 'fav', NOW())
                """, (book_id, current_user.id))
   cur.close()
   return redirect(url_for('books_home'))  # or whatever page you're returning to



    
@app.route('/update_status/<int:book_id>', methods=['POST'])
@login_required
def update_status(book_id):
    form_status = request.form.get('status')
    new_status = ""
    if form_status == 'Want To Read':
        new_status = "to-read"
    elif form_status == "Currently Reading":
        new_status = "reading"
    else:
        new_status = "finished"
    
    with psycopg2.connect(
        dbname="personal_library_manager",
        user="postgres",
        password="Supremo77!",
        host="localhost"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users_books
                SET status = %s
                WHERE user_id = %s AND book_id = %s
            """, (new_status, current_user.id, book_id))
            # Commit happens automatically on exiting 'with' block if no exceptions

    flash("Book status updated!", "success")
    cur.close()
    return redirect(url_for('books_home'))

@app.route('/update_progress/<int:book_id>', methods=["POST"])
@login_required
def update_progress(book_id):
    new_progress = request.form.get("new_progress")

    try:
        new_progress = int(new_progress)
    except (TypeError, ValueError):
        flash("Please enter a valid number.")
        return redirect(url_for('books_home'))

    # Get total pages
    cur = conn.cursor()
    cur.execute("""
        SELECT total_pages
        FROM users_books
        WHERE book_id = %s AND user_id = %s
    """, (book_id, current_user.id))
    result = cur.fetchone()

    if not result:
        flash("Book not found.")
        return redirect(url_for('books_home'))

    total_pages = result[0]

    if new_progress < 0 or new_progress > total_pages:
        flash(f"Progress must be between 0 and {total_pages}.")
        return redirect(url_for('books_home'))

    # Decide new status based on progress
    if new_progress == 0:
        new_status = "to-read"
    elif new_progress == total_pages:
        new_status = "finished"
    else:
        new_status = "reading"

    # Update both current_page and status
    cur.execute("""
        UPDATE users_books
        SET current_page = %s, status = %s
        WHERE book_id = %s AND user_id = %s
    """, (new_progress, new_status, book_id, current_user.id))
    conn.commit()
    cur.close()
    flash("Progress and status updated successfully.")
    return redirect(url_for('books_home'))


    
@app.route('/rate-book/<int:book_id>', methods=['POST'])
@login_required
def rate_book(book_id):
    rating = request.form.get('rating', type=int)
    if rating is None or not (1 <= rating <= 5):
        flash("Invalid rating", "danger")
        return redirect(url_for('books_home'))

    cur = conn.cursor()

    # Save or update rating
    cur.execute("""
        INSERT INTO reviews (user_id, book_id, rating)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, book_id)
        DO UPDATE SET rating = EXCLUDED.rating;
    """, (current_user.id, book_id, rating))

    conn.commit()
    cur.close()

    flash("Rating updated", "success")
    return redirect(url_for('books_home'))


@app.route('/add_recommend_book/<int:book_id>', methods=['POST'])
@login_required
def add_recommend_book(book_id):
    # Assuming conn is your active psycopg2 connection
    cur = conn.cursor()

    # Set default values
    user_id = current_user.id
    status = 'to-read'
    current_page = 0
    total_pages = 300  # You might want to pull this from the book info later

    try:
        cur.execute("""
            INSERT INTO users_books (user_id, book_id, status, added_at, current_page, total_pages)
            VALUES (%s, %s, %s, NOW(), %s, %s)
        """, (user_id, book_id, status, current_page, total_pages))

        conn.commit()
        flash("Book added to your library!", "success")
    except Exception as e:
        conn.rollback()
        flash("Failed to add book: " + str(e), "danger")
    finally:
        cur.close()

    return redirect(url_for('recommend'))

@app.route('/recommend_another/<int:book_id>', methods=["POST"])
@login_required
def recommend_another(book_id):

    return redirect(url_for('recommend', exclusions = book_id))


@app.route("/add", methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        # Handle form submission
        title = request.form.get('title')
        author = request.form.get('author')
        form_status = request.form.get('status')
        status_map = {
    'want to read': 'to-read',
    'currently reading': 'reading',
    'read': 'finished'
        }

        form_status = request.form.get('status', '').strip().lower()
        new_status = status_map.get(form_status)

        if not new_status:
            flash("Invalid status value!", "error")
            return redirect(url_for('add_book'))
        cur.close()
        # Check if any of the fields are empty
        if not title or not author or not form_status:
            return render_template("add_book.html", message="All fields are required!")

        # Proceed with DB operation if everything is valid
        with psycopg2.connect(
            dbname="personal_library_manager",
            user="postgres",
            password="Supremo77!",
            host="localhost"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM books WHERE title = %s", (title,))
                result = cur.fetchall()

                if not result:
                    # Insert book if it doesn't exist
                    cur.execute("""
                        INSERT INTO books (title, author, genre, published_year)
                        VALUES (%s, %s, %s, %s)
                    """, (title, author, 'Fiction', 2025))

                # Ensure you query for the book_id inside the same cursor context
                cur.execute("""SELECT id FROM books WHERE title = %s""", (title,))
                book_id = cur.fetchone()[0]  # Use .fetchone() to get the single result

                # Insert into users_books table
                cur.execute("""INSERT INTO users_books (user_id, book_id, status, added_at, current_page, total_pages)
                            VALUES (%s, %s, %s, NOW(), %s, %s)
                        """, (current_user.id, book_id, new_status, 0, 200))
        flash("Book added successfully!", "success")
        cur.close()
        return redirect(url_for('books_home'))
    
    # This part handles the GET request, which renders the form
    return render_template("add_book.html")

def delete_book_from_db(user_id, book_id):
    with psycopg2.connect(
        dbname="personal_library_manager",
        user="postgres",
        password="Supremo77!",
        host="localhost"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM users_books 
                WHERE user_id = %s AND book_id = %s
            """, (user_id, book_id))
            cur.execute("""SELECT * FROM fav_and_wish WHERE fav_and_wish.user_id = %s AND fav_and_wish.book_id = %s""", 
                        (user_id, book_id))
            result = cur.fetchone()
            if result:
                 cur.execute("""
                DELETE FROM fav_and_wish 
                WHERE user_id = %s AND book_id = %s
            """, (user_id, book_id))
    cur.close()
        
            
            
                        


@app.route("/delete_book/<int:book_id>", methods=['POST'])
@login_required
def delete_book(book_id):
    delete_book_from_db(current_user.id, book_id)
    return redirect(url_for('books_home'))

@app.route("/process_selection", methods=['POST'])
def process_selection():
    selected_ids = request.form.getlist('selected_books')  # Get selected book IDs

    # Perform the delete action for all selected books
    for book_id in selected_ids:
        delete_book_from_db(current_user.id, book_id)
    return redirect(url_for('books_home'))

from flask import session


@app.route("/recommend")
@login_required
def recommend():
    # Initialize exclusion list in session if missing
    if 'excluded_books' not in session:
        session['excluded_books'] = []

    exclusions = session['excluded_books']  # list of book IDs to exclude

    # Pass exclusions list to your recommend_book function
    book = recommend_book(current_user.id, exclusions)

    if not book:
        flash("No recommendations available right now.")
        session.pop('excluded_books', None)  # Clear exclusions if no books left
        return redirect(url_for("books_home"))

    # Add this recommended book ID to exclusion list so it's not recommended again
    session['excluded_books'].append(book['id'])
    session.modified = True  # Mark session as changed to save it

    return render_template("recommendation.html", book=book)


if __name__ == "__main__":
    app.run(debug=True)
