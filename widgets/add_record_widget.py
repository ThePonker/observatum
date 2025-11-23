"""
Add Record Widget for Observatum
Comprehensive data entry form for adding new observation records

This widget provides a complete form for entering species observations
with UKSI species search, UK grid reference validation, and auto-save
of default values from settings.

UPDATED: 23 November 2025 - Added UUID generation for iRecord integration
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, Dict
import logging
import json
from pathlib import Path
import uuid  # ADDED: For UUID generation

from database.db_manager import get_db_manager
from database.uksi_handler import UKSIHandler
from utils.validators import GridReferenceValidator, validate_all_record_fields

logger = logging.getLogger(__name__)


class AddRecordWidget(ttk.LabelFrame):
    """
    Widget for adding a single observation record
    
    Features:
    - Species autocomplete with UKSI integration
    - UK grid reference validation
    - Required field indicators
    - Settings integration for default values
    - Real-time validation feedback
    """
    
    def __init__(self, parent, app_instance, **kwargs):
        """
        Initialize the Add Record widget
        
        Args:
            parent: Parent widget
            app_instance: Reference to main application
        """
        super().__init__(parent, text="Add Single Record", padding="15", **kwargs)
        
        self.parent = parent
        self.app = app_instance
        
        # Species autocomplete data
        self.species_results = []
        self.selected_species = None
        self.autocomplete_window = None
        
        # Load settings
        self.settings = self._load_settings()
        
        # Create the form
        self._create_form()
        
        # Apply default values from settings
        self._apply_defaults()
        
    def _load_settings(self) -> Dict:
        """Load settings from config file"""
        config_file = Path(__file__).parent.parent / 'data' / 'config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
        return {}
    
    def _create_form(self):
        """Create the data entry form"""
        # Configure grid
        self.columnconfigure(1, weight=1)
        
        row = 0
        
        # Species Search* (Required)
        ttk.Label(self, text="Species Search:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=5
        )
        
        species_frame = ttk.Frame(self)
        species_frame.grid(row=row, column=1, sticky="ew", pady=5)
        species_frame.columnconfigure(0, weight=1)
        
        self.species_var = tk.StringVar()
        self.species_var.trace('w', self._on_species_search)
        
        self.species_entry = ttk.Entry(species_frame, textvariable=self.species_var)
        self.species_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.species_entry.bind('<Return>', lambda e: self._select_first_result())
        self.species_entry.bind('<Down>', lambda e: self._show_autocomplete())
        
        # Species status label
        self.species_status = ttk.Label(species_frame, text="", foreground="gray")
        self.species_status.grid(row=0, column=1)
        
        row += 1
        
        # Site Name* (Required)
        ttk.Label(self, text="Site Name:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=5
        )
        self.site_var = tk.StringVar()
        site_entry = ttk.Entry(self, textvariable=self.site_var)
        site_entry.grid(row=row, column=1, sticky="ew", pady=5)
        
        row += 1
        
        # Grid Reference* (Required)
        ttk.Label(self, text="Grid Reference:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=5
        )
        
        gridref_frame = ttk.Frame(self)
        gridref_frame.grid(row=row, column=1, sticky="ew", pady=5)
        gridref_frame.columnconfigure(0, weight=1)
        
        self.gridref_var = tk.StringVar()
        self.gridref_var.trace('w', self._on_gridref_change)
        
        gridref_entry = ttk.Entry(gridref_frame, textvariable=self.gridref_var)
        gridref_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # Grid ref validation status
        self.gridref_status = ttk.Label(gridref_frame, text="", foreground="gray")
        self.gridref_status.grid(row=0, column=1)
        
        row += 1
        
        # Date* (Required)
        ttk.Label(self, text="Date:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=5
        )
        
        date_frame = ttk.Frame(self)
        date_frame.grid(row=row, column=1, sticky="ew", pady=5)
        date_frame.columnconfigure(0, weight=1)
        
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=12)
        date_entry.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        ttk.Label(date_frame, text="(YYYY-MM-DD)", foreground="gray").grid(
            row=0, column=1, sticky="w"
        )
        
        ttk.Button(date_frame, text="Today", command=self._set_today, width=8).grid(
            row=0, column=2, padx=(10, 0)
        )
        
        row += 1
        
        # Recorder* (Required)
        ttk.Label(self, text="Recorder:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=5
        )
        self.recorder_var = tk.StringVar()
        recorder_entry = ttk.Entry(self, textvariable=self.recorder_var)
        recorder_entry.grid(row=row, column=1, sticky="ew", pady=5)
        
        row += 1
        
        # Determiner* (Required)
        ttk.Label(self, text="Determiner:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=5
        )
        self.determiner_var = tk.StringVar()
        determiner_entry = ttk.Entry(self, textvariable=self.determiner_var)
        determiner_entry.grid(row=row, column=1, sticky="ew", pady=5)
        
        row += 1
        
        # Certainty* (Required)
        ttk.Label(self, text="Certainty:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=5
        )
        self.certainty_var = tk.StringVar(value="Certain")
        certainty_combo = ttk.Combobox(
            self,
            textvariable=self.certainty_var,
            values=["Certain", "Likely", "Uncertain"],
            state="readonly",
            width=15
        )
        certainty_combo.grid(row=row, column=1, sticky="w", pady=5)
        
        row += 1
        
        # === OPTIONAL FIELDS ===
        ttk.Separator(self, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=10
        )
        
        row += 1
        
        # Sex (Optional)
        ttk.Label(self, text="Sex:").grid(row=row, column=0, sticky="w", pady=5)
        self.sex_var = tk.StringVar()
        sex_combo = ttk.Combobox(
            self,
            textvariable=self.sex_var,
            values=["", "Male", "Female", "Unknown"],
            state="readonly",
            width=15
        )
        sex_combo.grid(row=row, column=1, sticky="w", pady=5)
        
        row += 1
        
        # Quantity (Optional)
        ttk.Label(self, text="Quantity:").grid(row=row, column=0, sticky="w", pady=5)
        self.quantity_var = tk.StringVar()
        quantity_entry = ttk.Entry(self, textvariable=self.quantity_var, width=10)
        quantity_entry.grid(row=row, column=1, sticky="w", pady=5)
        
        row += 1
        
        # Sample Method (Optional)
        ttk.Label(self, text="Sample Method:").grid(row=row, column=0, sticky="w", pady=5)
        self.sample_method_var = tk.StringVar()
        method_entry = ttk.Entry(self, textvariable=self.sample_method_var)
        method_entry.grid(row=row, column=1, sticky="ew", pady=5)
        
        row += 1
        
        # Observation Type (Optional)
        ttk.Label(self, text="Observation Type:").grid(row=row, column=0, sticky="w", pady=5)
        self.obs_type_var = tk.StringVar()
        obs_type_entry = ttk.Entry(self, textvariable=self.obs_type_var)
        obs_type_entry.grid(row=row, column=1, sticky="ew", pady=5)
        
        row += 1
        
        # Sample Comment (Optional)
        ttk.Label(self, text="Sample Comment:").grid(row=row, column=0, sticky="nw", pady=5)
        
        comment_frame = ttk.Frame(self)
        comment_frame.grid(row=row, column=1, sticky="ew", pady=5)
        comment_frame.columnconfigure(0, weight=1)
        
        self.comment_text = tk.Text(comment_frame, height=4, width=40, wrap=tk.WORD)
        self.comment_text.grid(row=0, column=0, sticky="ew")
        
        comment_scroll = ttk.Scrollbar(comment_frame, command=self.comment_text.yview)
        comment_scroll.grid(row=0, column=1, sticky="ns")
        self.comment_text.config(yscrollcommand=comment_scroll.set)
        
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        
        self.submit_btn = ttk.Button(
            button_frame,
            text="Submit Record",
            command=self._save_record,
            style='Accent.TButton'
        )
        self.submit_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Clear Form",
            command=self._clear_form
        ).pack(side=tk.RIGHT)
        
        # Required fields note
        ttk.Label(
            button_frame,
            text="* Required fields",
            foreground="red",
            font=("TkDefaultFont", 8)
        ).pack(side=tk.LEFT)
    
    def _apply_defaults(self):
        """Apply default values from settings"""
        if self.settings.get('default_recorder'):
            self.recorder_var.set(self.settings['default_recorder'])
        
        if self.settings.get('default_determiner'):
            self.determiner_var.set(self.settings['default_determiner'])
        
        if self.settings.get('default_certainty'):
            self.certainty_var.set(self.settings['default_certainty'])
        
        if self.settings.get('default_sample_method'):
            self.sample_method_var.set(self.settings['default_sample_method'])
        
        if self.settings.get('default_observation_type'):
            self.obs_type_var.set(self.settings['default_observation_type'])
    
    def _set_today(self):
        """Set date to today"""
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
    
    def _on_species_search(self, *args):
        """Handle species search text change"""
        search_term = self.species_var.get()
        
        # Clear selected species when user types
        self.selected_species = None
        
        if len(search_term) < 2:
            self.species_status.config(text="", foreground="gray")
            self._hide_autocomplete()
            return
        
        # Show "Searching..." status
        self.species_status.config(text="🔍", foreground="blue")
        
        # Perform search
        try:
            db_manager = get_db_manager()
            uksi_db_path = db_manager.db_dir / 'uksi.db'
            
            if not uksi_db_path.exists():
                self.species_status.config(text="❌ UKSI DB missing", foreground="red")
                return
            
            # Get observations connection for smart ranking
            obs_conn = db_manager.get_observations_connection()
            
            with UKSIHandler(uksi_db_path) as uksi:
                # Search with smart ranking (prioritizes user's species)
                self.species_results = uksi.search_species(search_term, limit=10, obs_db_conn=obs_conn)
            
            if self.species_results:
                self.species_status.config(text=f"✓ {len(self.species_results)}", foreground="green")
                self._show_autocomplete()
            else:
                self.species_status.config(text="❌ No matches", foreground="orange")
                self._hide_autocomplete()
        
        except Exception as e:
            logger.error(f"Species search error: {e}")
            self.species_status.config(text="❌ Search error", foreground="red")
    
    def _show_autocomplete(self):
        """Show autocomplete dropdown"""
        if not self.species_results:
            return
        
        # Destroy existing window
        self._hide_autocomplete()
        
        # Create new autocomplete window
        self.autocomplete_window = tk.Toplevel(self)
        self.autocomplete_window.wm_overrideredirect(True)
        
        # Position below species entry
        x = self.species_entry.winfo_rootx()
        y = self.species_entry.winfo_rooty() + self.species_entry.winfo_height()
        width = self.species_entry.winfo_width()
        
        self.autocomplete_window.geometry(f"{width}x200+{x}+{y}")
        
        # Create listbox
        listbox_frame = ttk.Frame(self.autocomplete_window)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.autocomplete_listbox = tk.Listbox(
            listbox_frame,
            yscrollcommand=scrollbar.set,
            height=10
        )
        self.autocomplete_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.autocomplete_listbox.yview)
        
        # Populate listbox
        for species in self.species_results:
            display_text = species['scientific_name']
            if species.get('common_names'):
                display_text += f" ({species['common_names']})"
            self.autocomplete_listbox.insert(tk.END, display_text)
        
        # Bind selection
        self.autocomplete_listbox.bind('<<ListboxSelect>>', self._on_species_select)
        self.autocomplete_listbox.bind('<Return>', self._on_species_select)
        
        # Bind focus loss
        self.autocomplete_window.bind('<FocusOut>', lambda e: self._hide_autocomplete())
    
    def _hide_autocomplete(self):
        """Hide autocomplete dropdown"""
        if self.autocomplete_window:
            self.autocomplete_window.destroy()
            self.autocomplete_window = None
    
    def _select_first_result(self):
        """Select first autocomplete result"""
        if self.species_results:
            self.selected_species = self.species_results[0]
            self.species_var.set(self.selected_species['scientific_name'])
            self.species_status.config(text="✓", foreground="green")
            self._hide_autocomplete()
    
    def _on_species_select(self, event):
        """Handle species selection from autocomplete"""
        if not self.autocomplete_listbox.curselection():
            return
        
        index = self.autocomplete_listbox.curselection()[0]
        self.selected_species = self.species_results[index]
        
        # Update entry
        self.species_var.set(self.selected_species['scientific_name'])
        self.species_status.config(text="✓", foreground="green")
        
        self._hide_autocomplete()
    
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
    
    def _save_record(self):
        """Save the record to database"""
        # Collect data
        record = {
            'uuid': str(uuid.uuid4()),  # ADDED: Generate UUID for iRecord integration
            'species_name': self.selected_species.get('scientific_name') if self.selected_species else self.species_var.get().strip(),
            'taxon_id': self.selected_species.get('tvk') if self.selected_species else None,
            'common_name': self.selected_species.get('common_names') if self.selected_species else None,
            'taxon_version_key': self.selected_species.get('tvk') if self.selected_species else None,
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
        is_valid, errors = validate_all_record_fields(record)
        
        if not is_valid:
            messagebox.showerror(
                "Validation Error",
                "Please correct the following errors:\n\n• " + "\n• ".join(errors)
            )
            return
        
        # Additional validation: must have species selected from UKSI
        if not self.selected_species:
            response = messagebox.askyesno(
                "Species Not Selected",
                f"The species '{self.species_var.get()}' was not selected from UKSI.\n\n"
                "This means it may not have a valid Taxon Version Key (TVK).\n\n"
                "Continue anyway?"
            )
            if not response:
                return
        
        # Save to database
        try:
            db_manager = get_db_manager()
            obs_conn = db_manager.get_observations_connection()
            cursor = obs_conn.cursor()
            
            cursor.execute("""
                INSERT INTO records (
                    uuid, species_name, taxon_id, common_name, taxon_version_key,
                    site_name, grid_reference, date,
                    recorder, determiner, certainty,
                    sex, quantity, sample_method, observation_type, sample_comment,
                    created_at, modified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record['uuid'],  # ADDED: UUID now included in insert
                record['species_name'],
                record['taxon_id'],
                record['common_name'],
                record['taxon_version_key'],
                record['site_name'],
                record['grid_reference'],
                record['date'],
                record['recorder'],
                record['determiner'],
                record['certainty'],
                record['sex'],
                record['quantity'],
                record['sample_method'],
                record['observation_type'],
                record['sample_comment'],
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            obs_conn.commit()
            
            # Success!
            messagebox.showinfo(
                "Record Saved",
                f"Successfully saved record for {record['species_name']}"
            )
            
            logger.info(f"Saved record: {record['species_name']} at {record['site_name']}")
            
            # Update status
            if hasattr(self.app, 'update_status'):
                self.app.update_status(f"Record saved: {record['species_name']}")
            
            # Refresh Home tab stats
            if hasattr(self.app, 'tabs') and 'Home' in self.app.tabs:
                if hasattr(self.app.tabs['Home'], '_update_stats'):
                    self.app.tabs['Home']._update_stats()
            
            # Clear form for next entry
            self._clear_form()
            
        except Exception as e:
            logger.error(f"Error saving record: {e}")
            messagebox.showerror(
                "Database Error",
                f"Failed to save record:\n\n{str(e)}"
            )
    
    def _clear_form(self):
        """Clear all form fields"""
        self.species_var.set("")
        self.selected_species = None
        self.species_status.config(text="", foreground="gray")
        
        self.site_var.set("")
        self.gridref_var.set("")
        self.gridref_status.config(text="", foreground="gray")
        
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        
        self.sex_var.set("")
        self.quantity_var.set("")
        
        self.comment_text.delete("1.0", tk.END)
        
        # Re-apply defaults for recorder, determiner, etc.
        self._apply_defaults()
        
        # Focus on species search
        self.species_entry.focus_set()
