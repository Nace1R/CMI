from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
from tinydb import TinyDB, Query, where
from datetime import datetime, timedelta
import os
import requests
import uuid

# tinyDB začetk
db = TinyDB('database/database.json')
uporabniki = db.table('uporabniki')

profil = db.table('profile-info')
points = db.table('points') #userId, points(int)

pollsT = db.table('polls') # ime, rezultat, creditGet
pollResults = db.table('pollResults') # pollId, yes: integer, no: integer
admins = db.table('admins') # userId, država 
rewardsT = db.table('rewards') # rewardId, pointsR, Ime, Description, mesto
rewardsUser = db.table('rewardsUsers') # rewardId : userId

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
        uuidId = uuid.uuid4()
        ids = str(uuidId)

        ime = request.form.get("ime")
        email = request.form.get("email")
        geslo = request.form.get("geslo")

        if uporabniki.get(User.ime == ime):
            return jsonify({"success": False, "error": "Uporabnik ze obstaja!"})

        uporabniki.insert({"ime": ime, "email": email, "geslo": geslo, "id":ids})

        points.insert({"userId": ids, "points": 0})

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

    userIdF = request.cookies.get("userId")
    if userIdF:
        userF = uporabniki.get(User.id == userIdF)
        if userF:
            userDataF = userF

    return render_template("profileCreation.html", userData = userDataF)


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



#------------------------------------------------------------------------------------------------------------------------------------------------
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

    userMestoData = profil.search(User.userId == userId)
    print(userMestoData)
    userMesto = userMestoData[0]['city']

    #show poll info
    polls = pollsT.all()
    print(polls)
    print("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------")
    pollList = []
    for poll in polls:
        mesto = poll.get('mesto')
        pollId = poll.get('pollId')
        ifVotedPoll = pollResults.get(User.pollId == pollId)
        if ifVotedPoll is None:
            ifVoted = {}
        else:
            ifVoted = ifVotedPoll['voted']
        if userId not in ifVoted.values():
            if userMesto == mesto:
                naslov = poll.get('naslov')
                opis = poll.get('opis')
                exDate = poll.get('exDate')
                reward = poll.get('reward')
                zdle = datetime.today()
                sexDate = datetime.strptime(exDate, "%Y-%m-%d %H:%M:%S")
                
                if zdle < sexDate:
                    timeLeft = sexDate - datetime.today()
                    dni = timeLeft.days
                    sekunde = timeLeft.seconds
                    ure = sekunde // 3600

                    pollList.append({
                        "naslov": naslov,
                        "opis": opis,
                        "timeLeft": [dni,ure],
                        "mesto": mesto,
                        "pollId": pollId,
                        "reward": reward
                    })

                    #print("-----------------------------------------------------------------------------------------")
                    #print(len(showPollData))
                    #print("-----------------------------------------------------------------------------------------")
                    #print(showPollData)
                else: 
                    pollsT.remove(User.pollId == pollId) # zaenkrat

            #SHOW rezultate coming soon
    showPollData = {
    "polls": pollList
    }
    #vedno
    user = uporabniki.get(where('id') == userId)
    userData = user
    isAdmin = admins.contains(User.userId == userId)
    pfp = getPfp(userId)
    print(showPollData)
    return render_template("PublicPolls.html", isAdmin=isAdmin, showPollData = showPollData, userData=userData, pfp=pfp)
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


@app.route("/pollVote", methods=["POST"])
def pollVote():
    userId = request.cookies.get("userId")
    data = request.json # pricakuje: data = {"pollId" : {id}, "result" : "yes"/"no"}
    pollId = data["pollId"]
    poll = pollResults.get(User.pollId == pollId)
    print(poll["yes"])
    print(poll["no"])
    
    yes = poll['yes']
    no = poll['no']
    voted = poll['voted']
    if not voted:
        votedIndex = 1
    else:
        votedIndex = int(max(voted, key=int)) + 1 #ai, problemi

    if data["vote"] == "yes":
        yes += 1
    else:
        no += 1
    voted[str(votedIndex)] = userId

    pollResults.update({
        'yes': yes,
        'no': no,
        'voted': voted
    }, User.pollId == pollId)

    pointsTempData = points.get(User.userId == userId)
    pointsTemp = pointsTempData['points']
    rewardData = pollsT.get(User.pollId == pollId)
    reward = int(rewardData["reward"])

    pointsTemp += reward
    points.update({
        'points' : pointsTemp
    }, User.userId == userId)
    rewardDataDebug = pollsT.get(User.pollId == pollId)
    rewardDebug = rewardDataDebug["reward"]
    print(rewardDebug)
    return jsonify({"success": True, "message": "Poll voted successfully"}), 201


"""
rezultati = {
pollId: "id"
yes: int
no: int
voted: {1:userId, 2:userId2}
}
"""
"""
points = {
"userID": userId
"points": int
}

"""


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

@app.route("/perksRewards",methods=["GET" , "POST"])
def perksRewards():
    userId = request.cookies.get("userId")
    userData = {"ime": "gost"}
    user = uporabniki.get(where('id') == userId)
    if not userId:
        return redirect(url_for("login"))
    userData = user
    isAdmin = admins.contains(User.userId == userId)

    pfp = getPfp(userId)
    pointsData = points.get(User.userId == userId)
    pointsN = pointsData["points"]

    userMestoData = profil.get(User.userId == userId)
    userMesto = userMestoData["city"]

    rewardList = []
    rewards = rewardsT.all()
    for reward in rewards:
        rewardMesto = reward.get('mesto')
        if rewardMesto == userMesto:
            naslov = reward.get('naslov')
            opis = reward.get('opis')
            pointsR = reward.get('potTock')
            rewardId = reward.get('rewardId')

            rewardList.append({
                "naslov" : naslov,
                "opis" : opis,
                "potTock" : pointsR,
                "rewardId" : rewardId,
                "mesto" : rewardMesto
            })
            
    showRewardData = {
        "reward" : rewardList
    }





    #rewards = db.table('rewards') # rewardId, pointsR, Ime, Description, mesto
    return render_template("PerksAndRewards.html", isAdmin=isAdmin, userData = userData, pfp=pfp, points=pointsN, showRewardData = showRewardData)

@app.route("/claimReward", methods=["POST"])
def claimReward():
    userId = request.cookies.get("userId")

    data = request.json
    rewardId = data["rewardId"]
    if not data or "rewardId" not in data:
        print("error")
    claimedData = rewardsUser.get(User.rewardId == rewardId)
    print(f"REWARD ID ={rewardId}---------------------------------")
    if claimedData is None:
        claimedUsers = [userId]
        rewardsUser.insert({"rewardId": rewardId, "claimedU": claimedUsers}) 
    """ tole mi boste razložil kako dela profesor, hvala:) ta zadeva se že inserta u faking addReward, ista zadeva, (line 702), 
        seprav že obstaja, potem je bil error da sm dubiu none, ker je bil list faking prazn, notr sm dou "1", šezmer je bil none,
        mistral mi je naredu če je none da mi ŠE ENKRATA INSERTA Z IDJEM NAMEST "1" KAR JE ISTA ZADEVA
"""
    else:
        claimedUsers = claimedData['claimedU']
        claimedUsers.append(userId)
        rewardsUser.update({"claimedU": claimedUsers}, User.rewardId == rewardId) 

    return jsonify({"success": True, "message": "Reward claimed successfully"}), 201
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
    aUserData = admins.get(User.userId == userId)
    if aUserData:
        mesto = aUserData['mesto']
        print(mesto)
    data = request.json
    naslov = data['naslov']
    opis = data['opis']
    trajanje = data['trajanje'] # dobi integer število dni
    reward  = data['reward']
    #backend 
    timeAddS = datetime.today()
    #timeAdd = timeAddS.strftime('%Y-%m-%d %H:%M:%S') # cas dodelitve 
    #userId je ze
    #mesto je ze
    # za expiration
    sexDate = timeAddS + timedelta(days=trajanje) #;)
    exDate = sexDate.strftime('%Y-%m-%d %H:%M:%S')
    uuidPollId = uuid.uuid4()
    pollId = str(uuidPollId)
    pollsT.insert({"naslov": naslov, "opis": opis, "trajanje": trajanje, "reward":reward, "userId":userId, "mesto":mesto, "pollId" : pollId, "exDate": exDate})
    pollResults.insert({
        "pollId": pollId,
        "yes" : 0,
        "no": 0,
        "voted" : {}
    })
    return jsonify({"message": "Poll added successfully"}), 201

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
    userId = request.cookies.get("userId")
    aUserData = admins.get(User.userId == userId)
        # iz frontenda
    if aUserData:
        mesto = aUserData['mesto']
        print(mesto)
    else:
        return jsonify({"success": False, "message": "nisi admin/error"}), 400
    data = request.json
    naslov = data['naslov']
    opis = data['opis']
    pointsR = data['potTock']

    #backend
    uuidRewardId = uuid.uuid4()
    rewardId = str(uuidRewardId)


    rewardsT.insert({"naslov": naslov, "opis": opis, "userId":userId, "mesto":mesto, "rewardId" : rewardId, "potTock": pointsR})
    rewardsUser.insert({"rewardId":rewardId,
                        "claimedU" : []
                        })

    return jsonify({"success": True, "message": "Reward added successfully"}), 201

#rewards = db.table('rewards') # rewardId, pointsR, Ime, Description, mesto
#rewardsUser = db.table('rewardsUsers') # rewardId : userId
#-------------------KONEC ADMIN----------------------------------------

#admins.insert({'userId': "f2775f3f-58ba-4d75-b9fc-044c1432f160", 'mesto': 'Ljubljana'})
#admins.insert({'userId': "91278ae2-f660-4ef9-8e85-723cc45153ef", 'mesto': 'Skofja Loka'})

# konec ostlaih sitou
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
# support defi


#def isAdmin(userId):
#    isAdmin = admins.contains(User.userId == userId)
#    return isAdmin




if __name__ == "__main__":
    app.run(debug=True,port=8080)
