"""
Add Record Widget for Observatum
Embedded form for adding single observation records

REFACTORED VERSION - Now uses separate components:
- SpeciesSearchWidget: Species search functionality
- RecordFormBuilder: Form layout and field management
- Validation and submission logic (to be extracted later)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path
import sys
import logging
import uuid
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import UKSI handler
from database.uksi_handler import UKSIHandler

# Import new components
from widgets.species_search_widget import SpeciesSearchWidget
from widgets.record_form_builder import RecordFormBuilder

# Import validators
try:
    from utils.validators import GridReferenceValidator, validate_all_record_fields
except ImportError:
    GridReferenceValidator = None
    validate_all_record_fields = None

logger = logging.getLogger(__name__)


class AddRecordWidget(ttk.LabelFrame):
    """
    Widget for adding single observation records
    
    Refactored to use component-based architecture:
    - SpeciesSearchWidget handles species search
    - RecordFormBuilder handles form layout
    - This class orchestrates and handles submission
    """
    
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
        
        # Configure grid
        self.columnconfigure(0, weight=0)  # Labels
        self.columnconfigure(1, weight=1)  # Entry fields
        
        # Create components
        self._create_components()
        
        # Build form
        self._create_form()
    
    def _load_settings(self):
        """Load settings from JSON file"""
        config_file = Path(__file__).parent.parent / 'data' / 'config.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _create_components(self):
        """Create the component instances"""
        # Create species search widget
        self.species_search = SpeciesSearchWidget(
            self,
            self.uksi,
            on_species_selected=self._on_species_selected
        )
        
        # Create form builder
        self.form_builder = RecordFormBuilder(self, self.settings)
        
        logger.debug("Components created successfully")
    
    def _create_form(self):
        """Build the form using RecordFormBuilder"""
        # Build form with species search embedded
        self.field_vars = self.form_builder.build_form(self.species_search)
        
        # Add grid reference validation
        self.field_vars['grid_reference'].trace('w', self._validate_gridref)
        
        # Add buttons at bottom
        self._create_buttons()
        
        logger.info("Add Record form created successfully")
    
    def _create_buttons(self):
        """Create Submit and Cancel buttons"""
        # Button frame at bottom
        button_frame = ttk.Frame(self)
        button_frame.grid(row=100, column=0, columnspan=2, pady=(10, 0))
        
        # Cancel button (clears form)
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._clear_form,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        # Submit button
        ttk.Button(
            button_frame,
            text="Submit",
            command=self._submit_record,
            width=10
        ).pack(side=tk.LEFT, padx=5)
    
    def _on_species_selected(self, species):
        """
        Callback when species is selected from search
        
        Args:
            species: Species dict with TVK and name
        """
        self.selected_species = species
        logger.debug(f"Species selected: {species.get('scientific_name', 'Unknown')}")
    
    def _validate_gridref(self, *args):
        """Validate grid reference as user types"""
        gridref = self.field_vars['grid_reference'].get().strip()
        status_label = self.form_builder.get_gridref_status_label()
        
        if not gridref:
            status_label.config(text="", foreground="gray")
            return
        
        if GridReferenceValidator:
            validator = GridReferenceValidator()
            is_valid, message = validator.validate(gridref)
            
            if is_valid:
                status_label.config(text="✓", foreground="green")
            else:
                status_label.config(text="✗", foreground="red")
        else:
            # Basic validation if validator not available
            if len(gridref) >= 4:
                status_label.config(text="?", foreground="orange")
    
    def _validate_form(self):
        """
        Validate that all mandatory fields are filled
        
        Returns:
            tuple: (is_valid, error_message)
        """
        errors = []
        field_values = self.form_builder.get_field_values()
        
        # Check mandatory fields
        if not field_values.get('site_name', '').strip():
            errors.append("Site Name")
        if not field_values.get('grid_reference', '').strip():
            errors.append("Grid Ref")
        if not field_values.get('date', '').strip():
            errors.append("Date")
        if not field_values.get('recorder', '').strip():
            errors.append("Recorder")
        if not field_values.get('determiner', '').strip():
            errors.append("Determiner")
        if not field_values.get('certainty', '').strip():
            errors.append("Certainty")
        
        # Check species selection
        if not self.selected_species or 'tvk' not in self.selected_species:
            errors.insert(0, "Species Search (must select a species)")
        
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
        
        # Get field values
        field_values = self.form_builder.get_field_values()
        
        # Collect record data
        record_data = {
            'uuid': str(uuid.uuid4()),
            'species_name': self.selected_species['scientific_name'],
            'taxon_id': self.selected_species['tvk'],
            'site_name': field_values['site_name'].strip(),
            'grid_reference': field_values['grid_reference'].strip(),
            'date': field_values['date'].strip(),
            'recorder': field_values['recorder'].strip(),
            'determiner': field_values['determiner'].strip(),
            'certainty': field_values['certainty'],
            'sex': field_values.get('sex') if field_values.get('sex') else None,
            'quantity': int(field_values['quantity']) if field_values.get('quantity', '').strip().isdigit() else None,
            'sample_method': field_values.get('sample_method').strip() if field_values.get('sample_method', '').strip() else None,
            'observation_type': field_values.get('observation_type').strip() if field_values.get('observation_type', '').strip() else None,
            'sample_comment': field_values.get('sample_comment', '').strip() if field_values.get('sample_comment', '').strip() else None,
            'verification_status': 'Not reviewed',
            'submitted_to_irecord': 0
        }
        
        # Save to database
        try:
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            obs_conn = db_manager.get_observations_connection()
            cursor = obs_conn.cursor()
            
            cursor.execute("""
                INSERT INTO records (
                    uuid, species_name, taxon_id, site_name, grid_reference, date,
                    recorder, determiner, certainty, sex, quantity,
                    sample_method, observation_type, sample_comment,
                    verification_status, submitted_to_irecord
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_data['uuid'],
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
                record_data['sample_comment'],
                record_data['verification_status'],
                record_data['submitted_to_irecord']
            ))
            
            obs_conn.commit()
            
            # Refresh Home tab stats FIRST (before showing dialog)
            if hasattr(self.app, 'tabs') and 'Home' in self.app.tabs:
                home_tab = self.app.tabs['Home']
                if hasattr(home_tab, '_update_stats'):
                    try:
                        home_tab._update_stats()
                        self.app.root.update()
                    except Exception as e:
                        logger.warning(f"Failed to refresh stats: {e}")
            
            # Show success dialog
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
        # Clear form fields using builder
        self.form_builder.clear_fields(keep_defaults=True)
        
        # Clear species search
        self.species_search.clear()
        self.selected_species = None
        
        logger.debug("Form cleared")