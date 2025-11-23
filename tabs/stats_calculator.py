"""
Statistics Calculator for Observatum
Calculates statistics from observations database

Used by Home tab Quick Stats boxes
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class StatsCalculator:
    """Calculate statistics from observations database"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """
        Initialize stats calculator
        
        Args:
            db_connection: SQLite connection to observations database
        """
        self.conn = db_connection
        self.conn.row_factory = sqlite3.Row
    
    def get_all_stats(self) -> Dict[str, str]:
        """
        Get all statistics in one call
        
        Returns:
            Dictionary with all stat values formatted as strings
        """
        try:
            stats = {
                'total_records': self.get_total_records(),
                'this_year': self.get_records_this_year(),
                'last_7_days': self.get_records_last_n_days(7),
                'last_recorded': self.get_last_recorded_species(),
                'total_species': self.get_total_species(),
                'this_month': self.get_records_this_month(),
                'last_30_days': self.get_records_last_n_days(30),
                'unique_sites': self.get_unique_sites()
            }
            return stats
        except Exception as e:
            logger.error(f"Error calculating stats: {e}")
            return self._get_default_stats()
    
    def get_total_records(self) -> str:
        """Get total number of records"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM records")
            count = cursor.fetchone()[0]
            return f"{count:,}"
        except Exception as e:
            logger.error(f"Error getting total records: {e}")
            return "0"
    
    def get_records_this_year(self) -> str:
        """Get number of records this year"""
        try:
            current_year = datetime.now().year
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM records 
                WHERE strftime('%Y', date) = ?
            """, (str(current_year),))
            count = cursor.fetchone()[0]
            return f"{count:,}"
        except Exception as e:
            logger.error(f"Error getting records this year: {e}")
            return "0"
    
    def get_records_this_month(self) -> str:
        """Get number of records this month"""
        try:
            current_month = datetime.now().strftime("%Y-%m")
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM records 
                WHERE strftime('%Y-%m', date) = ?
            """, (current_month,))
            count = cursor.fetchone()[0]
            return f"{count:,}"
        except Exception as e:
            logger.error(f"Error getting records this month: {e}")
            return "0"
    
    def get_records_last_n_days(self, n_days: int) -> str:
        """
        Get number of records in last N days
        
        Args:
            n_days: Number of days to look back
            
        Returns:
            Formatted count string
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=n_days)).strftime("%Y-%m-%d")
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM records 
                WHERE date >= ?
            """, (cutoff_date,))
            count = cursor.fetchone()[0]
            return f"{count:,}"
        except Exception as e:
            logger.error(f"Error getting records last {n_days} days: {e}")
            return "0"
    
    def get_last_recorded_species(self) -> str:
        """
        Get the most recently recorded species
        
        Returns:
            String like "Robin (2024-11-22)" or "N/A"
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT species_name, date 
                FROM records 
                ORDER BY date DESC, id DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            
            if row:
                species = row['species_name']
                date = row['date']
                # Try to get common name if species is scientific
                if ' ' in species and species[0].isupper():
                    # Looks like scientific name, try to shorten
                    parts = species.split()
                    if len(parts) >= 2:
                        species = f"{parts[0][0]}. {parts[1]}"
                
                # Format date nicely
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    if date_obj.date() == datetime.now().date():
                        date_str = "Today"
                    elif date_obj.date() == (datetime.now() - timedelta(days=1)).date():
                        date_str = "Yesterday"
                    else:
                        date_str = date_obj.strftime("%d %b")
                except:
                    date_str = date
                
                return f"{species}\n({date_str})"
            else:
                return "N/A"
        except Exception as e:
            logger.error(f"Error getting last recorded species: {e}")
            return "N/A"
    
    def get_total_species(self) -> str:
        """Get total number of unique species"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT taxon_id) FROM records
                WHERE taxon_id IS NOT NULL
            """)
            count = cursor.fetchone()[0]
            return f"{count:,}"
        except Exception as e:
            logger.error(f"Error getting total species: {e}")
            return "0"
    
    def get_unique_sites(self) -> str:
        """Get number of unique sites"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT site_name) FROM records
                WHERE site_name IS NOT NULL AND site_name != ''
            """)
            count = cursor.fetchone()[0]
            return f"{count:,}"
        except Exception as e:
            logger.error(f"Error getting unique sites: {e}")
            return "0"
    
    def _get_default_stats(self) -> Dict[str, str]:
        """Get default stats when database is unavailable"""
        return {
            'total_records': "0",
            'this_year': "0",
            'last_7_days': "0",
            'last_recorded': "N/A",
            'total_species': "0",
            'this_month': "0",
            'last_30_days': "0",
            'unique_sites': "0"
        }
