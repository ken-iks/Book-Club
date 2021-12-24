import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, apology

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///bookclub.db")
""" all of the sql tables that I made for storing data """
#db.execute("CREATE TABLE user (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, hash TEXT NOT NULL)")
#db.execute("CREATE TABLE posts (post_id, name TEXT NOT NULL, content TEXT NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(post_id) REFERENCES users(id))")
#db.execute("ALTER TABLE user RENAME TO users")
#db.execute("ALTER TABLE posts ADD rating")
#db.execute("CREATE TABLE follows (my_id INTEGER, their_id INTEGER, followed_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
#db.execute("ALTER TABLE posts ADD author TEXT")

if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/", methods=["GET","POST"])
@login_required
def profile():
    """ Open user profile """
    if request.method == "GET":
        # loading posts and username into the profile page
        posts = db.execute("SELECT * FROM posts WHERE post_id = ? ORDER BY created_at DESC", session["user_id"])
        username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        return render_template("profile.html", posts=posts, possible_ratings=[i for i in range(1,11)], username=username, no_posts=len(posts), followers=len(db.execute("SELECT * FROM follows WHERE their_id = ?", session["user_id"])), following=len(db.execute("SELECT * FROM follows WHERE my_id = ?", session["user_id"])))
    else:
        name = request.form.get("name")
        author = request.form.get("author")
        post = request.form.get("review")
        rating = request.form.get("rating")
        # checking user input
        if not name:
            return apology("Must input name of book")
        elif not author:
            return apology("Must input name of author")
        elif not post:
            return apology("Must review book")
        elif not rating:
            return apology("Must rate book")
        else:
            db.execute("INSERT INTO posts (post_id, name, content, rating, author) VALUES (?, ?, ?, ?, ?)", session["user_id"], name, post, rating, author)
            return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        name = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        # check for user input
        if not name:
            return apology("must provide username")
        elif not password:
            return apology("must provide password")
        elif not confirmation:
            return apology("must confirm password")

        # check confirmation matches original password
        elif password != confirmation:
            return apology("password and confirmation do not match")

        # Password must contain at least 1 upper case, lower case and number
        elif not any([i.isupper() for i in list(password)]) or not any([i.islower() for i in list(password)]) or not any([i.isdigit() for i in list(password)]):
            return apology("password must contain at least 1 of the following: Upper case, Lower case, Number")
        # Must store a hash version of the password
        hashpassword = generate_password_hash(password)
        # check if password already exists
        duplicates = db.execute("SELECT * FROM users WHERE username = ?", name)
        if duplicates:
            return apology("username already taken")
        user_id = db.execute("INSERT INTO users (username,hash) VALUES (?, ?)", name, hashpassword)
        session["user_id"] = user_id
        return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure submissions
        if not request.form.get("username"):
            return apology("must provide username")
        elif not request.form.get("password"):
            return apology("must provide password")
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password")
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # Redirect user to their profile
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Search for a user profile"""
    if request.method == "GET":
        return render_template("search.html")
    else:
        name = request.form.get("symbol")
        # querying the sql table for the username and checking if it exists
        id = db.execute("SELECT id FROM users WHERE username = ?", name)
        if not id:
            return apology("No user with this username exists")
        else:
            # querying database for information about the user
            id_number = id[0]["id"]
            posts = db.execute("SELECT * FROM posts WHERE post_id = ? ORDER BY created_at DESC", id_number)
            # check if current user follows the account that they are searching for 
            follow = db.execute("SELECT * FROM follows WHERE my_id = ? AND their_id = ?", session["user_id"], id_number)
            if not follow:
                return render_template("searchedfollow.html", posts=posts, possible_ratings=[i for i in range(1,11)], username=name, no_posts=len(posts), followers=len(db.execute("SELECT * FROM follows WHERE their_id = ?", id_number)), following=len(db.execute("SELECT * FROM follows WHERE my_id = ?", id_number)), id_number=id_number)
            else:
                return render_template("searchedunfollow.html", posts=posts, possible_ratings=[i for i in range(1,11)], username=name, no_posts=len(posts), followers=len(db.execute("SELECT * FROM follows WHERE their_id = ?", id_number)), following=len(db.execute("SELECT * FROM follows WHERE my_id = ?", id_number)), id_number=id_number)

@app.route("/editprofile", methods=["GET", "POST"])
@login_required
def change():
    """ Edit user profile """
    if request.method == "GET":
        return render_template("editprofile.html")
    else:
        # check user input
        changing = request.form.get("change")
        if not changing:
            return apology("Must select an option")
        elif changing == "Delete Post":
            return render_template("delete.html", books=db.execute("SELECT * FROM posts WHERE post_id = ?", session["user_id"]))
        elif changing == "Change Password":
            return render_template("changep.html")
        else:
            return render_template("changeu.html")

@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    """ Delete a post """
    name = request.form.get("name")
    if not name:
        return apology("Must select a post")
    else:
        db.execute("DELETE FROM posts WHERE name = ? AND post_id = ?", name, session["user_id"])
        return redirect("/")

@app.route("/changep", methods=["GET", "POST"])
def changepassword():
    """Register user"""
    if request.method == "GET":
        return render_template("changep.html")
    else:
        old_password = request.form.get("passwordo")
        password = request.form.get("passwordn")
        confirmation = request.form.get("confirmation_passwordn")
        rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        # check for user input
        if not old_password:
            return apology("must provide old password")
        elif not password:
            return apology("must provide new password")
        elif not confirmation:
            return apology("must confirm new password")

        # check confirmation matches original password and old password matches current password
        elif password != confirmation:
            return apology("password and confirmation do not match")
        elif not check_password_hash(rows[0]["hash"], old_password):
            return apology("password entered is incorrect")

        # Password must contain at least 1 upper case, lower case and number
        elif not any([i.isupper() for i in list(password)]) or not any([i.islower() for i in list(password)]) or not any([i.isdigit() for i in list(password)]):
            return apology("password must contain at least 1 of the following: Upper case, Lower case, Number")
        # must store hash version of password in database
        hashpassword = generate_password_hash(password)

        db.execute("UPDATE users SET hash = ? WHERE id = ?", hashpassword, session["user_id"])
        return redirect("/")

@app.route("/changeu", methods=["GET", "POST"])
def changeusername():
    """Change password"""
    if request.method == "GET":
        return render_template("changeu.html")
    else:
        old_username = request.form.get("usernameo")
        username = request.form.get("usernamen")
        confirmation = request.form.get("confirmation_usernamen")
        # check for user input
        if not old_username:
            return apology("must provide old username")
        elif not username:
            return apology("must provide new username")
        elif not confirmation:
            return apology("must confirm new username")

        # check confirmation matches original username 
        elif username != confirmation:
            return apology("username and confirmation do not match")
        # check that username does not already exist
        duplicates = db.execute("SELECT * FROM users WHERE username = ?", username)
        if duplicates:
            return apology("username already taken")
        db.execute("UPDATE users SET username = ? WHERE id = ?", username, session["user_id"])
        return redirect("/")

@app.route("/searchedfollow", methods=["GET", "POST"])
@login_required
def follow():
    """ Follow user """
    if request.method == "POST":
        id_number = request.form.get("their_id")
        db.execute("INSERT INTO follows (my_id, their_id) VALUES (?, ?)", session["user_id"], id_number)
        return redirect("/")

@app.route("/searchedunfollow", methods=["GET", "POST"])
@login_required
def unfollow():
    """ Unfollow user """
    if request.method == "POST":
        id_number = request.form.get("their_id")
        db.execute("DELETE FROM follows WHERE my_id = ? AND their_id = ?", session["user_id"], id_number)
        return redirect("/")

@app.route("/following", methods=["GET", "POST"])
def following():
    """View accounts user follows"""
    if request.method == "GET":
        ids = [i["their_id"] for i in db.execute("SELECT their_id FROM follows WHERE my_id = ?", session["user_id"])]
        following = db.execute("SELECT * FROM users WHERE id IN (?)", ids)
        return render_template("following.html", following=following)

@app.route("/followers", methods=["GET", "POST"])
def followers():
    """View accounts that follow user"""
    if request.method == "GET":
        ids = [i["my_id"] for i in db.execute("SELECT my_id FROM follows WHERE their_id = ?", session["user_id"])]
        followers = db.execute("SELECT * FROM users WHERE id IN (?)", ids)
        return render_template("followers.html", followers=followers)

@app.route("/timeline", methods=["GET", "POST"])
def timeline():
    """ View timeline """
    if request.method == "GET":
        ids = [i["their_id"] for i in db.execute("SELECT their_id FROM follows WHERE my_id = ?", session["user_id"])]
        posts = db.execute("SELECT * FROM posts WHERE post_id IN (?) ORDER BY created_at DESC", ids)
        for post in posts:
            name = db.execute("SELECT username FROM users WHERE id = ?", post["post_id"])[0]["username"]
            post["username"] = name
        return render_template("timeline.html", posts=posts)