import os
import random
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)
# Secure key using Render Environment Variables.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_fallback_secure_key_12345!")

class RoulettePLCalculator:
    def __init__(self, total_pl=0, mode="Normal", last_dozen=None,
                 win_streak=0, loss_streak=0, warning=None,
                 highest_total=0, lowest_total=0, zero_rule="loss"):
        self.total_pl = total_pl
        self.mode = mode
        self.last_dozen = last_dozen
        self.win_streak = win_streak
        self.loss_streak = loss_streak
        self.warning = warning
        self.highest_total = highest_total
        self.lowest_total = lowest_total
        self.zero_rule = zero_rule

    def get_dozen(self, number):
        if number == 0:
            return 1 if self.zero_rule == "dozen1" else 0
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
        """Generates 17 random numbers based on the next bet recommendations."""
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
        
        # 7 from first rec, 7 from second rec, 3 from the remaining (total 17)
        pick1 = random.sample(dozen_ranges[d1], 7)
        pick2 = random.sample(dozen_ranges[d2], 7)
        pick3 = random.sample(dozen_ranges[remaining_dozen], 3)
        
        return sorted(pick1 + pick2 + pick3)

    def process_number(self, number):
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

def build_table_rows(history):
    rows = []
    miss_streak = 0
    
    if len(history) > 1:
        for i in range(1, len(history)):
            prev, curr = history[i - 1], history[i]
            mode_full = curr["mode"]
            
            prev_dozen = prev['dozen']
            curr_dozen = curr['dozen']
            dozen_display = f"{prev_dozen} → {curr_dozen}"
            
            if curr["bet"]:
                bet_display = f"Dozen {curr['bet'][0]} & {curr['bet'][1]} ({mode_full})"
            else:
                bet_display = "No Action (Push)"
                
            if curr["pl"] > 0 and curr["bet"]:
                if curr['dozen'] == curr['bet'][0]:
                    bet_display = f"<span class='highlight'>Dozen {curr['bet'][0]}</span> & {curr['bet'][1]} ({mode_full})"
                elif curr['dozen'] == curr['bet'][1]:
                    bet_display = f"{curr['bet'][0]} & <span class='highlight'>Dozen {curr['bet'][1]}</span> ({mode_full})"
                dozen_display = f"{prev_dozen} → <span class='highlight'>{curr_dozen}</span>"
                
            if prev['dozen'] == curr['dozen']:
                dozen_display = f"<span class='highlight'>{prev_dozen} → {curr_dozen}</span>"

            # Number prediction matching logic for the table
            predicted_nums = prev.get("predicted_numbers")
            pred_html = ""
            if predicted_nums:
                formatted_nums = []
                is_hit = False
                for n in predicted_nums:
                    if n == curr['number']:
                        formatted_nums.append(f"<span class='pred-hit'>{n}</span>")
                        is_hit = True
                    else:
                        formatted_nums.append(str(n))
                        
                if is_hit:
                    miss_streak = 0
                else:
                    miss_streak += 1

                pred_html = f"<div class='small-preds'>{', '.join(formatted_nums)}</div>"
                if miss_streak >= 3:
                    pred_html += f"<span class='miss-warning'>⚠️ Miss Streak {miss_streak}!</span>"
            else:
                pred_html = "<span class='small-preds'>-</span>"
                miss_streak = 0
                
            rows.append({
                "numbers": f"<span class='sno'>{i}</span> {prev['number']} → {curr['number']}",
                "dozens": dozen_display,
                "bet": bet_display,
                "predictions": pred_html, 
                "pl": curr['pl'],
                "total": curr['total'],
                "mode": mode_full,
                "warning": curr.get("warning"),
                "sno": i
            })
    return rows

def calculate_prediction_stats(history):
    """Calculates hits, misses, hit percentage, and current/max streaks."""
    hits = 0
    misses = 0
    curr_hit_streak = 0
    curr_miss_streak = 0
    max_hit_streak = 0
    max_miss_streak = 0
    
    if len(history) > 1:
        for i in range(1, len(history)):
            prev = history[i - 1]
            curr = history[i]
            preds = prev.get("predicted_numbers")
            if preds:
                if curr["number"] in preds:
                    hits += 1
                    curr_hit_streak += 1
                    curr_miss_streak = 0
                    max_hit_streak = max(max_hit_streak, curr_hit_streak)
                else:
                    misses += 1
                    curr_miss_streak += 1
                    curr_hit_streak = 0
                    max_miss_streak = max(max_miss_streak, curr_miss_streak)
                    
    total = hits + misses
    rate = round((hits / total * 100), 1) if total > 0 else 0.0
    return {
        "hits": hits, 
        "misses": misses, 
        "total": total, 
        "rate": rate,
        "curr_miss_streak": curr_miss_streak,
        "curr_hit_streak": curr_hit_streak,
        "max_hit_streak": max_hit_streak,
        "max_miss_streak": max_miss_streak
    }

@app.route("/", methods=["GET", "POST"])
def index():
    if "zero_rule" not in session:
        session["zero_rule"] = "loss"
    if "calc" not in session:
        session["calc"] = RoulettePLCalculator(zero_rule=session["zero_rule"]).__dict__
        session["history"] = []
        
    calc = RoulettePLCalculator(**session["calc"])
    history = session["history"]
    
    if request.method == "POST" and "number" in request.form:
        number = int(request.form["number"])
        result = calc.process_number(number)
        history.append(result)
        session["calc"] = calc.__dict__
        session["history"] = history
        
    return render_template("index.html",
                           table_rows=build_table_rows(history),
                           calc_history=history,
                           roulette_numbers=roulette_numbers,
                           zero_rule=session["zero_rule"],
                           pred_stats=calculate_prediction_stats(history))

@app.route("/set_zero_rule", methods=["POST"])
def set_zero_rule():
    new_rule = request.form.get("zero_rule", "loss")
    session["zero_rule"] = new_rule
    if "history" in session and session["history"]:
        calc = RoulettePLCalculator(zero_rule=new_rule)
        new_history = []
        for entry in session["history"]:
            result = calc.process_number(entry["number"])
            new_history.append(result)
        session["calc"] = calc.__dict__
        session["history"] = new_history
    elif "calc" in session:
        session["calc"]["zero_rule"] = new_rule
    return redirect(url_for("index"))

@app.route("/reset", methods=["POST"])
def reset():
    current_rule = session.get("zero_rule", "loss")
    session.clear()
    session["zero_rule"] = current_rule 
    return redirect(url_for("index"))

@app.route("/undo", methods=["POST"])
def undo():
    if "history" in session and session["history"]:
        session["history"].pop()
        calc = RoulettePLCalculator(zero_rule=session.get("zero_rule", "loss"))
        for entry in session["history"]:
            calc.process_number(entry["number"])
        session["calc"] = calc.__dict__
    return redirect(url_for("index"))

@app.route("/recalc/<int:start_row>", methods=["POST"])
def recalc(start_row):
    if "history" not in session or not session["history"]:
        return redirect(url_for("index"))
        
    sliced_history = session["history"][:start_row-1]
    calc = RoulettePLCalculator(zero_rule=session.get("zero_rule", "loss"))
    new_history = []
    
    for entry in sliced_history:
        result = calc.process_number(entry["number"])
        new_history.append(result)
        
    session["calc"] = calc.__dict__
    session["history"] = new_history
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
