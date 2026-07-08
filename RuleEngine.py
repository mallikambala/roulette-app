from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "super_secret_key"


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

    def calc_confidence(self, current_pl):
        if current_pl >= 10000:
            return {"text": "Low confidence (house edge likely to catch up)", "level": 25}
        elif current_pl <= -15000:
            return {"text": "High confidence (likely recovery towards -₹2500)", "level": 85}
        else:
            return {"text": "Medium confidence", "level": 50}

    def process_number(self, number):
        dozen = self.get_dozen(number)

        if self.last_dozen is None:
            self.last_dozen = dozen
            self.highest_total = self.total_pl
            self.lowest_total = self.total_pl
            confidence = self.calc_confidence(self.total_pl)
            return {
                "number": number,
                "dozen": dozen,
                "bet": None,
                "pl": 0,
                "total": self.total_pl,
                "mode": self.mode,
                "next_bet": self.get_bet(dozen),
                "next_mode": self.mode,
                "reason": "First spin, setting up game.",
                "warning": None,
                "highest_total": self.highest_total,
                "lowest_total": self.lowest_total,
                "confidence_text": confidence["text"],
                "confidence_level": confidence["level"]
            }

        bet = self.get_bet(self.last_dozen)
        current_mode = self.mode

        if dozen in bet:
            pl = 2500
            self.total_pl += pl
            if self.last_dozen == dozen:
                self.mode = "Normal"
            reason = f"Win hit on dozen {dozen}, staying steady."
            self.win_streak += 1
            self.loss_streak = 0
            if self.win_streak >= 5:
                self.warning = f"⚠️ Win streak of {self.win_streak}! Consider stopping."
            else:
                self.warning = None
        else:
            pl = -5000
            self.total_pl += pl
            self.mode = "Recovery" if self.mode == "Normal" else "Normal"
            reason = f"Loss on dozen {dozen}, switching to {self.mode} mode."
            self.loss_streak += 1
            self.win_streak = 0
            if self.loss_streak >= 5:
                self.warning = f"⚠️ Loss streak of {self.loss_streak}! Consider stopping."
            else:
                self.warning = None

        self.last_dozen = dozen
        self.highest_total = max(self.highest_total, self.total_pl)
        self.lowest_total = min(self.lowest_total, self.total_pl)
        confidence = self.calc_confidence(self.total_pl)

        return {
            "number": number,
            "dozen": dozen,
            "bet": bet,
            "pl": pl,
            "total": self.total_pl,
            "mode": current_mode,
            "next_bet": self.get_bet(dozen),
            "next_mode": self.mode,
            "reason": reason,
            "warning": self.warning,
            "highest_total": self.highest_total,
            "lowest_total": self.lowest_total,
            "confidence_text": confidence["text"],
            "confidence_level": confidence["level"]
        }


# ✅ Roulette numbers definition
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
    if len(history) > 1:
        for i in range(1, len(history)):
            prev, curr = history[i - 1], history[i]
            mode_full = curr["mode"]

            dozen_display = f"{prev['dozen']} → {curr['dozen']}"
            bet_display = f"{curr['bet'][0]} & {curr['bet'][1]} ({mode_full})" if curr["bet"] else "-"

            if curr["pl"] > 0 and curr["bet"]:
                if curr['dozen'] == curr['bet'][0]:
                    bet_display = f"<span class='highlight'>{curr['bet'][0]}</span> & {curr['bet'][1]} ({mode_full})"
                elif curr['dozen'] == curr['bet'][1]:
                    bet_display = f"{curr['bet'][0]} & <span class='highlight'>{curr['bet'][1]}</span> ({mode_full})"
                dozen_display = f"{prev['dozen']} → <span class='highlight'>{curr['dozen']}</span>"

            if prev['dozen'] == curr['dozen']:
                dozen_display = f"<span class='highlight'>{prev['dozen']} → {curr['dozen']}</span>"

            rows.append({
                "numbers": f"<span class='sno'>{i}</span> {prev['number']} → {curr['number']}",
                "dozens": dozen_display,
                "bet": bet_display,
                "pl": curr['pl'],
                "total": curr['total'],
                "mode": mode_full,
                "warning": curr.get("warning"),
                "sno": i
            })
    return rows


@app.route("/", methods=["GET", "POST"])
def index():
    if "calc" not in session:
        session["calc"] = RoulettePLCalculator().__dict__
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
                           roulette_numbers=roulette_numbers)

@app.route("/reset", methods=["POST"])
def reset():
    session.clear()
    return redirect(url_for("index"))


@app.route("/undo", methods=["POST"])
def undo():
    if "history" in session and session["history"]:
        session["history"].pop()
        calc = RoulettePLCalculator()
        for entry in session["history"]:
            calc.process_number(entry["number"])
        session["calc"] = calc.__dict__
    return redirect(url_for("index"))


@app.route("/recalc/<int:start_row>", methods=["POST"])
def recalc(start_row):
    if "history" not in session or not session["history"]:
        return redirect(url_for("index"))

    sliced_history = session["history"][start_row-1:]
    calc = RoulettePLCalculator()
    new_history = []

    for entry in sliced_history:
        result = calc.process_number(entry["number"])
        new_history.append(result)

    session["calc"] = calc.__dict__
    session["history"] = new_history

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
