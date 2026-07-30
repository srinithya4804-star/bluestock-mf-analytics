"""
Bluestock Capstone Project I - Mutual Fund Analytics
Day 2 - Run all queries in queries.sql against bluestock_mf.db and print results
"""

import sqlite3

DB_PATH = "bluestock_mf.db"
QUERIES_PATH = "queries.sql"


def main():
    conn = sqlite3.connect(DB_PATH)

    with open(QUERIES_PATH, "r") as f:
        sql_script = f.read()

    # Split on semicolons, drop empty/comment-only chunks
    raw_queries = sql_script.split(";")
    queries = []
    for chunk in raw_queries:
        lines = [line for line in chunk.splitlines() if line.strip() and not line.strip().startswith("--")]
        if lines:
            queries.append("\n".join(lines))

    for i, query in enumerate(queries, start=1):
        print("=" * 80)
        print(f"QUERY {i}")
        print("=" * 80)
        try:
            cursor = conn.execute(query)
            cols = [d[0] for d in cursor.description]
            print(cols)
            rows = cursor.fetchall()
            for row in rows[:10]:
                print(row)
            print(f"({len(rows)} total row(s), showing up to 10)\n")
        except Exception as e:
            print(f"Error running query {i}: {e}\n")

    conn.close()


if __name__ == "__main__":
    main()
