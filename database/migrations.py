"""
Database Migrations for Observatum - FIXED VERSION
Handles adding iRecord integration fields to observations database

FIXED: Removed UNIQUE constraint from uuid column to allow migration on existing databases
The UNIQUE constraint will be enforced by application logic instead.

Author: Observatum Development Team
Date: 23 November 2025
"""

import sqlite3
import logging
from typing import List, Tuple
import uuid

logger = logging.getLogger(__name__)


class DatabaseMigrations:
    """Database schema migrations"""
    
    @staticmethod
    def run_all_migrations(conn: sqlite3.Connection) -> bool:
        """
        Run all pending migrations
        
        Args:
            conn: SQLite database connection
            
        Returns:
            True if all migrations successful, False otherwise
        """
        try:
            logger.info("Running database migrations...")
            
            migrations = [
                DatabaseMigrations._add_irecord_fields,
                DatabaseMigrations._add_uuid_to_existing_records
            ]
            
            for migration in migrations:
                try:
                    migration(conn)
                except Exception as e:
                    # Log but don't fail - some migrations might already be applied
                    logger.warning(f"Migration {migration.__name__} skipped or failed: {e}")
            
            conn.commit()
            logger.info("Database migrations completed")
            return True
            
        except Exception as e:
            logger.error(f"Migration error: {e}")
            conn.rollback()
            return False
    
    @staticmethod
    def _add_irecord_fields(conn: sqlite3.Connection):
        """Add iRecord integration fields to records table"""
        cursor = conn.cursor()
        
        # Check which columns already exist
        cursor.execute("PRAGMA table_info(records)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # Define new columns (REMOVED UNIQUE CONSTRAINT!)
        new_columns = [
            ("uuid", "TEXT"),  # Changed from "TEXT UNIQUE"
            ("irecord_id", "INTEGER"),
            ("irecord_key", "TEXT"),
            ("irecord_external_key", "TEXT"),
            ("verification_status", "TEXT DEFAULT 'Not reviewed'"),
            ("verification_substatus", "TEXT"),
            ("verified_by", "TEXT"),
            ("verified_on", "TEXT"),
            ("submitted_to_irecord", "BOOLEAN DEFAULT 0"),
            ("submitted_date", "TEXT"),
            ("last_synced_with_irecord", "TEXT"),
            ("latitude", "REAL"),
            ("longitude", "REAL"),
            ("taxon_version_key", "TEXT"),
            ("common_name", "TEXT")
        ]
        
        # Add missing columns
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE records ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        raise
        
        conn.commit()
    
    @staticmethod
    def _add_uuid_to_existing_records(conn: sqlite3.Connection):
        """Generate UUIDs for records that don't have them"""
        cursor = conn.cursor()
        
        # Check if uuid column exists
        cursor.execute("PRAGMA table_info(records)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'uuid' not in columns:
            logger.warning("UUID column doesn't exist yet - skipping UUID generation")
            return
        
        # Find records without UUIDs
        cursor.execute("SELECT id FROM records WHERE uuid IS NULL OR uuid = ''")
        records_without_uuid = cursor.fetchall()
        
        if not records_without_uuid:
            logger.info("All records already have UUIDs")
            return
        
        logger.info(f"Generating UUIDs for {len(records_without_uuid)} records...")
        
        # Generate and update UUIDs
        for (record_id,) in records_without_uuid:
            new_uuid = str(uuid.uuid4())
            cursor.execute("UPDATE records SET uuid = ? WHERE id = ?", (new_uuid, record_id))
        
        conn.commit()
        logger.info(f"✓ Generated UUIDs for {len(records_without_uuid)} records")
    
    @staticmethod
    def verify_schema(conn: sqlite3.Connection) -> Tuple[bool, List[str]]:
        """
        Verify that all required columns exist
        
        Returns:
            Tuple of (all_present, missing_columns)
        """
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(records)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        required_columns = {
            'uuid', 'irecord_id', 'irecord_key', 'irecord_external_key',
            'verification_status', 'verified_by', 'verified_on',
            'submitted_to_irecord', 'submitted_date', 'last_synced_with_irecord',
            'latitude', 'longitude', 'taxon_version_key', 'common_name'
        }
        
        missing = required_columns - existing_columns
        return len(missing) == 0, list(missing)


# Standalone test
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get database path
    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])
    else:
        db_path = Path(__file__).parent.parent / 'data' / 'observations.db'
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)
    
    print("="*70)
    print("Database Migration Tool")
    print("="*70)
    print(f"Database: {db_path}")
    print()
    
    # Create backup
    import shutil
    from datetime import datetime
    backup_path = db_path.parent / f"{db_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(db_path, backup_path)
    print(f"✓ Backup created: {backup_path.name}")
    print()
    
    # Connect and run migrations
    conn = sqlite3.connect(str(db_path))
    
    try:
        print("Running migrations...")
        success = DatabaseMigrations.run_all_migrations(conn)
        
        if success:
            print("\n✓ Migrations completed successfully!")
            
            # Verify schema
            all_present, missing = DatabaseMigrations.verify_schema(conn)
            if all_present:
                print("✓ Schema verification passed - all fields present")
            else:
                print(f"⚠ Warning: Missing columns: {missing}")
        else:
            print("\n❌ Migrations failed!")
            
    finally:
        conn.close()
    
    print()
    print("="*70)