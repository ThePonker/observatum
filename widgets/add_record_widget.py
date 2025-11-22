"""
Add Record Widget for Observatum
Embedded form for adding single observation records

This widget replaces the placeholder in the Home tab and provides
a complete data entry form for observations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class AddRecordWidget(ttk.LabelFrame):
    """Widget for adding single observation records"""
    
    def __init__(self, parent, app_instance, **kwargs):
        """
        Initialize the Add Record widget
        
        Args:
            parent: Parent widget
            app_instance: Reference to main application
        """
        super().__init__(parent, text="Add Single Record", padding="10", **kwargs)
        self.app = app_instance
        self.settings = self._load_settings()
        
        # Configure grid
        self.columnconfigure(0, weight=0)  # Labels
        self.columnconfigure(1, weight=1)  # Entry fields
        
        self._create_form()
        
    def _load_settings(self):
        """Load settings from JSON file"""
        import json
        config_file = Path(__file__).parent.parent / 'data' / 'config.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
        
    def _create_form(self):
        """Create the data entry form"""
        row = 0
        
        # Species Search* (Mandatory)
        ttk.Label(self, text="Species Search:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.species_var = tk.StringVar()
        species_frame = ttk.Frame(self)
        species_frame.grid(row=row, column=1, sticky="ew", pady=3)
        species_frame.columnconfigure(0, weight=1)
        
        self.species_entry = ttk.Entry(species_frame, textvariable=self.species_var)
        self.species_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        ttk.Button(
            species_frame,
            text="Search",
            command=self._search_species,
            width=8
        ).grid(row=0, column=1)
        row += 1
        
        # Site Name* (Mandatory)
        ttk.Label(self, text="Site Name:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.site_var = tk.StringVar()
        self.site_entry = ttk.Entry(self, textvariable=self.site_var)
        self.site_entry.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        
        # Grid Ref* (Mandatory)
        ttk.Label(self, text="Grid Ref:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.gridref_var = tk.StringVar()
        self.gridref_entry = ttk.Entry(self, textvariable=self.gridref_var)
        self.gridref_entry.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        
        # Date* (Mandatory)
        ttk.Label(self, text="Date:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_entry = ttk.Entry(self, textvariable=self.date_var)
        self.date_entry.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        
        # Recorder* (Mandatory - can be pre-filled from settings)
        ttk.Label(self, text="Recorder:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        default_recorder = self.settings.get('default_recorder', '')
        self.recorder_var = tk.StringVar(value=default_recorder)
        self.recorder_entry = ttk.Entry(self, textvariable=self.recorder_var)
        self.recorder_entry.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        
        # Determiner* (Mandatory - can be pre-filled from settings)
        ttk.Label(self, text="Determiner:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        default_determiner = self.settings.get('default_determiner', '')
        self.determiner_var = tk.StringVar(value=default_determiner)
        self.determiner_entry = ttk.Entry(self, textvariable=self.determiner_var)
        self.determiner_entry.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        
        # Certainty* (Mandatory - can be pre-filled from settings)
        ttk.Label(self, text="Certainty:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        default_certainty = self.settings.get('default_certainty', 'Certain')
        self.certainty_var = tk.StringVar(value=default_certainty)
        certainty_combo = ttk.Combobox(
            self,
            textvariable=self.certainty_var,
            values=['Certain', 'Likely', 'Uncertain'],
            state='readonly',
            width=18
        )
        certainty_combo.grid(row=row, column=1, sticky="w", pady=3)
        row += 1
        
        # Separator
        ttk.Separator(self, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=5
        )
        row += 1
        
        # Sex (Optional)
        ttk.Label(self, text="Sex:").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.sex_var = tk.StringVar()
        sex_combo = ttk.Combobox(
            self,
            textvariable=self.sex_var,
            values=['', 'Male', 'Female', 'Unknown'],
            state='readonly',
            width=18
        )
        sex_combo.grid(row=row, column=1, sticky="w", pady=3)
        row += 1
        
        # Quantity (Optional)
        ttk.Label(self, text="Quantity:").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.quantity_var = tk.StringVar()
        self.quantity_entry = ttk.Entry(self, textvariable=self.quantity_var, width=20)
        self.quantity_entry.grid(row=row, column=1, sticky="w", pady=3)
        row += 1
        
        # Sample Method (Optional - can be pre-filled from settings)
        ttk.Label(self, text="Sample Method:").grid(
            row=row, column=0, sticky="w", pady=3
        )
        default_method = self.settings.get('default_sample_method', '')
        self.sample_method_var = tk.StringVar(value=default_method)
        self.sample_method_entry = ttk.Entry(self, textvariable=self.sample_method_var)
        self.sample_method_entry.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        
        # Observation Type (Optional - can be pre-filled from settings)
        ttk.Label(self, text="Observation Type:").grid(
            row=row, column=0, sticky="w", pady=3
        )
        default_obs_type = self.settings.get('default_observation_type', '')
        self.obs_type_var = tk.StringVar(value=default_obs_type)
        self.obs_type_entry = ttk.Entry(self, textvariable=self.obs_type_var)
        self.obs_type_entry.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        
        # Sample Comment (Optional)
        ttk.Label(self, text="Sample Comment:").grid(
            row=row, column=0, sticky="nw", pady=3
        )
        self.comment_text = tk.Text(self, height=3, width=30, wrap=tk.WORD)
        self.comment_text.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._clear_form
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="Submit",
            command=self._submit_record
        ).pack(side=tk.LEFT)
        
    def _search_species(self):
        """Search for species in UKSI database"""
        search_term = self.species_var.get().strip()
        
        if not search_term:
            messagebox.showwarning(
                "Search Required",
                "Please enter a species name to search."
            )
            return
            
        # TODO: Implement actual UKSI database search
        # For now, show placeholder message
        messagebox.showinfo(
            "Species Search",
            f"Searching UKSI database for: {search_term}\n\n"
            "(Database integration to be implemented)"
        )
        
    def _validate_form(self):
        """
        Validate that all mandatory fields are filled
        
        Returns:
            tuple: (is_valid, error_message)
        """
        errors = []
        
        if not self.species_var.get().strip():
            errors.append("Species Search")
        if not self.site_var.get().strip():
            errors.append("Site Name")
        if not self.gridref_var.get().strip():
            errors.append("Grid Ref")
        if not self.date_var.get().strip():
            errors.append("Date")
        if not self.recorder_var.get().strip():
            errors.append("Recorder")
        if not self.determiner_var.get().strip():
            errors.append("Determiner")
        if not self.certainty_var.get().strip():
            errors.append("Certainty")
            
        if errors:
            return False, "The following mandatory fields are missing:\n\n• " + "\n• ".join(errors)
            
        return True, ""
        
    def _submit_record(self):
        """Submit the record to the database"""
        # Validate form
        is_valid, error_msg = self._validate_form()
        
        if not is_valid:
            messagebox.showerror("Validation Error", error_msg)
            return
            
        # Collect form data
        record_data = {
            'species': self.species_var.get().strip(),
            'site_name': self.site_var.get().strip(),
            'grid_ref': self.gridref_var.get().strip(),
            'date': self.date_var.get().strip(),
            'recorder': self.recorder_var.get().strip(),
            'determiner': self.determiner_var.get().strip(),
            'certainty': self.certainty_var.get(),
            'sex': self.sex_var.get(),
            'quantity': self.quantity_var.get().strip(),
            'sample_method': self.sample_method_var.get().strip(),
            'observation_type': self.obs_type_var.get().strip(),
            'comment': self.comment_text.get("1.0", tk.END).strip()
        }
        
        # TODO: Save to database using db_manager
        # For now, show success message
        messagebox.showinfo(
            "Record Submitted",
            f"Observation record for {record_data['species']} has been saved.\n\n"
            "(Database integration to be implemented)"
        )
        
        # Clear form after successful submission
        self._clear_form()
        
    def _clear_form(self):
        """Clear all form fields (except defaults from settings)"""
        self.species_var.set("")
        self.site_var.set("")
        self.gridref_var.set("")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        
        # Keep defaults from settings
        self.recorder_var.set(self.settings.get('default_recorder', ''))
        self.determiner_var.set(self.settings.get('default_determiner', ''))
        self.certainty_var.set(self.settings.get('default_certainty', 'Certain'))
        
        self.sex_var.set("")
        self.quantity_var.set("")
        self.sample_method_var.set(self.settings.get('default_sample_method', ''))
        self.obs_type_var.set(self.settings.get('default_observation_type', ''))
        self.comment_text.delete("1.0", tk.END)
