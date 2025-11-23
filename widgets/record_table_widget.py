"""
Record Table Widget for Observatum
Reusable table component for displaying observation records

Extracted from data_tab.py to be reusable across:
- Data Tab
- Longhorns Tab  
- Insect Collection Tab

Configurable columns, sorting, context menus, and double-click editing.
"""

import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)


class RecordTableWidget(ttk.Frame):
    """
    Reusable table widget for displaying records
    
    Features:
    - Configurable columns
    - Sortable columns (click header)
    - Context menu (right-click)
    - Double-click to edit
    - Selection tracking
    """
    
    def __init__(self, parent, columns, on_double_click=None, on_selection_changed=None):
        """
        Initialize the table widget
        
        Args:
            parent: Parent widget
            columns: List of column dicts with keys:
                     - 'id': Column identifier
                     - 'heading': Display name
                     - 'width': Column width in pixels
                     - 'anchor': Text alignment (optional, default 'w')
            on_double_click: Callback function(record_id) when row double-clicked
            on_selection_changed: Callback function(selected_ids) when selection changes
        """
        super().__init__(parent)
        
        self.columns = columns
        self.on_double_click_callback = on_double_click
        self.on_selection_changed_callback = on_selection_changed
        
        # Sort tracking
        self._sort_reverse = {}
        
        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Create table
        self._create_table()
        
        logger.debug("RecordTableWidget initialized")
    
    def _create_table(self):
        """Create the treeview table with scrollbars"""
        # Create treeview
        column_ids = [col['id'] for col in self.columns]
        
        self.tree = ttk.Treeview(
            self,
            columns=column_ids,
            show='headings',
            selectmode='extended'  # Allow multiple selection
        )
        
        # Configure columns
        for col in self.columns:
            self.tree.heading(
                col['id'],
                text=col['heading'],
                command=lambda c=col['id']: self._sort_column(c)
            )
            self.tree.column(
                col['id'],
                width=col['width'],
                anchor=col.get('anchor', 'w')
            )
        
        # Add scrollbars
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Bind events
        self.tree.bind('<Double-Button-1>', self._on_double_click)
        self.tree.bind('<<TreeviewSelect>>', self._on_selection_changed)
        self.tree.bind('<Button-3>', self._on_right_click)  # Right-click for context menu
        
        logger.debug("Table created with {} columns".format(len(self.columns)))
    
    def _sort_column(self, col):
        """
        Sort table by column
        
        Args:
            col: Column identifier to sort by
        """
        # Get all items with their values for this column
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        
        # Toggle sort order
        reverse = self._sort_reverse.get(col, False)
        self._sort_reverse[col] = not reverse
        
        # Sort items
        try:
            # Try numeric sort first (for ID, quantity columns)
            items.sort(key=lambda x: (int(x[0]) if x[0] and str(x[0]).isdigit() else x[0]), reverse=reverse)
        except (ValueError, TypeError):
            # Fall back to string sort
            items.sort(reverse=reverse)
        
        # Rearrange items in sorted order
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
        
        logger.debug(f"Sorted by {col}, reverse={reverse}")
    
    def _on_double_click(self, event):
        """Handle double-click event"""
        selection = self.tree.selection()
        if selection and self.on_double_click_callback:
            # Get first selected item ID
            record_id = selection[0]
            self.on_double_click_callback(record_id)
    
    def _on_selection_changed(self, event):
        """Handle selection change event"""
        if self.on_selection_changed_callback:
            selected_ids = self.tree.selection()
            self.on_selection_changed_callback(selected_ids)
    
    def _on_right_click(self, event):
        """Handle right-click for context menu (to be implemented by parent)"""
        # This is a placeholder - parent class can override or bind differently
        pass
    
    def load_records(self, records):
        """
        Load records into table
        
        Args:
            records: List of tuples matching column order
        """
        # Clear existing items
        self.clear()
        
        # Insert records
        for record in records:
            # First value is typically the ID
            record_id = str(record[0])
            
            # Create values tuple for display
            values = record
            
            # Insert into tree
            self.tree.insert("", "end", iid=record_id, values=values)
        
        logger.debug(f"Loaded {len(records)} records into table")
    
    def clear(self):
        """Clear all items from table"""
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def get_selected_ids(self):
        """
        Get list of selected record IDs
        
        Returns:
            list: List of selected record IDs (as strings)
        """
        return list(self.tree.selection())
    
    def get_selected_values(self, column_id):
        """
        Get values from selected rows for a specific column
        
        Args:
            column_id: Column identifier
            
        Returns:
            list: List of values from selected rows
        """
        selected = self.tree.selection()
        values = []
        for item in selected:
            value = self.tree.set(item, column_id)
            values.append(value)
        return values
    
    def get_all_values(self, column_id):
        """
        Get all values for a specific column
        
        Args:
            column_id: Column identifier
            
        Returns:
            list: List of all values in the column
        """
        values = []
        for item in self.tree.get_children():
            value = self.tree.set(item, column_id)
            values.append(value)
        return values
    
    def get_record_count(self):
        """
        Get number of records currently displayed
        
        Returns:
            int: Number of records
        """
        return len(self.tree.get_children())
    
    def select_record(self, record_id):
        """
        Select a specific record by ID
        
        Args:
            record_id: Record ID to select
        """
        self.tree.selection_set(str(record_id))
        self.tree.see(str(record_id))  # Scroll to make visible
    
    def get_tree_widget(self):
        """
        Get the underlying Treeview widget for advanced usage
        
        Returns:
            ttk.Treeview: The treeview widget
        """
        return self.tree
