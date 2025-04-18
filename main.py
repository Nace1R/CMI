from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
from tinydb import TinyDB, Query, where
from datetime import datetime
import os
import requests


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


def getPfp(userId):
    pfp_path = url_for('static', filename='slike/default-avatar.png')
    profile = profil.get(where('userId') == userId)
    if profile:
        pfp_path = '/' + profile.get('pfp', 'slike/default-avatar.png')
    return pfp_path
#dava to v funkcijo za dobivanje slike pfp


@app.route("/manageProfile")
def manageProfile():
    userId = request.cookies.get("userId")
    if not userId:
        return redirect(url_for("login"))

    result = profil.get(User.userId == userId)
    print(userId)
    mesto = result['city']
    number = result['number']
    result1 = uporabniki.get(User.id == userId)
    username = result1['ime']
    email = result1['email']
    password = result1['geslo']
    pfp = getPfp(userId)
    
    
    return render_template("manage_profile.html",number=number,mesto=mesto,username=username,email=email,password=password,pfp=pfp)







#-----------------------------------------------------------------------------------
# ostali siti

@app.route("/cityGuides")
def cityGudies():
    userId = request.cookies.get("userId")
    if not userId:
        return redirect(url_for("login"))
    if request.method == "POST":
            pass
    
    return render_template("city_guides.html")

@app.route("/publicPolls")
def publicPolls():
    userId = request.cookies.get("userId")
    if not userId:
        return redirect(url_for("login"))
    if request.method == "POST":
            pass
    
    return render_template("PublicPolls.html")

@app.route("/weatherData")
def weatherData():
    apiKey = "8d80c9afce8da5a191e74cb02596e828"
    
    userId = request.cookies.get("userId")
    if not userId:
        return redirect(url_for("login"))
    result = profil.get(User.userId == userId)
    mesto = result['city']
    print(mesto)
    apiCall = f"https://api.openweathermap.org/data/2.5/weather?q={mesto}&appid={apiKey}&units=metric"
    response = requests.get(apiCall)
    data = response.json()

    #TRENUTNO VREME
    print(data["main"]["temp"]) # temperatura curr
    print(data["weather"][0]["main"]) # stanje vremena curr
    print(data["main"]["feels_like"]) # feels like curr
    print(data["main"]["humidity"]) #humidity curr
    print(data["wind"]["speed"]) #vetr hitrost
    print(data["sys"]["sunrise"]) # sunrise
    print(data["sys"]["sunset"]) # sunset

    temp = data["main"]["temp"]
    status =data["weather"][0]["main"]
    feels = data["main"]["feels_like"]
    humid = data["main"]["humidity"]
    wind = data["wind"]["speed"]
    sunrise = datetime.fromtimestamp(data["sys"]["sunrise"]).strftime('%H:%M:%S')
    sunset = datetime.fromtimestamp(data["sys"]["sunset"]).strftime('%H:%M:%S')


    # FORECAST


    return render_template("weatherData.html", temp=temp, status=status, feels=feels, humid=humid, wind=wind, sunrise=sunrise, sunset=sunset)

@app.route("/trafficData")
def trafficData():
    userId = request.cookies.get("userId")
    if not userId:
        return redirect(url_for("login"))
    if request.method == "POST":
            pass
    
    return render_template("TrafficData.html")

@app.route("/localEvents")
def localEvents():
    userId = request.cookies.get("userId")
    if not userId:
        return redirect(url_for("login"))
    if request.method == "POST":
            pass
    
    return render_template("localEvents.html")

@app.route("/electricalInfo")
def eleInfo():
    userId = request.cookies.get("userId")
    if not userId:
        return redirect(url_for("login"))
    if request.method == "POST":
            pass
    
    return render_template("Electrical_Info.html")

@app.route("/publicTransit")
def publicTrans():
    userId = request.cookies.get("userId")
    if not userId:
        return redirect(url_for("login"))
    if request.method == "POST":
            pass
    
    return render_template("Public_Transit_Data.html")

@app.route("/perksRewards")
def perksRewards():
    userId = request.cookies.get("userId")
    if not userId:
        return redirect(url_for("login"))
    if request.method == "POST":
            pass
    
    return render_template("PerksAndRewards.html")

# konec ostlaih sitou
#----------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True,port=8080)