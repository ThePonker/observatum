"""
Data Tab for Observatum
View, filter, edit, and delete observation records

Features:
- Sortable table view of all records
- Advanced filtering (date, species, site, recorder)
- Edit records (double-click)
- Delete records (selected)
- Export to CSV
- Bulk operations
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
try:
    from widgets.filter_panel import FilterPanel
    from dialogs.edit_record_dialog import EditRecordDialog
except ImportError:
    FilterPanel = None
    EditRecordDialog = None

logger = logging.getLogger(__name__)


class DataTab(BaseTab):
    """Data tab for viewing and managing records"""
    
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
        
        # Records table
        table_frame = self._create_records_table(main_container)
        table_frame.grid(row=1, column=0, sticky="nsew")
        
        # Action buttons at bottom
        button_frame = self._create_action_buttons(main_container)
        button_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        # Load initial data
        self._load_records()
        
    def _create_records_table(self, parent) -> ttk.Frame:
        """
        Create the records table view
        
        Args:
            parent: Parent widget
            
        Returns:
            Frame containing table
        """
        table_frame = ttk.Frame(parent)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Create treeview with scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        vsb.grid(row=0, column=1, sticky="ns")
        
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Define columns
        columns = (
            "ID", "Date", "Species", "Site", "Grid Ref", 
            "Recorder", "Determiner", "Quantity", "Certainty"
        )
        
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode="extended"
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        column_config = {
            "ID": (50, tk.CENTER),
            "Date": (100, tk.CENTER),
            "Species": (200, tk.W),
            "Site": (150, tk.W),
            "Grid Ref": (100, tk.CENTER),
            "Recorder": (120, tk.W),
            "Determiner": (120, tk.W),
            "Quantity": (70, tk.CENTER),
            "Certainty": (80, tk.CENTER)
        }
        
        for col in columns:
            width, anchor = column_config.get(col, (100, tk.W))
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_column(c))
            self.tree.column(col, width=width, anchor=anchor)
        
        # Bind double-click to edit
        self.tree.bind("<Double-Button-1>", self._on_double_click)
        
        # Bind right-click for context menu
        self.tree.bind("<Button-3>", self._show_context_menu)
        
        return table_frame
        
    def _create_action_buttons(self, parent) -> ttk.Frame:
        """
        Create action buttons
        
        Args:
            parent: Parent widget
            
        Returns:
            Frame containing buttons
        """
        button_frame = ttk.Frame(parent)
        
        # Left side buttons
        ttk.Button(
            button_frame,
            text="Refresh",
            command=self._load_records,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="Edit Selected",
            command=self._edit_selected,
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Delete Selected",
            command=self._delete_selected,
            width=14
        ).pack(side=tk.LEFT, padx=5)
        
        # Right side buttons
        ttk.Button(
            button_frame,
            text="Export to CSV",
            command=self._export_to_csv,
            width=14
        ).pack(side=tk.RIGHT)
        
        # Record count label
        self.count_label = ttk.Label(button_frame, text="0 records", foreground="gray")
        self.count_label.pack(side=tk.RIGHT, padx=(0, 10))
        
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
            
            # Build query with filters
            query = """
                SELECT 
                    id, date, species_name, site_name, grid_reference,
                    recorder, determiner, quantity, certainty,
                    taxon_id, sex, sample_method, observation_type, sample_comment,
                    created_at
                FROM records
                WHERE 1=1
            """
            params = []
            
            if filters:
                # Search filter (searches species, site, recorder)
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query += """ AND (
                        species_name LIKE ? OR 
                        site_name LIKE ? OR 
                        recorder LIKE ?
                    )"""
                    params.extend([search_term, search_term, search_term])
                
                # Date range filters
                if filters.get('date_from'):
                    query += " AND date >= ?"
                    params.append(filters['date_from'])
                
                if filters.get('date_to'):
                    query += " AND date <= ?"
                    params.append(filters['date_to'])
                
                # Species filter
                if filters.get('species'):
                    query += " AND species_name = ?"
                    params.append(filters['species'])
                
                # Site filter
                if filters.get('site'):
                    query += " AND site_name = ?"
                    params.append(filters['site'])
                
                # Recorder filter
                if filters.get('recorder'):
                    query += " AND recorder = ?"
                    params.append(filters['recorder'])
            
            query += " ORDER BY date DESC, id DESC"
            
            cursor.execute(query, params)
            records = cursor.fetchall()
            
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Insert records
            for record in records:
                # Format display values
                record_id = record[0]
                date = record[1]
                species = record[2]
                site = record[3]
                gridref = record[4]
                recorder = record[5]
                determiner = record[6]
                quantity = record[7] if record[7] else ""
                certainty = record[8]
                
                # Insert into tree
                self.tree.insert("", "end", iid=str(record_id), values=(
                    record_id, date, species, site, gridref,
                    recorder, determiner, quantity, certainty
                ))
                
                # Store full record data as tag for editing
            
            # Update count
            self.count_label.config(text=f"{len(records):,} record{'s' if len(records) != 1 else ''}")
            
            # Update filter panel if available
            if self.filter_panel:
                # Get unique values for filter dropdowns
                cursor.execute("SELECT DISTINCT species_name FROM records ORDER BY species_name")
                species_list = [row[0] for row in cursor.fetchall()]
                
                cursor.execute("SELECT DISTINCT site_name FROM records ORDER BY site_name")
                site_list = [row[0] for row in cursor.fetchall()]
                
                cursor.execute("SELECT DISTINCT recorder FROM records ORDER BY recorder")
                recorder_list = [row[0] for row in cursor.fetchall()]
                
                self.filter_panel.update_filter_options(species_list, site_list, recorder_list)
                self.filter_panel.update_count(len(records))
            
            self.update_status(f"Loaded {len(records):,} records")
            
        except Exception as e:
            logger.error(f"Error loading records: {e}")
            messagebox.showerror("Database Error", f"Failed to load records:\n\n{str(e)}")
    
    def _on_filter_changed(self, filters: dict):
        """
        Called when filter values change
        
        Args:
            filters: Dictionary of filter values
        """
        self._load_records(filters)
    
    def _sort_column(self, col: str):
        """
        Sort table by column
        
        Args:
            col: Column name to sort by
        """
        # Get all items
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        
        # Determine sort order (toggle)
        if not hasattr(self, '_sort_reverse'):
            self._sort_reverse = {}
        
        reverse = self._sort_reverse.get(col, False)
        self._sort_reverse[col] = not reverse
        
        # Sort items
        try:
            # Try numeric sort first
            items.sort(key=lambda x: (int(x[0]) if x[0].isdigit() else x[0]), reverse=reverse)
        except:
            # Fall back to string sort
            items.sort(reverse=reverse)
        
        # Rearrange items in sorted order
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
    
    def _on_double_click(self, event):
        """Handle double-click to edit record"""
        self._edit_selected()
    
    def _edit_selected(self):
        """Edit the selected record"""
        selection = self.tree.selection()
        
        if not selection:
            messagebox.showwarning("No Selection", "Please select a record to edit.")
            return
        
        if len(selection) > 1:
            messagebox.showwarning("Multiple Selection", "Please select only one record to edit.")
            return
        
        if not EditRecordDialog:
            messagebox.showerror("Feature Unavailable", "Edit dialog not available.")
            return
        
        # Get record ID
        record_id = selection[0]
        
        # Load full record data from database
        try:
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            conn = db_manager.get_observations_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM records WHERE id = ?
            """, (record_id,))
            
            row = cursor.fetchone()
            if not row:
                messagebox.showerror("Error", "Record not found in database.")
                return
            
            # Convert to dictionary
            columns = [description[0] for description in cursor.description]
            record_data = dict(zip(columns, row))
            
            # Open edit dialog
            EditRecordDialog(self, record_data, self._on_record_saved)
            
        except Exception as e:
            logger.error(f"Error loading record for edit: {e}")
            messagebox.showerror("Database Error", f"Failed to load record:\n\n{str(e)}")
    
    def _on_record_saved(self, updated_data: dict):
        """
        Callback when record is saved from edit dialog
        
        Args:
            updated_data: Dictionary with updated record data
        """
        try:
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            conn = db_manager.get_observations_connection()
            cursor = conn.cursor()
            
            # Update record
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
                updated_data['sex'],
                updated_data['quantity'],
                updated_data['sample_method'],
                updated_data['observation_type'],
                updated_data['sample_comment'],
                updated_data['id']
            ))
            
            conn.commit()
            
            # Reload records
            filters = self.filter_panel.get_filters() if self.filter_panel else None
            self._load_records(filters)
            
            self.update_status(f"Record #{updated_data['id']} updated successfully")
            
        except Exception as e:
            logger.error(f"Error saving record: {e}")
            messagebox.showerror("Save Error", f"Failed to save record:\n\n{str(e)}")
    
    def _delete_selected(self):
        """Delete selected records"""
        selection = self.tree.selection()
        
        if not selection:
            messagebox.showwarning("No Selection", "Please select record(s) to delete.")
            return
        
        # Confirm deletion
        count = len(selection)
        result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete {count} record{'s' if count > 1 else ''}?\n\n"
            "This action cannot be undone.",
            icon=messagebox.WARNING
        )
        
        if not result:
            return
        
        try:
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            conn = db_manager.get_observations_connection()
            cursor = conn.cursor()
            
            # Delete each record
            for record_id in selection:
                cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
            
            conn.commit()
            
            # Reload records
            filters = self.filter_panel.get_filters() if self.filter_panel else None
            self._load_records(filters)
            
            self.update_status(f"Deleted {count} record{'s' if count > 1 else ''}")
            
        except Exception as e:
            logger.error(f"Error deleting records: {e}")
            messagebox.showerror("Delete Error", f"Failed to delete records:\n\n{str(e)}")
    
    def _export_to_csv(self):
        """Export visible records to CSV"""
        # Get all visible records
        items = self.tree.get_children()
        
        if not items:
            messagebox.showinfo("No Data", "No records to export.")
            return
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Export to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"observatum_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                columns = self.tree['columns']
                writer.writerow(columns)
                
                # Write data
                for item in items:
                    values = [self.tree.set(item, col) for col in columns]
                    writer.writerow(values)
            
            messagebox.showinfo(
                "Export Successful",
                f"Exported {len(items)} records to:\n\n{filename}"
            )
            self.update_status(f"Exported {len(items)} records to CSV")
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            messagebox.showerror("Export Error", f"Failed to export:\n\n{str(e)}")
    
    def _show_context_menu(self, event):
        """Show right-click context menu"""
        # Select item under cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            
            # Create context menu
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Edit Record", command=self._edit_selected)
            menu.add_command(label="Delete Record", command=self._delete_selected)
            menu.add_separator()
            menu.add_command(label="Copy Grid Reference", command=lambda: self._copy_field('Grid Ref'))
            menu.add_command(label="Copy Species Name", command=lambda: self._copy_field('Species'))
            
            menu.post(event.x_root, event.y_root)
    
    def _copy_field(self, column: str):
        """Copy field value to clipboard"""
        selection = self.tree.selection()
        if selection:
            value = self.tree.set(selection[0], column)
            self.clipboard_clear()
            self.clipboard_append(value)
            self.update_status(f"Copied {column}: {value}")
    
    def refresh(self):
        """Refresh the data tab"""
        filters = self.filter_panel.get_filters() if self.filter_panel else None
        self._load_records(filters)
        self.update_status("Data tab refreshed")
