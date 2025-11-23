"""
Add Record Widget for Observatum
Embedded form for adding single observation records

This widget replaces the placeholder in the Home tab and provides
a complete data entry form for observations with UKSI integration.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path
import sys
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import UKSI handler
from database.uksi_handler import UKSIHandler

# Import validators
try:
    from utils.validators import GridReferenceValidator, validate_all_record_fields
except ImportError:
    # Fallback if validators not yet in utils
    GridReferenceValidator = None
    validate_all_record_fields = None

logger = logging.getLogger(__name__)


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
        
        # Initialize UKSI handler
        uksi_db_path = Path(__file__).parent.parent / 'database' / 'uksi.db'
        try:
            self.uksi = UKSIHandler(uksi_db_path)
            logger.info("UKSI handler initialized successfully")
        except FileNotFoundError as e:
            logger.error(f"UKSI database not found: {e}")
            self.uksi = None
            messagebox.showwarning(
                "UKSI Database Missing",
                "The UKSI species database (uksi.db) was not found.\n\n"
                "Please run 'uksi_extractor.py' to generate the database.\n\n"
                "Species search will not be available."
            )
        
        # Track selected species details
        self.selected_species = None
        self.autocomplete_window = None
        
        # Configure grid
        self.columnconfigure(0, weight=0)  # Labels
        self.columnconfigure(1, weight=1)  # Entry fields
        
        self._create_form()
    
    def _get_observations_db(self):
        """
        Get observations database connection for smart ranking.
        
        Returns:
            SQLite connection or None if not available
        """
        try:
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            return db_manager.get_observations_connection()
        except Exception as e:
            logger.warning(f"Could not get observations database: {e}")
            return None
        
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
        
        # Bind key release for autocomplete with debouncing
        self.species_entry.bind('<KeyRelease>', self._on_species_key_release)
        self.species_entry.bind('<FocusOut>', self._on_species_focus_out)
        
        # Debounce timer for autocomplete
        self._autocomplete_timer = None
        
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
        gridref_frame = ttk.Frame(self)
        gridref_frame.grid(row=row, column=1, sticky="ew", pady=3)
        gridref_frame.columnconfigure(0, weight=1)
        
        self.gridref_var = tk.StringVar()
        self.gridref_var.trace('w', self._validate_gridref)
        self.gridref_entry = ttk.Entry(gridref_frame, textvariable=self.gridref_var)
        self.gridref_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # Validation indicator
        self.gridref_status = ttk.Label(gridref_frame, text="", foreground="gray", width=3)
        self.gridref_status.grid(row=0, column=1)
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
        
    def _on_species_key_release(self, event):
        """Handle key release in species entry for autocomplete with debouncing"""
        # Ignore navigation keys
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Return', 'Escape'):
            return
        
        # Cancel any pending search
        if self._autocomplete_timer:
            self.after_cancel(self._autocomplete_timer)
        
        search_term = self.species_var.get().strip()
        
        # Close autocomplete if search term is too short
        if len(search_term) < 2:
            self._close_autocomplete()
            return
        
        # Debounce: wait 250ms after user stops typing before searching
        if self.uksi:
            self._autocomplete_timer = self.after(250, lambda: self._show_autocomplete(search_term))
    
    def _validate_gridref(self, *args):
        """Validate grid reference as user types"""
        if not GridReferenceValidator:
            return  # Validator not available
        
        gridref = self.gridref_var.get().strip()
        if not gridref:
            self.gridref_status.config(text="", foreground="gray")
            return
        
        is_valid, error = GridReferenceValidator.validate(gridref)
        if is_valid:
            self.gridref_status.config(text="✓", foreground="green")
        else:
            self.gridref_status.config(text="✗", foreground="red")
    
    def _on_species_focus_out(self, event):
        """Handle focus out - delay closing autocomplete to allow selection"""
        self.after(200, self._close_autocomplete)
    
    def _show_autocomplete(self, search_term):
        """Show autocomplete dropdown with search results"""
        if not self.uksi:
            return
        
        # Search UKSI database with smart ranking
        obs_db = self._get_observations_db()
        results = self.uksi.search_species(search_term, limit=8, obs_db_conn=obs_db)
        
        if not results:
            self._close_autocomplete()
            return
        
        # Create or update autocomplete window
        if self.autocomplete_window:
            self._close_autocomplete()
        
        # Create toplevel window
        self.autocomplete_window = tk.Toplevel(self)
        self.autocomplete_window.wm_overrideredirect(True)
        
        # Position below entry widget
        x = self.species_entry.winfo_rootx()
        y = self.species_entry.winfo_rooty() + self.species_entry.winfo_height()
        self.autocomplete_window.wm_geometry(f"+{x}+{y}")
        
        # Create Text widget (allows mixed fonts) instead of Listbox
        text_widget = tk.Text(
            self.autocomplete_window,
            width=self.species_entry.winfo_width() // 7,
            height=min(len(results), 10),
            font=('TkDefaultFont', 9),
            cursor="hand2",
            wrap=tk.NONE
        )
        text_widget.pack()
        
        # Configure tags for formatting
        text_widget.tag_configure("scientific", font=('TkDefaultFont', 9, 'italic'))
        text_widget.tag_configure("common", font=('TkDefaultFont', 9, 'bold'))
        
        # Populate with formatted species names
        line_to_species = {}  # Map line number to species data
        for idx, species in enumerate(results):
            scientific = species['scientific_name']
            common_names = species.get('common_names')
            
            # Insert scientific name in italic
            text_widget.insert(tk.END, scientific, "scientific")
            
            # Insert common names in regular font (if available)
            if common_names:
                text_widget.insert(tk.END, f" {common_names}", "common")
            
            text_widget.insert(tk.END, "\n")
            line_to_species[idx + 1] = species  # Lines are 1-indexed
        
        # Make text read-only
        text_widget.config(state=tk.DISABLED)
        
        # Bind click to select species
        def on_click(event):
            # Get clicked line
            index = text_widget.index(f"@{event.x},{event.y}")
            line = int(index.split('.')[0])
            
            if line in line_to_species:
                selected = line_to_species[line]
                self._select_species(selected)
                self._close_autocomplete()
        
        text_widget.bind('<Button-1>', on_click)
        
        # Store results for selection
        self.autocomplete_results = results
    
    def _close_autocomplete(self):
        """Close autocomplete window if open"""
        if self.autocomplete_window:
            self.autocomplete_window.destroy()
            self.autocomplete_window = None
            self.autocomplete_results = None
    
    def _select_species(self, species):
        """Handle species selection from autocomplete"""
        # Set species name with common names
        display_text = self.uksi.format_species_display(species, include_common=True)
        self.species_var.set(display_text)
        
        # Store full species details
        self.selected_species = species
        
        logger.info(f"Selected species: {species['scientific_name']} (TVK: {species['tvk']}), Common: {species.get('common_names', 'None')}")
    
    def _search_species(self):
        """Handle Search button click - show detailed search dialog"""
        search_term = self.species_var.get().strip()
        
        if not search_term:
            messagebox.showwarning(
                "Search Required",
                "Please enter a species name to search."
            )
            return
        
        if not self.uksi:
            messagebox.showerror(
                "UKSI Unavailable",
                "UKSI database is not available.\n\n"
                "Please run uksi_extractor.py to generate the database."
            )
            return
        
        # Perform search with smart ranking
        obs_db = self._get_observations_db()
        results = self.uksi.search_species(search_term, limit=20, obs_db_conn=obs_db)
        
        if not results:
            messagebox.showinfo(
                "No Results",
                f"No species found matching '{search_term}'.\n\n"
                "Try:\n"
                "- Checking spelling\n"
                "- Using scientific name\n"
                "- Using common name\n"
                "- Searching for genus only"
            )
            return
        
        # Show results in dialog
        self._show_search_results_dialog(results)
    
    def _show_search_results_dialog(self, results):
        """Show search results in a selection dialog"""
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Species Search Results")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Title
        ttk.Label(
            dialog,
            text=f"Found {len(results)} species:",
            font=('TkDefaultFont', 10, 'bold')
        ).pack(pady=10)
        
        # Create listbox with scrollbar
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(
            frame, 
            yscrollcommand=scrollbar.set, 
            font=('TkDefaultFont', 9, 'italic')  # Italic for scientific names
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Populate listbox with scientific names + common names
        for species in results:
            display_text = self.uksi.format_species_display(species, include_common=True)
            listbox.insert(tk.END, display_text)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def on_select():
            if listbox.curselection():
                index = listbox.curselection()[0]
                selected = results[index]
                self._select_species(selected)
                dialog.destroy()
        
        ttk.Button(button_frame, text="Select", command=on_select, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
        
        # Double-click to select
        listbox.bind('<Double-Button-1>', lambda e: on_select())
        
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
        
        # Check if a valid species was selected (with TVK)
        if not self.selected_species or 'tvk' not in self.selected_species:
            messagebox.showerror(
                "Species Not Selected",
                "Please select a species from the dropdown or search results.\n\n"
                "The species must have a valid UKSI identifier (TVK) to be recorded."
            )
            return
            
        # Collect form data
        record_data = {
            'species_name': self.selected_species['scientific_name'],
            'taxon_id': self.selected_species['tvk'],  # TVK for smart ranking!
            'site_name': self.site_var.get().strip(),
            'grid_reference': self.gridref_var.get().strip(),
            'date': self.date_var.get().strip(),
            'recorder': self.recorder_var.get().strip(),
            'determiner': self.determiner_var.get().strip(),
            'certainty': self.certainty_var.get(),
            'sex': self.sex_var.get() if self.sex_var.get() else None,
            'quantity': int(self.quantity_var.get()) if self.quantity_var.get().strip().isdigit() else None,
            'sample_method': self.sample_method_var.get().strip() if self.sample_method_var.get().strip() else None,
            'observation_type': self.obs_type_var.get().strip() if self.obs_type_var.get().strip() else None,
            'sample_comment': self.comment_text.get("1.0", tk.END).strip() if self.comment_text.get("1.0", tk.END).strip() else None
        }
        
        # Save to database
        try:
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            obs_conn = db_manager.get_observations_connection()
            cursor = obs_conn.cursor()
            
            cursor.execute("""
                INSERT INTO records (
                    species_name, taxon_id, site_name, grid_reference, date,
                    recorder, determiner, certainty, sex, quantity,
                    sample_method, observation_type, sample_comment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_data['species_name'],
                record_data['taxon_id'],
                record_data['site_name'],
                record_data['grid_reference'],
                record_data['date'],
                record_data['recorder'],
                record_data['determiner'],
                record_data['certainty'],
                record_data['sex'],
                record_data['quantity'],
                record_data['sample_method'],
                record_data['observation_type'],
                record_data['sample_comment']
            ))
            
            obs_conn.commit()
            
            # Refresh Home tab stats FIRST (before showing dialog)
            if hasattr(self.app, 'tabs') and 'Home' in self.app.tabs:
                home_tab = self.app.tabs['Home']
                if hasattr(home_tab, '_update_stats'):
                    try:
                        home_tab._update_stats()
                        self.app.root.update()  # Force FULL UI update
                    except Exception as e:
                        logger.warning(f"Failed to refresh stats: {e}")
            
            # NOW show success dialog (stats are already updated in background!)
            messagebox.showinfo(
                "Record Saved",
                f"Observation record for {record_data['species_name']} has been saved successfully!\n\n"
                f"TVK: {record_data['taxon_id']}"
            )
            
            logger.info(f"Saved record: {record_data['species_name']} (TVK: {record_data['taxon_id']})")
            
            # Clear form after successful submission
            self._clear_form()
            
        except Exception as e:
            logger.error(f"Error saving record: {e}")
            messagebox.showerror(
                "Database Error",
                f"Failed to save record:\n\n{str(e)}"
            )
        
    def _clear_form(self):
        """Clear all form fields (except defaults from settings)"""
        self.species_var.set("")
        self.selected_species = None  # Reset selected species
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
