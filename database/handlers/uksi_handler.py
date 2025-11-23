"""
UKSI Database Handler for Observatum

Provides interface to query the UK Species Inventory database (uksi.db)
for species searches, autocomplete, and taxonomy information.

Refactored version:
- Delegates search logic to UKSISearch
- Delegates ranking logic to UKSIRanker
- Main handler focuses on coordination and simple queries

Author: Observatum Development Team
Date: 23 November 2025
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional

from database.handlers.uksi_search import UKSISearch
from database.handlers.uksi_ranker import UKSIRanker

logger = logging.getLogger(__name__)


class UKSIHandler:
    """
    Handler for UKSI (UK Species Inventory) database operations.
    
    Provides methods to search for species by scientific name, common name,
    or partial matches, and retrieve full taxonomic information.
    
    Delegates to:
    - UKSISearch: Fuzzy search and query building
    - UKSIRanker: Smart ranking based on user history
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize UKSI handler.
        
        Args:
            db_path: Path to uksi.db file
        """
        self.db_path = db_path
        self.conn = None
        
        if not db_path.exists():
            raise FileNotFoundError(
                f"UKSI database not found at {db_path}. "
                "Please run uksi_extractor.py to generate the database."
            )
        
        self._connect()
        
        # Initialize helper classes
        self.searcher = UKSISearch(self.conn)
        self.ranker = UKSIRanker()
        
    def _connect(self):
        """Establish connection to UKSI database"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to UKSI database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to UKSI database: {e}")
            raise
    
    def search_species(self, search_term: str, limit: int = 20, obs_db_conn=None) -> List[Dict]:
        """
        Search for species by scientific or common name with FUZZY MATCHING and SMART RANKING.
        
        Smart Ranking (when obs_db_conn provided):
        - Priority 1: Species recorded in last 30 days (most relevant)
        - Priority 2: Species recorded ever (user's species list)
        - Priority 3: Never recorded (general UKSI results)
        
        Fuzzy search breaks down multi-word searches and finds partial matches.
        Examples:
        - "Platy viola" matches "Platydema violaceum"
        - "Black bird" matches "Blackbird" and "Turdus merula"
        - "Oak" matches "Quercus robur", "Oak", "Pedunculate Oak"
        
        Searches both scientific names and common names, returning matches
        where the search term appears anywhere in the name (case-insensitive).
        Returns only one entry per unique scientific name (the preferred one).
        
        Args:
            search_term: Text to search for (partial match supported)
            limit: Maximum number of results to return (default 20)
            obs_db_conn: Optional SQLite connection to observations database for smart ranking
            
        Returns:
            List of dictionaries containing species information:
            - tvk: Taxon Version Key (unique identifier)
            - scientific_name: Scientific name
            - common_names: Comma-separated common names (if available)
            - rank: Taxonomic rank
            - kingdom, phylum, class, order, family, genus: Taxonomy
        """
        if not search_term or len(search_term) < 2:
            return []
        
        # Execute search (get extra results for smart ranking to filter)
        results = self.searcher.search(search_term, limit * 3)
        
        # Apply smart ranking if observations database provided
        if obs_db_conn:
            results = self.ranker.rank_results(results, obs_db_conn)
        
        # Limit to requested number
        results = results[:limit]
        
        logger.debug(f"Smart search '{search_term}' returned {len(results)} species")
        return results
    
    def get_species_by_tvk(self, tvk: str) -> Optional[Dict]:
        """
        Get detailed species information by TVK.
        
        Args:
            tvk: Taxon Version Key
            
        Returns:
            Dictionary with species details, or None if not found
        """
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            t.tvk,
            t.scientific_name,
            t.rank,
            t.parent_tvk,
            t.kingdom,
            t.phylum,
            t.class,
            t."order",
            t.family,
            t.genus,
            GROUP_CONCAT(cn.common_name, ', ') as common_names
        FROM taxa t
        LEFT JOIN common_names cn ON t.tvk = cn.tvk
        WHERE t.tvk = ?
        GROUP BY t.tvk
        """
        
        cursor.execute(query, (tvk,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return {
            'tvk': row['tvk'],
            'scientific_name': row['scientific_name'],
            'common_names': row['common_names'],
            'rank': row['rank'],
            'parent_tvk': row['parent_tvk'],
            'kingdom': row['kingdom'],
            'phylum': row['phylum'],
            'class': row['class'],
            'order': row['order'],
            'family': row['family'],
            'genus': row['genus']
        }
    
    def get_common_names(self, tvk: str) -> List[str]:
        """
        Get all common names for a species.
        
        Args:
            tvk: Taxon Version Key
            
        Returns:
            List of common names
        """
        cursor = self.conn.cursor()
        
        query = "SELECT common_name FROM common_names WHERE tvk = ?"
        cursor.execute(query, (tvk,))
        
        return [row['common_name'] for row in cursor.fetchall()]
    
    def get_synonyms(self, tvk: str) -> List[str]:
        """
        Get all synonyms for a species.
        
        Args:
            tvk: Taxon Version Key
            
        Returns:
            List of synonym names
        """
        cursor = self.conn.cursor()
        
        query = "SELECT synonym FROM synonyms WHERE tvk = ?"
        cursor.execute(query, (tvk,))
        
        return [row['synonym'] for row in cursor.fetchall()]
    
    def get_taxonomy_path(self, tvk: str) -> str:
        """
        Get full taxonomy path for a species.
        
        Args:
            tvk: Taxon Version Key
            
        Returns:
            Formatted taxonomy string (e.g., "Animalia > Chordata > Aves > ...")
        """
        species = self.get_species_by_tvk(tvk)
        
        if not species:
            return ""
        
        # Build taxonomy path from kingdom to genus
        path_parts = []
        for rank in ['kingdom', 'phylum', 'class', 'order', 'family', 'genus']:
            value = species.get(rank)
            if value and value.strip():
                path_parts.append(value)
        
        return " > ".join(path_parts) if path_parts else ""
    
    def format_species_display(self, species: Dict, include_common: bool = True) -> str:
        """
        Format species for display.
        
        Args:
            species: Dictionary with species information
            include_common: If True, include common names; if False, scientific name only
            
        Returns:
            Formatted string for display
        """
        scientific = species['scientific_name']
        common_names = species.get('common_names')
        
        if include_common and common_names:
            return f"{scientific} ({common_names})"
        else:
            return scientific
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Closed UKSI database connection")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
