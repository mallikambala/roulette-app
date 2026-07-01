from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

class RoulettePLCalculator:
    def __init__(self):
        self.total_pl = 0
        self.mode = "Normal"
        self.last_dozen = None

    def get_dozen(self, number):
        if 0 <= number <= 12: return 1
        elif 13 <= number <= 24: return 2
        elif 25 <= number <= 36: return 3
        raise ValueError("Invalid roulette number")

    def get_bet(self, dozen):
        if self.mode == "Normal":
            return [1, 2] if dozen == 1 else [2, 3] if dozen == 2 else [3, 1]
        else:  # Recovery
            return [1, 3] if dozen == 1 else [2, 1] if dozen == 2 else [3, 2]

    def process_number(self, number):
        dozen = self.get_dozen(number)

        if self.last_dozen is None:
            self.last_dozen = dozen
            return {
                "number": number,
                "dozen": dozen,
                "bet": None,
                "pl": 0,
                "total": self.total_pl,
                "mode": self.mode,
                "next_bet": self.get_bet(dozen)
            }

        bet = self.get_bet(self.last_dozen)
        current_mode = self.mode  # capture mode at time of bet

        if dozen in bet:
            pl = 2500
            self.total_pl += pl
            if self.last_dozen == dozen:
                self.mode = "Normal"
        else:
            pl = -5000
            self.total_pl += pl
            self.mode = "Recovery" if self.mode == "Normal" else "Normal"

        self.last_dozen = dozen
        return {
            "number": number,
            "dozen": dozen,
            "bet": bet,
            "pl": pl,
            "total": self.total_pl,
            "mode": current_mode,          # row shows mode at time of bet
            "next_bet": self.get_bet(dozen) # prediction for upcoming row
        }

calc = RoulettePLCalculator()
calc_history = []

# Roulette table layout with colors
roulette_numbers = [
    {"num":0,"color":"green"},
    {"num":1,"color":"red"},{"num":2,"color":"black"},{"num":3,"color":"red"},
    {"num":4,"color":"black"},{"num":5,"color":"red"},{"num":6,"color":"black"},
    {"num":7,"color":"red"},{"num":8,"color":"black"},{"num":9,"color":"red"},
    {"num":10,"color":"black"},{"num":11,"color":"black"},{"num":12,"color":"red"},
    {"num":13,"color":"black"},{"num":14,"color":"red"},{"num":15,"color":"black"},
    {"num":16,"color":"red"},{"num":17,"color":"black"},{"num":18,"color":"red"},
    {"num":19,"color":"red"},{"num":20,"color":"black"},{"num":21,"color":"red"},
    {"num":22,"color":"black"},{"num":23,"color":"red"},{"num":24,"color":"black"},
    {"num":25,"color":"red"},{"num":26,"color":"black"},{"num":27,"color":"red"},
    {"num":28,"color":"black"},{"num":29,"color":"black"},{"num":30,"color":"red"},
    {"num":31,"color":"black"},{"num":32,"color":"red"},{"num":33,"color":"black"},
    {"num":34,"color":"red"},{"num":35,"color":"black"},{"num":36,"color":"red"},
]

def build_table_rows():
    rows = []
    if len(calc_history) > 1:
        for i in range(1, len(calc_history)):
            prev, curr = calc_history[i-1], calc_history[i]

            mode_full = curr["mode"]

            dozen_display = f"{prev['dozen']} → {curr['dozen']}"
            bet_display = f"{curr['bet'][0]} & {curr['bet'][1]} ({mode_full})"

            if curr["pl"] > 0:
                if curr['dozen'] == curr['bet'][0]:
                    bet_display = f"<span class='highlight'>{curr['bet'][0]}</span> & {curr['bet'][1]} ({mode_full})"
                elif curr['dozen'] == curr['bet'][1]:
                    bet_display = f"{curr['bet'][0]} & <span class='highlight'>{curr['bet'][1]}</span> ({mode_full})"
                dozen_display = f"{prev['dozen']} → <span class='highlight'>{curr['dozen']}</span>"

            rows.append({
                "numbers": f"{prev['number']} → {curr['number']}",
                "dozens": dozen_display,
                "bet": bet_display,
                "pl": curr['pl'],
                "total": curr['total'],
                "mode": mode_full
            })
    return rows

@app.route("/", methods=["GET", "POST"])
def index():
    global calc_history
    if request.method == "POST" and "number" in request.form:
        number = int(request.form["number"])
        calc_history.append(calc.process_number(number))

    return render_template("index.html",
                           table_rows=build_table_rows(),
                           calc_history=calc_history,
                           roulette_numbers=roulette_numbers)

@app.route("/reset", methods=["POST"])
def reset():
    global calc, calc_history
    calc, calc_history = RoulettePLCalculator(), []
    return redirect(url_for("index"))

@app.route("/undo", methods=["POST"])
def undo():
    global calc, calc_history
    if calc_history:
        calc_history.pop()
        calc = RoulettePLCalculator()
        for entry in calc_history:
            calc.process_number(entry["number"])
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
