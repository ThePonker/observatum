"""
Species Search Widget for Observatum (Minimal Placeholder)
Provides species search functionality with UKSI integration

This is a minimal version to allow RecordFormBuilder to work.
Full autocomplete and search dialog will be added later.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SpeciesSearchWidget:
    """
    Minimal species search widget
    
    Provides:
    - Search entry field
    - Search button
    - Species selection tracking
    
    TODO: Add full autocomplete and search dialog functionality
    """
    
    def __init__(self, parent, uksi_handler, on_species_selected=None):
        """
        Initialize the species search widget
        
        Args:
            parent: Parent widget
            uksi_handler: UKSIHandler instance for species lookup
            on_species_selected: Callback function(species_dict) when species selected
        """
        self.parent = parent
        self.uksi = uksi_handler
        self.on_species_selected = on_species_selected
        
        # Track selected species
        self.selected_species = None
        
        # Create the search frame
        self.search_frame = ttk.Frame(parent)
        self.search_frame.columnconfigure(0, weight=1)
        
        # Species entry field
        self.species_var = tk.StringVar()
        self.species_entry = ttk.Entry(
            self.search_frame,
            textvariable=self.species_var
        )
        self.species_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # Bind key release for future autocomplete
        # (Placeholder - will add autocomplete later)
        self.species_entry.bind('<KeyRelease>', self._on_key_release)
        self.species_entry.bind('<FocusOut>', self._on_focus_out)
        
        # Search button
        self.search_button = ttk.Button(
            self.search_frame,
            text="Search",
            command=self._open_search_dialog,
            width=8
        )
        self.search_button.grid(row=0, column=1)
        
        # Autocomplete window (will be implemented later)
        self.autocomplete_window = None
        
        logger.info("SpeciesSearchWidget initialized (minimal version)")
    
    def get_search_frame(self):
        """
        Get the search frame widget for embedding in forms
        
        Returns:
            ttk.Frame: The search frame containing entry and button
        """
        return self.search_frame
    
    def get_entry_widget(self):
        """
        Get the entry widget directly
        
        Returns:
            ttk.Entry: The species entry widget
        """
        return self.species_entry
    
    def get_selected_species(self):
        """
        Get the currently selected species
        
        Returns:
            dict: Species dict with TVK and name, or None
        """
        return self.selected_species
    
    def clear(self):
        """Clear the search field and selection"""
        self.species_var.set("")
        self.selected_species = None
        logger.debug("Species search cleared")
    
    def _on_key_release(self, event):
        """
        Handle key release in search field
        
        TODO: Implement autocomplete dropdown
        """
        # Placeholder for autocomplete functionality
        pass
    
    def _on_focus_out(self, event):
        """
        Handle focus out event
        
        TODO: Close autocomplete if open
        """
        pass
    
    def _open_search_dialog(self):
        """
        Open species search dialog
        
        This is a minimal implementation that uses UKSI search
        """
        if not self.uksi:
            messagebox.showwarning(
                "UKSI Database Missing",
                "Species search is not available.\n\n"
                "The UKSI database (uksi.db) was not found."
            )
            return
        
        search_term = self.species_var.get().strip()
        
        if not search_term:
            messagebox.showinfo(
                "Search Required",
                "Please enter a species name to search for."
            )
            return
        
        # Perform search
        try:
            # Get observations database for smart ranking
            obs_conn = self._get_observations_db()
            
            # Search using UKSI handler
            if hasattr(self.uksi, 'smart_search') and obs_conn:
                results = self.uksi.smart_search(search_term, obs_conn, limit=50)
            else:
                results = self.uksi.search_species(search_term, limit=50)
            
            if not results:
                messagebox.showinfo(
                    "No Results",
                    f"No species found matching: {search_term}"
                )
                return
            
            # Show results in dialog
            self._show_results_dialog(results)
            
        except Exception as e:
            logger.error(f"Error searching species: {e}")
            messagebox.showerror(
                "Search Error",
                f"An error occurred while searching:\n\n{str(e)}"
            )
    
    def _show_results_dialog(self, results):
        """
        Show search results in a selection dialog
        
        Args:
            results: List of species dicts from UKSI
        """
        # Create dialog window
        dialog = tk.Toplevel(self.parent)
        dialog.title("Species Search Results")
        dialog.geometry("600x400")
        dialog.transient(self.parent)
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
            font=('TkDefaultFont', 9, 'italic')
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Populate listbox
        for species in results:
            display_text = self._format_species_display(species)
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
        
        ttk.Button(
            button_frame,
            text="Select",
            command=on_select,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        # Double-click to select
        listbox.bind('<Double-Button-1>', lambda e: on_select())
    
    def _select_species(self, species):
        """
        Handle species selection
        
        Args:
            species: Species dict from UKSI with tvk and scientific_name
        """
        self.selected_species = species
        
        # Update entry field with scientific name
        if 'scientific_name' in species:
            self.species_var.set(species['scientific_name'])
        
        # Call callback if provided
        if self.on_species_selected:
            self.on_species_selected(species)
        
        logger.info(f"Species selected: {species.get('scientific_name', 'Unknown')}")
    
    def _format_species_display(self, species):
        """
        Format species for display in listbox
        
        Args:
            species: Species dict from UKSI
            
        Returns:
            str: Formatted display string
        """
        if hasattr(self.uksi, 'format_species_display'):
            return self.uksi.format_species_display(species, include_common=True)
        else:
            # Fallback formatting
            name = species.get('scientific_name', 'Unknown')
            common = species.get('common_name', '')
            if common:
                return f"{name} ({common})"
            return name
    
    def _get_observations_db(self):
        """
        Get observations database connection for smart ranking
        
        Returns:
            SQLite connection or None
        """
        try:
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            return db_manager.get_observations_connection()
        except Exception as e:
            logger.warning(f"Could not get observations database: {e}")
            return None
