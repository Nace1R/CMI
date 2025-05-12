from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
from tinydb import TinyDB, Query, where
from datetime import datetime, timedelta
import os
import requests

# tinyDB začetk
db = TinyDB('database/database.json')
uporabniki = db.table('uporabniki')

profil = db.table('profile-info')


polls = db.table('polls') # ime, rezultat, creditGet
admins = db.table('admins') # userId, država 
rewards = db.table('rewards')


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
                fileExtension = os.path.splitext(file.filename)[1]
                filename = f"pfp_{userId}{fileExtension}"
                file_path = os.path.join('static', 'pfp', filename)
                file.save(file_path)
                print(userId)

                pot = f"static/pfp/pfp_{userId}{fileExtension}"
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
    
    #prikaz mesta na dashboardu
    result = profil.get(User.userId == userId)
    mesto = result['city']
    userData = user

    profile = profil.get(where('userId') == userId)
    if profile:
        pfp_path = '/' + profile.get('pfp', 'slike/default-avatar.png')


    print("User Data:", userData)
    print("PFP:", pfp_path)

    #isAdmin = admins.contains(User.userId == userId)
    isAdmin = bool(admins.contains(User.userId == userId))
    print(isAdmin)
    return render_template("dashboard.html", userData=userData,pfp_path=pfp_path,mesto=mesto, userId = userId, isAdmin=isAdmin)

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


    isAdmin = admins.contains(User.userId == userId)
    return render_template("about_us.html", userData=userData, pfp_path=pfp_path, isAdmin=isAdmin)


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
    isAdmin = admins.contains(User.userId == userId)
    return render_template("city_guides.html", isAdmin=isAdmin)

@app.route("/publicPolls")
def publicPolls():
    userId = request.cookies.get("userId")
    if not userId:
        return redirect(url_for("login"))
    if request.method == "POST":
            pass
    isAdmin = admins.contains(User.userId == userId)
    return render_template("PublicPolls.html", isAdmin=isAdmin)

@app.route("/weatherData")
def weatherData():
    apiKey = "8d80c9afce8da5a191e74cb02596e828"
    
    userId = request.cookies.get("userId")
    userData = {"ime": "gost"}
    user = uporabniki.get(where('id') == userId)
    if not userId:
        return redirect(url_for("login"))
    userData = user
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

    #profilna slika
    pfp = getPfp(userId)


    isAdmin = admins.contains(User.userId == userId)
    return render_template("weatherData.html", temp=temp, status=status, feels=feels, humid=humid, wind=wind, sunrise=sunrise, sunset=sunset,userData=userData,pfp=pfp, isAdmin=isAdmin)



@app.route("/weatherFor",methods=["GET" , "POST"])
def weatherFor():
    #default za page
    apiKey = "8d80c9afce8da5a191e74cb02596e828"
    userId = request.cookies.get("userId")
    userData = {"ime": "gost"}
    user = uporabniki.get(where('id') == userId)
    if not userId:
        return redirect(url_for("login"))
    userData = user
    result = profil.get(User.userId == userId)
    mesto = result['city']
    print(mesto)
    pfp = getPfp(userId)
    
    #forecast


    apiCall = f"https://api.openweathermap.org/data/2.5/forecast?q={mesto}&appid={apiKey}&units=metric"
    response = requests.get(apiCall)
    dataF = response.json()


    today = datetime.today().date()
    tommorow = today + timedelta(days=1)
    dayAfterTom = today + timedelta(days=2)


    def getDate(index):
        dt = datetime.strptime(dataF["list"][index-1]["dt_txt"], "%Y-%m-%d %H:%M:%S") #ai
        date_only = dt.date()
        return date_only

    def getUra(index):
        dt = datetime.strptime(dataF["list"][index-1]["dt_txt"], "%Y-%m-%d %H:%M:%S")
        time_only = dt.time()
        return time_only
    
    index = 0

    forToday = {}
    forTommorow = {}
    forDayAftrTom = {}

    for vremeU in dataF["list"]:
        index += 1
        dan = getDate(index)
        if today == dan:
            print("---------------------------DANES----------------------------")
            
            vremeFor = {
                "čas" : dataF["list"][index]["dt_txt"],
                "temp" : dataF["list"][index]["main"]["temp"],
                "status": dataF["list"][index]["weather"][0]["main"],
                "wind": dataF["list"][index]["wind"]["speed"],
                "index" : index
            }

            forToday[f"{getUra(index)}"] = vremeFor
            print(forToday)
        
        elif tommorow ==  dan:
            print("---------------------------TOMMOROW----------------------------")
            vremeForT = {
                "čas" : dataF["list"][index]["dt_txt"],
                "temp" : dataF["list"][index]["main"]["temp"],
                "status": dataF["list"][index]["weather"][0]["main"],
                "wind": dataF["list"][index]["wind"]["speed"],
                "index" : index
            }
            forTommorow[f"{getUra(index)}"] = vremeForT
            print(forTommorow)


        elif dayAfterTom ==  dan:
            print("---------------------------DAY AFTER TOMMOROW----------------------------")
            vremeForDT = {
                "čas" : dataF["list"][index]["dt_txt"],
                "temp" : dataF["list"][index]["main"]["temp"],
                "status": dataF["list"][index]["weather"][0]["main"],
                "wind": dataF["list"][index]["wind"]["speed"],
                "index" : index
            }
            forDayAftrTom[f"{getUra(index)}"] = vremeForDT
            print(forDayAftrTom)



    '''dan1 = {
        "ura1": {
            "čas" : dataF["list"][0]["dt_txt"],
            "temp" : dataF["list"][0]["main"]["temp"],
            "status": dataF["list"][0]["weather"]["main"],
            "wind": dataF["list"][0]["wind"]["speed"]
        },
        "ura2" : {
            "čas" : dataF["list"][1]["dt_txt"],
            "temp" : dataF["list"][1]["main"]["temp"],
            "status": dataF["list"][1]["weather"]["main"],
            "wind": dataF["list"][1]["wind"]["speed"]
        }
    }
    dan2 = {
        "ura1": {
            "čas" : dataF["list"][4]["dt_txt"],
            "temp" : dataF["list"][4]["main"]["temp"],
            "status": dataF["list"][4]["weather"]["main"],
            "status": dataF["list"][4]["wind"]["speed"]
        },
        "ura2" : {
            "čas" : dataF["list"][5]["dt_txt"],
            "temp" : dataF["list"][5]["main"]["temp"],
            "status": dataF["list"][5]["weather"]["main"],
            "status": dataF["list"][5]["wind"]["speed"]
        }
    }'''    
    isAdmin = admins.contains(User.userId == userId)
    return render_template("weatherFor.html",userData=userData, pfp=pfp, forToday=forToday,forTommorow = forTommorow, forDayAftrTom = forDayAftrTom, isAdmin=isAdmin)

@app.route("/trafficData")
def trafficData():
    userId = request.cookies.get("userId")
    if not userId:
        return redirect(url_for("login"))
    if request.method == "POST":
            pass
    isAdmin = admins.contains(User.userId == userId)
    return render_template("TrafficData.html", isAdmin = isAdmin)

@app.route("/localEvents")
def localEvents():
    userId = request.cookies.get("userId")
    if not userId:
        return redirect(url_for("login"))
    if request.method == "POST":
            pass
    isAdmin = admins.contains(User.userId == userId)
    return render_template("localEvents.html", isAdmin=isAdmin)

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
    isAdmin = admins.contains(User.userId == userId)
    return render_template("PerksAndRewards.html", isAdmin=isAdmin)


#---------------- ADMIN SHIT -------------------------



@app.route("/adminDashboard")
def adminDashboard():
    userId = request.cookies.get("userId")
    user = uporabniki.get(where('id') == userId)
    if not userId:
        return redirect(url_for("login"))
    isAdmin = admins.contains(User.userId == userId)
    if isAdmin == False:
        return redirect(url_for("Dashboard"))
    if request.method == "POST":
            pass
    


    # vedno
    userData = user
    pfp = getPfp(userId)

    return render_template("adDashboard.html",userData=userData,pfp=pfp, isAdmin=isAdmin)

# endpointi za polls, rewards in events za admine k dodajajo
@app.route("/addPoll", methods=["POST"])
def addPoll():
    userId = request.cookies.get("userId")
    userData = admins.get(User.userId == userId)
    if userData:
        mesto = userData['mesto']
        print(mesto)
    data = request.json
    ime = data['ime']
    opis = data['opis']
    trajanje = data['trajanje']
    #ime opis trajanje

    #backend 
    timeAddS = datetime.today()
    timeAdd = timeAddS.strftime('%Y-%m-%d %H:%M:%S') # cas dodelitve
    #userId je ze
    #mesto je ze

    polls.insert({"ime": ime, "opis": opis, "trajanje": trajanje, "timeAdd":timeAdd, "userId":userId, "mesto":mesto})



"""
poll = {
Ime: "lala" ( pride iz frontenda)
Opis: "blabla" (pride iz frontenda)
trajanje: "1dan" ( pride iz frontenda)
časDodelitve: " 12.5.2025 12.12" ("disabled input za računanje časa) (backend auto)
Kdo: "adminIme" (backend auto)
mesto : "mesto" (backend auto)
}

"""

@app.route("/addEvent", methods=["POST"])
def addEvent():
    pass

@app.route("/addReward", methods=["POST"])
def addReward():
    pass



#-------------------KONEC ADMIN----------------------------------------

#admins.insert({'userId': 20250411121455, 'mesto': 'Ljubljana'})
#admins.insert({'userId': 20250411123639, 'mesto': 'Skofja Loka'})




# konec ostlaih sitou
#----------------------------------------------------------
# support defi


def isAdmin(userId):
    isAdmin = admins.contains(User.userId == userId)
    return isAdmin




if __name__ == "__main__":
    app.run(debug=True,port=8080)
