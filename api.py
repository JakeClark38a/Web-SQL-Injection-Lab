from flask import Flask, render_template, abort, make_response, session, request, redirect, render_template_string
from database import Database, sha3_256_to_base64
import secrets
from datetime import timedelta
import hashlib
import uuid
import os

app = Flask(__name__)
# Configure the template folder
app.template_folder = 'templates'

# Configure the static folder
app.static_folder = 'static'
app.secret_key = secrets.token_hex(16)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

db = Database()
# Create predefine account "JakeClark" and "tu_1_den_8"
db.create_table()
# Init username and password
db.insert_user("JakeClark", "tu_1_den_8")
# with open("admin_passwd.txt", "r") as f:
#     db.insert_user("administrator", f.read())
# Init code
db.add_code("LOGINGIFT", "10/10/2023", "10/10/2024", "160")
# 3 secret code that will be release later
db.add_code("XZH3UOFOUQUR", "08/11/2023", "09/11/2023", "100")
db.add_code("LLSTCJ8T7C1R", "08/11/2023", "09/11/2023", "100")
db.add_code("W23K4N8I5VYS", "08/11/2023", "09/11/2023", "100")
del db

@app.get("/")
@app.get("/index.html")
def index() -> str:
    # Get UUID and username session
    uuid = session.get("uuid", None)
    username = session.get("username", None)
    # If uuid or username is empty, means that session is cleared
    if uuid is None or username is None: 
        return render_template('index.html', login=False)
    else:
        # Get gems and cards from database
        db = Database()
        gems, cards = db.get_gems_and_card(uuid, username)
        # If no gems or cards found, means that first "if" statement is broken
        if gems==None or cards==None:
            abort(404)
        # Else fill index.html with username, gems and cards
        else:
            res = make_response(render_template("index.html", username=username, gems=gems, card=cards))
            res.set_cookie("uuid", uuid)
            return res

@app.route("/login.html", methods=["GET", "POST"])
def login():
    
     # If request method is GET, render login.html with no error line
    if request.method == "GET":
        return render_template("login.html", status=None)
    else: # Else: Pick username and password from POST request
        username = request.form.get("username")
        password = request.form.get("password")
        # Login
        db = Database()
        result = db.login(username, password)
        # If username and password didn't exist in database, reload login.html with red line
        if result is None:
            return render_template("login.html", status=False)
        # Else set session uuid and username to remember you in 10 minutes session
        else:
            session["username"] = username
            session["uuid"] = result[0]
            return redirect("/")
        
@app.route("/redemption.html", methods=["GET", "POST"])
def redemption():
    # Pick uuid and username
    uuid = session.get("uuid", None)
    username = session.get("username", None)
    # If request method is GET, return page with login status and username
    if request.method == "GET":
        if uuid is None or username is None:
            return render_template("redemption.html", login=False)
        else:
            return render_template("redemption.html", login=True, username=username)
    # Else check code existence and render result
    else:
        code = request.form.get("code")
        db = Database()
        res = db.check_code(code, uuid, username)
        return render_template_string('''
                                      <head>
                                        <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
                                      </head>
                                      <body class="body">
                                        {res}<br><a href="/redemption.html">Back</a>
                                      </body>'''.replace("{res}", res))

@app.route("/exchange.html", methods=["GET", "POST"])
def exchange():
    # Pick uuid and username
    uuid = session.get("uuid", None)
    username = session.get("username", None)
    db = Database()
    # If request method is GET, return page with login status and username
    if request.method == "GET":
        if uuid is None or username is None:
            return render_template("exchange.html", login=False)
        else:
            # Get gems and cards from database
            gems, cards = db.get_gems_and_card(uuid, username)
            # If no gems or cards found, means that first "if" statement is broken
            if gems==None or cards==None:
                abort(404)
            # Else fill index.html with username, gems and cards
            else:
                return render_template("exchange.html", login=True, username=username, gems=gems, card=cards, max_val=(gems//160)*160)
    else:
        card_ex = request.form.get("value")
        res = db.exchange_card(uuid, username, card_ex)
        return "Exchange Successfully" if res else "Failed. Try again"


@app.get("/signout")
def signout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1337, debug=True)