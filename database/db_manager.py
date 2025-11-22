"""
Database Manager for Observatum
Handles SQLite database connections and initialization

This module manages connections to three separate databases:
1. observations.db - Main user observation records
2. longhorns.db - National Longhorn Beetle Recording Scheme data
3. insect_collection.db - Physical specimen collection records
4. uksi.db - UK Species Inventory (reference database)
"""

import sqlite3
from pathlib import Path
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and initialization for Observatum"""
    
    def __init__(self, db_dir: Optional[Path] = None):
        """
        Initialize the database manager
        
        Args:
            db_dir: Directory where database files are stored.
                   Defaults to 'data' folder in project root.
        """
        if db_dir is None:
            # Default to 'data' directory in project root
            project_root = Path(__file__).parent.parent
            db_dir = project_root / 'data'
        
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        # Database file paths
        self.observations_db_path = self.db_dir / 'observations.db'
        self.longhorns_db_path = self.db_dir / 'longhorns.db'
        self.collection_db_path = self.db_dir / 'insect_collection.db'
        self.uksi_db_path = self.db_dir / 'uksi.db'
        
        # Connection instances (initially None)
        self._observations_conn = None
        self._longhorns_conn = None
        self._collection_conn = None
        self._uksi_conn = None
        
        logger.info(f"DatabaseManager initialized with db_dir: {self.db_dir}")
        
    def get_observations_connection(self) -> sqlite3.Connection:
        """Get connection to observations database"""
        if self._observations_conn is None:
            self._observations_conn = self._create_connection(self.observations_db_path)
            self._init_observations_db(self._observations_conn)
        return self._observations_conn
        
    def get_longhorns_connection(self) -> sqlite3.Connection:
        """Get connection to longhorns database"""
        if self._longhorns_conn is None:
            self._longhorns_conn = self._create_connection(self.longhorns_db_path)
            self._init_longhorns_db(self._longhorns_conn)
        return self._longhorns_conn
        
    def get_collection_connection(self) -> sqlite3.Connection:
        """Get connection to insect collection database"""
        if self._collection_conn is None:
            self._collection_conn = self._create_connection(self.collection_db_path)
            self._init_collection_db(self._collection_conn)
        return self._collection_conn
        
    def get_uksi_connection(self) -> sqlite3.Connection:
        """Get connection to UKSI reference database"""
        if self._uksi_conn is None:
            self._uksi_conn = self._create_connection(self.uksi_db_path)
            self._init_uksi_db(self._uksi_conn)
        return self._uksi_conn
        
    def _create_connection(self, db_path: Path) -> sqlite3.Connection:
        """
        Create a database connection
        
        Args:
            db_path: Path to the database file
            
        Returns:
            SQLite connection object
        """
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"Connected to database: {db_path.name}")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database {db_path.name}: {e}")
            raise
            
    def _init_observations_db(self, conn: sqlite3.Connection):
        """Initialize observations database schema"""
        cursor = conn.cursor()
        
        # Records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                species_name TEXT NOT NULL,
                taxon_id TEXT,
                site_name TEXT NOT NULL,
                grid_reference TEXT NOT NULL,
                date TEXT NOT NULL,
                recorder TEXT NOT NULL,
                determiner TEXT NOT NULL,
                certainty TEXT NOT NULL,
                sex TEXT,
                quantity INTEGER,
                sample_method TEXT,
                observation_type TEXT,
                sample_comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sites table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_name TEXT UNIQUE NOT NULL,
                grid_reference TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                habitat TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Recorders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recorders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                email TEXT,
                organization TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("Observations database schema initialized")
        
    def _init_longhorns_db(self, conn: sqlite3.Connection):
        """Initialize longhorns database schema"""
        cursor = conn.cursor()
        
        # Longhorn records table (similar structure to observations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS longhorn_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                species_name TEXT NOT NULL,
                taxon_id TEXT,
                site_name TEXT NOT NULL,
                grid_reference TEXT NOT NULL,
                date TEXT NOT NULL,
                recorder TEXT NOT NULL,
                determiner TEXT NOT NULL,
                certainty TEXT NOT NULL,
                sex TEXT,
                quantity INTEGER,
                sample_method TEXT,
                observation_type TEXT,
                sample_comment TEXT,
                scheme_specific_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("Longhorns database schema initialized")
        
    def _init_collection_db(self, conn: sqlite3.Connection):
        """Initialize insect collection database schema"""
        cursor = conn.cursor()
        
        # Specimen collection table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS specimens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                species_name TEXT NOT NULL,
                taxon_id TEXT,
                collection_date TEXT NOT NULL,
                collection_site TEXT NOT NULL,
                grid_reference TEXT NOT NULL,
                collector TEXT NOT NULL,
                determiner TEXT NOT NULL,
                certainty TEXT NOT NULL,
                sex TEXT,
                life_stage TEXT,
                preparation_method TEXT,
                storage_location TEXT,
                cabinet_number TEXT,
                drawer_number TEXT,
                specimen_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("Insect collection database schema initialized")
        
    def _init_uksi_db(self, conn: sqlite3.Connection):
        """Initialize UKSI reference database schema"""
        cursor = conn.cursor()
        
        # Taxa table (UK Species Inventory)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS taxa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                taxon_id TEXT UNIQUE NOT NULL,
                scientific_name TEXT NOT NULL,
                common_name TEXT,
                kingdom TEXT,
                phylum TEXT,
                class TEXT,
                order_name TEXT,
                family TEXT,
                genus TEXT,
                species TEXT,
                rank TEXT NOT NULL,
                parent_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for faster searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scientific_name 
            ON taxa(scientific_name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_common_name 
            ON taxa(common_name)
        """)
        
        conn.commit()
        logger.info("UKSI database schema initialized")
        
    def close_all(self):
        """Close all database connections"""
        connections = [
            (self._observations_conn, "observations"),
            (self._longhorns_conn, "longhorns"),
            (self._collection_conn, "collection"),
            (self._uksi_conn, "uksi")
        ]
        
        for conn, name in connections:
            if conn is not None:
                try:
                    conn.close()
                    logger.info(f"Closed {name} database connection")
                except sqlite3.Error as e:
                    logger.error(f"Error closing {name} database: {e}")
                    
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close all connections"""
        self.close_all()
        

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
    Get the global database manager instance
    
    Returns:
        DatabaseManager singleton instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def close_databases():
    """Close all database connections (call on application exit)"""
    global _db_manager
    if _db_manager is not None:
        _db_manager.close_all()
        _db_manager = None
