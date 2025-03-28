from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
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

    if request.method == "POST":
        now = datetime.now()
        ids = now.strftime("%Y%m%d%H%M%S")
        ime = request.form.get("ime")  
        email = request.form.get("email")
        geslo = request.form.get("geslo")
        
        if uporabniki.get(User.ime == ime):
            return jsonify({"success": False, "error": "Uporabnik ze obstaja!"})

        
        uporabniki.insert({"ime": ime, "email": email, "geslo": geslo, "id":ids})
        response = make_response(jsonify({"success": True, "redirect_url": url_for('profileCreation')}))
        response.set_cookie("user_id", ids, max_age=600)  # Store for 10 minutes
        return response
    return render_template("register.html")

@app.route("/login")
def login():

    return render_template("login.html")


@app.route("/profileCreation", methods=["GET", "POST"])
def profileCreation():
    user_id = request.cookies.get("user_id")  # Read user_id from cookie
    if not user_id: 
        return redirect(url_for("register"))  # Redirect if no ID found
    if request.method == "POST":
        print("✅ Request received!")  # Debugging step 1
        data = request.get_json()  # Ensure correct JSON retrieval

        if not data:
            print("❌ No data received!")  # Debugging step 2
            return jsonify({"success": False, "error": "No data received"}), 400
        print(data)
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        print(name,email,password)



    return render_template("profileCreation.html", user_id=user_id)



if __name__ == "__main__":
    app.run(debug=True,port=8080)