import os

from flask import Flask, jsonify, render_template

import adhan
import bvg
import facility
import mawaqit
import screen
import weather

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(_ROOT, "frontend", "templates"),
    static_folder=os.path.join(_ROOT, "frontend", "static"),
)


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/prayer")
def api_prayer():
    try:
        return jsonify(mawaqit.snapshot())
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/weather")
def api_weather():
    try:
        return jsonify(weather.snapshot())
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/transit")
def api_transit():
    try:
        return jsonify(bvg.snapshot())
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/facility")
def api_facility():
    try:
        return jsonify(facility.snapshot())
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/test-adhan", methods=["GET", "POST"])
def api_test_adhan():
    adhan.play_now()
    return jsonify({"ok": True, "playing": "adhan.mp3"})


def _start_background_jobs():
    adhan.start()
    screen.start()


_start_background_jobs()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
