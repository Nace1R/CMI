from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
from tinydb import TinyDB, Query, where
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

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ime = request.form.get("ime")
        geslo = request.form.get("geslo")
        user = uporabniki.get(User.ime == ime)
        if user:
            # Check if password matches
            if user["geslo"] == geslo:
                userId = user["id"]
                response = make_response(jsonify({"success": True, "redirect_url": url_for('dashboard')}))
                response.set_cookie("userId", userId, max_age=60*60*24)  # 1 day cookie
                return response
            else:
                return "Wrong password"
        else:
            return "User not found"
    return render_template("login.html")


@app.route("/profileCreation", methods=["GET", "POST"])
def profileCreation():
    userId = request.cookies.get("userId")
    if not userId: 
        return redirect(url_for("register"))
    

    if request.method == "POST":
        # shranjevanje slike
        if 'picture' in request.files:
            file = request.files['picture']
            if file.filename != '':
                file_extension = os.path.splitext(file.filename)[1]
                filename = f"pfp_{userId}{file_extension}"
                file_path = os.path.join('static', 'pfp', filename)
                file.save(file_path)
                print(userId)

                pot = f"static/pfp/pfp_{userId}{file_extension}"
                profil.insert({"userId": userId, "pfp": pot})
        elif request.is_json:
            data = request.json
            if 'city' in data:
                profil.update({"city": data['city']}, Query().userId == userId)
            elif 'phoneNumber' in data:
                profil.update({"number": data['phoneNumber']}, Query().userId == userId)
                #city = request.form.get("city")
                #number = request.form.get("phoneNumber")
                return {'message': 'profile succewsfuly created'}, 200
            
    return render_template("profileCreation.html")

@app.route("/dashboard")
def dashboard():
    userId = request.cookies.get("userId", None)
    userData = {"ime": "Guest"}
    pfp_path = url_for('static', filename='slike/default-avatar.png')

    if not userId:
        return redirect(url_for("login"))

    user = uporabniki.get(where('id') == userId)
    if not user:
        return redirect(url_for("login"))

    userData = user

    profile = profil.get(where('userId') == userId)
    if profile:
        pfp_path = '/' + profile.get('pfp', 'slike/default-avatar.png')


    print("User Data:", userData)
    print("PFP:", pfp_path)
    return render_template("dashboard.html", userData=userData,pfp_path=pfp_path)


@app.route("/manageProfile")
def manageProfile():

    return render_template("manage_profile.html")

@app.route("/logout")
def logout():
    response = make_response(redirect(url_for('login')))
    response.set_cookie('userId', '', expires=0)
    return response

@app.route("/about_us")
def about_us():    
    userId = request.cookies.get("userId")
    if userId:
        user = uporabniki.get(User.id == userId)
        if user:
            userData = user
    else:
        return redirect(url_for("login"))
    


    pfp_path = url_for('static', filename='slike/default-avatar.png')
    profile = profil.get(where('userId') == userId)
    if profile:
        pfp_path = '/' + profile.get('pfp', 'slike/default-avatar.png')

    return render_template("about_us.html", userData=userData, pfp_path=pfp_path)


def pfp():
    pass
#dava to v funkcijo za dobivanje slike pfp


if __name__ == "__main__":
    app.run(debug=True,port=8080)