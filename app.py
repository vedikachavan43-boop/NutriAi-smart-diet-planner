
from flask import Flask, render_template, request, session, redirect
import os
import sqlite3

def create_history_table():

    conn = sqlite3.connect("nutriai.db")

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food TEXT,
            calories REAL,
            protein REAL,
            carbs REAL,
            fat REAL,
            status TEXT,
            date_time TEXT
        )
    """)

    conn.commit()
    conn.close()

# =========================================
# PYTORCH FIX
# =========================================

# Disable oneDNN CPU optimization
os.environ["ONEDNN_DISABLE"] = "1"

import torch

# Disable MKLDNN CPU backend
torch.backends.mkldnn.enabled = False

from ultralytics import YOLO
from nutrition_data import nutrition_data


# =========================================
# FLASK APP
# =========================================

app = Flask(__name__)
app.secret_key = "nutriai-secret-key"

app = Flask(__name__)

app.secret_key = "nutriai-secret-key"


# =====================================
# CREATE DATABASE TABLES
# =====================================

def create_tables():

    conn = sqlite3.connect(
        os.path.join(app.root_path, "nutriai.db")
    )

    cursor = conn.cursor()


    # USERS TABLE

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL

        )
    """)


    # HISTORY TABLE

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            food TEXT,

            calories REAL,

            protein REAL,

            carbs REAL,

            fat REAL,

            status TEXT,

            date_time TEXT

        )
    """)


    conn.commit()

    conn.close()
# =========================================
# YOLO MODEL
# =========================================

model = YOLO("best.pt")


# =========================================
# UPLOAD FOLDER
# =========================================

UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================================
# UPLOAD FOLDER
# =========================================

UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================
# YOLO MODEL
# =========================================

# best.pt project folder मध्ये असणे आवश्यक आहे

model = YOLO("best.pt")


# =========================================
# HOME PAGE
# =========================================

@app.route("/")
def home():

    return render_template("home.html")


# =========================================
# LOGIN PAGE
# =========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("nutriai.db")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
            """,
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()


        # =====================================
        # LOGIN SUCCESS
        # =====================================

        if user:

            session["user_id"] = user["id"]

            session["user_name"] = user["name"]

            session["user_email"] = user["email"]

            return redirect("/dashboard")


        # =====================================
        # LOGIN FAILED
        # =====================================

        return render_template(
            "login.html",
            error="Invalid email or password."
        )


    return render_template(
        "login.html"
    )

# =========================================
# REGISTER PAGE
# =========================================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")


        # Check empty fields

        if not name or not email or not password or not confirm_password:

            return render_template(
                "register.html",
                error="Please fill all fields."
            )


        # Check password

        if password != confirm_password:

            return render_template(
                "register.html",
                error="Passwords do not match."
            )


        # =====================================
        # DATABASE
        # =====================================

        conn = sqlite3.connect(
            os.path.join(
                app.root_path,
                "nutriai.db"
            )
        )

        cursor = conn.cursor()


        try:

            cursor.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,
                (
                    name,
                    email,
                    password
                )
            )

            conn.commit()

            conn.close()


            # Registration successful
            return redirect("/login")


        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "register.html",
                error="Email already registered."
            )


    return render_template(
        "register.html"
    )


# =========================================
# DASHBOARD
# =========================================
@app.route("/dashboard")
def dashboard():

    # Check whether user is logged in
    if "user_id" not in session:
        return redirect("/login")

    # ==============================
    # DATABASE CONNECTION
    # ==============================

    import sqlite3

    conn = sqlite3.connect("nutriai.db")
    cursor = conn.cursor()

    # ==============================
    # TOTAL FOODS
    # ==============================

    cursor.execute("""
        SELECT COUNT(*)
        FROM history
    """)

    total_foods = cursor.fetchone()[0]

    # ==============================
    # TOTAL CALORIES
    # ==============================

    cursor.execute("""
        SELECT COALESCE(SUM(calories), 0)
        FROM history
    """)

    total_calories = cursor.fetchone()[0]

    # ==============================
    # HISTORY COUNT
    # ==============================

    cursor.execute("""
        SELECT COUNT(*)
        FROM history
    """)

    history_count = cursor.fetchone()[0]

    # ==============================
    # TOTAL USERS
    # ==============================

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    total_users = cursor.fetchone()[0]

    conn.close()

    # ==============================
    # BMI
    # ==============================

    bmi_value = session.get("bmi")

    # ==============================
    # SEND DATA TO DASHBOARD
    # ==============================

    return render_template(
        "dashboard.html",
        total_foods=total_foods,
        total_calories=round(total_calories),
        history_count=history_count,
        bmi=bmi_value,
        total_users=total_users
    )
# =========================================
# ABOUT PAGE
# =========================================

@app.route("/about")
def about():

    return render_template("about.html")

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================
# FOOD HISTORY
# =========================================

@app.route("/history")
def history():

    import sqlite3

    conn = sqlite3.connect("nutriai.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT food, calories, protein, carbs, fat, date_time
        FROM history
        ORDER BY id DESC
    """)

    records = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        records=records
    )

# =========================================
# PROGRESS TRACKING
# =========================================

@app.route("/progress")
def progress():

    import sqlite3
    from datetime import datetime, timedelta

    # =====================================
    # DATABASE PATH
    # =====================================

    db_path = os.path.join(
        app.root_path,
        "nutriai.db"
    )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()


    # =====================================
    # CREATE HISTORY TABLE
    # =====================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food TEXT,
            calories REAL,
            protein REAL,
            carbs REAL,
            fat REAL,
            status TEXT,
            date_time TEXT
        )
    """)


    # =====================================
    # LAST 7 DAYS
    # =====================================

    today = datetime.now().date()

    start_date = today - timedelta(days=6)


    weekly_data = []

    weekly_calories = 0

    meals_tracked = 0


    # =====================================
    # GET DAILY CALORIES
    # =====================================

    for i in range(7):

        current_date = start_date + timedelta(days=i)

        date_string = current_date.strftime(
            "%Y-%m-%d"
        )


        cursor.execute("""
            SELECT
                COALESCE(SUM(calories), 0)
                AS total_calories,

                COUNT(*) AS meal_count

            FROM history

            WHERE date_time LIKE ?
        """, (
            date_string + "%",
        ))


        row = cursor.fetchone()


        calories = float(
            row["total_calories"] or 0
        )


        meal_count = int(
            row["meal_count"] or 0
        )


        # Add to weekly total

        weekly_calories += calories

        meals_tracked += meal_count


        # =================================
        # CALCULATE BAR HEIGHT
        # =================================

        if calories > 0:

            bar_height = round(
                (calories / 15000) * 100,
                1
            )

            # Minimum visible height

            bar_height = max(
                bar_height,
                3
            )

        else:

            bar_height = 2


        weekly_data.append({

            "day":
                current_date.strftime("%a"),

            "calories":
                round(calories, 0),

            "height":
                bar_height

        })


    # =====================================
    # WEEKLY GOAL
    # =====================================

    weekly_goal = 14000


    if weekly_goal > 0:

        goal_percentage = round(
            (weekly_calories / weekly_goal) * 100
        )

    else:

        goal_percentage = 0


    goal_percentage = min(
        goal_percentage,
        100
    )


    remaining_calories = max(
        weekly_goal - weekly_calories,
        0
    )


    # =====================================
    # CLOSE DATABASE
    # =====================================

    conn.close()


    # =====================================
    # BMI
    # =====================================

    current_bmi = session.get(
    "bmi",
    "--"
)


    # =====================================
    # HEALTHY STREAK
    # =====================================

    healthy_streak = 0


    for day_data in reversed(
        weekly_data
    ):

        if day_data["calories"] > 0:

            healthy_streak += 1

        else:

            break


    # =====================================
    # RENDER PROGRESS PAGE
    # =====================================

    return render_template(

        "progress.html",

        weekly_calories=
            round(weekly_calories),

        current_bmi=
            current_bmi,

        meals_tracked=
            meals_tracked,

        healthy_streak=
            healthy_streak,

        weekly_data=
            weekly_data,

        weekly_goal=
            weekly_goal,

        goal_percentage=
            goal_percentage,

        remaining_calories=
            round(remaining_calories)

    )
# =========================================
# BMI CALCULATOR
# =========================================

@app.route("/bmi", methods=["GET", "POST"])
def bmi():

    bmi_value = None
    category = None

    if request.method == "POST":

        height = float(
            request.form["height"]
        )

        weight = float(
            request.form["weight"]
        )

        # =====================================
        # HEIGHT: CM → METERS
        # =====================================

        height_m = height / 100

        # =====================================
        # BMI CALCULATION
        # =====================================

        bmi_value = weight / (
            height_m * height_m
        )

        bmi_value = round(
            bmi_value,
            2
        )

        # =====================================
        # BMI CATEGORY
        # =====================================

        if bmi_value < 18.5:

            category = "Underweight"

        elif bmi_value < 25:

            category = "Normal Weight"

        elif bmi_value < 30:

            category = "Overweight"

        else:

            category = "Obese"

        # =====================================
        # SAVE BMI IN SESSION
        # =====================================

        session["bmi"] = bmi_value
        session["bmi_category"] = category

    return render_template(
        "bmi.html",
        bmi=bmi_value,
        category=category
    )

# =========================================
# HEALTHY RECIPES
# =========================================

@app.route("/recipes")
def recipes():

    recipes = [

        {
            "name": "Aloo Gobhi",
            "icon": "🥔",
            "category": "Main Course",
            "description": "Healthy Indian potato and cauliflower vegetable dish.",
            "ingredients": "Potato, cauliflower, onion, tomato, turmeric, cumin, spices.",
            "time": "30 min",
            "calories": "180 kcal",
            "protein": "5 g",
            "carbs": "28 g",
            "fat": "6 g"
        },

        {
            "name": "Aloo Sabji",
            "icon": "🥔",
            "category": "Main Course",
            "description": "Simple and delicious Indian potato vegetable curry.",
            "ingredients": "Potato, onion, tomato, cumin, turmeric, coriander, spices.",
            "time": "25 min",
            "calories": "190 kcal",
            "protein": "4 g",
            "carbs": "30 g",
            "fat": "7 g"
        },

        {
            "name": "Bhakarwadi",
            "icon": "🥨",
            "category": "Snack",
            "description": "Crispy and spicy Maharashtrian snack.",
            "ingredients": "Flour, coconut, sesame, spices, chilli, coriander.",
            "time": "40 min",
            "calories": "170 kcal",
            "protein": "4 g",
            "carbs": "22 g",
            "fat": "8 g"
        },

        {
            "name": "Bhakri",
            "icon": "🫓",
            "category": "Healthy Meal",
            "description": "Traditional healthy Indian flatbread.",
            "ingredients": "Jowar flour, water, salt.",
            "time": "20 min",
            "calories": "120 kcal",
            "protein": "3 g",
            "carbs": "24 g",
            "fat": "1 g"
        },

        {
            "name": "Bhindi",
            "icon": "🥬",
            "category": "Healthy Meal",
            "description": "Nutritious and tasty Indian okra vegetable.",
            "ingredients": "Ladyfinger, onion, tomato, turmeric, cumin, spices.",
            "time": "25 min",
            "calories": "110 kcal",
            "protein": "3 g",
            "carbs": "15 g",
            "fat": "5 g"
        },

        {
            "name": "Chole",
            "icon": "🍲",
            "category": "Main Course",
            "description": "Protein-rich chickpea curry prepared with Indian spices.",
            "ingredients": "Chickpeas, onion, tomato, ginger, garlic, spices.",
            "time": "40 min",
            "calories": "240 kcal",
            "protein": "12 g",
            "carbs": "35 g",
            "fat": "6 g"
        },

        {
            "name": "Coconut Chutney",
            "icon": "🥥",
            "category": "Side Dish",
            "description": "Fresh and refreshing coconut chutney.",
            "ingredients": "Coconut, green chilli, coriander, ginger, lemon, salt.",
            "time": "10 min",
            "calories": "90 kcal",
            "protein": "2 g",
            "carbs": "5 g",
            "fat": "7 g"
        },

        {
            "name": "Daal",
            "icon": "🍲",
            "category": "Healthy Meal",
            "description": "Protein-rich Indian lentil preparation.",
            "ingredients": "Toor dal, tomato, onion, turmeric, cumin, coriander.",
            "time": "30 min",
            "calories": "180 kcal",
            "protein": "10 g",
            "carbs": "25 g",
            "fat": "4 g"
        },

        {
            "name": "Dosa",
            "icon": "🥞",
            "category": "Breakfast",
            "description": "Crispy South Indian rice and lentil pancake.",
            "ingredients": "Rice, urad dal, salt, water.",
            "time": "25 min",
            "calories": "170 kcal",
            "protein": "4 g",
            "carbs": "30 g",
            "fat": "4 g"
        },

        {
            "name": "Eggs",
            "icon": "🥚",
            "category": "Non-Veg",
            "description": "Nutritious eggs rich in protein and essential nutrients.",
            "ingredients": "Eggs, salt, pepper, herbs.",
            "time": "10 min",
            "calories": "140 kcal",
            "protein": "12 g",
            "carbs": "1 g",
            "fat": "10 g"
        },

        {
            "name": "Idli",
            "icon": "🍘",
            "category": "Breakfast",
            "description": "Soft and healthy steamed South Indian breakfast.",
            "ingredients": "Rice, urad dal, salt, water.",
            "time": "25 min",
            "calories": "120 kcal",
            "protein": "4 g",
            "carbs": "25 g",
            "fat": "1 g"
        },

        {
            "name": "Khandvi",
            "icon": "🍥",
            "category": "Snack",
            "description": "Light and soft Gujarati gram flour snack.",
            "ingredients": "Besan, yogurt, turmeric, ginger, green chilli.",
            "time": "30 min",
            "calories": "140 kcal",
            "protein": "6 g",
            "carbs": "18 g",
            "fat": "5 g"
        },

        {
            "name": "Medu Vada",
            "icon": "🍩",
            "category": "Breakfast",
            "description": "Crispy South Indian lentil-based breakfast snack.",
            "ingredients": "Urad dal, onion, green chilli, curry leaves, spices.",
            "time": "35 min",
            "calories": "180 kcal",
            "protein": "6 g",
            "carbs": "22 g",
            "fat": "8 g"
        },

        {
            "name": "Omelette",
            "icon": "🍳",
            "category": "Non-Veg",
            "description": "Protein-rich omelette with vegetables and herbs.",
            "ingredients": "Eggs, onion, tomato, green chilli, coriander, spices.",
            "time": "10 min",
            "calories": "160 kcal",
            "protein": "13 g",
            "carbs": "4 g",
            "fat": "10 g"
        },

        {
            "name": "Paratha",
            "icon": "🫓",
            "category": "Breakfast",
            "description": "Traditional Indian flatbread that can be enjoyed with vegetables or yogurt.",
            "ingredients": "Wheat flour, water, salt, oil, spices.",
            "time": "25 min",
            "calories": "210 kcal",
            "protein": "5 g",
            "carbs": "32 g",
            "fat": "7 g"
        },

        {
            "name": "Poha",
            "icon": "🍚",
            "category": "Breakfast",
            "description": "Light and nutritious Indian breakfast made with flattened rice.",
            "ingredients": "Poha, onion, potato, peanuts, mustard seeds, curry leaves, lemon.",
            "time": "20 min",
            "calories": "180 kcal",
            "protein": "4 g",
            "carbs": "30 g",
            "fat": "6 g"
        },

        {
            "name": "Puri",
            "icon": "🫓",
            "category": "Breakfast",
            "description": "Traditional deep-fried Indian flatbread.",
            "ingredients": "Wheat flour, water, salt, oil.",
            "time": "25 min",
            "calories": "200 kcal",
            "protein": "4 g",
            "carbs": "30 g",
            "fat": "8 g"
        },

        {
            "name": "Rajma",
            "icon": "🍛",
            "category": "Healthy Meal",
            "description": "Protein and fiber-rich kidney bean curry.",
            "ingredients": "Rajma, onion, tomato, ginger, garlic, spices.",
            "time": "45 min",
            "calories": "220 kcal",
            "protein": "12 g",
            "carbs": "32 g",
            "fat": "5 g"
        },

        {
            "name": "Rice",
            "icon": "🍚",
            "category": "Healthy Meal",
            "description": "Simple steamed rice that pairs well with dal and vegetables.",
            "ingredients": "Rice, water, salt.",
            "time": "20 min",
            "calories": "200 kcal",
            "protein": "4 g",
            "carbs": "45 g",
            "fat": "1 g"
        },

        {
            "name": "Roti Phulka",
            "icon": "🫓",
            "category": "Healthy Meal",
            "description": "Healthy whole wheat Indian flatbread.",
            "ingredients": "Whole wheat flour, water, salt.",
            "time": "20 min",
            "calories": "100 kcal",
            "protein": "3 g",
            "carbs": "20 g",
            "fat": "1 g"
        },

        {
            "name": "Saag",
            "icon": "🥬",
            "category": "Healthy Meal",
            "description": "Nutritious leafy green vegetable preparation.",
            "ingredients": "Spinach, mustard greens, onion, garlic, spices.",
            "time": "30 min",
            "calories": "130 kcal",
            "protein": "6 g",
            "carbs": "12 g",
            "fat": "5 g"
        },

        {
            "name": "Salad",
            "icon": "🥗",
            "category": "Healthy Meal",
            "description": "Fresh vegetable salad packed with vitamins and fiber.",
            "ingredients": "Cucumber, tomato, carrot, onion, lemon, coriander.",
            "time": "10 min",
            "calories": "80 kcal",
            "protein": "2 g",
            "carbs": "12 g",
            "fat": "2 g"
        },

        {
            "name": "Sambhar",
            "icon": "🍲",
            "category": "Healthy Meal",
            "description": "Healthy South Indian lentil and vegetable curry.",
            "ingredients": "Toor dal, vegetables, tamarind, tomato, sambhar powder.",
            "time": "35 min",
            "calories": "150 kcal",
            "protein": "7 g",
            "carbs": "22 g",
            "fat": "4 g"
        },

        {
            "name": "Thepla",
            "icon": "🫓",
            "category": "Breakfast",
            "description": "Healthy Gujarati flatbread prepared with spices and herbs.",
            "ingredients": "Wheat flour, fenugreek leaves, yogurt, spices.",
            "time": "25 min",
            "calories": "170 kcal",
            "protein": "5 g",
            "carbs": "27 g",
            "fat": "5 g"
        },

        {
            "name": "Upma",
            "icon": "🥣",
            "category": "Breakfast",
            "description": "Light and filling South Indian semolina breakfast.",
            "ingredients": "Semolina, onion, vegetables, mustard seeds, curry leaves.",
            "time": "20 min",
            "calories": "160 kcal",
            "protein": "4 g",
            "carbs": "27 g",
            "fat": "5 g"
        },

        {
            "name": "Varan",
            "icon": "🍲",
            "category": "Healthy Meal",
            "description": "Simple Maharashtrian dal preparation served with rice.",
            "ingredients": "Toor dal, turmeric, salt, cumin, coriander.",
            "time": "25 min",
            "calories": "150 kcal",
            "protein": "8 g",
            "carbs": "22 g",
            "fat": "3 g"
        },

        {
            "name": "Veg Pulao",
            "icon": "🍛",
            "category": "Main Course",
            "description": "Flavorful rice cooked with fresh vegetables and mild spices.",
            "ingredients": "Rice, carrot, peas, beans, onion, spices.",
            "time": "30 min",
            "calories": "230 kcal",
            "protein": "6 g",
            "carbs": "38 g",
            "fat": "6 g"
        },

        {
            "name": "Yellow Dhokla",
            "icon": "🟨",
            "category": "Snack",
            "description": "Soft and steamed Gujarati snack made from gram flour.",
            "ingredients": "Besan, yogurt, lemon, turmeric, eno, spices.",
            "time": "30 min",
            "calories": "150 kcal",
            "protein": "6 g",
            "carbs": "20 g",
            "fat": "4 g"
        },

        {
            "name": "Yogurt",
            "icon": "🥛",
            "category": "Healthy Meal",
            "description": "Refreshing yogurt that provides protein and calcium.",
            "ingredients": "Fresh milk, yogurt culture.",
            "time": "5 min",
            "calories": "100 kcal",
            "protein": "5 g",
            "carbs": "7 g",
            "fat": "4 g"
        }

    ]

    return render_template(
        "recipes.html",
        recipes=recipes
    )

# =========================================
# AI DIET PLAN
# =========================================

# =========================================================
# DIET PLAN
# =========================================================

@app.route("/diet")
def diet():
    return render_template("diet.html")


# =========================================================
# GENERATE PERSONALIZED DIET PLAN
# =========================================================

@app.route("/generate_diet", methods=["POST"])
def generate_diet():

    try:

        # -----------------------------
        # GET USER INPUT
        # -----------------------------

        age = int(request.form.get("age"))
        weight = float(request.form.get("weight"))
        height = float(request.form.get("height"))

        goal = request.form.get("goal")
        diet_preference = request.form.get("diet_preference")


        # -----------------------------
        # BASIC VALIDATION
        # -----------------------------

        if age < 1 or weight <= 0 or height <= 0:

            return "Please enter valid details."


        # -----------------------------
        # BMR - Mifflin St Jeor
        # -----------------------------
        # Since gender is not collected,
        # we use a general estimation.

        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5


        # -----------------------------
        # DAILY CALORIE TARGET
        # -----------------------------

        maintenance = bmr * 1.4


        if goal == "weight-loss":

            calories = maintenance - 300

        elif goal == "weight-gain":

            calories = maintenance + 300

        elif goal == "muscle-gain":

            calories = maintenance + 250

        else:

            calories = maintenance


        calories = max(1200, int(calories))


        # -----------------------------
        # MACROS
        # -----------------------------

        protein = int(weight * 1.2)

        fat = int((calories * 0.25) / 9)

        carbs = int(
            (calories - (protein * 4) - (fat * 9)) / 4
        )


        # -----------------------------
        # WATER
        # -----------------------------

        water = round(weight * 0.035, 1)


        # -----------------------------
        # GOAL NAME
        # -----------------------------

        goal_names = {

            "weight-loss": "Weight Loss",

            "weight-gain": "Weight Gain",

            "maintain": "Maintain Weight",

            "muscle-gain": "Muscle Gain"

        }

        goal_title = goal_names.get(
            goal,
            "Healthy Lifestyle"
        )


        # =================================================
        # VEGETARIAN PLAN
        # =================================================

        if diet_preference == "vegetarian":

            if goal == "weight-loss":

                breakfast = {
                    "title": "Vegetable Poha",
                    "food": "Vegetable Poha + Curd + Green Tea",
                    "calories": int(calories * 0.25)
                }

                lunch = {
                    "title": "Balanced Lunch",
                    "food": "2 Roti + Dal + Mixed Vegetable + Salad",
                    "calories": int(calories * 0.35)
                }

                snack = {
                    "title": "Healthy Snack",
                    "food": "Apple + 8 Almonds",
                    "calories": int(calories * 0.15)
                }

                dinner = {
                    "title": "Light Dinner",
                    "food": "Vegetable Soup + 2 Roti + Salad",
                    "calories": int(calories * 0.25)
                }


            elif goal == "weight-gain":

                breakfast = {
                    "title": "Power Breakfast",
                    "food": "Oats + Banana + Milk + Nuts",
                    "calories": int(calories * 0.25)
                }

                lunch = {
                    "title": "High Energy Lunch",
                    "food": "3 Roti + Dal + Paneer + Rice + Salad",
                    "calories": int(calories * 0.35)
                }

                snack = {
                    "title": "Energy Snack",
                    "food": "Banana Shake + Peanut Butter",
                    "calories": int(calories * 0.15)
                }

                dinner = {
                    "title": "Nutritious Dinner",
                    "food": "Paneer + 2 Roti + Vegetable + Curd",
                    "calories": int(calories * 0.25)
                }


            elif goal == "muscle-gain":

                breakfast = {
                    "title": "Protein Breakfast",
                    "food": "Oats + Milk + Banana + Paneer",
                    "calories": int(calories * 0.25)
                }

                lunch = {
                    "title": "Protein Rich Lunch",
                    "food": "Rice + Dal + Paneer + Roti + Salad",
                    "calories": int(calories * 0.35)
                }

                snack = {
                    "title": "Protein Snack",
                    "food": "Greek Yogurt + Banana + Almonds",
                    "calories": int(calories * 0.15)
                }

                dinner = {
                    "title": "Muscle Recovery Dinner",
                    "food": "Paneer + Roti + Vegetable Soup",
                    "calories": int(calories * 0.25)
                }


            else:

                breakfast = {
                    "title": "Healthy Breakfast",
                    "food": "Idli + Sambar + Fruit",
                    "calories": int(calories * 0.25)
                }

                lunch = {
                    "title": "Balanced Lunch",
                    "food": "2 Roti + Dal + Sabji + Salad + Curd",
                    "calories": int(calories * 0.35)
                }

                snack = {
                    "title": "Healthy Snack",
                    "food": "Fruit + Handful of Nuts",
                    "calories": int(calories * 0.15)
                }

                dinner = {
                    "title": "Balanced Dinner",
                    "food": "Khichdi + Vegetable Soup + Salad",
                    "calories": int(calories * 0.25)
                }


        # =================================================
        # NON-VEGETARIAN PLAN
        # =================================================

        elif diet_preference == "non-vegetarian":

            breakfast = {
                "title": "Protein Breakfast",
                "food": "2 Eggs + Brown Bread + Fruit",
                "calories": int(calories * 0.25)
            }

            lunch = {
                "title": "Balanced Lunch",
                "food": "2 Roti + Grilled Chicken + Dal + Salad",
                "calories": int(calories * 0.35)
            }

            snack = {
                "title": "Healthy Snack",
                "food": "Apple + Almonds",
                "calories": int(calories * 0.15)
            }

            dinner = {
                "title": "Light Dinner",
                "food": "Grilled Chicken + Vegetable Soup + Salad",
                "calories": int(calories * 0.25)
            }


        # =================================================
        # VEGAN PLAN
        # =================================================

        else:

            breakfast = {
                "title": "Vegan Breakfast",
                "food": "Oats + Banana + Soy Milk + Nuts",
                "calories": int(calories * 0.25)
            }

            lunch = {
                "title": "Plant Based Lunch",
                "food": "Brown Rice + Dal + Vegetables + Salad",
                "calories": int(calories * 0.35)
            }

            snack = {
                "title": "Vegan Snack",
                "food": "Fruit + Almonds",
                "calories": int(calories * 0.15)
            }

            dinner = {
                "title": "Healthy Vegan Dinner",
                "food": "Vegetable Soup + Roti + Salad",
                "calories": int(calories * 0.25)
            }


        # =================================================
        # FINAL PLAN
        # =================================================

        plan = {

            "breakfast": breakfast,

            "lunch": lunch,

            "snack": snack,

            "dinner": dinner,

            "total_calories": calories,

            "protein": protein,

            "carbs": carbs,

            "fat": fat,

            "water": f"{water} L"

        }


        # =================================================
        # RESULT PAGE
        # =================================================

        return render_template(

            "result.html",

            plan=plan,

            age=age,

            weight=weight,

            height=height,

            goal=goal_title,

            diet_preference=diet_preference.title()

        )


    except Exception as e:

        print("DIET ERROR:", e)

        return "Something went wrong. Please enter valid details."

# =========================================
# EXERCISE PLANNER
# =========================================

@app.route("/exercise")
def exercise():

    return render_template(
        "exercise.html"
    )


# =========================================
# AI FOOD DETECTION PAGE
# =========================================

@app.route("/food-detection")
def food_detection():

    return render_template(
        "food_detection.html"
    )


# =========================================
# AI FOOD PREDICTION
# =========================================

# =========================================
# AI FOOD PREDICTION
# =========================================

@app.route("/predict", methods=["POST"])
def predict():

    # =====================================
    # CHECK IMAGE
    # =====================================

    if "food_image" not in request.files:
        return "No image uploaded"

    file = request.files["food_image"]

    if file.filename == "":
        return "Please select an image"


    # =====================================
    # SAVE IMAGE
    # =====================================

    filename = os.path.basename(file.filename)

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)


    # =====================================
    # YOLO PREDICTION
    # =====================================

    results = model.predict(
        source=filepath,
        conf=0.25
    )


    detected_food = "Unknown"
    confidence = 0


    # =====================================
    # GET DETECTED FOOD
    # =====================================

    for result in results:

        if result.boxes is not None and len(result.boxes) > 0:

            # Find highest confidence detection
            best_box = max(
                result.boxes,
                key=lambda box: float(box.conf[0])
            )

            class_id = int(best_box.cls[0])

            confidence = float(best_box.conf[0])

            detected_food = model.names[class_id]

            break


    # =====================================
    # GET NUTRITION DATA
    # =====================================

    food_key = detected_food.lower().strip()

    nutrition = nutrition_data.get(
        food_key,
        {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0
        }
    )


    # =====================================
    # SAVE TO FOOD HISTORY
    # =====================================

    import sqlite3
    from datetime import datetime

    # Database path
    db_path = os.path.join(
        app.root_path,
        "nutriai.db"
    )

    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()


    # =====================================
    # CREATE HISTORY TABLE
    # =====================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food TEXT,
            calories REAL,
            protein REAL,
            carbs REAL,
            fat REAL,
            status TEXT,
            date_time TEXT
        )
    """)


    # =====================================
    # INSERT FOOD RECORD
    # =====================================

    cursor.execute("""
        INSERT INTO history
        (
            food,
            calories,
            protein,
            carbs,
            fat,
            status,
            date_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (

        detected_food,

        nutrition["calories"],

        nutrition["protein"],

        nutrition["carbs"],

        nutrition["fat"],

        "Detected",

        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))


    # =====================================
    # SAVE DATABASE CHANGES
    # =====================================

    conn.commit()

    conn.close()


    # =====================================
    # RESULT PAGE
    # =====================================

    image_filename = os.path.basename(filepath)


    return render_template(

        "food_result.html",

        food=detected_food,

        confidence=round(
            confidence * 100,
            2
        ),

        image_path=image_filename,

        calories=nutrition["calories"],

        protein=nutrition["protein"],

        carbs=nutrition["carbs"],

        fat=nutrition["fat"]
    )
# =========================================
# RUN FLASK APP
# =========================================

if __name__ == "__main__":

    create_tables()

    app.run(
        debug=True
    )

