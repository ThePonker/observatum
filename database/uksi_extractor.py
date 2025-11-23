"""
UKSI Database Extractor for Observatum FV - V6 FIXED
==========================================
Extracts species data from UKSI.mdb Access database into uksi.db SQLite database.

KEY FIX: Uses TAXON_LIST_ITEM table with PARENT field for hierarchy!

Database Structure Discovery:
- TAXON_LIST_ITEM: Main table with TAXON_LIST_ITEM_KEY, PARENT field, TAXON_VERSION_KEY
- ORGANISM_MASTER: Has scientific names, linked via TAXON_VERSION_KEY  
- NAMESERVER: Links common names to recommended TVKs

The Fix:
1. Use TAXON_LIST_ITEM_KEY as the primary TVK (not TAXON_VERSION_KEY)
2. Get hierarchy from TAXON_LIST_ITEM.PARENT field
3. Join to ORGANISM_MASTER for scientific names via TAXON_VERSION_KEY
4. Link common names via NAMESERVER

Author: Observatum Development Team
Date: 24 November 2025
Version: 6 (Fixed hierarchy extraction)
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
    - taxa: Scientific names with TAXON_LIST_ITEM_KEY as TVK
    - common_names: English common names
    - synonyms: Alternative scientific names
    - hierarchy: Parent-child relationships from TAXON_LIST_ITEM.PARENT
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Taxa table - use TAXON_LIST_ITEM_KEY as TVK
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS taxa (
            tvk TEXT PRIMARY KEY,
            scientific_name TEXT NOT NULL,
            rank TEXT NOT NULL,
            taxon_version_key TEXT
        )
    """)
    
    # Common names table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS common_names (
            common_name TEXT NOT NULL,
            tvk TEXT NOT NULL,
            PRIMARY KEY (common_name, tvk),
            FOREIGN KEY (tvk) REFERENCES taxa(tvk)
        )
    """)
    
    # Synonyms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS synonyms (
            synonym TEXT NOT NULL,
            tvk TEXT NOT NULL,
            PRIMARY KEY (synonym, tvk),
            FOREIGN KEY (tvk) REFERENCES taxa(tvk)
        )
    """)
    
    # Hierarchy table - from TAXON_LIST_ITEM.PARENT
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hierarchy (
            tvk TEXT PRIMARY KEY,
            parent_tvk TEXT,
            FOREIGN KEY (tvk) REFERENCES taxa(tvk)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_taxa_scientific ON taxa(scientific_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_taxa_tvkey ON taxa(taxon_version_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_common_name ON common_names(common_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_common_tvk ON common_names(tvk)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_synonym ON synonyms(synonym)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hierarchy_parent ON hierarchy(parent_tvk)")
    
    conn.commit()
    conn.close()
    logger.info("✅ Created uksi.db with V6 schema")


def extract_taxa(access_cur, sqlite_conn):
    """
    Extract taxa from TAXON_LIST_ITEM table.
    
    Uses:
    - TAXON_LIST_ITEM_KEY as the TVK (primary identifier)
    - Joins to TAXON_VERSION -> TAXON for scientific name
    - Joins to TAXON_RANK for rank name
    """
    logger.info("Extracting taxa from TAXON_LIST_ITEM...")
    
    # Get scientific names from TAXON table via TAXON_VERSION
    # TAXON_NAME_TYPE_KEY = 'NBNSYS0000000001' means scientific name
    query = """
        SELECT 
            TLI.TAXON_LIST_ITEM_KEY,
            TLI.TAXON_VERSION_KEY,
            T.ITEM_NAME,
            TR.LONG_NAME
        FROM (((TAXON_LIST_ITEM AS TLI
        INNER JOIN TAXON_VERSION AS TV ON TLI.TAXON_VERSION_KEY = TV.TAXON_VERSION_KEY)
        INNER JOIN TAXON AS T ON TV.TAXON_KEY = T.TAXON_KEY)
        INNER JOIN TAXON_RANK AS TR ON TV.TAXON_RANK_KEY = TR.TAXON_RANK_KEY)
        WHERE T.TAXON_NAME_TYPE_KEY = 'NBNSYS0000000001'
    """
    
    access_cur.execute(query)
    taxa = access_cur.fetchall()
    
    logger.info(f"Found {len(taxa):,} taxa records")
    logger.info("Writing to uksi.db...")
    
    sqlite_cur = sqlite_conn.cursor()
    
    # Insert with TAXON_LIST_ITEM_KEY as TVK
    for row in taxa:
        tli_key = row[0]  # TAXON_LIST_ITEM_KEY
        tv_key = row[1]   # TAXON_VERSION_KEY
        sci_name = row[2] # ITEM_NAME (scientific name)
        rank = row[3]     # LONG_NAME (rank name)
        
        if sci_name and rank:
            sqlite_cur.execute(
                "INSERT OR IGNORE INTO taxa (tvk, scientific_name, rank, taxon_version_key) VALUES (?, ?, ?, ?)",
                (tli_key, sci_name, rank, tv_key)
            )
    
    sqlite_conn.commit()
    
    actual_count = sqlite_cur.execute("SELECT COUNT(*) FROM taxa").fetchone()[0]
    logger.info(f"✅ Imported {actual_count:,} taxa")
    return actual_count


def extract_hierarchy(access_cur, sqlite_conn):
    """
    Extract hierarchy from TAXON_LIST_ITEM.PARENT field.
    
    This is the KEY FIX - uses PARENT field from TAXON_LIST_ITEM!
    """
    logger.info("Extracting hierarchy from TAXON_LIST_ITEM.PARENT...")
    
    query = """
        SELECT TAXON_LIST_ITEM_KEY, PARENT
        FROM TAXON_LIST_ITEM
        WHERE PARENT IS NOT NULL
    """
    
    access_cur.execute(query)
    hierarchy = access_cur.fetchall()
    
    logger.info(f"Found {len(hierarchy):,} parent-child relationships")
    logger.info("Writing to uksi.db...")
    
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.executemany(
        "INSERT OR IGNORE INTO hierarchy (tvk, parent_tvk) VALUES (?, ?)",
        [(row[0], row[1]) for row in hierarchy if row[1]]
    )
    sqlite_conn.commit()
    
    actual_count = sqlite_cur.execute("SELECT COUNT(*) FROM hierarchy").fetchone()[0]
    logger.info(f"✅ Imported {actual_count:,} hierarchy links")
    return actual_count


def extract_common_names(access_cur, sqlite_conn):
    """
    Extract common names from TAXON table via NAMESERVER.
    
    Strategy:
    1. Get common names linked to TAXON_VERSION_KEYs via NAMESERVER
    2. Map TAXON_VERSION_KEY -> TAXON_LIST_ITEM_KEY
    3. Insert with TAXON_LIST_ITEM_KEY as the TVK
    """
    logger.info("Extracting common names...")
    
    # STEP 1: Build mapping from TAXON_VERSION_KEY to TAXON_LIST_ITEM_KEY
    logger.info("Building TAXON_VERSION_KEY -> TAXON_LIST_ITEM_KEY mapping...")
    
    mapping_query = """
        SELECT TAXON_VERSION_KEY, TAXON_LIST_ITEM_KEY
        FROM TAXON_LIST_ITEM
        WHERE TAXON_VERSION_KEY IS NOT NULL
    """
    
    access_cur.execute(mapping_query)
    tv_to_tli = {}
    for row in access_cur.fetchall():
        tv_key = row[0]
        tli_key = row[1]
        if tv_key not in tv_to_tli:
            tv_to_tli[tv_key] = []
        tv_to_tli[tv_key].append(tli_key)
    
    logger.info(f"Found {len(tv_to_tli):,} TAXON_VERSION_KEYs")
    
    # STEP 2: Get common names from TAXON table
    logger.info("Extracting common names from TAXON...")
    
    # TAXON_NAME_TYPE_KEY = 'NBNSYS0000000002' means common name
    # LANGUAGE = 'en' means English
    query = """
        SELECT DISTINCT T.ITEM_NAME, NS.RECOMMENDED_TAXON_VERSION_KEY
        FROM (TAXON AS T
        INNER JOIN TAXON_VERSION AS TV ON T.TAXON_KEY = TV.TAXON_KEY)
        INNER JOIN NAMESERVER AS NS ON TV.TAXON_VERSION_KEY = NS.INPUT_TAXON_VERSION_KEY
        WHERE T.TAXON_NAME_TYPE_KEY = 'NBNSYS0000000002'
        AND T.LANGUAGE = 'en'
    """
    
    access_cur.execute(query)
    common_names_data = access_cur.fetchall()
    
    logger.info(f"Found {len(common_names_data):,} common name records")
    logger.info("Mapping to TAXON_LIST_ITEM_KEYs and writing to uksi.db...")
    
    # STEP 3: Map to TAXON_LIST_ITEM_KEYs and insert
    sqlite_cur = sqlite_conn.cursor()
    inserted = 0
    
    for common_name, recommended_tv_key in common_names_data:
        if recommended_tv_key in tv_to_tli:
            # Insert for each TAXON_LIST_ITEM_KEY that maps to this TAXON_VERSION_KEY
            for tli_key in tv_to_tli[recommended_tv_key]:
                try:
                    sqlite_cur.execute(
                        "INSERT OR IGNORE INTO common_names (common_name, tvk) VALUES (?, ?)",
                        (common_name, tli_key)
                    )
                    inserted += 1
                except Exception as e:
                    logger.debug(f"Error inserting common name: {e}")
    
    sqlite_conn.commit()
    
    actual_count = sqlite_cur.execute("SELECT COUNT(*) FROM common_names").fetchone()[0]
    logger.info(f"✅ Imported {actual_count:,} common name links")
    return actual_count


def main():
    """
    Main extraction function.
    
    V6 - Fixed to use TAXON_LIST_ITEM properly:
    1. Extract taxa from TAXON_LIST_ITEM (join to ORGANISM_MASTER for names)
    2. Extract hierarchy from TAXON_LIST_ITEM.PARENT
    3. Extract common names via NAMESERVER, mapped to TAXON_LIST_ITEM_KEYs
    """
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent if script_dir.name == 'database' else script_dir
    
    # UKSI.mdb location
    mdb_path = project_root / "data" / "UKSI.mdb"
    
    # uksi.db output location
    uksi_db_path = project_root / "data" / "uksi.db"
    
    logger.info("=" * 70)
    logger.info("UKSI EXTRACTOR V6 - FIXED HIERARCHY")
    logger.info("=" * 70)
    logger.info(f"Source: {mdb_path}")
    logger.info(f"Output: {uksi_db_path}")
    logger.info("")
    
    # Check source exists
    if not mdb_path.exists():
        logger.error(f"❌ UKSI.mdb not found at: {mdb_path}")
        return
    
    # Remove old database if exists
    if uksi_db_path.exists():
        logger.info("Removing old uksi.db...")
        os.remove(uksi_db_path)
    
    # Create new database
    logger.info("Creating uksi.db schema...")
    create_uksi_database(uksi_db_path)
    
    # Connect to Access database
    logger.info("Connecting to UKSI.mdb...")
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        f'DBQ={mdb_path};'
    )
    
    try:
        access_conn = pyodbc.connect(conn_str)
        access_cur = access_conn.cursor()
        
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(str(uksi_db_path))
        
        logger.info("✅ Connected to both databases")
        logger.info("")
        
        # Extract data
        logger.info("STEP 1: Extracting taxa...")
        taxa_count = extract_taxa(access_cur, sqlite_conn)
        logger.info("")
        
        logger.info("STEP 2: Extracting hierarchy...")
        hierarchy_count = extract_hierarchy(access_cur, sqlite_conn)
        logger.info("")
        
        logger.info("STEP 3: Extracting common names...")
        common_count = extract_common_names(access_cur, sqlite_conn)
        logger.info("")
        
        # Summary
        logger.info("=" * 70)
        logger.info("EXTRACTION COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"Taxa: {taxa_count:,}")
        logger.info(f"Hierarchy links: {hierarchy_count:,}")
        logger.info(f"Common names: {common_count:,}")
        logger.info("")
        logger.info(f"✅ Database created: {uksi_db_path}")
        logger.info("=" * 70)
        
        # Close connections
        sqlite_conn.close()
        access_conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()