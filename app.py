from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
import os

app = Flask(__name__)
CORS(app)

# 讀取 Render 環境變數
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

engine = create_engine(DATABASE_URL, future=True)

@app.route("/api/facilities", methods=["GET"])
def get_facilities():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT name, lat, lon, drive_time_s, walk_time_s, "group", "layer"
            FROM drive_time_results
        """)).mappings().all()
    return jsonify([dict(r) for r in rows])

@app.route("/api/drive_time", methods=["GET"])
def get_drive_time():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if lat is None or lon is None:
        return jsonify({"error":"lat/lon required"}), 400
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT name, lat, lon, drive_time_s, walk_time_s,
                   ST_Distance(geom::geography,
                   ST_SetSRID(ST_MakePoint(:lon,:lat),4326)::geography) AS dist_m
            FROM drive_time_results
            ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:lon,:lat),4326)
            LIMIT 1;
        """), {"lat": lat, "lon": lon}).mappings().first()
    return jsonify(dict(row))

if __name__ == "__main__":
    app.run(debug=True)
