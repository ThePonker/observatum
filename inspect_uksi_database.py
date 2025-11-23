"""
UKSI Database Inspector
Quick script to check what's actually in the database
"""

import sqlite3
from pathlib import Path

# Path to UKSI database
DB_PATH = Path("database/uksi.db")

if not DB_PATH.exists():
    DB_PATH = Path("data/uksi.db")

if not DB_PATH.exists():
    print("❌ UKSI database not found!")
    print(f"   Looked in: database/uksi.db and data/uksi.db")
    exit(1)

print("═" * 70)
print(f"Inspecting UKSI Database: {DB_PATH}")
print("═" * 70)

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# 1. Show all tables
print("\n📋 TABLES IN DATABASE:")
print("─" * 70)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  • {table[0]}")

# 2. Show taxa table structure
print("\n📊 TAXA TABLE STRUCTURE:")
print("─" * 70)
cursor.execute("PRAGMA table_info(taxa)")
columns = cursor.fetchall()
print(f"{'Column Name':<25} {'Type':<15} {'Not Null':<10}")
print("─" * 70)
for col in columns:
    col_name = col[1]
    col_type = col[2]
    not_null = "YES" if col[3] else "NO"
    print(f"{col_name:<25} {col_type:<15} {not_null:<10}")

# 3. Get column names for querying
col_names = [col[1] for col in columns]

# 4. Sample record - Rutpela maculata
print("\n🔍 SAMPLE RECORD: Rutpela maculata")
print("═" * 70)
cursor.execute("SELECT * FROM taxa WHERE scientific_name LIKE 'Rutpela%' LIMIT 1")
row = cursor.fetchone()

if row:
    for col_name, value in zip(col_names, row):
        # Highlight important taxonomy fields
        marker = "🌳" if col_name.lower() in ['kingdom', 'phylum', 'class', 'order', 'family', 'genus'] else "  "
        print(f"{marker} {col_name:<25} = {value}")
else:
    print("❌ No Rutpela species found in database")

# 5. Another sample - Robin (common species)
print("\n🔍 SAMPLE RECORD: Robin (Erithacus rubecula)")
print("═" * 70)
cursor.execute("SELECT * FROM taxa WHERE scientific_name = 'Erithacus rubecula' LIMIT 1")
row = cursor.fetchone()

if row:
    for col_name, value in zip(col_names, row):
        marker = "🌳" if col_name.lower() in ['kingdom', 'phylum', 'class', 'order', 'family', 'genus'] else "  "
        print(f"{marker} {col_name:<25} = {value}")
else:
    print("❌ No Robin found in database")

# 6. Check how many records have taxonomy data
print("\n📈 TAXONOMY DATA COVERAGE:")
print("─" * 70)

taxonomy_fields = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus']
total_records = cursor.execute("SELECT COUNT(*) FROM taxa").fetchone()[0]
print(f"Total records: {total_records:,}")

for field in taxonomy_fields:
    if field in col_names:
        query = f"SELECT COUNT(*) FROM taxa WHERE {field} IS NOT NULL AND {field} != ''"
        count = cursor.execute(query).fetchone()[0]
        percentage = (count / total_records * 100) if total_records > 0 else 0
        print(f"  {field.capitalize():<15} {count:>8,} records ({percentage:>5.1f}%)")
    else:
        print(f"  {field.capitalize():<15} ⚠️  Column doesn't exist!")

conn.close()

print("\n" + "═" * 70)
print("✅ Inspection complete!")
print("═" * 70)
