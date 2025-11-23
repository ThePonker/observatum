"""
Record Form Builder for Observatum
Handles creation and layout of observation record entry forms

This component extracts the form creation logic from AddRecordWidget,
making it focused, reusable, and easier to maintain.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class RecordFormBuilder:
    """
    Builds and manages observation record entry forms
    
    Responsibilities:
    - Create form fields and labels
    - Manage grid layout
    - Apply default values from settings
    - Provide access to field variables
    """
    
    def __init__(self, parent, settings=None):
        """
        Initialize the form builder
        
        Args:
            parent: Parent widget (typically a ttk.LabelFrame)
            settings: Dict of user settings for default values
        """
        self.parent = parent
        self.settings = settings or {}
        self.field_vars = {}
        self.field_widgets = {}
        
        # Grid reference validation components
        self.gridref_status_label = None
        
    def build_form(self, species_search_widget):
        """
        Build the complete observation record form
        
        Args:
            species_search_widget: SpeciesSearchWidget instance to embed
            
        Returns:
            dict: Dictionary of field variables {field_name: tk.Variable}
        """
        row = 0
        
        # Species Search* (Mandatory) - Use provided widget
        ttk.Label(self.parent, text="Species Search:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        
        # Get the species search frame from the widget
        species_frame = species_search_widget.get_search_frame()
        species_frame.grid(row=row, column=1, sticky="ew", pady=3)
        
        # Store reference to species search widget
        self.species_search_widget = species_search_widget
        row += 1
        
        # Site Name* (Mandatory)
        ttk.Label(self.parent, text="Site Name:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.field_vars['site_name'] = tk.StringVar()
        self.field_widgets['site_name'] = ttk.Entry(
            self.parent, 
            textvariable=self.field_vars['site_name']
        )
        self.field_widgets['site_name'].grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        
        # Grid Ref* (Mandatory)
        ttk.Label(self.parent, text="Grid Ref:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        gridref_frame = ttk.Frame(self.parent)
        gridref_frame.grid(row=row, column=1, sticky="ew", pady=3)
        gridref_frame.columnconfigure(0, weight=1)
        
        self.field_vars['grid_reference'] = tk.StringVar()
        self.field_widgets['grid_reference'] = ttk.Entry(
            gridref_frame,
            textvariable=self.field_vars['grid_reference']
        )
        self.field_widgets['grid_reference'].grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # Validation indicator
        self.gridref_status_label = ttk.Label(gridref_frame, text="", foreground="gray", width=3)
        self.gridref_status_label.grid(row=0, column=1)
        row += 1
        
        # Date* (Mandatory)
        ttk.Label(self.parent, text="Date:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.field_vars['date'] = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.field_widgets['date'] = ttk.Entry(
            self.parent,
            textvariable=self.field_vars['date']
        )
        self.field_widgets['date'].grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        
        # Recorder* (Mandatory - can be pre-filled from settings)
        ttk.Label(self.parent, text="Recorder:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        default_recorder = self.settings.get('default_recorder', '')
        self.field_vars['recorder'] = tk.StringVar(value=default_recorder)
        self.field_widgets['recorder'] = ttk.Entry(
            self.parent,
            textvariable=self.field_vars['recorder']
        )
        self.field_widgets['recorder'].grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        
        # Determiner* (Mandatory - can be pre-filled from settings)
        ttk.Label(self.parent, text="Determiner:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        default_determiner = self.settings.get('default_determiner', '')
        self.field_vars['determiner'] = tk.StringVar(value=default_determiner)
        self.field_widgets['determiner'] = ttk.Entry(
            self.parent,
            textvariable=self.field_vars['determiner']
        )
        self.field_widgets['determiner'].grid(row=row, column=1, sticky="ew", pady=3)
        row += 1
        
        # Certainty* (Mandatory - can be pre-filled from settings)
        ttk.Label(self.parent, text="Certainty:*", foreground="red").grid(
            row=row, column=0, sticky="w", pady=3
        )
        default_certainty = self.settings.get('default_certainty', 'Certain')
        self.field_vars['certainty'] = tk.StringVar(value=default_certainty)
        certainty_combo = ttk.Combobox(
            self.parent,
            textvariable=self.field_vars['certainty'],
            values=['Certain', 'Likely', 'Uncertain'],
            state='readonly',
            width=18
        )
        certainty_combo.grid(row=row, column=1, sticky="w", pady=3)
        self.field_widgets['certainty'] = certainty_combo
        row += 1
        
        # Optional Fields Section
        ttk.Separator(self.parent, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=10
        )
        row += 1
        
        # Sex (Optional)
        ttk.Label(self.parent, text="Sex:").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.field_vars['sex'] = tk.StringVar()
        sex_combo = ttk.Combobox(
            self.parent,
            textvariable=self.field_vars['sex'],
            values=['Male', 'Female', 'Unknown'],
            width=18
        )
        sex_combo.grid(row=row, column=1, sticky="w", pady=3)
        self.field_widgets['sex'] = sex_combo
        row += 1
        
        # Quantity (Optional)
        ttk.Label(self.parent, text="Quantity:").grid(
            row=row, column=0, sticky="w", pady=3
        )
        self.field_vars['quantity'] = tk.StringVar()
        self.field_widgets['quantity'] = ttk.Entry(
            self.parent,
            textvariable=self.field_vars['quantity'],
            width=10
        )
        self.field_widgets['quantity'].grid(row=row, column=1, sticky="w", pady=3)
        row += 1
        
        # Sample Method (Optional)
        ttk.Label(self.parent, text="Sample Method:").grid(
            row=row, column=0, sticky="w", pady=3
        )
        default_method = self.settings.get('default_sample_method', '')
        self.field_vars['sample_method'] = tk.StringVar(value=default_method)
        method_combo = ttk.Combobox(
            self.parent,
            textvariable=self.field_vars['sample_method'],
            values=['Visual', 'Net', 'Trap', 'Light Trap', 'Pitfall', 'Other'],
            width=18
        )
        method_combo.grid(row=row, column=1, sticky="w", pady=3)
        self.field_widgets['sample_method'] = method_combo
        row += 1
        
        # Observation Type (Optional)
        ttk.Label(self.parent, text="Observation Type:").grid(
            row=row, column=0, sticky="w", pady=3
        )
        default_obs_type = self.settings.get('default_observation_type', '')
        self.field_vars['observation_type'] = tk.StringVar(value=default_obs_type)
        obs_type_combo = ttk.Combobox(
            self.parent,
            textvariable=self.field_vars['observation_type'],
            values=['Field Record', 'Specimen', 'Photo', 'Sound Recording'],
            width=18
        )
        obs_type_combo.grid(row=row, column=1, sticky="w", pady=3)
        self.field_widgets['observation_type'] = obs_type_combo
        row += 1
        
        # Sample Comment (Optional - Text area)
        ttk.Label(self.parent, text="Sample Comment:").grid(
            row=row, column=0, sticky="nw", pady=3
        )
        comment_frame = ttk.Frame(self.parent)
        comment_frame.grid(row=row, column=1, sticky="ew", pady=3)
        
        self.field_widgets['sample_comment'] = tk.Text(
            comment_frame,
            height=3,
            width=30,
            wrap=tk.WORD
        )
        self.field_widgets['sample_comment'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        comment_scroll = ttk.Scrollbar(
            comment_frame,
            command=self.field_widgets['sample_comment'].yview
        )
        comment_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.field_widgets['sample_comment'].config(yscrollcommand=comment_scroll.set)
        row += 1
        
        logger.info("Record form built successfully")
        return self.field_vars
    
    def get_field_values(self):
        """
        Get all current field values
        
        Returns:
            dict: {field_name: value} for all fields
        """
        values = {}
        
        # Get values from StringVar fields
        for field_name, var in self.field_vars.items():
            values[field_name] = var.get()
        
        # Get text from comment field (special case)
        if 'sample_comment' in self.field_widgets:
            comment_widget = self.field_widgets['sample_comment']
            values['sample_comment'] = comment_widget.get("1.0", tk.END).strip()
        
        return values
    
    def set_field_value(self, field_name, value):
        """
        Set a specific field value
        
        Args:
            field_name: Name of the field
            value: Value to set
        """
        if field_name == 'sample_comment':
            # Special handling for text widget
            if 'sample_comment' in self.field_widgets:
                comment_widget = self.field_widgets['sample_comment']
                comment_widget.delete("1.0", tk.END)
                if value:
                    comment_widget.insert("1.0", value)
        elif field_name in self.field_vars:
            self.field_vars[field_name].set(value)
        else:
            logger.warning(f"Attempted to set unknown field: {field_name}")
    
    def clear_fields(self, keep_defaults=True):
        """
        Clear all form fields
        
        Args:
            keep_defaults: If True, restore default values from settings
        """
        if keep_defaults:
            # Restore defaults from settings
            self.field_vars['site_name'].set("")
            self.field_vars['grid_reference'].set("")
            self.field_vars['date'].set(datetime.now().strftime("%Y-%m-%d"))
            self.field_vars['recorder'].set(self.settings.get('default_recorder', ''))
            self.field_vars['determiner'].set(self.settings.get('default_determiner', ''))
            self.field_vars['certainty'].set(self.settings.get('default_certainty', 'Certain'))
            self.field_vars['sex'].set("")
            self.field_vars['quantity'].set("")
            self.field_vars['sample_method'].set(self.settings.get('default_sample_method', ''))
            self.field_vars['observation_type'].set(self.settings.get('default_observation_type', ''))
            
            # Clear comment text
            if 'sample_comment' in self.field_widgets:
                self.field_widgets['sample_comment'].delete("1.0", tk.END)
        else:
            # Clear everything
            for var in self.field_vars.values():
                var.set("")
            
            if 'sample_comment' in self.field_widgets:
                self.field_widgets['sample_comment'].delete("1.0", tk.END)
        
        # Clear grid ref validation status
        if self.gridref_status_label:
            self.gridref_status_label.config(text="", foreground="gray")
        
        logger.debug("Form fields cleared")
    
    def get_gridref_status_label(self):
        """
        Get the grid reference validation status label
        
        Returns:
            ttk.Label: The validation status label widget
        """
        return self.gridref_status_label
    
    def get_field_widget(self, field_name):
        """
        Get a specific field widget for additional configuration
        
        Args:
            field_name: Name of the field
            
        Returns:
            Widget or None if not found
        """
        return self.field_widgets.get(field_name)
