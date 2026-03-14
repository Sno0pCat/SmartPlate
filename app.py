from flask import Flask, render_template, request
import json
from datetime import date

app = Flask(__name__)

MEALS_FILE = "data/meals.json"
FOOD_DATABASE_FILE = "data/food_database.json"


def load_meals():
    with open(MEALS_FILE, "r") as file:
        return json.load(file)


def save_meals(meals_data):
    with open(MEALS_FILE, "w") as file:
        json.dump(meals_data, file, indent=4)


def load_food_database():
    with open(FOOD_DATABASE_FILE, "r") as file:
        return json.load(file)


def save_food_database(food_data):
    with open(FOOD_DATABASE_FILE, "w") as file:
        json.dump(food_data, file, indent=4)


def get_daily_totals(meals):
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    total_calories = 0

    for meal in meals:
        total_protein += meal["protein"]
        total_carbs += meal["carbs"]
        total_fat += meal["fat"]
        total_calories += meal["calories"]

    return total_protein, total_carbs, total_fat, total_calories


def split_meals_by_type(meals):
    breakfast_meals = []
    lunch_meals = []
    dinner_meals = []

    for meal in meals:
        if meal["meal_type"] == "Breakfast":
            breakfast_meals.append(meal)
        elif meal["meal_type"] == "Lunch":
            lunch_meals.append(meal)
        elif meal["meal_type"] == "Dinner":
            dinner_meals.append(meal)

    return breakfast_meals, lunch_meals, dinner_meals


def build_home_page(message=""):
    meals_data = load_meals()
    food_database = load_food_database()

    today = str(date.today())
    todays_meals = meals_data.get(today, [])

    breakfast_meals, lunch_meals, dinner_meals = split_meals_by_type(todays_meals)
    total_protein, total_carbs, total_fat, total_calories = get_daily_totals(todays_meals)

    food_names = sorted(food_database.keys())

    return render_template(
        "index.html",
        today=today,
        total_protein=total_protein,
        total_carbs=total_carbs,
        total_fat=total_fat,
        total_calories=total_calories,
        breakfast_meals=breakfast_meals,
        lunch_meals=lunch_meals,
        dinner_meals=dinner_meals,
        message=message,
        food_names=food_names
    )


@app.route("/")
def home():
    return build_home_page()


@app.route("/add_meal", methods=["POST"])
def add_meal():
    food = request.form["food"].strip()
    food_key = food.lower()
    meal_type = request.form["meal_type"]
    quantity_consumed = float(request.form["quantity_consumed"])

    food_database = load_food_database()

    if food_key in food_database:
        saved_food = food_database[food_key]
        base_amount = float(saved_food["base_amount"])
        protein = float(saved_food["protein"])
        carbs = float(saved_food["carbs"])
        fat = float(saved_food["fat"])
    else:
        base_amount_text = request.form.get("base_amount", "").strip()
        protein_text = request.form.get("protein", "").strip()
        carbs_text = request.form.get("carbs", "").strip()
        fat_text = request.form.get("fat", "").strip()

        missing_new_food_info = (
            base_amount_text == "" or
            protein_text == "" or
            carbs_text == "" or
            fat_text == ""
    )

    if missing_new_food_info:
        return build_home_page(message="For a new food, enter base amount, protein, carbs, and fat.")

    base_amount = float(base_amount_text)
    protein = float(protein_text)
    carbs = float(carbs_text)
    fat = float(fat_text)

    food_database[food_key] = {
        "base_amount": base_amount,
        "base_unit": "grams",
        "protein": protein,
        "carbs": carbs,
        "fat": fat
    }
    save_food_database(food_database)

    multiplier = quantity_consumed / base_amount

    scaled_protein = round(protein * multiplier, 1)
    scaled_carbs = round(carbs * multiplier, 1)
    scaled_fat = round(fat * multiplier, 1)
    calories = round((scaled_protein * 4) + (scaled_carbs * 4) + (scaled_fat * 9), 1)

    new_meal = {
        "food": food,
        "meal_type": meal_type,
        "quantity_consumed": quantity_consumed,
        "base_amount": base_amount,
        "protein": scaled_protein,
        "carbs": scaled_carbs,
        "fat": scaled_fat,
        "calories": calories
    }

    meals_data = load_meals()
    today = str(date.today())

    if today not in meals_data:
        meals_data[today] = []

    meals_data[today].append(new_meal)
    save_meals(meals_data)

    return build_home_page(message="Meal added successfully.")


if __name__ == "__main__":
    app.run(debug=True)