from flask import Flask, request, jsonify, render_template, redirect, session
from pymongo import MongoClient
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
import datetime

app = Flask(__name__)

# folders
app.template_folder = "../templates"
app.static_folder = "../static"

app.secret_key = "smartwastekey"

bcrypt = Bcrypt(app)
CORS(app)

# ================= DATABASE =================

client = MongoClient("mongodb+srv://bhargavkola53:12345@mydtabase.5iadk.mongodb.net/?appName=MyDtabase")

db = client["smart_waste"]

sensor_collection = db["bin_data"]
complaint_collection = db["complaints"]
user_collection = db["users"]


# ================= LANDING PAGE =================

@app.route('/')
def landing():
    return render_template("home.html")


# ================= DASHBOARD =================

@app.route('/dashboard')
def dashboard():

    if "user" not in session:
        return redirect("/login")

    return render_template("index.html")


# ================= REGISTER =================

@app.route('/register', methods=["GET","POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        bins = request.form.getlist("bins")
        alert_type = request.form.get("alert_type")

        # validation checks
        if not name or not email or not password:
            return "All fields are required"

        if user_collection.find_one({"email": email}):
            return "User already exists"

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        user = {
            "name": name,
            "email": email,
            "password": hashed,
            "role": "user",
            "bins": bins,
            "alert_type": alert_type,
            "created_at": datetime.datetime.now()
        }

        user_collection.insert_one(user)

        return redirect("/login")

    return render_template("register.html")


# ================= LOGIN =================

@app.route('/login', methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return "Email and password required"

        user = user_collection.find_one({"email": email})

        if user and bcrypt.check_password_hash(user["password"], password):

            session["user"] = user["name"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin")

            return redirect("/dashboard")

        return "Invalid Login"

    return render_template("login.html")


# ================= LOGOUT =================

@app.route('/logout')
def logout():

    session.clear()

    return redirect("/")


# ================= SENSOR DATA SAVE =================

@app.route('/sensor', methods=['POST'])
def sensor():

    if not request.is_json:
        return jsonify({"error":"JSON data required"}), 400

    data = request.json

    sensor_data = {

        "bin1": data.get("bin1", 0),
        "bin2": data.get("bin2", 0),
        "bin3": data.get("bin3", 0),

        "time": datetime.datetime.now()

    }

    sensor_collection.insert_one(sensor_data)

    return jsonify({"message": "Weight Data Saved"})


# ================= GET SENSOR DATA =================

@app.route('/data')
def get_data():

    latest = sensor_collection.find_one(sort=[("_id",-1)])

    if latest:
        return jsonify({
            "bin1": latest.get("bin1",0),
            "bin2": latest.get("bin2",0),
            "bin3": latest.get("bin3",0)
        })

    return jsonify({"bin1":0,"bin2":0,"bin3":0})


# ================= COMPLAINT PAGE =================

@app.route('/complaint', methods=["GET","POST"])
def complaint():

    if request.method == "GET":
        return render_template("complaint.html")

    name = request.form.get("name")
    bins = request.form.getlist("bins")
    actions = request.form.getlist("action")

    if not name or not bins or not actions:
        return "All complaint fields required"

    bin_no = ", ".join(bins)
    action = ", ".join(actions)

    complaint = {

        "name": name,
        "bin": bin_no,
        "action": action,
        "status": "Pending",
        "time": datetime.datetime.now()

    }

    complaint_collection.insert_one(complaint)

    return redirect("/")


# ================= ADMIN DASHBOARD =================

@app.route('/admin')
def admin():

    if session.get("role") != "admin":
        return redirect("/login")

    complaints = list(complaint_collection.find().sort("_id", -1))

    return render_template("admin.html", complaints=complaints)


# ================= COMPLETE COMPLAINT =================

@app.route('/complete/<id>')
def complete(id):

    if session.get("role") != "admin":
        return redirect("/login")

    complaint_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"status": "Completed"}}
    )

    return redirect("/admin")


# ================= RUN SERVER =================

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=True)