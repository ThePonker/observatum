"""
Record Query Builder for Observatum
Builds SQL queries for fetching observation records with filters

Extracted from data_tab.py to separate data access logic from UI.
This makes queries reusable across different tabs (Data, Longhorns, Collection).
"""

import logging

logger = logging.getLogger(__name__)


class RecordQueryBuilder:
    """
    Builds SQL queries for fetching observation records
    
    Supports filtering by:
    - Search term (species, site, recorder)
    - Date range
    - Specific species
    - Specific site
    - Specific recorder
    """
    
    def __init__(self, table_name='records'):
        """
        Initialize query builder
        
        Args:
            table_name: Name of the table to query (default: 'records')
        """
        self.table_name = table_name
    
    def build_query(self, filters=None, columns=None, order_by=None):
        """
        Build SELECT query with optional filters
        
        Args:
            filters: Dict of filter criteria
            columns: List of column names to select (None = all)
            order_by: Order by clause (default: "date DESC, id DESC")
            
        Returns:
            tuple: (query_string, params_list)
        """
        # Default columns if not specified
        if columns is None:
            columns = [
                'id', 'date', 'species_name', 'site_name', 'grid_reference',
                'recorder', 'determiner', 'quantity', 'certainty',
                'taxon_id', 'sex', 'sample_method', 'observation_type',
                'sample_comment', 'created_at'
            ]
        
        # Build SELECT clause
        columns_str = ', '.join(columns)
        query = f"SELECT {columns_str} FROM {self.table_name} WHERE 1=1"
        params = []
        
        # Apply filters
        if filters:
            filter_clauses, filter_params = self._build_filter_clauses(filters)
            query += filter_clauses
            params.extend(filter_params)
        
        # Add ORDER BY
        if order_by is None:
            order_by = "date DESC, id DESC"
        query += f" ORDER BY {order_by}"
        
        return query, params
    
    def _build_filter_clauses(self, filters):
        """
        Build WHERE clause from filter dict
        
        Args:
            filters: Dict of filter criteria
            
        Returns:
            tuple: (where_clauses_string, params_list)
        """
        clauses = ""
        params = []
        
        # Search filter (searches across multiple fields)
        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            clauses += """ AND (
                species_name LIKE ? OR 
                site_name LIKE ? OR 
                recorder LIKE ?
            )"""
            params.extend([search_term, search_term, search_term])
        
        # Date range filters
        if filters.get('date_from'):
            clauses += " AND date >= ?"
            params.append(filters['date_from'])
        
        if filters.get('date_to'):
            clauses += " AND date <= ?"
            params.append(filters['date_to'])
        
        # Species filter (exact match)
        if filters.get('species'):
            clauses += " AND species_name = ?"
            params.append(filters['species'])
        
        # Site filter (exact match)
        if filters.get('site'):
            clauses += " AND site_name = ?"
            params.append(filters['site'])
        
        # Recorder filter (exact match)
        if filters.get('recorder'):
            clauses += " AND recorder = ?"
            params.append(filters['recorder'])
        
        # Certainty filter
        if filters.get('certainty'):
            clauses += " AND certainty = ?"
            params.append(filters['certainty'])
        
        # Sex filter
        if filters.get('sex'):
            clauses += " AND sex = ?"
            params.append(filters['sex'])
        
        return clauses, params
    
    def build_distinct_values_query(self, column):
        """
        Build query to get distinct values for a column
        
        Used for populating filter dropdowns.
        
        Args:
            column: Column name to get distinct values for
            
        Returns:
            str: SQL query string
        """
        return f"SELECT DISTINCT {column} FROM {self.table_name} WHERE {column} IS NOT NULL ORDER BY {column}"
    
    def build_count_query(self, filters=None):
        """
        Build COUNT query with optional filters
        
        Args:
            filters: Dict of filter criteria
            
        Returns:
            tuple: (query_string, params_list)
        """
        query = f"SELECT COUNT(*) FROM {self.table_name} WHERE 1=1"
        params = []
        
        if filters:
            filter_clauses, filter_params = self._build_filter_clauses(filters)
            query += filter_clauses
            params.extend(filter_params)
        
        return query, params
    
    def execute_query(self, cursor, filters=None, columns=None):
        """
        Build and execute query
        
        Args:
            cursor: Database cursor
            filters: Dict of filter criteria
            columns: List of columns to select
            
        Returns:
            list: Query results
        """
        query, params = self.build_query(filters, columns)
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def get_distinct_values(self, cursor, column):
        """
        Get distinct values for a column
        
        Args:
            cursor: Database cursor
            column: Column name
            
        Returns:
            list: List of distinct values
        """
        query = self.build_distinct_values_query(column)
        cursor.execute(query)
        return [row[0] for row in cursor.fetchall()]
