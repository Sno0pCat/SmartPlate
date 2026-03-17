from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import json
import os
from datetime import date, timedelta

app = Flask(__name__)

MEALS_FILE = "data/meals.json"
FOOD_DATABASE_FILE = "data/food_database.json"
GOALS_FILE = "data/goals.json"
WEIGHTS_FILE = "data/weights.json"
UPLOAD_FOLDER = "uploads"
WATER_FILE = "data/water.json"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


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

def load_goals():
    try:
        with open(GOALS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"daily_calorie_goal": 2000}

def save_goals(goals_data):
    with open(GOALS_FILE, "w") as file:
        json.dump(goals_data, file, indent=4)

def load_weights():
    try:
        with open(WEIGHTS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_weights(weights_data):
    with open(WEIGHTS_FILE, "w") as file:
        json.dump(weights_data, file, indent=4)

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
        meal_type = meal.get("meal_type", "").strip().title()

        if meal_type == "Breakfast":
            breakfast_meals.append(meal)
        elif meal_type == "Lunch":
            lunch_meals.append(meal)
        elif meal_type == "Dinner":
            dinner_meals.append(meal)

    return breakfast_meals, lunch_meals, dinner_meals

def get_last_7_days_calories(meals_data):
    today = date.today()
    labels = []
    calories_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = str(day)

        labels.append(day_str)

        meals = meals_data.get(day_str, [])
        _, _, _, total_calories = get_daily_totals(meals)

        calories_data.append(total_calories)

    return labels, calories_data

def get_last_7_days_macros(meals_data):
    today = date.today()

    labels = []
    protein_data = []
    carbs_data = []
    fat_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = str(day)

        labels.append(day_str)

        meals = meals_data.get(day_str, [])
        total_protein, total_carbs, total_fat, _ = get_daily_totals(meals)

        protein_data.append(total_protein)
        carbs_data.append(total_carbs)
        fat_data.append(total_fat)

    return labels, protein_data, carbs_data, fat_data

def add_meal_indexes(meals):
    indexed_meals = []

    for index, meal in enumerate(meals):
        meal_copy = meal.copy()
        meal_copy["meal_index"] = index
        indexed_meals.append(meal_copy)

    return indexed_meals

def get_last_7_days_weights(weights_data):
    today = date.today()
    weight_labels = []
    weight_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = str(day)

        weight_labels.append(day_str)
        weight_data.append(weights_data.get(day_str, 0))

    return weight_labels, weight_data

def get_chart_range():
    chart_range = request.args.get("range", "7days")
    allowed_ranges = ["7days", "4weeks", "6months", "lastyear", "ytd"]

    if chart_range not in allowed_ranges:
        chart_range = "7days"

    return chart_range

def get_last_7_days_data(meals_data, weights_data):
    labels = []
    calories_data = []
    protein_data = []
    carbs_data = []
    fat_data = []
    weight_data = []

    today = date.today()

    for i in range(6, -1, -1):
        current_day = today - timedelta(days=i)
        day_str = str(current_day)

        labels.append(day_str)

        meals = meals_data.get(day_str, [])
        total_protein, total_carbs, total_fat, total_calories = get_daily_totals(meals)

        calories_data.append(total_calories)
        protein_data.append(total_protein)
        carbs_data.append(total_carbs)
        fat_data.append(total_fat)
        weight_data.append(weights_data.get(day_str, 0))

    return labels, calories_data, protein_data, carbs_data, fat_data, weight_data


def get_last_4_weeks_data(meals_data, weights_data):
    labels = []
    calories_data = []
    protein_data = []
    carbs_data = []
    fat_data = []
    weight_data = []

    today = date.today()

    for i in range(3, -1, -1):
        week_end = today - timedelta(days=i * 7)
        week_start = week_end - timedelta(days=6)

        label = f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}"
        labels.append(label)

        week_calories = 0
        week_protein = 0
        week_carbs = 0
        week_fat = 0
        latest_weight = 0

        for j in range(7):
            current_day = week_start + timedelta(days=j)
            day_str = str(current_day)

            meals = meals_data.get(day_str, [])
            total_protein, total_carbs, total_fat, total_calories = get_daily_totals(meals)

            week_calories += total_calories
            week_protein += total_protein
            week_carbs += total_carbs
            week_fat += total_fat

            if day_str in weights_data:
                latest_weight = weights_data[day_str]

        calories_data.append(round(week_calories, 1))
        protein_data.append(round(week_protein, 1))
        carbs_data.append(round(week_carbs, 1))
        fat_data.append(round(week_fat, 1))
        weight_data.append(latest_weight)

    return labels, calories_data, protein_data, carbs_data, fat_data, weight_data


def get_last_6_months_data(meals_data, weights_data):
    labels = []
    calories_data = []
    protein_data = []
    carbs_data = []
    fat_data = []
    weight_data = []

    today = date.today()
    current_year = today.year
    current_month = today.month

    months = []

    for i in range(5, -1, -1):
        month = current_month - i
        year = current_year

        while month <= 0:
            month += 12
            year -= 1

        months.append((year, month))

    for year, month in months:
        label = f"{year}-{str(month).zfill(2)}"
        labels.append(label)

        month_calories = 0
        month_protein = 0
        month_carbs = 0
        month_fat = 0
        latest_weight = 0

        for day_str, meals in meals_data.items():
            parts = day_str.split("-")
            meal_year = int(parts[0])
            meal_month = int(parts[1])

            if meal_year == year and meal_month == month:
                total_protein, total_carbs, total_fat, total_calories = get_daily_totals(meals)
                month_calories += total_calories
                month_protein += total_protein
                month_carbs += total_carbs
                month_fat += total_fat

        matching_weight_dates = []

        for day_str, weight in weights_data.items():
            parts = day_str.split("-")
            weight_year = int(parts[0])
            weight_month = int(parts[1])

            if weight_year == year and weight_month == month:
                matching_weight_dates.append(day_str)

        if matching_weight_dates:
            latest_date = max(matching_weight_dates)
            latest_weight = weights_data[latest_date]

        calories_data.append(round(month_calories, 1))
        protein_data.append(round(month_protein, 1))
        carbs_data.append(round(month_carbs, 1))
        fat_data.append(round(month_fat, 1))
        weight_data.append(latest_weight)

    return labels, calories_data, protein_data, carbs_data, fat_data, weight_data

def get_today_photo_filename():
    today = str(date.today())

    possible_extensions = ["jpg", "jpeg", "png", "webp"]

    for ext in possible_extensions:
        filename = f"{today}.{ext}"
        full_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        if os.path.exists(full_path):
            return filename

    return None

def get_uploaded_photos():
    photo_files = []

    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        return photo_files

    allowed_extensions = ["jpg", "jpeg", "png", "webp"]

    for filename in os.listdir(app.config["UPLOAD_FOLDER"]):
        lower_name = filename.lower()

        if "." not in lower_name:
            continue

        extension = lower_name.rsplit(".", 1)[1]

        if extension in allowed_extensions:
            photo_files.append(filename)

    photo_files.sort(reverse=True)
    return photo_files


def get_photo_for_date(selected_date):
    if not selected_date:
        return None

    allowed_extensions = ["jpg", "jpeg", "png", "webp"]

    for ext in allowed_extensions:
        filename = f"{selected_date}.{ext}"
        full_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        if os.path.exists(full_path):
            return filename

    return None

def load_progress_photos():
    try:
        with open("progress_photos.json", "r") as f:
            return json.load(f)
    except:
        return {}
    
def save_progress_photos(data):
    with open("progress_photos.json", "w") as f:
        json.dump(data, f, indent=4)


def get_uploaded_photo_dates():
    photo_files = get_uploaded_photos()
    dates = []

    for filename in photo_files:
        date_part = filename.rsplit(".", 1)[0]
        dates.append(date_part)

    return dates

def convert_to_grams(amount, unit):
    if unit == "g":
        return amount
    elif unit == "oz":
        return amount * 28.3495
    elif unit == "ml":
        return amount  
    else:
        return amount

def get_last_year_data(meals_data, weights_data):
    labels = []
    calories_data = []
    protein_data = []
    carbs_data = []
    fat_data = []
    weight_data = []

    today = date.today()
    current_year = today.year
    current_month = today.month

    months = []

    for i in range(11, -1, -1):
        month = current_month - i
        year = current_year

        while month <= 0:
            month += 12
            year -= 1

        months.append((year, month))

    for year, month in months:
        label = f"{year}-{str(month).zfill(2)}"
        labels.append(label)

        month_calories = 0
        month_protein = 0
        month_carbs = 0
        month_fat = 0
        latest_weight = 0

        for day_str, meals in meals_data.items():
            parts = day_str.split("-")
            meal_year = int(parts[0])
            meal_month = int(parts[1])

            if meal_year == year and meal_month == month:
                total_protein, total_carbs, total_fat, total_calories = get_daily_totals(meals)
                month_calories += total_calories
                month_protein += total_protein
                month_carbs += total_carbs
                month_fat += total_fat

        matching_weight_dates = []

        for day_str, weight in weights_data.items():
            parts = day_str.split("-")
            weight_year = int(parts[0])
            weight_month = int(parts[1])

            if weight_year == year and weight_month == month:
                matching_weight_dates.append(day_str)

        if matching_weight_dates:
            latest_date = max(matching_weight_dates)
            latest_weight = weights_data[latest_date]

        calories_data.append(round(month_calories, 1))
        protein_data.append(round(month_protein, 1))
        carbs_data.append(round(month_carbs, 1))
        fat_data.append(round(month_fat, 1))
        weight_data.append(latest_weight)

    return labels, calories_data, protein_data, carbs_data, fat_data, weight_data


def get_ytd_data(meals_data, weights_data):
    labels = []
    calories_data = []
    protein_data = []
    carbs_data = []
    fat_data = []
    weight_data = []

    today = date.today()
    current_year = today.year
    current_month = today.month

    for month in range(1, current_month + 1):
        label = f"{current_year}-{str(month).zfill(2)}"
        labels.append(label)

        month_calories = 0
        month_protein = 0
        month_carbs = 0
        month_fat = 0
        latest_weight = 0

        for day_str, meals in meals_data.items():
            parts = day_str.split("-")
            meal_year = int(parts[0])
            meal_month = int(parts[1])

            if meal_year == current_year and meal_month == month:
                total_protein, total_carbs, total_fat, total_calories = get_daily_totals(meals)
                month_calories += total_calories
                month_protein += total_protein
                month_carbs += total_carbs
                month_fat += total_fat

        matching_weight_dates = []

        for day_str, weight in weights_data.items():
            parts = day_str.split("-")
            weight_year = int(parts[0])
            weight_month = int(parts[1])

            if weight_year == current_year and weight_month == month:
                matching_weight_dates.append(day_str)

        if matching_weight_dates:
            latest_date = max(matching_weight_dates)
            latest_weight = weights_data[latest_date]

        calories_data.append(round(month_calories, 1))
        protein_data.append(round(month_protein, 1))
        carbs_data.append(round(month_carbs, 1))
        fat_data.append(round(month_fat, 1))
        weight_data.append(latest_weight)

    return labels, calories_data, protein_data, carbs_data, fat_data, weight_data

def build_home_page(
    message="",
    selected_food_name="",
    selected_food_data=None,
    edit_meal=None,
    edit_meal_index=None,
    selected_photo_date="",
    compare_date_1="",
    compare_date_2=""
):

    food_database = load_food_database()
    weights_data = load_weights()
    chart_range = get_chart_range()
    meals_data = load_meals()
    
    photo_dates = get_uploaded_photo_dates()

    if selected_photo_date == "":
        selected_photo_date = str(date.today())

    selected_photo = get_photo_for_date(selected_photo_date)
    today_photo = get_today_photo_filename()

    compare_photo_1 = get_photo_for_date(compare_date_1) if compare_date_1 else None
    compare_photo_2 = get_photo_for_date(compare_date_2) if compare_date_2 else None


    today = str(date.today())
    todays_meals = meals_data.get(today, [])
    indexed_meals = add_meal_indexes(todays_meals)

    breakfast_meals, lunch_meals, dinner_meals = split_meals_by_type(indexed_meals)
    total_protein, total_carbs, total_fat, total_calories = get_daily_totals(todays_meals)

    goals_data = load_goals()
    daily_calorie_goal = goals_data.get("daily_calorie_goal", 2000)
    calories_remaining = round(daily_calorie_goal - total_calories, 1)

    if chart_range == "7days":
        labels, calories_data, protein_data, carbs_data, fat_data, weight_data = get_last_7_days_data(meals_data, weights_data)
    elif chart_range == "4weeks":
        labels, calories_data, protein_data, carbs_data, fat_data, weight_data = get_last_4_weeks_data(meals_data, weights_data)
    elif chart_range == "6months":
        labels, calories_data, protein_data, carbs_data, fat_data, weight_data = get_last_6_months_data(meals_data, weights_data)
    elif chart_range == "lastyear":
        labels, calories_data, protein_data, carbs_data, fat_data, weight_data = get_last_year_data(meals_data, weights_data)
    elif chart_range == "ytd":
        labels, calories_data, protein_data, carbs_data, fat_data, weight_data = get_ytd_data(meals_data, weights_data)
    else:
        labels, calories_data, protein_data, carbs_data, fat_data, weight_data = get_last_7_days_data(meals_data, weights_data)

    macro_labels = labels
    weight_labels = labels

    latest_weight = weights_data.get(today, "")
    food_names = sorted(food_database.keys())


    return render_template(
        "index.html",
        today=today,
        total_protein=total_protein,
        total_carbs=total_carbs,
        total_fat=total_fat,
        total_calories=total_calories,
        macro_labels=macro_labels,
        protein_data=protein_data,
        carbs_data=carbs_data,
        fat_data=fat_data,
        breakfast_meals=breakfast_meals,
        lunch_meals=lunch_meals,
        dinner_meals=dinner_meals,
        message=message,
        food_names=food_names,
        selected_food_name=selected_food_name,
        selected_food_data=selected_food_data,
        daily_calorie_goal=daily_calorie_goal,
        calories_remaining=calories_remaining,
        labels=labels,
        edit_meal=edit_meal,
        edit_meal_index=edit_meal_index,
        weight_labels=weight_labels,
        weight_data=weight_data,
        today_photo=today_photo,
        photo_dates=photo_dates,
        selected_photo_date=selected_photo_date,
        selected_photo=selected_photo,
        compare_date_1=compare_date_1,
        compare_date_2=compare_date_2,
        compare_photo_1=compare_photo_1,
        compare_photo_2=compare_photo_2,
        chart_range=chart_range,
        calories_data=calories_data
    )

def get_selected_home_date():
    selected_date = request.args.get("date", "")

    if selected_date == "":
        return str(date.today())

    return selected_date

def get_shared_page_data(selected_date=None):
    meals_data = load_meals()
    food_database = load_food_database()
    weights_data = load_weights()
    water_data = load_water()

    today = str(date.today())
    if selected_date is None:
        selected_date = today

    todays_meals = meals_data.get(selected_date, [])
    indexed_meals = add_meal_indexes(todays_meals)
    water_count = water_data.get(selected_date, 0)
    water_goal = 8
    water_percent = round((water_count / water_goal) * 100, 1) if water_goal > 0 else 0

    breakfast_meals, lunch_meals, dinner_meals = split_meals_by_type(indexed_meals)
    total_protein, total_carbs, total_fat, total_calories = get_daily_totals(todays_meals)

    goals_data = load_goals()
    daily_calorie_goal = goals_data.get("daily_calorie_goal", 2000)
    calories_remaining = round(daily_calorie_goal - total_calories, 1)

    protein_goal = goals_data.get("protein_goal", 0)
    carbs_goal = goals_data.get("carbs_goal", 0)
    fat_goal = goals_data.get("fat_goal", 0)

    protein_remaining = round(protein_goal - total_protein, 1)
    carbs_remaining = round(carbs_goal - total_carbs, 1)
    fat_remaining = round(fat_goal - total_fat, 1)

    chart_range = get_chart_range()

    if chart_range == "7days":
        labels, calories_data, protein_data, carbs_data, fat_data, weight_data = get_last_7_days_data(meals_data, weights_data)
    elif chart_range == "4weeks":
        labels, calories_data, protein_data, carbs_data, fat_data, weight_data = get_last_4_weeks_data(meals_data, weights_data)
    elif chart_range == "6months":
        labels, calories_data, protein_data, carbs_data, fat_data, weight_data = get_last_6_months_data(meals_data, weights_data)
    elif chart_range == "lastyear":
        labels, calories_data, protein_data, carbs_data, fat_data, weight_data = get_last_year_data(meals_data, weights_data)
    elif chart_range == "ytd":
        labels, calories_data, protein_data, carbs_data, fat_data, weight_data = get_ytd_data(meals_data, weights_data)
    else:
        labels, calories_data, protein_data, carbs_data, fat_data, weight_data = get_last_7_days_data(meals_data, weights_data)

    macro_labels = labels
    weight_labels = labels

    latest_weight = weights_data.get(selected_date, "")
    food_names = sorted(food_database.keys())

    photo_dates = get_uploaded_photo_dates()
    selected_photo_date = selected_date
    selected_photo = get_photo_for_date(selected_photo_date)
    
    return {
        "today": today,
        "breakfast_meals": breakfast_meals,
        "lunch_meals": lunch_meals,
        "dinner_meals": dinner_meals,
        "total_protein": total_protein,
        "total_carbs": total_carbs,
        "total_fat": total_fat,
        "total_calories": total_calories,
        "daily_calorie_goal": daily_calorie_goal,
        "calories_remaining": calories_remaining,
        "chart_range": chart_range,
        "labels": labels,
        "calories_data": calories_data,
        "macro_labels": macro_labels,
        "protein_data": protein_data,
        "carbs_data": carbs_data,
        "fat_data": fat_data,
        "weight_labels": weight_labels,
        "weight_data": weight_data,
        "latest_weight": latest_weight,
        "food_names": food_names,
        "photo_dates": photo_dates,
        "selected_photo_date": selected_photo_date,
        "protein_goal": protein_goal,
        "carbs_goal": carbs_goal,
        "fat_goal": fat_goal,
        "protein_remaining": protein_remaining,
        "carbs_remaining": carbs_remaining,
        "fat_remaining": fat_remaining,
        "water_count": water_count,
        "water_goal": water_goal,
        "water_percent": water_percent,
        "selected_date": selected_date,
        "selected_photo": selected_photo
    }

def build_home_dashboard(message=""):
    selected_date = get_selected_home_date()
    page_data = get_shared_page_data(selected_date=selected_date)
    current_date_obj = date.fromisoformat(selected_date)
    prev_date = str(current_date_obj - timedelta(days=1))
    next_date = str(current_date_obj + timedelta(days=1))


    food_consumed = page_data["total_calories"]
    exercise_calories = 0
    remaining_calories = round(page_data["daily_calorie_goal"] - food_consumed + exercise_calories, 1)

    if page_data["daily_calorie_goal"] > 0:
        progress_percent = round((food_consumed / page_data["daily_calorie_goal"]) * 100, 1)
    else:
        progress_percent = 0

    progress_percent = max(0, min(progress_percent, 100))

    protein_goal = page_data.get("protein_goal", 0)
    carbs_goal = page_data.get("carbs_goal", 0)
    fat_goal = page_data.get("fat_goal", 0)

    protein_progress = 0
    carbs_progress = 0
    fat_progress = 0

    if protein_goal > 0:
        protein_progress = round((page_data["total_protein"] / protein_goal) * 100, 1)
    if carbs_goal > 0:
        carbs_progress = round((page_data["total_carbs"] / carbs_goal) * 100, 1)
    if fat_goal > 0:
        fat_progress = round((page_data["total_fat"] / fat_goal) * 100, 1)

    protein_progress = max(0, min(protein_progress, 100))
    carbs_progress = max(0, min(carbs_progress, 100))
    fat_progress = max(0, min(fat_progress, 100))

    return render_template(
        "home.html",
        message=message,
        food_consumed=food_consumed,
        exercise_calories=exercise_calories,
        remaining_calories=remaining_calories,
        progress_percent=progress_percent,
        protein_progress=protein_progress,
        carbs_progress=carbs_progress,
        fat_progress=fat_progress,
        prev_date=prev_date,
        next_date=next_date,
        **page_data
    )

def build_diary_page(message="", edit_meal=None, edit_meal_index=None):
    page_data = get_shared_page_data()
    return render_template(
        "diary.html",
        message=message,
        edit_meal=edit_meal,
        edit_meal_index=edit_meal_index,
        **page_data
    )

def build_log_meal_page(message=""):
    page_data = get_shared_page_data()
    return render_template("log_meal.html", message=message, **page_data)

def build_progress_page(message="", compare_date_1="", compare_date_2="", selected_photo_date=""):
    page_data = get_shared_page_data()

    if selected_photo_date == "":
        selected_photo_date = page_data.get("selected_photo_date", "")

    selected_photo = get_photo_for_date(selected_photo_date)
    compare_photo_1 = get_photo_for_date(compare_date_1) if compare_date_1 else None
    compare_photo_2 = get_photo_for_date(compare_date_2) if compare_date_2 else None

    page_data["selected_photo_date"] = selected_photo_date
    page_data["selected_photo"] = selected_photo
    page_data["compare_date_1"] = compare_date_1
    page_data["compare_date_2"] = compare_date_2
    page_data["compare_photo_1"] = compare_photo_1
    page_data["compare_photo_2"] = compare_photo_2

    return render_template(
        "progress.html",
        message=message,
        **page_data
    )

def build_charts_page(message=""):
    page_data = get_shared_page_data()

    return render_template(
        "charts.html",
        message=message,
        **page_data
    )

def build_weight_page(message=""):
    page_data = get_shared_page_data()
    return render_template(
        "weight.html",
        message=message,
        **page_data
    )

def calculate_goal_plan(goal_type, current_weight, weeks, workout_days):
    maintenance_calories = current_weight * 15

    if goal_type == "cut":
        target_calories = maintenance_calories - 300
    elif goal_type == "bulk":
        target_calories = maintenance_calories + 250
    else:
        target_calories = maintenance_calories

    if workout_days <= 2:
        target_calories -= 100
    elif workout_days >= 5:
        target_calories += 100

    protein_grams = current_weight * 1.0
    fat_grams = current_weight * 0.3

    protein_calories = protein_grams * 4
    fat_calories = fat_grams * 9

    remaining_calories = target_calories - protein_calories - fat_calories
    carbs_grams = remaining_calories / 4

    if carbs_grams < 0:
        carbs_grams = 0

    return {
        "target_calories": round(target_calories, 1),
        "protein_grams": round(protein_grams, 1),
        "fat_grams": round(fat_grams, 1),
        "carbs_grams": round(carbs_grams, 1),
        "weeks": weeks,
        "goal_type": goal_type,
        "workout_days": workout_days
    }

def build_goal_planner_page(message="", plan_result=None):
    page_data = get_shared_page_data()
    return render_template(
        "goal_planner.html",
        message=message,
        plan_result=plan_result,
        **page_data
    )

def load_water():
    try:
        with open(WATER_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_water(water_data):
    with open(WATER_FILE, "w") as file:
        json.dump(water_data, file, indent=4)


@app.route("/")
def home():
    return build_home_dashboard()


@app.route("/check_food", methods=["POST"])
def check_food():
    food = request.form["food"].strip()
    food_key = food.lower()
    food_database = load_food_database()

    if food_key in food_database:
        return build_home_page(
            message="Saved food found.",
            selected_food_name=food,
            selected_food_data=food_database[food_key]
        )
    else:
        return build_home_page(
            message="Food not found in saved database.",
            selected_food_name=food,
            selected_food_data=None
        )

@app.route("/set_goal", methods=["POST"])
def set_goal():
    daily_calorie_goal = float(request.form["daily_calorie_goal"])
    selected_date = request.form.get("selected_date", str(date.today()))

    goals_data = load_goals()
    goals_data["daily_calorie_goal"] = daily_calorie_goal

    if "protein_goal" not in goals_data:
        goals_data["protein_goal"] = 0
    if "carbs_goal" not in goals_data:
        goals_data["carbs_goal"] = 0
    if "fat_goal" not in goals_data:
        goals_data["fat_goal"] = 0

    save_goals(goals_data)

    return redirect(url_for("home", date=selected_date))

@app.route("/add_meal", methods=["POST"])
def add_meal():
    food = request.form["food"].strip()
    food_key = food.lower()
    meal_type = request.form["meal_type"].strip().title()
    quantity_input = float(request.form["quantity_consumed"])
    unit = request.form["unit"]

    quantity_consumed = convert_to_grams(quantity_input, unit)

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
            return build_log_meal_page(message="For a new food, enter base amount, protein, carbs, and fat.")

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
        "unit": unit,
        "original_quantity": quantity_input,
        "calories": calories
    }

    meals_data = load_meals()
    today = str(date.today())

    if today not in meals_data:
        meals_data[today] = []

    meals_data[today].append(new_meal)
    save_meals(meals_data)

    return build_log_meal_page(message="Meal added successfully.")

@app.route("/delete_meal", methods=["POST"])
def delete_meal():
    meal_index = int(request.form["meal_index"])

    meals_data = load_meals()
    today = str(date.today())
    todays_meals = meals_data.get(today, [])

    if 0 <= meal_index < len(todays_meals):
        todays_meals.pop(meal_index)

    meals_data[today] = todays_meals
    save_meals(meals_data)

    return build_diary_page(message="Meal deleted successfully.")

@app.route("/edit_meal", methods=["POST"])
def edit_meal():
    meal_index = int(request.form["meal_index"])

    meals_data = load_meals()
    today = str(date.today())
    todays_meals = meals_data.get(today, [])

    if 0 <= meal_index < len(todays_meals):
        meal_to_edit = todays_meals[meal_index]

        if "original_quantity" not in meal_to_edit:
            meal_to_edit["original_quantity"] = meal_to_edit.get("quantity_consumed", "")
        if "unit" not in meal_to_edit:
            meal_to_edit["unit"] = "g"

        return build_diary_page(
            message="Editing meal.",
            edit_meal=meal_to_edit,
            edit_meal_index=meal_index
        )

    return build_diary_page(message="Meal not found.")


@app.route("/update_meal", methods=["POST"])
def update_meal():
    meal_index = int(request.form["meal_index"])
    food = request.form["food"].strip()
    food_key = food.lower()
    meal_type = request.form["meal_type"].strip().title()

    quantity_input = float(request.form["quantity_consumed"])
    unit = request.form["unit"]
    quantity_consumed = convert_to_grams(quantity_input, unit)

    food_database = load_food_database()

    if food_key not in food_database:
        return build_diary_page(message="This food is not in the saved food database, so it cannot be edited here.")

    saved_food = food_database[food_key]
    base_amount = float(saved_food["base_amount"])
    protein = float(saved_food["protein"])
    carbs = float(saved_food["carbs"])
    fat = float(saved_food["fat"])

    multiplier = quantity_consumed / base_amount

    scaled_protein = round(protein * multiplier, 1)
    scaled_carbs = round(carbs * multiplier, 1)
    scaled_fat = round(fat * multiplier, 1)
    calories = round((scaled_protein * 4) + (scaled_carbs * 4) + (scaled_fat * 9), 1)

    updated_meal = {
        "food": food,
        "meal_type": meal_type,
        "quantity_consumed": quantity_consumed,
        "original_quantity": quantity_input,
        "unit": unit,
        "base_amount": base_amount,
        "protein": scaled_protein,
        "carbs": scaled_carbs,
        "fat": scaled_fat,
        "calories": calories
    }

    meals_data = load_meals()
    today = str(date.today())
    todays_meals = meals_data.get(today, [])

    if 0 <= meal_index < len(todays_meals):
        todays_meals[meal_index] = updated_meal

    meals_data[today] = todays_meals
    save_meals(meals_data)

    return build_diary_page(message="Meal updated successfully.")

@app.route("/save_weight", methods=["POST"])
def save_weight():
    weight = float(request.form["weight"])
    weight_date = request.form["weight_date"]

    weights_data = load_weights()
    weights_data[weight_date] = weight
    save_weights(weights_data)

    return build_weight_page(message="Weight saved successfully.")

@app.route("/upload_photo", methods=["POST"])
def upload_photo():
    if "progress_photo" not in request.files:
        return build_home_page(message="No file selected.")

    file = request.files["progress_photo"]

    if file.filename == "":
        return build_home_page(message="No file selected.")

    original_filename = file.filename.lower()

    if "." not in original_filename:
        return build_home_page(message="Invalid file type.")

    extension = original_filename.rsplit(".", 1)[1]

    allowed_extensions = ["jpg", "jpeg", "png", "webp"]

    if extension not in allowed_extensions:
        return build_home_page(message="Only JPG, JPEG, PNG, and WEBP files are allowed.")

    today = str(date.today())
    filename = f"{today}.{extension}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    for ext in allowed_extensions:
        old_file = os.path.join(app.config["UPLOAD_FOLDER"], f"{today}.{ext}")
        if os.path.exists(old_file):
            os.remove(old_file)

    file.save(save_path)

    return build_progress_page(
    message="Photo uploaded successfully.",
    selected_photo_date=today
)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/view_photo", methods=["GET"])
def view_photo():
    selected_photo_date = request.args.get("photo_date", "")
    return build_progress_page(selected_photo_date=selected_photo_date)

@app.route("/compare_photos_home", methods=["GET"])
def compare_photos_home():
    compare_date_1 = request.args.get("compare_date_1", "")
    compare_date_2 = request.args.get("compare_date_2", "")

    return build_progress_page(
        selected_photo_date=compare_date_1,
        compare_date_1=compare_date_1,
        compare_date_2=compare_date_2
    )

@app.route("/home")
def home_page():
    return build_home_dashboard()


@app.route("/diary")
def diary_page():
    return build_diary_page()


@app.route("/progress")
def progress_page():
    return build_progress_page()


@app.route("/charts")
def charts_page():
    return build_charts_page()


@app.route("/more")
def more_page():
    return render_template("more.html")

@app.route("/log-meal")
def log_meal_page():
    return build_log_meal_page()

@app.route("/weight")
def weight_page():
    return build_weight_page()

@app.route("/goal-planner")
def goal_planner_page():
    return build_goal_planner_page()


@app.route("/calculate-goal-plan", methods=["POST"])
def calculate_goal_plan_route():
    goal_type = request.form["goal_type"]
    current_weight = float(request.form["current_weight"])
    weeks = int(request.form["weeks"])
    workout_days = int(request.form["workout_days"])

    plan_result = calculate_goal_plan(goal_type, current_weight, weeks, workout_days)

    return build_goal_planner_page(
        message="Plan calculated successfully.",
        plan_result=plan_result
    )


@app.route("/apply_goal_calories", methods=["POST"])
def apply_goal_calories():
    target_calories = float(request.form["target_calories"])
    protein_grams = float(request.form["protein_grams"])
    fat_grams = float(request.form["fat_grams"])
    carbs_grams = float(request.form["carbs_grams"])

    goals_data = {
        "daily_calorie_goal": target_calories,
        "protein_goal": protein_grams,
        "carbs_goal": carbs_grams,
        "fat_goal": fat_grams
    }

    save_goals(goals_data)

    plan_result = {
        "target_calories": round(target_calories, 1),
        "protein_grams": protein_grams,
        "fat_grams": fat_grams,
        "carbs_grams": carbs_grams,
        "weeks": int(request.form["weeks"]),
        "goal_type": request.form["goal_type"],
        "workout_days": int(request.form["workout_days"])
    }

    return build_goal_planner_page(
        message="Recommended calories and macros applied.",
        plan_result=plan_result
    )

@app.route("/add_water", methods=["POST"])
def add_water():
    water_data = load_water()
    selected_date = request.form.get("selected_date", str(date.today()))

    current_glasses = water_data.get(selected_date, 0)

    if current_glasses >= 8:
        current_glasses = 0
    else:
        current_glasses += 1

    water_data[selected_date] = current_glasses
    save_water(water_data)

    return redirect(url_for("home", date=selected_date))

if __name__ == "__main__":
    app.run(debug=True)