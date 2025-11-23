"""
UKSI Smart Ranking
Prioritizes species based on user recording history

Author: Observatum Development Team
Date: 23 November 2025
"""

import sqlite3
import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)


class UKSIRanker:
    """
    Applies smart ranking to species search results.
    
    Ranking Priorities:
    1. Species recorded in last 30 days (most relevant)
    2. Species recorded ever (user's species list)
    3. Never recorded (general UKSI results)
    
    This makes the autocomplete "learn" from user's recording patterns,
    showing frequently recorded species first.
    """
    
    def rank_results(self, results: List[Dict], obs_db_conn: sqlite3.Connection) -> List[Dict]:
        """
        Apply smart ranking to search results
        
        Args:
            results: Search results from UKSISearch
            obs_db_conn: Connection to observations database
            
        Returns:
            Ranked results list (sorted by priority)
        """
        # Get recorded species from observations database
        recent_tvks = self._get_recent_species(obs_db_conn)
        all_recorded_tvks = self._get_all_recorded_species(obs_db_conn)
        
        logger.debug(
            f"Smart ranking: {len(recent_tvks)} recent species, "
            f"{len(all_recorded_tvks)} total recorded"
        )
        
        # Assign priorities to each result
        self._assign_priorities(results, recent_tvks, all_recorded_tvks)
        
        # Sort by priority (1=recent, 2=recorded, 3=never)
        results.sort(key=lambda x: (x['_priority'], x['scientific_name']))
        
        # Remove internal priority field before returning
        for species in results:
            del species['_priority']
        
        return results
    
    def _get_recent_species(self, obs_db_conn: sqlite3.Connection) -> Set[str]:
        """
        Get TVKs of species recorded in last 30 days
        
        Args:
            obs_db_conn: Observations database connection
            
        Returns:
            Set of TVKs (Taxon Version Keys)
        """
        try:
            cursor = obs_db_conn.cursor()
            cursor.execute("""
                SELECT DISTINCT taxon_id 
                FROM records 
                WHERE taxon_id IS NOT NULL 
                AND date >= date('now', '-30 days')
            """)
            return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            logger.warning(f"Could not load recent species: {e}")
            return set()
    
    def _get_all_recorded_species(self, obs_db_conn: sqlite3.Connection) -> Set[str]:
        """
        Get TVKs of all species ever recorded
        
        Args:
            obs_db_conn: Observations database connection
            
        Returns:
            Set of TVKs
        """
        try:
            cursor = obs_db_conn.cursor()
            cursor.execute("""
                SELECT DISTINCT taxon_id 
                FROM records 
                WHERE taxon_id IS NOT NULL
            """)
            return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            logger.warning(f"Could not load recorded species: {e}")
            return set()
    
    def _assign_priorities(
        self, 
        results: List[Dict], 
        recent_tvks: Set[str], 
        all_recorded_tvks: Set[str]
    ):
        """
        Assign priority to each result
        
        Priority levels:
        - 1: Recorded in last 30 days (highest priority)
        - 2: Ever recorded (medium priority)
        - 3: Never recorded (lowest priority)
        
        Args:
            results: Results list (modified in place)
            recent_tvks: Set of recently recorded TVKs
            all_recorded_tvks: Set of all recorded TVKs
        """
        for species in results:
            tvk = species['tvk']
            
            if tvk in recent_tvks:
                species['_priority'] = 1  # Recently recorded
            elif tvk in all_recorded_tvks:
                species['_priority'] = 2  # Ever recorded
            else:
                species['_priority'] = 3  # Never recorded
