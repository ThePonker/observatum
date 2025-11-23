"""
Data Tab for Observatum
View, filter, edit, and delete observation records

REFACTORED VERSION - Component-based architecture:
- RecordTableWidget: Table display with sorting
- RecordQueryBuilder: SQL query generation with filters
- This class: Orchestration and data operations
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import sys
import logging
import csv
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tabs.base_tab import BaseTab

# Import new components
from widgets.tables.record_table_widget import RecordTableWidget
from database.queries.record_query_builder import RecordQueryBuilder

# Import optional components
try:
    from widgets.panels.filter_panel import FilterPanel
except ImportError:
    FilterPanel = None

try:
    from dialogs.edit_record_dialog import EditRecordDialog
except ImportError:
    EditRecordDialog = None

logger = logging.getLogger(__name__)


class DataTab(BaseTab):
    """
    Data tab for viewing and managing records
    
    Refactored to use:
    - RecordTableWidget for display
    - RecordQueryBuilder for SQL queries
    """
    
    def setup_ui(self):
        """Create the data tab interface"""
        # Main container
        main_container = ttk.Frame(self, padding="10")
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # Filter panel at top (if available)
        if FilterPanel:
            self.filter_panel = FilterPanel(main_container, self._on_filter_changed)
            self.filter_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        else:
            self.filter_panel = None
            logger.warning("FilterPanel not available - filtering disabled")
        
        # Create query builder
        self.query_builder = RecordQueryBuilder(table_name='records')
        
        # Records table using RecordTableWidget
        table_container = self._create_records_table(main_container)
        table_container.grid(row=1, column=0, sticky="nsew")
        
        # Action buttons at bottom
        button_frame = self._create_action_buttons(main_container)
        button_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        # Load initial data
        self._load_records()
        
        logger.info("DataTab initialized successfully")
    
    def _create_records_table(self, parent) -> ttk.Frame:
        """
        Create the records table view using RecordTableWidget
        
        Args:
            parent: Parent widget
            
        Returns:
            Frame containing table and count label
        """
        # Container frame
        container = ttk.Frame(parent)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        
        # Define columns for the table
        columns = [
            {'id': 'id', 'heading': 'ID', 'width': 50, 'anchor': 'center'},
            {'id': 'date', 'heading': 'Date', 'width': 100},
            {'id': 'species', 'heading': 'Species', 'width': 200},
            {'id': 'site', 'heading': 'Site', 'width': 150},
            {'id': 'gridref', 'heading': 'Grid Ref', 'width': 100},
            {'id': 'recorder', 'heading': 'Recorder', 'width': 120},
            {'id': 'determiner', 'heading': 'Determiner', 'width': 120},
            {'id': 'quantity', 'heading': 'Qty', 'width': 50, 'anchor': 'center'},
            {'id': 'certainty', 'heading': 'Certainty', 'width': 100}
        ]
        
        # Create table widget
        self.table = RecordTableWidget(
            container,
            columns=columns,
            on_double_click=self._edit_selected,
            on_selection_changed=self._on_selection_changed
        )
        self.table.grid(row=0, column=0, sticky="nsew")
        
        # Count label at bottom
        self.count_label = ttk.Label(container, text="0 records")
        self.count_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        # Add right-click context menu to tree
        tree = self.table.get_tree_widget()
        tree.bind('<Button-3>', self._show_context_menu)
        
        return container
    
    def _create_action_buttons(self, parent) -> ttk.Frame:
        """
        Create action buttons
        
        Args:
            parent: Parent widget
            
        Returns:
            Frame containing buttons
        """
        button_frame = ttk.Frame(parent)
        
        # Import button
        ttk.Button(
            button_frame,
            text="Import CSV",
            command=self._import_csv,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        # Export button
        ttk.Button(
            button_frame,
            text="Export CSV",
            command=self._export_to_csv,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(button_frame, orient='vertical').pack(side=tk.LEFT, fill='y', padx=10)
        
        # Edit button
        self.edit_button = ttk.Button(
            button_frame,
            text="Edit",
            command=self._edit_selected,
            width=10,
            state='disabled'
        )
        self.edit_button.pack(side=tk.LEFT, padx=5)
        
        # Delete button
        self.delete_button = ttk.Button(
            button_frame,
            text="Delete",
            command=self._delete_selected,
            width=10,
            state='disabled'
        )
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(button_frame, orient='vertical').pack(side=tk.LEFT, fill='y', padx=10)
        
        # Refresh button
        ttk.Button(
            button_frame,
            text="Refresh",
            command=self.refresh,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        return button_frame
    
    def _load_records(self, filters: dict = None):
        """
        Load records from database with optional filters
        
        Args:
            filters: Dictionary of filter criteria
        """
        try:
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            conn = db_manager.get_observations_connection()
            cursor = conn.cursor()
            
            # Use query builder to get records
            raw_records = self.query_builder.execute_query(cursor, filters)
            
            # Format records for display (extract only the fields we need for the table)
            formatted_records = []
            for record in raw_records:
                # Extract fields matching our column order
                formatted_record = (
                    record[0],   # id
                    record[1],   # date
                    record[2],   # species_name
                    record[3],   # site_name
                    record[4],   # grid_reference
                    record[5],   # recorder
                    record[6],   # determiner
                    record[7] if record[7] else "",  # quantity (blank if None)
                    record[8]    # certainty
                )
                formatted_records.append(formatted_record)
            
            # Load into table widget
            self.table.load_records(formatted_records)
            
            # Update count
            record_count = len(formatted_records)
            self.count_label.config(text=f"{record_count:,} record{'s' if record_count != 1 else ''}")
            
            # Update filter panel if available
            if self.filter_panel:
                species_list = self.query_builder.get_distinct_values(cursor, 'species_name')
                site_list = self.query_builder.get_distinct_values(cursor, 'site_name')
                recorder_list = self.query_builder.get_distinct_values(cursor, 'recorder')
                
                self.filter_panel.update_filter_options(species_list, site_list, recorder_list)
                self.filter_panel.update_count(record_count)
            
            self.update_status(f"Loaded {record_count:,} records")
            logger.info(f"Loaded {record_count} records")
            
        except Exception as e:
            logger.error(f"Error loading records: {e}", exc_info=True)
            messagebox.showerror("Database Error", f"Failed to load records:\n\n{str(e)}")
    
    def _on_filter_changed(self, filters: dict):
        """
        Called when filter values change
        
        Args:
            filters: Dictionary of filter values
        """
        self._load_records(filters)
    
    def _on_selection_changed(self, selected_ids):
        """
        Called when table selection changes
        
        Args:
            selected_ids: List of selected record IDs
        """
        # Enable/disable action buttons based on selection
        has_selection = len(selected_ids) > 0
        self.edit_button.config(state='normal' if has_selection else 'disabled')
        self.delete_button.config(state='normal' if has_selection else 'disabled')
    
    def _edit_selected(self, record_id=None):
        """
        Edit selected record(s)
        
        Args:
            record_id: Specific record ID to edit (from double-click)
        """
        if not EditRecordDialog:
            messagebox.showinfo("Not Available", "Edit dialog not yet implemented")
            return
        
        # Get record ID to edit
        if record_id is None:
            selected = self.table.get_selected_ids()
            if not selected:
                return
            record_id = selected[0]  # Edit first selected
        
        # Get full record data from database
        try:
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            conn = db_manager.get_observations_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id, species_name, taxon_id, site_name, grid_reference, date,
                    recorder, determiner, certainty, sex, quantity,
                    sample_method, observation_type, sample_comment
                FROM records WHERE id = ?
            """, (record_id,))
            
            record = cursor.fetchone()
            
            if not record:
                messagebox.showerror("Error", "Record not found")
                return
            
            # Convert to dict
            record_data = {
                'id': record[0],
                'species_name': record[1],
                'taxon_id': record[2],
                'site_name': record[3],
                'grid_reference': record[4],
                'date': record[5],
                'recorder': record[6],
                'determiner': record[7],
                'certainty': record[8],
                'sex': record[9],
                'quantity': record[10],
                'sample_method': record[11],
                'observation_type': record[12],
                'sample_comment': record[13]
            }
            
            # Open edit dialog
            dialog = EditRecordDialog(self, record_data, self._on_record_saved)
            
        except Exception as e:
            logger.error(f"Error loading record for edit: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to load record:\n\n{str(e)}")
    
    def _on_record_saved(self, updated_data: dict):
        """
        Callback when record is saved from edit dialog
        
        Args:
            updated_data: Updated record data
        """
        try:
            # Get database connection
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            conn = db_manager.get_observations_connection()
            cursor = conn.cursor()
            
            # Update the record
            cursor.execute("""
                UPDATE records SET
                    species_name = ?,
                    site_name = ?,
                    grid_reference = ?,
                    date = ?,
                    recorder = ?,
                    determiner = ?,
                    certainty = ?,
                    sex = ?,
                    quantity = ?,
                    sample_method = ?,
                    observation_type = ?,
                    sample_comment = ?
                WHERE id = ?
            """, (
                updated_data['species_name'],
                updated_data['site_name'],
                updated_data['grid_reference'],
                updated_data['date'],
                updated_data['recorder'],
                updated_data['determiner'],
                updated_data['certainty'],
                updated_data.get('sex'),
                updated_data.get('quantity'),
                updated_data.get('sample_method'),
                updated_data.get('observation_type'),
                updated_data.get('sample_comment'),
                updated_data['id']
            ))
            
            conn.commit()
            
            # Refresh table
            self._load_records()
            
            # Show success message
            messagebox.showinfo("Success", "Record updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating record: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to update record:\n\n{str(e)}")
    
    def _delete_selected(self):
        """Delete selected record(s)"""
        selected = self.table.get_selected_ids()
        
        if not selected:
            return
        
        # Confirm deletion
        count = len(selected)
        message = f"Are you sure you want to delete {count} record{'s' if count != 1 else ''}?\n\n"
        message += "This action cannot be undone."
        
        if not messagebox.askyesno("Confirm Delete", message):
            return
        
        # Delete records
        try:
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            conn = db_manager.get_observations_connection()
            cursor = conn.cursor()
            
            # Delete each selected record
            for record_id in selected:
                cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
            
            conn.commit()
            
            # Refresh table
            self._load_records()
            
            self.update_status(f"Deleted {count} record{'s' if count != 1 else ''}")
            messagebox.showinfo("Success", f"Deleted {count} record{'s' if count != 1 else ''} successfully")
            
        except Exception as e:
            logger.error(f"Error deleting records: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to delete records:\n\n{str(e)}")
    
    def _export_to_csv(self):
        """Export visible records to CSV"""
        # Get file path from user
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Records to CSV"
        )
        
        if not file_path:
            return
        
        try:
            # Get tree widget to access displayed data
            tree = self.table.get_tree_widget()
            
            # Get column names
            columns = [col['heading'] for col in self.table.columns]
            
            # Open CSV file for writing
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(columns)
                
                # Write data rows
                for item in tree.get_children():
                    values = tree.item(item)['values']
                    writer.writerow(values)
            
            record_count = self.table.get_record_count()
            messagebox.showinfo("Export Complete", f"Exported {record_count} records to:\n{file_path}")
            self.update_status(f"Exported {record_count} records to CSV")
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}", exc_info=True)
            messagebox.showerror("Export Error", f"Failed to export records:\n\n{str(e)}")
    
    def _import_csv(self):
        """Import records from CSV (placeholder)"""
        messagebox.showinfo("Not Implemented", "CSV import functionality coming soon!")
    
    def _show_context_menu(self, event):
        """
        Show context menu on right-click
        
        Args:
            event: Click event
        """
        # Get tree widget
        tree = self.table.get_tree_widget()
        
        # Identify clicked item
        item = tree.identify_row(event.y)
        if not item:
            return
        
        # Select the item
        tree.selection_set(item)
        
        # Create context menu
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Edit", command=lambda: self._edit_selected(item))
        menu.add_command(label="Delete", command=self._delete_selected)
        menu.add_separator()
        menu.add_command(label="Copy ID", command=lambda: self._copy_field('id'))
        menu.add_command(label="Copy Species", command=lambda: self._copy_field('species'))
        
        # Show menu
        menu.post(event.x_root, event.y_root)
    
    def _copy_field(self, column: str):
        """
        Copy field value to clipboard
        
        Args:
            column: Column ID to copy
        """
        values = self.table.get_selected_values(column)
        if values:
            self.clipboard_clear()
            self.clipboard_append(values[0])
            self.update_status(f"Copied {column}: {values[0]}")
    
    def refresh(self):
        """Refresh the records table"""
        self._load_records()