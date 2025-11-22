"""
UKSI Extractor for Observatum
Extracts taxonomic data from UKSI.mdb and creates streamlined uksi.db

This script:
1. Connects to UKSI.mdb (Microsoft Access database)
2. Extracts taxa, common names (English only), and synonyms
3. Filters out Welsh language names
4. Builds taxonomy hierarchy
5. Creates optimized SQLite database (uksi.db)

Usage:
    python database/uksi_extractor.py

Requirements:
    - UKSI.mdb in data/ directory (799MB)
    - pyodbc installed
    - Microsoft Access ODBC driver installed
"""

import pyodbc
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Welsh language patterns to filter out
WELSH_PATTERNS = ['mwy', 'alch', 'ych', 'dd ', 'll ', 'ch', 'ff', 'rh']

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
UKSI_MDB_PATH = PROJECT_ROOT / 'data' / 'UKSI.mdb'
UKSI_DB_PATH = PROJECT_ROOT / 'database' / 'uksi.db'


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_progress(message: str, end='\n'):
    """Print a progress message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", end=end, flush=True)


def is_welsh_name(name: str) -> bool:
    """
    Check if a name contains Welsh language patterns
    
    Args:
        name: Name to check
        
    Returns:
        True if name appears to be Welsh
    """
    if not name:
        return False
    name_lower = name.lower()
    return any(pattern in name_lower for pattern in WELSH_PATTERNS)


def connect_to_uksi() -> pyodbc.Connection:
    """
    Connect to UKSI.mdb Access database
    
    Returns:
        Database connection
        
    Raises:
        FileNotFoundError: If UKSI.mdb not found
        pyodbc.Error: If connection fails
    """
    print_section("STEP 1: Connecting to UKSI.mdb")
    
    if not UKSI_MDB_PATH.exists():
        raise FileNotFoundError(
            f"UKSI.mdb not found at: {UKSI_MDB_PATH}\n"
            f"Please place UKSI.mdb in the data/ directory"
        )
    
    print_progress(f"Database location: {UKSI_MDB_PATH}")
    print_progress("Attempting connection...")
    
    # Connection string for Access database
    conn_str = (
        r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
        f'DBQ={UKSI_MDB_PATH};'
    )
    
    try:
        conn = pyodbc.connect(conn_str)
        print_progress("✅ Connected successfully!")
        return conn
    except pyodbc.Error as e:
        print_progress(f"❌ Connection failed: {e}")
        raise


def inspect_uksi_structure(conn: pyodbc.Connection):
    """
    Inspect UKSI database structure
    
    Args:
        conn: Database connection
    """
    print_section("STEP 2: Inspecting Database Structure")
    
    cursor = conn.cursor()
    
    # Get all tables
    print_progress("Fetching table list...")
    tables = []
    for table in cursor.tables(tableType='TABLE'):
        table_name = table.table_name
        # Skip system tables
        if not table_name.startswith('MSys'):
            tables.append(table_name)
    
    print_progress(f"Found {len(tables)} tables:")
    for table in sorted(tables):
        print(f"  - {table}")
    
    # Examine key tables
    key_tables = ['NAMESERVER', 'TAXON_LIST_ITEM', 'TAXON_VERSION', 'TAXON']
    
    for table_name in key_tables:
        if table_name in tables:
            print_progress(f"\nExamining {table_name} structure:")
            try:
                cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
                columns = [column[0] for column in cursor.description]
                print(f"  Columns: {', '.join(columns)}")
            except Exception as e:
                print(f"  ⚠️  Could not examine: {e}")


def extract_taxa(conn: pyodbc.Connection) -> List[Dict]:
    """
    Extract core taxa data from UKSI
    
    Args:
        conn: Database connection
        
    Returns:
        List of taxa dictionaries
    """
    print_section("STEP 3: Extracting Taxa Data")
    
    cursor = conn.cursor()
    
    # Access requires parentheses around multiple JOINs
    # Filter for current preferred names only to avoid duplicates
    print_progress("Querying UKSI tables (TAXON_LIST_ITEM + TAXON + TAXON_VERSION + TAXON_RANK)...")
    
    query = """
    SELECT DISTINCT
        TLI.TAXON_LIST_ITEM_KEY,
        T.ITEM_NAME,
        TR.LONG_NAME,
        TLI.PARENT
    FROM ((TAXON_LIST_ITEM AS TLI
    INNER JOIN TAXON_VERSION AS TV ON TLI.TAXON_VERSION_KEY = TV.TAXON_VERSION_KEY)
    INNER JOIN TAXON AS T ON TV.TAXON_KEY = T.TAXON_KEY)
    LEFT JOIN TAXON_RANK AS TR ON TV.TAXON_RANK_KEY = TR.TAXON_RANK_KEY
    WHERE T.LANGUAGE = 'La'
        AND TLI.PREFERRED_NAME = TLI.TAXON_LIST_ITEM_KEY
        AND TLI.TAXON_LIST_VERSION_TO IS NULL
    """
    
    try:
        cursor.execute(query)
        print_progress("Reading taxa records...")
        
        taxa = []
        seen_tvks = set()  # Track seen TVKs to avoid duplicates
        count = 0
        duplicates = 0
        
        for row in cursor:
            tvk = row[0]  # TAXON_VERSION_KEY
            
            # Skip if we've already seen this TVK
            if tvk in seen_tvks:
                duplicates += 1
                continue
            seen_tvks.add(tvk)
            
            scientific_name = row[1]  # ITEM_NAME
            rank = row[2]  # LONG_NAME (from TAXON_RANK)
            parent = row[3]  # PARENT
            
            taxa.append({
                'tvk': tvk,
                'scientific_name': scientific_name,
                'rank': rank if rank else 'Unknown',
                'parent_tvk': parent
            })
            count += 1
            if count % 10000 == 0:
                print_progress(f"  Processed {count} taxa (skipped {duplicates} duplicates)...", end='\r')
        
        print_progress(f"✅ Extracted {len(taxa)} unique taxa records with rank information")
        if duplicates > 0:
            print_progress(f"   (Skipped {duplicates} duplicate TVKs)")
        return taxa
        
    except Exception as e:
        print_progress(f"❌ Query failed: {e}")
        print_progress("\nTrying simpler query without joins...")
        
        # Simpler fallback - just get TAXON with Latin names
        query = """
        SELECT DISTINCT
            TV.TAXON_VERSION_KEY,
            T.ITEM_NAME
        FROM TAXON AS T
        INNER JOIN TAXON_VERSION AS TV ON T.TAXON_KEY = TV.TAXON_KEY
        WHERE T.LANGUAGE = 'La'
        """
        
        try:
            cursor.execute(query)
            print_progress("Reading taxa records (simplified)...")
            taxa = []
            seen_tvks = set()
            
            for row in cursor:
                tvk = row[0]
                if tvk in seen_tvks:
                    continue
                seen_tvks.add(tvk)
                
                taxa.append({
                    'tvk': tvk,
                    'scientific_name': row[1],
                    'rank': 'Unknown',
                    'parent_tvk': None
                })
            
            print_progress(f"✅ Extracted {len(taxa)} unique taxa records (simplified)")
            print_progress("⚠️  Warning: Rank and hierarchy information not available")
            return taxa
            
        except Exception as e:
            print_progress(f"❌ Simplified query also failed: {e}")
            raise


def extract_common_names(conn: pyodbc.Connection) -> Dict[str, str]:
    """
    Extract English common names (filter out Welsh)
    
    Args:
        conn: Database connection
        
    Returns:
        Dictionary mapping PREFERRED_NAME (scientific name's TAXON_LIST_ITEM_KEY) to common name
    """
    print_section("STEP 4: Extracting Common Names (English Only)")
    
    cursor = conn.cursor()
    
    print_progress("Querying for common names linked via PREFERRED_NAME...")
    
    # Common names link to scientific names via PREFERRED_NAME field!
    # Extract where LANGUAGE='En' and PREFERRED_NAME != TAXON_LIST_ITEM_KEY
    query = """
    SELECT DISTINCT
        TLI.PREFERRED_NAME,
        T.ITEM_NAME
    FROM (TAXON_LIST_ITEM AS TLI
    INNER JOIN TAXON_VERSION AS TV ON TLI.TAXON_VERSION_KEY = TV.TAXON_VERSION_KEY)
    INNER JOIN TAXON AS T ON TV.TAXON_KEY = T.TAXON_KEY
    WHERE T.LANGUAGE = 'En'
        AND T.ITEM_NAME IS NOT NULL
        AND TLI.TAXON_LIST_VERSION_TO IS NULL
        AND TLI.PREFERRED_NAME <> TLI.TAXON_LIST_ITEM_KEY
    """
    
    try:
        cursor.execute(query)
        print_progress("Reading common names...")
        
        common_names = {}
        total_count = 0
        welsh_filtered = 0
        
        for row in cursor:
            total_count += 1
            
            tvk = row[0]  # TAXON_KEY (links to scientific name!)
            name = row[1]  # ITEM_NAME
            
            if not name:
                continue
                
            # Filter Welsh names
            if is_welsh_name(name):
                welsh_filtered += 1
                continue
            
            # Keep English name (use first one if multiple for same TVK)
            if tvk not in common_names:
                common_names[tvk] = name
            
            if total_count % 5000 == 0:
                print_progress(f"  Processed {total_count} names...", end='\r')
        
        print_progress(f"✅ Extracted {len(common_names)} English common names")
        print_progress(f"   Filtered out {welsh_filtered} Welsh names")
        return common_names
        
    except Exception as e:
        print_progress(f"⚠️  Could not extract common names: {e}")
        print_progress("   Continuing without common names...")
        return {}


def extract_synonyms(conn: pyodbc.Connection) -> List[Tuple[str, str]]:
    """
    Extract synonyms
    
    Args:
        conn: Database connection
        
    Returns:
        List of (synonym, tvk) tuples
    """
    print_section("STEP 5: Extracting Synonyms")
    
    cursor = conn.cursor()
    
    print_progress("Attempting to extract synonyms...")
    
    # In UKSI, synonyms are taxa where PREFERRED_NAME != TAXON_LIST_ITEM_KEY
    # They point to the preferred name via PREFERRED_NAME
    # Access requires parentheses around multiple JOINs
    # Filter for current versions only
    
    try:
        query = """
        SELECT DISTINCT
            T.ITEM_NAME,
            TLI.PREFERRED_NAME
        FROM (TAXON_LIST_ITEM AS TLI
        INNER JOIN TAXON_VERSION AS TV ON TLI.TAXON_VERSION_KEY = TV.TAXON_VERSION_KEY)
        INNER JOIN TAXON AS T ON TV.TAXON_KEY = T.TAXON_KEY
        WHERE TLI.PREFERRED_NAME <> TLI.TAXON_LIST_ITEM_KEY
            AND T.LANGUAGE = 'La'
            AND TLI.TAXON_LIST_VERSION_TO IS NULL
        """
        
        cursor.execute(query)
        synonyms = []
        seen = set()  # Track seen combinations to avoid duplicates
        count = 0
        duplicates = 0
        
        for row in cursor:
            synonym = row[0]
            preferred_key = row[1]
            
            # Avoid duplicates
            key = (synonym, preferred_key)
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            
            # Store as (synonym, preferred_key)
            synonyms.append((synonym, preferred_key))
            
            count += 1
            if count % 5000 == 0:
                print_progress(f"  Processed {count} synonyms (skipped {duplicates} duplicates)...", end='\r')
        
        print_progress(f"✅ Extracted {len(synonyms)} unique synonyms")
        if duplicates > 0:
            print_progress(f"   (Skipped {duplicates} duplicate synonym pairs)")
        return synonyms
        
    except Exception as e:
        print_progress(f"⚠️  Could not extract synonyms: {e}")
        print_progress("   Continuing without synonyms...")
        return []


def create_uksi_database():
    """Create the SQLite database with schema"""
    print_section("STEP 6: Creating SQLite Database (uksi.db)")
    
    # Check if database exists
    if UKSI_DB_PATH.exists():
        response = input(f"\n⚠️  {UKSI_DB_PATH} already exists. Overwrite? (yes/no): ")
        if response.lower() != 'yes':
            print_progress("Aborted by user")
            sys.exit(0)
        print_progress("Removing existing database...")
        UKSI_DB_PATH.unlink()
    
    print_progress(f"Creating database at: {UKSI_DB_PATH}")
    
    conn = sqlite3.connect(UKSI_DB_PATH)
    cursor = conn.cursor()
    
    # Create taxa table
    print_progress("Creating taxa table...")
    cursor.execute("""
        CREATE TABLE taxa (
            tvk TEXT PRIMARY KEY,
            scientific_name TEXT NOT NULL,
            rank TEXT,
            parent_tvk TEXT,
            kingdom TEXT,
            phylum TEXT,
            class TEXT,
            "order" TEXT,
            family TEXT,
            genus TEXT
        )
    """)
    
    # Create indexes
    print_progress("Creating indexes...")
    cursor.execute("CREATE INDEX idx_taxa_scientific ON taxa(scientific_name)")
    cursor.execute("CREATE INDEX idx_taxa_rank ON taxa(rank)")
    cursor.execute("CREATE INDEX idx_taxa_parent ON taxa(parent_tvk)")
    
    # Create separate common_names table (many-to-many)
    print_progress("Creating common_names table...")
    cursor.execute("""
        CREATE TABLE common_names (
            common_name TEXT NOT NULL,
            tvk TEXT NOT NULL,
            PRIMARY KEY (common_name, tvk),
            FOREIGN KEY (tvk) REFERENCES taxa(tvk)
        )
    """)
    cursor.execute("CREATE INDEX idx_common_name ON common_names(common_name)")
    cursor.execute("CREATE INDEX idx_common_tvk ON common_names(tvk)")
    
    # Create synonyms table
    print_progress("Creating synonyms table...")
    cursor.execute("""
        CREATE TABLE synonyms (
            synonym TEXT,
            tvk TEXT,
            FOREIGN KEY (tvk) REFERENCES taxa(tvk)
        )
    """)
    cursor.execute("CREATE INDEX idx_synonyms_synonym ON synonyms(synonym)")
    cursor.execute("CREATE INDEX idx_synonyms_tvk ON synonyms(tvk)")
    
    conn.commit()
    print_progress("✅ Database schema created")
    
    return conn


def populate_database(conn: sqlite3.Connection, taxa: List[Dict], 
                     common_names: Dict[str, str], synonyms: List[Tuple[str, str]]):
    """
    Populate the database with extracted data
    
    Args:
        conn: SQLite connection
        taxa: List of taxa dictionaries
        common_names: Dictionary of TVK to common name (or list of common names)
        synonyms: List of (synonym, tvk) tuples
    """
    print_section("STEP 7: Populating Database")
    
    cursor = conn.cursor()
    
    # Insert taxa (without common names)
    print_progress(f"Inserting {len(taxa)} taxa records...")
    
    if len(taxa) > 0 and len(common_names) > 0:
        sample_taxon_tvk = taxa[0]['tvk']
        sample_common_tvk = list(common_names.keys())[0]
        print_progress(f"   Sample taxon TVK: {sample_taxon_tvk}")
        print_progress(f"   Sample common name TVK: {sample_common_tvk}")
    
    for idx, taxon in enumerate(taxa):
        tvk = taxon['tvk']
        
        cursor.execute("""
            INSERT INTO taxa (tvk, scientific_name, rank, parent_tvk)
            VALUES (?, ?, ?, ?)
        """, (tvk, taxon['scientific_name'], taxon['rank'], taxon['parent_tvk']))
        
        if (idx + 1) % 10000 == 0:
            print_progress(f"  Inserted {idx + 1} taxa...", end='\r')
            conn.commit()
    
    conn.commit()
    print_progress(f"✅ Inserted {len(taxa)} taxa records")
    
    # Insert common names into separate table
    if common_names:
        print_progress(f"Inserting {len(common_names)} common names...")
        matched_count = 0
        
        for tvk, common_name in common_names.items():
            # Check if this TVK exists in taxa
            cursor.execute("SELECT 1 FROM taxa WHERE tvk = ?", (tvk,))
            if cursor.fetchone():
                cursor.execute("""
                    INSERT OR IGNORE INTO common_names (common_name, tvk)
                    VALUES (?, ?)
                """, (common_name, tvk))
                matched_count += 1
                
                if matched_count <= 5:  # Show first 5 matches
                    cursor.execute("SELECT scientific_name FROM taxa WHERE tvk = ?", (tvk,))
                    sci_name = cursor.fetchone()[0]
                    print_progress(f"   Matched: {sci_name} -> {common_name}")
        
        conn.commit()
        print_progress(f"✅ Inserted {matched_count} common names")
    
    # Insert synonyms
    if synonyms:
        print_progress(f"Inserting {len(synonyms)} synonyms...")
        cursor.executemany("INSERT INTO synonyms (synonym, tvk) VALUES (?, ?)", synonyms)
        conn.commit()
        print_progress(f"✅ Inserted {len(synonyms)} synonyms")


def build_taxonomy_hierarchy(conn: sqlite3.Connection):
    """
    Build full taxonomy hierarchy for each taxon
    
    Args:
        conn: SQLite connection
    """
    print_section("STEP 8: Building Taxonomy Hierarchy")
    
    cursor = conn.cursor()
    
    print_progress("Calculating full taxonomy paths...")
    print_progress("This may take several minutes...")
    
    # Get all taxa
    cursor.execute("SELECT tvk, parent_tvk FROM taxa")
    taxa = cursor.fetchall()
    
    # Build parent lookup
    parent_lookup = {tvk: parent for tvk, parent in taxa if parent}
    
    # Get rank information
    cursor.execute("SELECT tvk, scientific_name, rank FROM taxa")
    rank_info = {tvk: (name, rank) for tvk, name, rank in cursor.fetchall()}
    
    updates = []
    processed = 0
    
    for tvk, _ in taxa:
        # Walk up the hierarchy
        taxonomy = {}
        current_tvk = tvk
        visited = set()
        
        while current_tvk and current_tvk in parent_lookup:
            # Prevent infinite loops
            if current_tvk in visited:
                break
            visited.add(current_tvk)
            
            parent_tvk = parent_lookup[current_tvk]
            if parent_tvk in rank_info:
                name, rank = rank_info[parent_tvk]
                if rank:
                    rank_lower = rank.lower()
                    taxonomy[rank_lower] = name
            
            current_tvk = parent_tvk
        
        # Prepare update
        updates.append((
            taxonomy.get('kingdom'),
            taxonomy.get('phylum'),
            taxonomy.get('class'),
            taxonomy.get('order'),
            taxonomy.get('family'),
            taxonomy.get('genus'),
            tvk
        ))
        
        processed += 1
        if processed % 10000 == 0:
            print_progress(f"  Processed {processed}/{len(taxa)} taxa...", end='\r')
            
            # Batch update
            cursor.executemany("""
                UPDATE taxa 
                SET kingdom=?, phylum=?, class=?, "order"=?, family=?, genus=?
                WHERE tvk=?
            """, updates)
            conn.commit()
            updates = []
    
    # Final batch
    if updates:
        cursor.executemany("""
            UPDATE taxa 
            SET kingdom=?, phylum=?, class=?, "order"=?, family=?, genus=?
            WHERE tvk=?
        """, updates)
        conn.commit()
    
    print_progress(f"✅ Built taxonomy for {len(taxa)} taxa")


def verify_database(conn: sqlite3.Connection):
    """
    Verify the database contents
    
    Args:
        conn: SQLite connection
    """
    print_section("STEP 9: Verifying Database")
    
    cursor = conn.cursor()
    
    # Count records
    cursor.execute("SELECT COUNT(*) FROM taxa")
    taxa_count = cursor.fetchone()[0]
    print_progress(f"Total taxa: {taxa_count:,}")
    
    cursor.execute("SELECT COUNT(*) FROM common_names")
    common_count = cursor.fetchone()[0]
    print_progress(f"Total common names: {common_count:,}")
    
    cursor.execute("SELECT COUNT(DISTINCT tvk) FROM common_names")
    taxa_with_common = cursor.fetchone()[0]
    print_progress(f"Taxa with common names: {taxa_with_common:,}")
    
    cursor.execute("SELECT COUNT(*) FROM synonyms")
    synonym_count = cursor.fetchone()[0]
    print_progress(f"Total synonyms: {synonym_count:,}")
    
    # Show sample common names
    print_progress("\nSample common names in database:")
    cursor.execute("""
        SELECT t.scientific_name, cn.common_name 
        FROM common_names cn
        JOIN taxa t ON cn.tvk = t.tvk
        LIMIT 10
    """)
    for sci_name, common_name in cursor.fetchall():
        print(f"  {common_name} ({sci_name})")
    
    # Test search for "Blackbird"
    print_progress("\nTesting search for 'Blackbird':")
    cursor.execute("""
        SELECT t.tvk, t.scientific_name, cn.common_name, t.kingdom, t.class, t."order", t.family
        FROM common_names cn
        JOIN taxa t ON cn.tvk = t.tvk
        WHERE cn.common_name LIKE '%Blackbird%'
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"  ✅ Found: {row[2]} ({row[1]})")
            print(f"     TVK: {row[0]}")
            if row[3]:  # If taxonomy populated
                print(f"     Taxonomy: {row[3]} > {row[4]} > {row[5]} > {row[6]}")
    else:
        print("  ⚠️  No results found for 'Blackbird'")
        
        # Try to find "Turdus merula" directly
        print_progress("\n  Trying to find 'Turdus merula' by scientific name:")
        cursor.execute("""
            SELECT t.tvk, t.scientific_name, cn.common_name 
            FROM taxa t
            LEFT JOIN common_names cn ON t.tvk = cn.tvk
            WHERE t.scientific_name LIKE '%Turdus%merula%'
            LIMIT 3
        """)
        turdus_results = cursor.fetchall()
        if turdus_results:
            for tvk, sci, common in turdus_results:
                print(f"    Found: {sci}, Common name: {common if common else '(none)'}")
        else:
            print("    Turdus merula not found either")
    
    # Test that Welsh names are filtered
    print_progress("\nVerifying Welsh filter (searching for 'Mwyalch'):")
    cursor.execute("SELECT COUNT(*) FROM common_names WHERE common_name LIKE '%Mwyalch%'")
    welsh_count = cursor.fetchone()[0]
    if welsh_count == 0:
        print_progress("  ✅ Welsh names successfully filtered")
    else:
        print_progress(f"  ⚠️  Found {welsh_count} Welsh names (filter may need adjustment)")
    
    # Database size
    db_size_mb = UKSI_DB_PATH.stat().st_size / (1024 * 1024)
    print_progress(f"\nDatabase size: {db_size_mb:.2f} MB")


def main():
    """Main execution function"""
    print_section("UKSI Extractor for Observatum")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1-2: Connect and inspect
        uksi_conn = connect_to_uksi()
        inspect_uksi_structure(uksi_conn)
        
        # Step 3-5: Extract data
        taxa = extract_taxa(uksi_conn)
        common_names = extract_common_names(uksi_conn)
        synonyms = extract_synonyms(uksi_conn)
        
        # Close Access connection
        uksi_conn.close()
        print_progress("\nClosed UKSI.mdb connection")
        
        # Step 6: Create SQLite database
        sqlite_conn = create_uksi_database()
        
        # Step 7-8: Populate and build hierarchy
        populate_database(sqlite_conn, taxa, common_names, synonyms)
        build_taxonomy_hierarchy(sqlite_conn)
        
        # Step 9: Verify
        verify_database(sqlite_conn)
        
        # Close SQLite connection
        sqlite_conn.close()
        
        print_section("EXTRACTION COMPLETE!")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n✅ UKSI database created successfully at: {UKSI_DB_PATH}")
        print(f"✅ You can now use this database in Observatum")
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
    except pyodbc.Error as e:
        print(f"\n❌ DATABASE ERROR: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure Microsoft Access ODBC driver is installed")
        print("  2. Check that UKSI.mdb is not corrupted")
        print("  3. Verify Python and ODBC driver are same architecture (32/64-bit)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
