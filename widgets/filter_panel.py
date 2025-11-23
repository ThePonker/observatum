"""
Filter Panel Widget for Observatum
Filtering controls for Data tab records view

Allows filtering by:
- Date range
- Species
- Site
- Recorder
- Text search
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FilterPanel(ttk.LabelFrame):
    """Filter panel widget for records"""
    
    def __init__(self, parent, on_filter_changed: Callable, **kwargs):
        """
        Initialize filter panel
        
        Args:
            parent: Parent widget
            on_filter_changed: Callback function when filters change
        """
        super().__init__(parent, text="Filters", padding="10", **kwargs)
        self.on_filter_changed = on_filter_changed
        
        # Configure grid
        self.columnconfigure(1, weight=1)
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create filter controls"""
        row = 0
        
        # Search box
        ttk.Label(self, text="Search:").grid(row=row, column=0, sticky="w", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._on_filter_change())
        search_entry = ttk.Entry(self, textvariable=self.search_var, width=30)
        search_entry.grid(row=row, column=1, sticky="ew", padx=(0, 5))
        
        row += 1
        
        # Date range
        ttk.Label(self, text="Date From:").grid(row=row, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.date_from_var = tk.StringVar()
        self.date_from_var.trace('w', lambda *args: self._on_filter_change())
        date_from_entry = ttk.Entry(self, textvariable=self.date_from_var, width=12)
        date_from_entry.grid(row=row, column=1, sticky="w", padx=(0, 5), pady=(5, 0))
        
        ttk.Label(self, text="To:").grid(row=row, column=2, sticky="w", padx=(5, 5), pady=(5, 0))
        self.date_to_var = tk.StringVar()
        self.date_to_var.trace('w', lambda *args: self._on_filter_change())
        date_to_entry = ttk.Entry(self, textvariable=self.date_to_var, width=12)
        date_to_entry.grid(row=row, column=3, sticky="w", padx=(0, 5), pady=(5, 0))
        
        row += 1
        
        # Quick date filters
        quick_date_frame = ttk.Frame(self)
        quick_date_frame.grid(row=row, column=1, columnspan=3, sticky="w", pady=(5, 0))
        
        ttk.Button(quick_date_frame, text="Today", command=self._set_today, width=8).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(quick_date_frame, text="This Week", command=self._set_this_week, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_date_frame, text="This Month", command=self._set_this_month, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_date_frame, text="This Year", command=self._set_this_year, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_date_frame, text="All", command=self._set_all_dates, width=8).pack(side=tk.LEFT, padx=2)
        
        row += 1
        
        # Species filter
        ttk.Label(self, text="Species:").grid(row=row, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.species_var = tk.StringVar()
        self.species_var.set("All Species")
        self.species_var.trace('w', lambda *args: self._on_filter_change())
        self.species_combo = ttk.Combobox(self, textvariable=self.species_var, state="readonly", width=28)
        self.species_combo.grid(row=row, column=1, sticky="ew", padx=(0, 5), pady=(5, 0))
        
        row += 1
        
        # Site filter
        ttk.Label(self, text="Site:").grid(row=row, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.site_var = tk.StringVar()
        self.site_var.set("All Sites")
        self.site_var.trace('w', lambda *args: self._on_filter_change())
        self.site_combo = ttk.Combobox(self, textvariable=self.site_var, state="readonly", width=28)
        self.site_combo.grid(row=row, column=1, sticky="ew", padx=(0, 5), pady=(5, 0))
        
        row += 1
        
        # Recorder filter
        ttk.Label(self, text="Recorder:").grid(row=row, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.recorder_var = tk.StringVar()
        self.recorder_var.set("All Recorders")
        self.recorder_var.trace('w', lambda *args: self._on_filter_change())
        self.recorder_combo = ttk.Combobox(self, textvariable=self.recorder_var, state="readonly", width=28)
        self.recorder_combo.grid(row=row, column=1, sticky="ew", padx=(0, 5), pady=(5, 0))
        
        row += 1
        
        # Action buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        
        ttk.Button(button_frame, text="Clear All Filters", command=self.clear_filters).pack(side=tk.LEFT, padx=(0, 5))
        
        # Record count label
        self.count_label = ttk.Label(button_frame, text="0 records", foreground="gray")
        self.count_label.pack(side=tk.RIGHT)
        
    def _set_today(self):
        """Set date filter to today"""
        today = datetime.now().strftime("%Y-%m-%d")
        self.date_from_var.set(today)
        self.date_to_var.set(today)
    
    def _set_this_week(self):
        """Set date filter to this week"""
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        self.date_from_var.set(start_of_week.strftime("%Y-%m-%d"))
        self.date_to_var.set(today.strftime("%Y-%m-%d"))
    
    def _set_this_month(self):
        """Set date filter to this month"""
        today = datetime.now()
        start_of_month = today.replace(day=1)
        self.date_from_var.set(start_of_month.strftime("%Y-%m-%d"))
        self.date_to_var.set(today.strftime("%Y-%m-%d"))
    
    def _set_this_year(self):
        """Set date filter to this year"""
        today = datetime.now()
        start_of_year = today.replace(month=1, day=1)
        self.date_from_var.set(start_of_year.strftime("%Y-%m-%d"))
        self.date_to_var.set(today.strftime("%Y-%m-%d"))
    
    def _set_all_dates(self):
        """Clear date filters"""
        self.date_from_var.set("")
        self.date_to_var.set("")
    
    def clear_filters(self):
        """Clear all filters"""
        self.search_var.set("")
        self.date_from_var.set("")
        self.date_to_var.set("")
        self.species_var.set("All Species")
        self.site_var.set("All Sites")
        self.recorder_var.set("All Recorders")
    
    def get_filters(self) -> Dict[str, str]:
        """
        Get current filter values
        
        Returns:
            Dictionary of filter values
        """
        return {
            'search': self.search_var.get().strip(),
            'date_from': self.date_from_var.get().strip(),
            'date_to': self.date_to_var.get().strip(),
            'species': self.species_var.get() if self.species_var.get() != "All Species" else "",
            'site': self.site_var.get() if self.site_var.get() != "All Sites" else "",
            'recorder': self.recorder_var.get() if self.recorder_var.get() != "All Recorders" else ""
        }
    
    def update_filter_options(self, species_list: list, site_list: list, recorder_list: list):
        """
        Update the combobox options
        
        Args:
            species_list: List of species names
            site_list: List of site names
            recorder_list: List of recorder names
        """
        # Update species
        self.species_combo['values'] = ["All Species"] + sorted(species_list)
        
        # Update sites
        self.site_combo['values'] = ["All Sites"] + sorted(site_list)
        
        # Update recorders
        self.recorder_combo['values'] = ["All Recorders"] + sorted(recorder_list)
    
    def update_count(self, count: int):
        """
        Update the record count label
        
        Args:
            count: Number of records
        """
        self.count_label.config(text=f"{count:,} record{'s' if count != 1 else ''}")
    
    def _on_filter_change(self):
        """Called when any filter changes"""
        # Debounce search input (wait a bit before filtering)
        if hasattr(self, '_filter_timer'):
            self.after_cancel(self._filter_timer)
        
        self._filter_timer = self.after(300, self._apply_filters)
    
    def _apply_filters(self):
        """Apply filters and call callback"""
        filters = self.get_filters()
        self.on_filter_changed(filters)
