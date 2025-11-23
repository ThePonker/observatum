"""
UKSI Search Logic
Handles species search queries with fuzzy matching

Author: Observatum Development Team
Date: 23 November 2025
"""

import sqlite3
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class UKSISearch:
    """
    Handles UKSI database search operations.
    
    Provides fuzzy matching for species names (scientific and common).
    Splits multi-word searches and finds partial matches.
    
    Examples:
    - "Platy viola" finds "Platydema violaceum"
    - "Black bird" finds "Blackbird" and "Turdus merula"
    - "Oak" finds "Quercus robur", "Oak", "Pedunculate Oak"
    """
    
    def __init__(self, db_conn: sqlite3.Connection):
        """
        Initialize search handler
        
        Args:
            db_conn: SQLite connection to UKSI database
        """
        self.conn = db_conn
    
    def search(self, search_term: str, limit: int = 60) -> List[Dict]:
        """
        Execute fuzzy search for species
        
        Features:
        - Multi-word fuzzy matching (each word must appear somewhere)
        - Searches both scientific and common names
        - Deduplication by scientific name
        - Results sorted by relevance (exact matches first)
        
        Args:
            search_term: Search string
            limit: Maximum results to return
            
        Returns:
            List of species dictionaries with:
            - tvk: Taxon Version Key
            - scientific_name: Scientific name
            - common_names: Comma-separated common names (or None)
            - rank: Taxonomic rank
            - kingdom, phylum, class, order, family, genus: Taxonomy
        """
        cursor = self.conn.cursor()
        
        # Build fuzzy query
        query, params = self._build_fuzzy_query(search_term, limit)
        
        # Execute query
        cursor.execute(query, params)
        
        # Assemble results
        results = []
        tvks = []
        
        for row in cursor.fetchall():
            tvk = row['tvk']
            tvks.append(tvk)
            
            results.append({
                'tvk': tvk,
                'scientific_name': row['scientific_name'],
                'common_names': None,  # Will be filled in bulk below
                'rank': row['rank']
            })
        
        # Bulk fetch all common names (much faster than individual queries)
        self._fetch_common_names_bulk(cursor, results, tvks)
        
        logger.debug(f"Search '{search_term}' returned {len(results)} species")
        return results
    
    def _build_fuzzy_query(self, search_term: str, limit: int) -> tuple:
        """
        Build SQL query for fuzzy matching
        
        Splits search term into words and requires each word to appear
        somewhere in either scientific or common name.
        
        Example: "black bird" becomes:
        - (scientific LIKE '%black%' OR common LIKE '%black%') AND
        - (scientific LIKE '%bird%' OR common LIKE '%bird%')
        
        Args:
            search_term: Search string
            limit: Result limit
            
        Returns:
            Tuple of (query_string, parameters_list)
        """
        # Split search term into individual words
        search_words = search_term.strip().split()
        
        # Build WHERE clauses for each word
        where_clauses = []
        params = []
        
        for word in search_words:
            word_pattern = f"%{word}%"
            where_clauses.append(
                "(t.scientific_name LIKE ? COLLATE NOCASE OR cn.common_name LIKE ? COLLATE NOCASE)"
            )
            params.extend([word_pattern, word_pattern])
        
        where_sql = " AND ".join(where_clauses)
        
        # Build full query with proper deduplication
        # Returns ONLY ONE entry per unique scientific name
        # Picks the best TVK based on: pure species > subspecies > hybrids
        query = f"""
        WITH ranked_results AS (
            SELECT 
                t.tvk,
                t.scientific_name,
                t.rank,
                ROW_NUMBER() OVER (
                    PARTITION BY t.scientific_name
                    ORDER BY 
                        CASE 
                            WHEN t.scientific_name LIKE '% x %' THEN 3
                            WHEN t.rank LIKE '%Subspecies%' OR t.rank LIKE '%Variety%' OR t.rank LIKE '%Form%' THEN 2
                            ELSE 1
                        END,
                        LENGTH(t.scientific_name),
                        t.tvk
                ) as rn
            FROM taxa t
            LEFT JOIN common_names cn ON t.tvk = cn.tvk
            WHERE {where_sql}
        )
        SELECT 
            tvk,
            scientific_name,
            rank
        FROM ranked_results
        WHERE rn = 1
        ORDER BY 
            CASE 
                WHEN scientific_name LIKE ? COLLATE NOCASE THEN 1
                ELSE 2
            END,
            LENGTH(scientific_name),
            scientific_name
        LIMIT ?
        """
        
        # Add parameters for ranking (names starting with search term get priority)
        start_pattern = f"{search_term}%"
        params.extend([start_pattern, limit])
        
        return query, params
    
    def _fetch_common_names_bulk(self, cursor, results: List[Dict], tvks: List[str]):
        """
        Fetch all common names in single bulk query
        
        This is MUCH faster than querying one-by-one!
        Uses GROUP_CONCAT to get comma-separated list per TVK.
        
        Args:
            cursor: Database cursor
            results: Results list to update (modified in place)
            tvks: List of TVKs to fetch common names for
        """
        if not tvks:
            return
        
        # Build parameterized query with placeholders
        placeholders = ','.join('?' * len(tvks))
        common_query = f"""
            SELECT tvk, GROUP_CONCAT(common_name, ', ') as common_names
            FROM common_names
            WHERE tvk IN ({placeholders})
            GROUP BY tvk
        """
        cursor.execute(common_query, tvks)
        
        # Create lookup dictionary: tvk -> common_names
        common_names_dict = {
            row['tvk']: row['common_names'] 
            for row in cursor.fetchall()
        }
        
        # Update results with common names
        for species in results:
            species['common_names'] = common_names_dict.get(species['tvk'])