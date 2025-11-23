"""
Add Record Widget for Observatum
Embedded form for adding single observation records

FULLY REFACTORED VERSION - Component-based architecture:
- SpeciesSearchWidget: Species search functionality
- RecordFormBuilder: Form layout and field management
- RecordSubmissionHandler: Validation and database operations
- This class: Orchestration only
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import sys
import logging
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import UKSI handler
from database.handlers.uksi_handler import UKSIHandler

# Import components
from widgets.forms.species_search_widget import SpeciesSearchWidget
from widgets.forms.record_form_builder import RecordFormBuilder
from utils.submission.record_submission_handler import RecordSubmissionHandler

# Import validators
try:
    from utils.validation.validators import GridReferenceValidator
except ImportError:
    GridReferenceValidator = None

logger = logging.getLogger(__name__)


class AddRecordWidget(ttk.LabelFrame):
    """
    Widget for adding single observation records
    
    Fully refactored component-based architecture:
    - SpeciesSearchWidget: Handles species search and selection
    - RecordFormBuilder: Manages form layout and fields
    - RecordSubmissionHandler: Handles validation and database operations
    - AddRecordWidget: Orchestrates components and user interactions
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
        uksi_db_path = Path(__file__).parent.parent.parent / 'database' / 'uksi.db'
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
        
        # Track selected species
        self.selected_species = None
        
        # Configure grid
        self.columnconfigure(0, weight=0)  # Labels
        self.columnconfigure(1, weight=1)  # Entry fields
        
        # Create components
        self._create_components()
        
        # Build form
        self._create_form()
        
        logger.info("AddRecordWidget initialized successfully")
    
    def _load_settings(self):
        """Load settings from JSON file"""
        config_file = Path(__file__).parent.parent / 'data' / 'config.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load settings: {e}")
                return {}
        return {}
    
    def _create_components(self):
        """Create component instances"""
        # Create species search widget
        self.species_search = SpeciesSearchWidget(
            self,
            self.uksi,
            on_species_selected=self._on_species_selected
        )
        
        # Create form builder
        self.form_builder = RecordFormBuilder(self, self.settings)
        
        # Create submission handler
        self.submission_handler = RecordSubmissionHandler(self.app)
        
        logger.debug("Components created successfully")
    
    def _create_form(self):
        """Build the form using RecordFormBuilder"""
        # Build form with species search embedded
        self.field_vars = self.form_builder.build_form(self.species_search)
        
        # Add grid reference validation
        self.field_vars['grid_reference'].trace('w', self._validate_gridref)
        
        # Add buttons at bottom
        self._create_buttons()
        
        logger.debug("Form built successfully")
    
    def _create_buttons(self):
        """Create Submit and Cancel buttons"""
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
        Callback when species is selected
        
        Args:
            species: Species dict with TVK and scientific name
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
    
    def _submit_record(self):
        """
        Submit the record using RecordSubmissionHandler
        
        Orchestrates: validation → data collection → submission → UI update
        """
        # Get field values from form
        field_values = self.form_builder.get_field_values()
        
        # Submit using handler (validates, prepares, saves)
        success, message, errors = self.submission_handler.submit_record(
            field_values,
            self.selected_species
        )
        
        if success:
            # Show success message
            messagebox.showinfo("Record Saved", message)
            
            # Clear form for next entry
            self._clear_form()
        else:
            # Show error message
            messagebox.showerror("Validation Error" if errors else "Database Error", message)
    
    def _clear_form(self):
        """Clear form fields and reset to defaults"""
        # Clear form using builder
        self.form_builder.clear_fields(keep_defaults=True)
        
        # Clear species search
        self.species_search.clear()
        self.selected_species = None
        
        logger.debug("Form cleared and reset")