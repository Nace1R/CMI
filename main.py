from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
from tinydb import TinyDB, Query
from datetime import datetime
import os

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
        response.set_cookie("userId", ids, max_age=600)
        return response
    return render_template("register.html")

@app.route("/login")
def login():

    return render_template("login.html")


@app.route("/profileCreation", methods=["GET", "POST"])
def profileCreation():
    userId = request.cookies.get("userId")
    if not userId: 
        return redirect(url_for("register"))
    

    if request.method == "POST":
        if 'picture' in request.files:
            file = request.files['picture']
            if file.filename != '':
                file_extension = os.path.splitext(file.filename)[1]
                filename = f"pfp_{userId}{file_extension}"
                file_path = os.path.join('static', 'pfp', filename)
                file.save(file_path)
                print(userId)
                return {'message': 'File uploaded successfully', 'path': file_path}, 200
            else:
                return {'error': 'No selected file'}, 400
            

    return render_template("profileCreation.html")



if __name__ == "__main__":
    app.run(debug=True,port=8080)