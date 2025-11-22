"""
Base Tab Class for Observatum
Provides common functionality for all tabs

All tab implementations should inherit from this base class to ensure
consistent behavior and interface across the application.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
from abc import ABC, abstractmethod


class BaseTab(ttk.Frame, ABC):
    """
    Abstract base class for all Observatum tabs
    
    Provides common functionality:
    - Standard frame structure
    - Database access
    - Status bar updates
    - Common UI patterns
    """
    
    def __init__(self, parent, app_instance, **kwargs):
        """
        Initialize the base tab
        
        Args:
            parent: Parent widget (usually the notebook)
            app_instance: Reference to main ObservatumApp instance
            **kwargs: Additional arguments passed to ttk.Frame
        """
        super().__init__(parent, **kwargs)
        
        self.parent = parent
        self.app = app_instance
        
        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Tab-specific state
        self.is_initialized = False
        self.data_modified = False
        
        # Create the tab UI
        self.setup_ui()
        
    @abstractmethod
    def setup_ui(self):
        """
        Setup the user interface for this tab
        
        Must be implemented by each tab subclass
        """
        pass
        
    def update_status(self, message: str):
        """
        Update the application status bar
        
        Args:
            message: Status message to display
        """
        if hasattr(self.app, 'update_status'):
            self.app.update_status(message)
            
    def mark_modified(self):
        """Mark that data in this tab has been modified"""
        self.data_modified = True
        if hasattr(self.app, 'unsaved_changes'):
            self.app.unsaved_changes = True
            
    def clear_modified(self):
        """Clear the modified flag"""
        self.data_modified = False
        
    def on_tab_selected(self):
        """
        Called when this tab is selected/shown
        
        Override in subclasses to perform actions when tab becomes active
        """
        pass
        
    def on_tab_deselected(self):
        """
        Called when this tab is deselected/hidden
        
        Override in subclasses to perform cleanup when tab becomes inactive
        """
        pass
        
    def refresh(self):
        """
        Refresh the tab content
        
        Override in subclasses to reload data from database
        """
        pass
        
    def save(self) -> bool:
        """
        Save any changes in this tab
        
        Override in subclasses to implement save functionality
        
        Returns:
            True if save was successful, False otherwise
        """
        return True
        
    def validate(self) -> bool:
        """
        Validate the current tab data
        
        Override in subclasses to implement validation
        
        Returns:
            True if validation passes, False otherwise
        """
        return True


class DataTab(BaseTab):
    """
    Base class for tabs that display data grids
    
    Provides common functionality for Data, Longhorns, and Insect Collection tabs
    """
    
    def __init__(self, parent, app_instance, **kwargs):
        """Initialize the data tab"""
        super().__init__(parent, app_instance, **kwargs)
        
    def setup_ui(self):
        """Setup the standard data tab UI"""
        # Main container
        main_container = ttk.Frame(self)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # Button bar at top
        self.button_bar = self._create_button_bar(main_container)
        self.button_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Search and filter frame
        self.search_filter_frame = self._create_search_filter_frame(main_container)
        self.search_filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # Data grid (to be implemented with actual data grid widget)
        self.data_frame = self._create_data_grid(main_container)
        self.data_frame.grid(row=2, column=0, sticky="nsew")
        
    def _create_button_bar(self, parent) -> ttk.Frame:
        """
        Create the button bar with Import, Export, Add Record, Stats buttons
        
        Args:
            parent: Parent widget
            
        Returns:
            Button bar frame
        """
        button_frame = ttk.Frame(parent)
        
        # Import Data button
        self.import_btn = ttk.Button(
            button_frame,
            text="Import Data",
            command=self.on_import_data
        )
        self.import_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Export Data button
        self.export_btn = ttk.Button(
            button_frame,
            text="Export Data",
            command=self.on_export_data
        )
        self.export_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add Single Record button
        self.add_record_btn = ttk.Button(
            button_frame,
            text="Add Single Record",
            command=self.on_add_record
        )
        self.add_record_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Stats button
        self.stats_btn = ttk.Button(
            button_frame,
            text=f"{self.get_tab_name()} Stats",
            command=self.on_show_stats
        )
        self.stats_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        return button_frame
        
    def _create_search_filter_frame(self, parent) -> ttk.Frame:
        """
        Create the search and filter frame
        
        Args:
            parent: Parent widget
            
        Returns:
            Search/filter frame
        """
        search_frame = ttk.Frame(parent)
        
        # Search label
        search_label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_var.trace_add("write", self.on_search_changed)
        
        # Filter button (placeholder for future filter implementation)
        self.filter_btn = ttk.Button(
            search_frame,
            text="Filters...",
            command=self.on_show_filters
        )
        self.filter_btn.pack(side=tk.LEFT)
        
        return search_frame
        
    def _create_data_grid(self, parent) -> ttk.Frame:
        """
        Create the data grid area
        
        Args:
            parent: Parent widget
            
        Returns:
            Data grid frame (placeholder for now)
        """
        grid_frame = ttk.Frame(parent, relief=tk.SUNKEN, borderwidth=1)
        
        # Placeholder label
        placeholder = ttk.Label(
            grid_frame,
            text="Data Grid\n(To be implemented with actual data grid widget)",
            font=("Arial", 12),
            foreground="gray"
        )
        placeholder.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        return grid_frame
        
    def get_tab_name(self) -> str:
        """
        Get the name of this tab
        
        Override in subclasses to return appropriate name
        
        Returns:
            Tab name string
        """
        return "Data"
        
    def on_import_data(self):
        """Handle Import Data button click"""
        self.update_status("Import Data dialog (to be implemented)")
        
    def on_export_data(self):
        """Handle Export Data button click"""
        self.update_status("Export Data dialog (to be implemented)")
        
    def on_add_record(self):
        """Handle Add Single Record button click"""
        self.update_status("Add Record dialog (to be implemented)")
        
    def on_show_stats(self):
        """Handle Stats button click"""
        self.update_status("Stats dialog (to be implemented)")
        
    def on_show_filters(self):
        """Handle Filters button click"""
        self.update_status("Filters dialog (to be implemented)")
        
    def on_search_changed(self, *args):
        """Handle search text changes"""
        search_text = self.search_var.get()
        if search_text:
            self.update_status(f"Searching for: {search_text}")
        else:
            self.update_status("Ready")
