import sqlite3

DB_NAME = "weather.db"

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

# エリアテーブル
cur.execute("""
CREATE TABLE IF NOT EXISTS areas (
    office_code TEXT PRIMARY KEY,
    name TEXT NOT NULL
)
""")

# 天気予報テーブル
cur.execute("""
CREATE TABLE IF NOT EXISTS weather_forecast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    office_code TEXT,
    date TEXT,
    weather TEXT,
    temp_min INTEGER,
    temp_max INTEGER,
    UNIQUE (office_code, date),
    FOREIGN KEY (office_code) REFERENCES areas(office_code)
)
""")


conn.commit()
conn.close()

print("DB作成完了")
