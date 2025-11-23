"""
Edit Record Dialog for Observatum
Dialog for editing existing observation records

Allows users to modify any field and save changes
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Dict, Optional
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.validation.validators import validate_all_record_fields, GridReferenceValidator

logger = logging.getLogger(__name__)


class EditRecordDialog(tk.Toplevel):
    """Dialog for editing an existing record"""
    
    def __init__(self, parent, record_data: Dict, on_save: callable):
        """
        Initialize edit record dialog
        
        Args:
            parent: Parent window
            record_data: Dictionary with current record data
            on_save: Callback function when record is saved (receives updated record_data)
        """
        super().__init__(parent)
        self.record_data = record_data
        self.on_save = on_save
        
        # Configure window
        self.title(f"Edit Record #{record_data.get('id', '')}")
        self.geometry("600x700")
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        self._create_form()
        self._populate_form()
        
    def _create_form(self):
        """Create the edit form"""
        # Main container with scrollbar
        container = ttk.Frame(self, padding="10")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Form area
        form_frame = ttk.Frame(container)
        form_frame.pack(fill=tk.BOTH, expand=True)
        form_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Species Name* (read-only - show scientific name)
        ttk.Label(form_frame, text="Species:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.species_var = tk.StringVar()
        species_entry = ttk.Entry(form_frame, textvariable=self.species_var, state="readonly")
        species_entry.grid(row=row, column=1, sticky="ew", pady=3)
        
        row += 1
        
        # Site Name*
        ttk.Label(form_frame, text="Site Name:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.site_var = tk.StringVar()
        site_entry = ttk.Entry(form_frame, textvariable=self.site_var)
        site_entry.grid(row=row, column=1, sticky="ew", pady=3)
        
        row += 1
        
        # Grid Reference*
        ttk.Label(form_frame, text="Grid Ref:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.gridref_var = tk.StringVar()
        self.gridref_var.trace('w', self._on_gridref_change)
        gridref_entry = ttk.Entry(form_frame, textvariable=self.gridref_var)
        gridref_entry.grid(row=row, column=1, sticky="ew", pady=3)
        
        # Grid ref validation label
        self.gridref_status = ttk.Label(form_frame, text="", foreground="gray")
        self.gridref_status.grid(row=row, column=2, sticky="w", padx=(5, 0))
        
        row += 1
        
        # Date*
        ttk.Label(form_frame, text="Date:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.date_var = tk.StringVar()
        date_entry = ttk.Entry(form_frame, textvariable=self.date_var)
        date_entry.grid(row=row, column=1, sticky="ew", pady=3)
        
        row += 1
        
        # Recorder*
        ttk.Label(form_frame, text="Recorder:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.recorder_var = tk.StringVar()
        recorder_entry = ttk.Entry(form_frame, textvariable=self.recorder_var)
        recorder_entry.grid(row=row, column=1, sticky="ew", pady=3)
        
        row += 1
        
        # Determiner*
        ttk.Label(form_frame, text="Determiner:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.determiner_var = tk.StringVar()
        determiner_entry = ttk.Entry(form_frame, textvariable=self.determiner_var)
        determiner_entry.grid(row=row, column=1, sticky="ew", pady=3)
        
        row += 1
        
        # Certainty*
        ttk.Label(form_frame, text="Certainty:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.certainty_var = tk.StringVar()
        certainty_combo = ttk.Combobox(
            form_frame,
            textvariable=self.certainty_var,
            values=["Certain", "Likely", "Uncertain"],
            state="readonly"
        )
        certainty_combo.grid(row=row, column=1, sticky="ew", pady=3)
        
        row += 1
        
        # Sex (optional)
        ttk.Label(form_frame, text="Sex:").grid(row=row, column=0, sticky="w", pady=3)
        self.sex_var = tk.StringVar()
        sex_combo = ttk.Combobox(
            form_frame,
            textvariable=self.sex_var,
            values=["", "Male", "Female", "Unknown"],
            state="readonly"
        )
        sex_combo.grid(row=row, column=1, sticky="ew", pady=3)
        
        row += 1
        
        # Quantity (optional)
        ttk.Label(form_frame, text="Quantity:").grid(row=row, column=0, sticky="w", pady=3)
        self.quantity_var = tk.StringVar()
        quantity_entry = ttk.Entry(form_frame, textvariable=self.quantity_var)
        quantity_entry.grid(row=row, column=1, sticky="ew", pady=3)
        
        row += 1
        
        # Sample Method (optional)
        ttk.Label(form_frame, text="Sample Method:").grid(row=row, column=0, sticky="w", pady=3)
        self.sample_method_var = tk.StringVar()
        method_entry = ttk.Entry(form_frame, textvariable=self.sample_method_var)
        method_entry.grid(row=row, column=1, sticky="ew", pady=3)
        
        row += 1
        
        # Observation Type (optional)
        ttk.Label(form_frame, text="Observation Type:").grid(row=row, column=0, sticky="w", pady=3)
        self.obs_type_var = tk.StringVar()
        obs_type_entry = ttk.Entry(form_frame, textvariable=self.obs_type_var)
        obs_type_entry.grid(row=row, column=1, sticky="ew", pady=3)
        
        row += 1
        
        # Comment (optional)
        ttk.Label(form_frame, text="Comment:").grid(row=row, column=0, sticky="nw", pady=3)
        self.comment_text = tk.Text(form_frame, height=5, wrap=tk.WORD)
        self.comment_text.grid(row=row, column=1, sticky="ew", pady=3)
        
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Save Changes", command=self._save).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)
        
        # Record info
        info_text = f"Record ID: {self.record_data.get('id', 'N/A')} | Created: {self.record_data.get('created_at', 'N/A')}"
        ttk.Label(button_frame, text=info_text, foreground="gray", font=("TkDefaultFont", 8)).pack(side=tk.LEFT)
        
    def _populate_form(self):
        """Populate form with current record data"""
        self.species_var.set(self.record_data.get('species_name', ''))
        self.site_var.set(self.record_data.get('site_name', ''))
        self.gridref_var.set(self.record_data.get('grid_reference', ''))
        self.date_var.set(self.record_data.get('date', ''))
        self.recorder_var.set(self.record_data.get('recorder', ''))
        self.determiner_var.set(self.record_data.get('determiner', ''))
        self.certainty_var.set(self.record_data.get('certainty', 'Certain'))
        self.sex_var.set(self.record_data.get('sex', '') or '')
        self.quantity_var.set(str(self.record_data.get('quantity', '')) if self.record_data.get('quantity') else '')
        self.sample_method_var.set(self.record_data.get('sample_method', '') or '')
        self.obs_type_var.set(self.record_data.get('observation_type', '') or '')
        
        comment = self.record_data.get('sample_comment', '') or ''
        self.comment_text.insert("1.0", comment)
    
    def _on_gridref_change(self, *args):
        """Validate grid reference as user types"""
        gridref = self.gridref_var.get().strip()
        if not gridref:
            self.gridref_status.config(text="", foreground="gray")
            return
        
        is_valid, error = GridReferenceValidator.validate(gridref)
        if is_valid:
            self.gridref_status.config(text="✓", foreground="green")
        else:
            self.gridref_status.config(text="✗", foreground="red")
    
    def _save(self):
        """Save changes to record"""
        # Collect updated data
        updated_data = {
            'id': self.record_data['id'],
            'species_name': self.species_var.get().strip(),
            'taxon_id': self.record_data.get('taxon_id'),  # Keep original TVK
            'site_name': self.site_var.get().strip(),
            'grid_reference': self.gridref_var.get().strip(),
            'date': self.date_var.get().strip(),
            'recorder': self.recorder_var.get().strip(),
            'determiner': self.determiner_var.get().strip(),
            'certainty': self.certainty_var.get(),
            'sex': self.sex_var.get() if self.sex_var.get() else None,
            'quantity': int(self.quantity_var.get()) if self.quantity_var.get().strip() else None,
            'sample_method': self.sample_method_var.get().strip() if self.sample_method_var.get().strip() else None,
            'observation_type': self.obs_type_var.get().strip() if self.obs_type_var.get().strip() else None,
            'sample_comment': self.comment_text.get("1.0", tk.END).strip() if self.comment_text.get("1.0", tk.END).strip() else None
        }
        
        # Validate
        is_valid, errors = validate_all_record_fields(updated_data)
        
        if not is_valid:
            messagebox.showerror(
                "Validation Error",
                "Please correct the following errors:\n\n• " + "\n• ".join(errors)
            )
            return
        
        # Confirm save
        result = messagebox.askyesno(
            "Save Changes",
            "Are you sure you want to save these changes?"
        )
        
        if result:
            try:
                self.on_save(updated_data)
                self.destroy()
            except Exception as e:
                logger.error(f"Error saving record: {e}")
                messagebox.showerror(
                    "Save Error",
                    f"Failed to save changes:\n\n{str(e)}"
                )
