"""
Quick check of the hierarchy table structure
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("database/uksi.db")
if not DB_PATH.exists():
    DB_PATH = Path("data/uksi.db")

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

print("═" * 70)
print("HIERARCHY TABLE INSPECTION")
print("═" * 70)

# Show hierarchy table structure
print("\n📊 HIERARCHY TABLE STRUCTURE:")
print("─" * 70)
cursor.execute("PRAGMA table_info(hierarchy)")
columns = cursor.fetchall()
col_names = [col[1] for col in columns]

print(f"{'Column Name':<25} {'Type':<15}")
print("─" * 70)
for col in columns:
    print(f"{col[1]:<25} {col[2]:<15}")

# Sample records
print("\n🔍 SAMPLE RECORDS FROM HIERARCHY TABLE:")
print("─" * 70)
cursor.execute("SELECT * FROM hierarchy LIMIT 5")
rows = cursor.fetchall()

if rows:
    for row in rows:
        print("\nRecord:")
        for col_name, value in zip(col_names, row):
            print(f"  {col_name:<20} = {value}")
else:
    print("❌ No records in hierarchy table")

# Check if there's a record for Rutpela
print("\n🔍 HIERARCHY FOR Rutpela maculata:")
print("─" * 70)
cursor.execute("""
    SELECT h.* FROM hierarchy h
    JOIN taxa t ON h.tvk = t.tvk
    WHERE t.scientific_name = 'Rutpela maculata'
    LIMIT 1
""")
row = cursor.fetchone()

if row:
    for col_name, value in zip(col_names, row):
        print(f"  {col_name:<20} = {value}")
else:
    print("❌ No hierarchy record found")
    # Try just by TVK
    cursor.execute("SELECT * FROM hierarchy WHERE tvk = 'NBNSYS0000011024' LIMIT 1")
    row = cursor.fetchone()
    if row:
        print("\n✅ Found by TVK directly:")
        for col_name, value in zip(col_names, row):
            print(f"  {col_name:<20} = {value}")

# Count records
total = cursor.execute("SELECT COUNT(*) FROM hierarchy").fetchone()[0]
print(f"\n📈 Total records in hierarchy table: {total:,}")

conn.close()
print("\n" + "═" * 70)
