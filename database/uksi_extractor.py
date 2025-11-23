"""
UKSI Database Extractor for Observatum FV - V5 FIXED
==========================================
Extracts species data from UKSI.mdb Access database into uksi.db SQLite database.

This version uses the OFFICIAL Nameserver approach from the NHM guide:
- Links common names to ALL TVKs via RECOMMENDED_TAXON_VERSION_KEY
- Uses self-join pattern from official documentation
- Correctly handles multiple TVKs per species

Critical Discovery from Official Guide:
"The Nameserver can be joined to itself and so you can report on related names,
even if you do not know that your TVK is the recommended scientific name"

Author: Observatum Development Team
Date: 22 November 2025
Version: 5 (Fixed based on NHM Nameserver Guide)
"""

import pyodbc
import sqlite3
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_uksi_database(db_path: Path):
    """
    Create uksi.db with proper schema.
    
    Tables:
    - taxa: Scientific names with TAXON_VERSION_KEY
    - common_names: English common names linked via NAMESERVER
    - synonyms: Old scientific names linked via NAMESERVER
    - hierarchy: Parent-child relationships from ORGANISM_MASTER
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Taxa table - scientific names only
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS taxa (
            tvk TEXT PRIMARY KEY,
            scientific_name TEXT NOT NULL,
            rank TEXT NOT NULL,
            parent_tvk TEXT,
            kingdom TEXT,
            phylum TEXT,
            class TEXT,
            "order" TEXT,
            family TEXT,
            genus TEXT
        )
    """)
    
    # Common names table - linked via NAMESERVER
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS common_names (
            common_name TEXT NOT NULL,
            tvk TEXT NOT NULL,
            PRIMARY KEY (common_name, tvk),
            FOREIGN KEY (tvk) REFERENCES taxa(tvk)
        )
    """)
    
    # Synonyms table - old scientific names
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS synonyms (
            synonym TEXT NOT NULL,
            tvk TEXT NOT NULL,
            PRIMARY KEY (synonym, tvk),
            FOREIGN KEY (tvk) REFERENCES taxa(tvk)
        )
    """)
    
    # Hierarchy table - parent-child relationships
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hierarchy (
            tvk TEXT PRIMARY KEY,
            parent_tvk TEXT,
            FOREIGN KEY (tvk) REFERENCES taxa(tvk)
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_taxa_scientific ON taxa(scientific_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_common_name ON common_names(common_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_common_tvk ON common_names(tvk)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_synonym ON synonyms(synonym)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_synonym_tvk ON synonyms(tvk)")
    
    conn.commit()
    conn.close()
    logger.info("Created uksi.db with V5-compatible schema")


def extract_scientific_names(access_cur, sqlite_conn):
    """
    Extract scientific names using TAXON_VERSION_KEY.
    
    Uses TAXON_VERSION table (not TAXON_LIST_ITEM) to get the
    correct TVKs that match what NAMESERVER expects.
    """
    logger.info("Extracting scientific names...")
    
    # Query scientific names with TAXON_VERSION_KEY
    # TAXON_NAME_TYPE_KEY = 'NBNSYS0000000001' means scientific name
    query = """
        SELECT T_VER.TAXON_VERSION_KEY, T.ITEM_NAME, TR.LONG_NAME
        FROM ((TAXON_VERSION AS T_VER
        INNER JOIN TAXON AS T ON T_VER.TAXON_KEY = T.TAXON_KEY)
        INNER JOIN TAXON_RANK AS TR ON T_VER.TAXON_RANK_KEY = TR.TAXON_RANK_KEY)
        WHERE T.TAXON_NAME_TYPE_KEY = 'NBNSYS0000000001'
    """
    
    access_cur.execute(query)
    taxa = access_cur.fetchall()
    
    logger.info(f"Found {len(taxa):,} scientific names")
    logger.info("Writing to uksi.db...")
    
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.executemany(
        "INSERT OR IGNORE INTO taxa (tvk, scientific_name, rank) VALUES (?, ?, ?)",
        [(row[0], row[1], row[2]) for row in taxa]
    )
    sqlite_conn.commit()
    
    logger.info(f"✅ Imported {len(taxa):,} scientific names")
    return len(taxa)


def extract_common_names_and_synonyms(access_cur, sqlite_conn):
    """
    Extract common names and synonyms via NAMESERVER table.
    
    OFFICIAL APPROACH from NHM Nameserver Guide (page 7):
    "The Nameserver can be joined to itself and so you can report on related names,
    even if you do not know that your TVK is the recommended scientific name"
    
    The Problem:
    - "Blackbird" is linked to TVK NHMSYS0000530674 (recommended)
    - But "Turdus merula" might have TVK NBNSYS0000000082 (synonym)  
    - These are DIFFERENT TVKs for the SAME species!
    
    The Solution:
    - Build a mapping of RECOMMENDED_TVK -> ALL TVKs that map to it
    - Link each common name to ALL TVKs in that group
    - This is the official NBN approach!
    """
    logger.info("Extracting common names and synonyms via NAMESERVER...")
    logger.info("Using official NBN self-join approach...")
    
    # STEP 1: Build TVK groups (recommended_tvk -> all tvks that map to it)
    logger.info("Building TVK mapping from NAMESERVER...")
    mapping_query = """
        SELECT INPUT_TAXON_VERSION_KEY, RECOMMENDED_TAXON_VERSION_KEY
        FROM NAMESERVER
    """
    access_cur.execute(mapping_query)
    mappings = access_cur.fetchall()
    
    # Create dict: recommended_tvk -> set of all tvks
    tvk_groups = {}
    for input_tvk, recommended_tvk in mappings:
        if recommended_tvk not in tvk_groups:
            tvk_groups[recommended_tvk] = set()
        tvk_groups[recommended_tvk].add(input_tvk)
        tvk_groups[recommended_tvk].add(recommended_tvk)
    
    logger.info(f"Found {len(tvk_groups):,} species groups with {len(mappings):,} TVK mappings")
    
    # STEP 2: Extract all names
    logger.info("Extracting names from TAXON table...")
    query = """
        SELECT T.ITEM_NAME, NS.RECOMMENDED_TAXON_VERSION_KEY, T.TAXON_NAME_TYPE_KEY, T.LANGUAGE
        FROM ((TAXON AS T
        INNER JOIN TAXON_VERSION AS TV ON T.TAXON_KEY = TV.TAXON_KEY)
        INNER JOIN NAMESERVER AS NS ON TV.TAXON_VERSION_KEY = NS.INPUT_TAXON_VERSION_KEY)
    """
    
    access_cur.execute(query)
    all_names = access_cur.fetchall()
    
    logger.info(f"Found {len(all_names):,} names via NAMESERVER")
    
    # Welsh common name patterns
    welsh_patterns = [
        'wyf', 'ych', 'wys', 'ddw', 'fyw', 'wen', 'mwy', 'alch',
        'ydd', 'wyd', 'awd', 'wch', 'gwn', 'gwy',
        ' dd', ' ff', ' ll', ' ch', ' th', ' ph',
        'dd ', 'ff ', 'll ', 'ch ', 'th ', 'ph ',
        'bach', 'mawr', 'goch', 'fach', 'fawr', 'glas', 'du',
        'wen', 'wyn', 'werdd', 'felen', 'aderyn'
    ]
    
    # STEP 3: Link names to ALL TVKs in their group
    common_names_to_insert = []
    synonyms_to_insert = []
    
    for name, recommended_tvk, name_type_key, language in all_names:
        # Get ALL TVKs for this species
        all_tvks_for_species = tvk_groups.get(recommended_tvk, {recommended_tvk})
        
        if name_type_key == 'NBNSYS0000000002':  # Common name
            # Filter Welsh names (keep only English)
            if language and language.lower() == 'en':
                # Double-check it's not Welsh by pattern matching
                name_lower = name.lower()
                is_welsh = any(pattern in name_lower for pattern in welsh_patterns)
                if not is_welsh:
                    # Link this common name to ALL TVKs in the group!
                    for tvk in all_tvks_for_species:
                        common_names_to_insert.append((name, tvk))
        else:  # Synonym
            # Link this synonym to ALL TVKs in the group!
            for tvk in all_tvks_for_species:
                synonyms_to_insert.append((name, tvk))
    
    logger.info(f"Linked common names to {len(common_names_to_insert):,} TVK pairs")
    logger.info(f"Linked synonyms to {len(synonyms_to_insert):,} TVK pairs")
    logger.info("Writing to uksi.db...")
    
    sqlite_cur = sqlite_conn.cursor()
    
    # Insert common names
    sqlite_cur.executemany(
        "INSERT OR IGNORE INTO common_names (common_name, tvk) VALUES (?, ?)",
        common_names_to_insert
    )
    
    # Insert synonyms  
    sqlite_cur.executemany(
        "INSERT OR IGNORE INTO synonyms (synonym, tvk) VALUES (?, ?)",
        synonyms_to_insert
    )
    
    sqlite_conn.commit()
    
    # Count unique common names
    sqlite_cur.execute("SELECT COUNT(DISTINCT common_name) FROM common_names")
    unique_common = sqlite_cur.fetchone()[0]
    
    sqlite_cur.execute("SELECT COUNT(DISTINCT synonym) FROM synonyms")
    unique_synonyms = sqlite_cur.fetchone()[0]
    
    logger.info(f"✅ Imported {unique_common:,} unique common names")
    logger.info(f"✅ Imported {unique_synonyms:,} unique synonyms")
    
    return unique_common, unique_synonyms


def extract_hierarchy(access_cur, sqlite_conn):
    """
    Extract taxonomic hierarchy from ORGANISM_MASTER.
    
    Uses TAXON_VERSION_KEY for parent-child relationships.
    """
    logger.info("Extracting taxonomic hierarchy...")
    
    query = """
        SELECT TAXON_VERSION_KEY, PARENT_TVK 
        FROM ORGANISM_MASTER
    """
    
    access_cur.execute(query)
    hierarchy = access_cur.fetchall()
    
    logger.info(f"Found {len(hierarchy):,} parent-child relationships")
    logger.info("Writing to uksi.db...")
    
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.executemany(
        "INSERT OR IGNORE INTO hierarchy (tvk, parent_tvk) VALUES (?, ?)",
        [(row[0], row[1]) for row in hierarchy]
    )
    sqlite_conn.commit()
    
    logger.info(f"✅ Imported {len(hierarchy):,} hierarchy links")
    return len(hierarchy)


def main():
    """
    Main extraction function.
    
    Uses V5 approach based on official NHM Nameserver guide:
    1. TAXON_VERSION_KEY for TVKs
    2. NAMESERVER self-join to link names to ALL TVKs
    3. ORGANISM_MASTER for hierarchy
    """
    print("=" * 70)
    print("UKSI EXTRACTOR V5 - Official Nameserver Guide Approach")
    print("=" * 70)
    
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    access_db_path = project_root / 'data' / 'UKSI.mdb'
    sqlite_db_path = script_dir / 'uksi.db'
    
    # Check if UKSI.mdb exists
    if not access_db_path.exists():
        print(f"\n❌ ERROR: UKSI.mdb not found at {access_db_path}")
        print("\nPlease:")
        print("1. Locate your UKSI.mdb file")
        print("2. Place it in the data/ directory")
        print("3. Run this script again")
        return False
    
    print(f"\n📂 Source: {access_db_path}")
    print(f"📊 Size: {access_db_path.stat().st_size / (1024*1024):.1f} MB")
    print(f"💾 Target: {sqlite_db_path}")
    print("\n" + "=" * 70)
    
    # Create SQLite database
    print("\n[1/4] Creating uksi.db with V5 schema...")
    create_uksi_database(sqlite_db_path)
    
    # Connect to Access database
    print("\n[2/4] Connecting to UKSI.mdb...")
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        rf'DBQ={str(access_db_path)};'
    )
    
    try:
        access_conn = pyodbc.connect(conn_str)
        access_conn.setdecoding(pyodbc.SQL_CHAR, encoding='latin-1')
        access_conn.setdecoding(pyodbc.SQL_WCHAR, encoding='latin-1')
        access_cur = access_conn.cursor()
        logger.info("✅ Connected to UKSI.mdb")
        
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(str(sqlite_db_path))
        
        # Extract data
        print("\n[3/4] Extracting data using V5 approach...")
        print("  → Scientific names (TAXON_VERSION_KEY)...")
        taxa_count = extract_scientific_names(access_cur, sqlite_conn)
        
        print("  → Common names & synonyms (NAMESERVER self-join)...")
        common_count, synonym_count = extract_common_names_and_synonyms(access_cur, sqlite_conn)
        
        print("  → Hierarchy (ORGANISM_MASTER)...")
        hierarchy_count = extract_hierarchy(access_cur, sqlite_conn)
        
        # Final statistics
        print("\n[4/4] Extraction complete!")
        print("\n" + "=" * 70)
        print("UKSI DATABASE CREATED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\n✅ Scientific names:  {taxa_count:,}")
        print(f"✅ Common names:     {common_count:,} unique (English only)")
        print(f"✅ Synonyms:         {synonym_count:,} unique")
        print(f"✅ Hierarchy links:  {hierarchy_count:,}")
        
        # Database size
        db_size_mb = sqlite_db_path.stat().st_size / (1024 * 1024)
        print(f"\n📊 Database size: {db_size_mb:.1f} MB")
        print(f"📂 Location: {sqlite_db_path}")
        
        print("\n" + "=" * 70)
        print("KEY IMPROVEMENTS IN V5:")
        print("=" * 70)
        print("  ✅ Uses official NBN Nameserver self-join approach")
        print("  ✅ Links common names to ALL TVKs (not just recommended)")
        print("  ✅ Handles NBNSYS, NHMSYS, and other TVK prefixes")
        print("  ✅ Based on NHM Species Dictionary Guide documentation")
        print("  ✅ Common names should now appear for ANY TVK variant!")
        print("\n" + "=" * 70)
        
        # Cleanup
        access_conn.close()
        sqlite_conn.close()
        
        return True
        
    except pyodbc.Error as ex:
        print(f"\n❌ DATABASE ERROR: {ex}")
        print("\nPossible causes:")
        print("  - Microsoft Access Driver not installed")
        print("  - UKSI.mdb file is corrupted")
        print("  - 32/64-bit mismatch")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n")
    success = main()
    
    if success:
        print("\n✅ EXTRACTION COMPLETED SUCCESSFULLY!")
        print("\nNEXT STEPS:")
        print("1. Copy uksi.db to data/ folder:")
        print("   Move-Item database\\uksi.db data\\uksi.db")
        print("2. Copy to database/ folder too (for compatibility):")
        print("   Copy-Item data\\uksi.db database\\uksi.db")
        print("3. Test species search - common names should now appear!")
        print("4. Try searching 'Blackbird', 'Turdus merula', or 'NBNSYS0000000082'")
        print("\n")
    else:
        print("\n❌ Extraction failed - please resolve errors above")
        print("\n")
