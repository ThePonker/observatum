"""
Diagnose taxonomy issues for specific species
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("database/uksi.db")
if not DB_PATH.exists():
    DB_PATH = Path("data/uksi.db")

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def trace_hierarchy(scientific_name):
    """Trace the parent hierarchy for a species"""
    print("═" * 70)
    print(f"TRACING HIERARCHY: {scientific_name}")
    print("═" * 70)
    
    # Get initial record
    cursor.execute("SELECT * FROM taxa WHERE scientific_name = ?", (scientific_name,))
    species = cursor.fetchone()
    
    if not species:
        print(f"❌ Species not found: {scientific_name}")
        return
    
    print(f"\n✅ Found species:")
    print(f"   TVK: {species['tvk']}")
    print(f"   Name: {species['scientific_name']}")
    print(f"   Rank: {species['rank']}")
    
    # Check hierarchy table for parent
    cursor.execute("SELECT * FROM hierarchy WHERE tvk = ?", (species['tvk'],))
    hier_row = cursor.fetchone()
    
    if hier_row:
        print(f"\n✅ Found in hierarchy table:")
        print(f"   Parent TVK: {hier_row['parent_tvk']}")
    else:
        print(f"\n❌ NOT in hierarchy table!")
        print(f"   This species has no parent relationship stored.")
        return
    
    # Trace up the parent chain
    print(f"\n📊 PARENT CHAIN:")
    print("─" * 70)
    
    current_tvk = hier_row['parent_tvk']
    depth = 0
    visited = set()
    
    while current_tvk and depth < 20:
        if current_tvk in visited:
            print(f"⚠️  Circular reference detected!")
            break
        visited.add(current_tvk)
        
        # Get parent info
        cursor.execute("SELECT * FROM taxa WHERE tvk = ?", (current_tvk,))
        parent = cursor.fetchone()
        
        if not parent:
            print(f"❌ Parent TVK {current_tvk} not found in taxa table!")
            break
        
        indent = "  " * depth
        marker = "🌳" if parent['rank'].lower() in ['kingdom', 'phylum', 'class', 'order', 'family', 'genus'] else "  "
        print(f"{indent}{marker} {parent['rank']}: {parent['scientific_name']} (TVK: {parent['tvk']})")
        
        # Get next parent
        cursor.execute("SELECT parent_tvk FROM hierarchy WHERE tvk = ?", (current_tvk,))
        hier = cursor.fetchone()
        
        if hier and hier['parent_tvk']:
            current_tvk = hier['parent_tvk']
        else:
            if parent['rank'].lower() != 'kingdom':
                print(f"{indent}   ⚠️  Chain ends here (not at Kingdom)")
            else:
                print(f"{indent}   ✅ Reached Kingdom!")
            break
        
        depth += 1
    
    print("─" * 70)

# Test species
print("\n" + "═" * 70)
print("TESTING SPECIES WITH ISSUES")
print("═" * 70)

test_species = [
    "Turdus merula",  # Blackbird - not working
    "Erithacus rubecula",  # Robin - working
    "Rutpela maculata",  # Your beetle - was not working earlier
]

for species_name in test_species:
    trace_hierarchy(species_name)
    print("\n")

conn.close()

print("═" * 70)
print("DIAGNOSIS COMPLETE")
print("═" * 70)