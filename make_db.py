import sqlite3

rows = [
    ("Algorithms", 8, 1, 5.5),
    ("Databases", 6, 1, 5.0),
    ("Machine Learning", 8, 2, 5.75),
    ("Operating Systems", 8, 2, 5.25),
    ("Probability", 6, 1, 6.0),
    ("Computer Networks", 6, 2, 4.75),
    ("Software Engineering", 7, 3, 5.5),
    ("Distributed Systems", 8, 3, 5.0),
]

conn = sqlite3.connect("courses.db")
conn.execute("DROP TABLE IF EXISTS courses")
conn.execute(
    "CREATE TABLE courses (id INTEGER PRIMARY KEY, name TEXT, ects INTEGER, semester INTEGER, grade REAL)"
)
conn.executemany("INSERT INTO courses (name, ects, semester, grade) VALUES (?, ?, ?, ?)", rows)
conn.commit()
conn.close()
print("courses.db created with", len(rows), "rows")
