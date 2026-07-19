import os
import random
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)
# Secure key using Render Environment Variables.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_fallback_secure_key_12345!")

class RoulettePLCalculator:
    def __init__(self, total_pl=0, mode="Normal", last_dozen=None,
                 win_streak=0, loss_streak=0, warning=None,
                 highest_total=0, lowest_total=0):
        self.total_pl = total_pl
        self.mode = mode
        self.last_dozen = last_dozen
        self.win_streak = win_streak
        self.loss_streak = loss_streak
        self.warning = warning
        self.highest_total = highest_total
        self.lowest_total = lowest_total
        self.zero_rule = "loss" # Locked permanently to standard

    def get_dozen(self, number):
        if number == 0:
            return 0
        elif 1 <= number <= 12: 
            return 1
        elif 13 <= number <= 24: 
            return 2
        elif 25 <= number <= 36: 
            return 3
        raise ValueError("Invalid roulette number")

    def get_bet(self, dozen):
        if dozen is None:
            return None
            
        if self.mode == "Normal":
            return [1, 2] if dozen == 1 else [2, 3] if dozen == 2 else [3, 1]
        else:  # Recovery Mode
            return [1, 3] if dozen == 1 else [2, 1] if dozen == 2 else [3, 2]

    def _generate_predictions(self, next_bet):
        """Generates 17 random numbers based on the next bet recommendations safely."""
        if not next_bet:
            return None
            
        d1, d2 = next_bet[0], next_bet[1]
        all_dozens = {1, 2, 3}
        remaining_dozen = list(all_dozens - {d1, d2})[0]
        
        dozen_ranges = {
            1: list(range(1, 13)),
            2: list(range(13, 25)),
            3: list(range(25, 37))
        }
        
        # Safe sampling fallback using min() to ensure it never crashes
        len1 = min(len(dozen_ranges[d1]), 7)
        len2 = min(len(dozen_ranges[d2]), 7)
        len3 = min(len(dozen_ranges[remaining_dozen]), 3)

        # We seed the random generator using the exact sequence of spun numbers to guarantee deterministic logic.
        seed_val = "seed_" + "_".join(str(n) for n in self.past_spins)
        random.seed(seed_val)

        pick1 = random.sample(dozen_ranges[d1], len1)
        pick2 = random.sample(dozen_ranges[d2], len2)
        pick3 = random.sample(dozen_ranges[remaining_dozen], len3)
        
        # Reset seed back to system entropy
        random.seed() 
        
        return sorted(pick1 + pick2 + pick3)

    def process_number(self, number):
        self.past_spins.append(number) # Track sequence
        dozen = self.get_dozen(number)
        
        if self.last_dozen is None:
            self.last_dozen = 1 if dozen == 0 else dozen
            self.highest_total = self.total_pl
            self.lowest_total = self.total_pl
            
            next_bet_val = self.get_bet(self.last_dozen)
            
            return {
                "number": number,
                "dozen": dozen,
                "bet": None,
                "pl": 0,
                "total": self.total_pl,
                "mode": self.mode,
                "next_bet": next_bet_val,
                "predicted_numbers": self._generate_predictions(next_bet_val),
                "next_mode": self.mode,
                "reason": "First spin, setting up game logic.",
                "warning": None,
                "highest_total": self.highest_total,
                "lowest_total": self.lowest_total
            }

        bet = self.get_bet(self.last_dozen)
        current_mode = self.mode

        if dozen != 0 and (dozen in bet):
            pl = 2500
            self.total_pl += pl
            if self.last_dozen == dozen:
                self.mode = "Normal"
            reason = f"Win hit on dozen {dozen} (Number {number}), staying steady."
            self.win_streak += 1
            self.loss_streak = 0
            if self.win_streak >= 5:
                self.warning = f"⚠️ Win streak of {self.win_streak}! Consider stopping."
            else:
                self.warning = None
                
            self.last_dozen = dozen
        else:
            pl = -5000
            self.total_pl += pl
            self.mode = "Recovery" if self.mode == "Normal" else "Normal"
            reason = f"Loss on {'Green Zero (0)' if dozen == 0 else f'dozen {dozen}'} (Number {number}). Switching to {self.mode} mode."
                
            self.loss_streak += 1
            self.win_streak = 0
            if self.loss_streak >= 5:
                self.warning = f"⚠️ Loss streak of {self.loss_streak}! Consider stopping."
            else:
                self.warning = None
                
            self.last_dozen = 1 if dozen == 0 else dozen

        self.highest_total = max(self.highest_total, self.total_pl)
        self.lowest_total = min(self.lowest_total, self.total_pl)
        
        next_bet_val = self.get_bet(self.last_dozen)

        return {
            "number": number,
            "dozen": dozen,
            "bet": bet,
            "pl": pl,
            "total": self.total_pl,
            "mode": current_mode,
            "next_bet": next_bet_val,
            "predicted_numbers": self._generate_predictions(next_bet_val),
            "next_mode": self.mode,
            "reason": reason,
            "warning": self.warning,
            "highest_total": self.highest_total,
            "lowest_total": self.lowest_total
        }

roulette_numbers = [
    {"num": 0, "color": "green"},
    {"num": 1, "color": "red"}, {"num": 2, "color": "black"}, {"num": 3, "color": "red"},
    {"num": 4, "color": "black"}, {"num": 5, "color": "red"}, {"num": 6, "color": "black"},
    {"num": 7, "color": "red"}, {"num": 8, "color": "black"}, {"num": 9, "color": "red"},
    {"num": 10, "color": "black"}, {"num": 11, "color": "black"}, {"num": 12, "color": "red"},
    {"num": 13, "color": "black"}, {"num": 14, "color": "red"}, {"num": 15, "color": "black"},
    {"num": 16, "color": "red"}, {"num": 17, "color": "black"}, {"num": 18, "color": "red"},
    {"num": 19, "color": "red"}, {"num": 20, "color": "black"}, {"num": 21, "color": "red"},
    {"num": 22, "color": "black"}, {"num": 23, "color": "red"}, {"num": 24, "color": "black"},
    {"num": 25, "color": "red"}, {"num": 26, "color": "black"}, {"num": 27, "color": "red"},
    {"num": 28, "color": "black"}, {"num": 29, "color": "black"}, {"num": 30, "color": "red"},
    {"num": 31, "color": "black"}, {"num": 32, "color": "red"}, {"num": 33, "color": "black"},
    {"num": 34, "color": "red"}, {"num": 35, "color": "black"}, {"num": 36, "color": "red"},
]

# --- JSON API ENDPOINT FOR SPA ---
@app.route("/process_click", methods=["POST"])
def process_click():
    session.pop("history", None)
    session.pop("calc", None)

    numbers = session.get("numbers", [])
    action = request.form.get("action")
    
    if action == "spin":
        number = int(request.form["number"])
        numbers.append(number)
    elif action == "undo":
        if numbers:
            numbers.pop()
    elif action == "reset":
        session.clear() 
        numbers = []
    
    session["numbers"] = numbers
    
    calc = RoulettePLCalculator()
    calc.past_spins = [] # Rebuild helper list cleanly
    history = []
    for num in numbers:
        history.append(calc.process_number(num))
    
    return {
        "history": history
    }

# --- Load initial layout route ---
@app.route("/")
def index():
    session.pop("history", None)
    session.pop("calc", None)

    numbers = session.get("numbers", [])
    calc = RoulettePLCalculator()
    calc.past_spins = []
    history = []
    for num in numbers:
        history.append(calc.process_number(num))

    return render_template("index.html",
                           initial_history=history,
                           roulette_numbers=roulette_numbers)

# Recalc truncates the numbers list
@app.route("/recalc/<int:start_row>", methods=["POST"])
def recalc(start_row):
    session.pop("history", None)
    session.pop("calc", None)

    numbers = session.get("numbers", [])
    
    if start_row > 0 and start_row <= len(numbers):
        session["numbers"] = numbers[start_row-1:]
        
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
