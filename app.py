import json
import datetime
from flask import Flask, request
import requests

TOKEN = "8505621358:AAG77jUhKuNoQUTwGPfJMT6qNftIKS6kx2o"  # <-- Вставь сюда токен
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"

app = Flask(__name__)
DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def calculate_salary(lines):
    return 240 * 14 + 3.1 * lines

def get_period_dates():
    today = datetime.date.today()
    year = today.year
    month = today.month
    if today.day >= 27:
        start = datetime.date(year, month, 27)
        end_month = month + 1 if month < 12 else 1
        end_year = year if month < 12 else year + 1
        end = datetime.date(end_year, end_month, 26)
    else:
        end = datetime.date(year, month, 26)
        start_month = month - 1 if month > 1 else 12
        start_year = year if month > 1 else year - 1
        start = datetime.date(start_year, start_month, 27)
    return start, end

def get_summary():
    data = load_data()
    start, end = get_period_dates()
    total_lines = 0
    total_salary = 0
    total_shifts = 0
    for date_str, info in data.items():
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        if start <= date <= end:
            total_shifts += 1
            total_lines += info["lines"]
            total_salary += info["salary"]
    return {
        "start": start,
        "end": end,
        "shifts": total_shifts,
        "lines": total_lines,
        "hours": total_shifts * 14,
        "salary": total_salary,
        "avg": total_salary // total_shifts if total_shifts > 0 else 0
    }

def send_message(chat_id, text):
    requests.post(BASE_URL + "sendMessage", data={"chat_id": chat_id, "text": text})

@app.route("/", methods=["POST"])
def main():
    data = request.get_json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        if text.startswith("/смена"):
            try:
                parts = text.split()
                lines = int(parts[1])
                today = datetime.date.today().strftime("%Y-%m-%d")
                salary = calculate_salary(lines)
                db = load_data()
                db[today] = {"hours": 14, "lines": lines, "salary": salary}
                save_data(db)
                send_message(chat_id, f"Смена сохранена!\nСтрок: {lines}\nЗарплата: {salary:.0f} ₽")
            except:
                send_message(chat_id, "Бро, введи так: /смена 1520")
        elif text == "/итог":
            s = get_summary()
            msg = (
                f"Период: {s['start']} — {s['end']}\n\n"
                f"Смен: {s['shifts']}\n"
                f"Всего строк: {s['lines']}\n"
                f"Всего часов: {s['hours']}\n"
                f"Зарплата: {s['salary']} ₽\n"
                f"Средняя за смену: {s['avg']} ₽"
            )
            send_message(chat_id, msg)
        else:
            send_message(chat_id, "Команды:\n/смена 1520\n/итог")
    return {"ok": True}

if name == "__main__":
    app.run(port=5000)