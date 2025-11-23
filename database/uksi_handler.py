"""
UKSI Database Handler for Observatum

Provides interface to query the UK Species Inventory database (uksi.db)
for species searches, autocomplete, and taxonomy information.

Author: Observatum Development Team
Date: 22 November 2025
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class UKSIHandler:
    """
    Handler for UKSI (UK Species Inventory) database operations.
    
    Provides methods to search for species by scientific name, common name,
    or partial matches, and retrieve full taxonomic information.
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
        
        cursor = self.conn.cursor()
        
        # Get user's recorded species for smart ranking (if observations DB provided)
        recent_tvks = set()  # Recorded in last 30 days
        all_recorded_tvks = set()  # Ever recorded
        
        if obs_db_conn:
            try:
                obs_cursor = obs_db_conn.cursor()
                
                # Get species recorded in last 30 days
                obs_cursor.execute("""
                    SELECT DISTINCT taxon_id 
                    FROM records 
                    WHERE taxon_id IS NOT NULL 
                    AND date >= date('now', '-30 days')
                """)
                recent_tvks = {row[0] for row in obs_cursor.fetchall()}
                
                # Get all species ever recorded
                obs_cursor.execute("""
                    SELECT DISTINCT taxon_id 
                    FROM records 
                    WHERE taxon_id IS NOT NULL
                """)
                all_recorded_tvks = {row[0] for row in obs_cursor.fetchall()}
                
                logger.debug(f"Smart ranking: {len(recent_tvks)} recent species, {len(all_recorded_tvks)} total recorded")
            except Exception as e:
                logger.warning(f"Could not load user's recorded species: {e}")
        
        # Split search term into words for fuzzy matching
        search_words = search_term.strip().split()
        
        # Build WHERE clause for fuzzy matching
        # Each word must appear somewhere in either scientific or common name
        where_clauses = []
        params = []
        
        for word in search_words:
            word_pattern = f"%{word}%"
            where_clauses.append(
                "(t.scientific_name LIKE ? COLLATE NOCASE OR cn.common_name LIKE ? COLLATE NOCASE)"
            )
            params.extend([word_pattern, word_pattern])
        
        where_sql = " AND ".join(where_clauses)
        
        # Deduplicate by scientific_name - take first TVK found for each unique scientific name
        # This eliminates duplicate entries from different taxonomic lists
        query = f"""
        WITH unique_taxa AS (
            SELECT 
                t.scientific_name,
                MIN(t.tvk) as tvk,
                COUNT(DISTINCT cn.common_name) as common_count
            FROM taxa t
            LEFT JOIN common_names cn ON t.tvk = cn.tvk
            WHERE {where_sql}
            GROUP BY t.scientific_name
        )
        SELECT
            ut.tvk,
            t.scientific_name,
            t.rank,
            t.kingdom,
            t.phylum,
            t.class,
            t."order",
            t.family,
            t.genus
        FROM unique_taxa ut
        JOIN taxa t ON ut.tvk = t.tvk
        ORDER BY 
            CASE 
                WHEN t.scientific_name LIKE ? COLLATE NOCASE THEN 1
                ELSE 2
            END,
            t.scientific_name
        LIMIT ?
        """
        
        # Add parameters for ranking (starts-with gets priority)
        start_pattern = f"{search_term}%"
        params.extend([start_pattern, limit * 3])  # Get more results for smart ranking
        
        cursor.execute(query, params)
        
        results = []
        tvks = []
        
        for row in cursor.fetchall():
            tvk = row['tvk']
            tvks.append(tvk)
            
            # Determine priority for smart ranking
            if tvk in recent_tvks:
                priority = 1  # Recorded in last 30 days
            elif tvk in all_recorded_tvks:
                priority = 2  # Ever recorded
            else:
                priority = 3  # Never recorded
            
            results.append({
                'tvk': tvk,
                'scientific_name': row['scientific_name'],
                'common_names': None,  # Will be filled below
                'rank': row['rank'],
                'kingdom': row['kingdom'],
                'phylum': row['phylum'],
                'class': row['class'],
                'order': row['order'],
                'family': row['family'],
                'genus': row['genus'],
                '_priority': priority  # Internal field for sorting
            })
        
        # Fetch ALL common names in a single query (much faster!)
        if tvks:
            placeholders = ','.join('?' * len(tvks))
            common_query = f"""
                SELECT tvk, GROUP_CONCAT(common_name, ', ') as common_names
                FROM common_names
                WHERE tvk IN ({placeholders})
                GROUP BY tvk
            """
            cursor.execute(common_query, tvks)
            
            # Create a dict of tvk -> common_names
            common_names_dict = {row['tvk']: row['common_names'] for row in cursor.fetchall()}
            
            # Update results with common names
            for species in results:
                species['common_names'] = common_names_dict.get(species['tvk'])
        
        # Sort by priority (1 = recent, 2 = recorded, 3 = never)
        results.sort(key=lambda x: (x['_priority'], x['scientific_name']))
        
        # Remove priority field before returning
        for species in results:
            del species['_priority']
        
        # Limit to requested number
        results = results[:limit]
        
        logger.debug(f"Smart search '{search_term}' returned {len(results)} species (prioritized by user history)")
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


# Standalone test
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Path to uksi.db (adjust as needed)
    db_path = Path(__file__).parent / "uksi.db"
    
    if not db_path.exists():
        print(f"Error: uksi.db not found at {db_path}")
        print("Please run uksi_extractor.py first to generate the database.")
        exit(1)
    
    print("="*70)
    print("UKSI Handler Test")
    print("="*70)
    
    with UKSIHandler(db_path) as uksi:
        # Test 1: Search for "Blackbird"
        print("\n1. Searching for 'Blackbird':")
        results = uksi.search_species("Blackbird", limit=5)
        for species in results:
            display = uksi.format_species_display(species)
            print(f"   - {display}")
            print(f"     TVK: {species['tvk']}")
            print(f"     Rank: {species['rank']}")
            if species['family']:
                print(f"     Family: {species['family']}")
        
        # Test 2: Search for "Turdus"
        print("\n2. Searching for 'Turdus':")
        results = uksi.search_species("Turdus", limit=5)
        for species in results:
            print(f"   - {uksi.format_species_display(species)}")
        
        # Test 3: Get details for specific TVK
        if results:
            tvk = results[0]['tvk']
            print(f"\n3. Getting details for TVK {tvk}:")
            details = uksi.get_species_by_tvk(tvk)
            if details:
                print(f"   Scientific name: {details['scientific_name']}")
                print(f"   Common names: {details['common_names']}")
                print(f"   Taxonomy: {uksi.get_taxonomy_path(tvk)}")
                
                synonyms = uksi.get_synonyms(tvk)
                if synonyms:
                    print(f"   Synonyms: {', '.join(synonyms[:3])}")
        
        # Test 4: Search for "oak"
        print("\n4. Searching for 'oak':")
        results = uksi.search_species("oak", limit=5)
        for species in results:
            print(f"   - {uksi.format_species_display(species)}")
    
    print("\n" + "="*70)
    print("Test complete!")
