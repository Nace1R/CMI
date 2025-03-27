from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from tinydb import TinyDB, Query
from datetime import datetime

db = TinyDB('database/database.json')
uporabniki = db.table('uporabniki')
admin = db.table('admin')
profil = db.table('profile-info')

User = Query() 

app = Flask(__name__)
#Disabled caching
app.config['CACHE_TYPE'] = 'null'


@app.route("/")
def index():
    text = "test"
    return render_template("index.html", text=text)

@app.route("/register", methods=["GET", "POST"])
def register():
    now = datetime.now()
    ids = now.strftime("%Y%m%d%H%M%S")
    if request.method == "POST":
        ime = request.form.get("ime")  
        email = request.form.get("email")
        geslo = request.form.get("geslo")
        
        if uporabniki.get(User.ime == ime):
            return jsonify({"success": False, "error": "Uporabnik ze obstaja!"})

        
        uporabniki.insert({"ime": ime, "email": email, "geslo": geslo, "id":ids})
        return jsonify({"success": True})
    return render_template("register.html")

@app.route("/login")
def login():

    return render_template("login.html")

@app.route("/profileCreation")
def profileCreation():

    return render_template("profileCreation.html")


if __name__ == "__main__":
    app.run(debug=True,port=8080)