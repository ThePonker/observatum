"""
Species Search Widget for Observatum
Provides species search functionality with UKSI integration

ENHANCED VERSION with:
- Autocomplete dropdown (type-ahead)
- Mixed formatting (italic scientific, bold common names)
- Debounced search (250ms)
- Smart ranking from user history
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SpeciesSearchWidget:
    """
    Enhanced species search widget with autocomplete
    
    Features:
    - Real-time autocomplete dropdown as user types
    - Mixed font formatting (italic/bold)
    - Debounced search (250ms delay)
    - Smart ranking based on user's recording history
    - Fallback search button for manual search
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
        
        # Autocomplete tracking
        self.autocomplete_window = None
        self.autocomplete_results = None
        self._autocomplete_timer = None
        
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
        
        # Bind events for autocomplete
        self.species_entry.bind('<KeyRelease>', self._on_key_release)
        self.species_entry.bind('<FocusOut>', self._on_focus_out)
        
        # Search button (fallback for those who prefer clicking)
        self.search_button = ttk.Button(
            self.search_frame,
            text="Search",
            command=self._open_search_dialog,
            width=8
        )
        self.search_button.grid(row=0, column=1)
        
        logger.info("SpeciesSearchWidget initialized (enhanced version with autocomplete)")
    
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
        self._close_autocomplete()
        logger.debug("Species search cleared")
    
    def _on_key_release(self, event):
        """
        Handle key release in species entry for autocomplete with debouncing
        
        Args:
            event: Key release event
        """
        # Ignore navigation keys
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Return', 'Escape'):
            return
        
        # Cancel any pending search
        if self._autocomplete_timer:
            self.search_frame.after_cancel(self._autocomplete_timer)
        
        search_term = self.species_var.get().strip()
        
        # Close autocomplete if search term is too short
        if len(search_term) < 2:
            self._close_autocomplete()
            return
        
        # Debounce: wait 250ms after user stops typing before searching
        if self.uksi:
            self._autocomplete_timer = self.search_frame.after(
                250, 
                lambda: self._show_autocomplete(search_term)
            )
    
    def _on_focus_out(self, event):
        """
        Handle focus out event - delay closing to allow selection
        
        Args:
            event: Focus out event
        """
        # Delay closing to allow user to click on autocomplete
        self.search_frame.after(200, self._close_autocomplete)
    
    def _show_autocomplete(self, search_term):
        """
        Show autocomplete dropdown with search results
        
        Args:
            search_term: Search string
        """
        if not self.uksi:
            return
        
        # Get observations database for smart ranking
        obs_db = self._get_observations_db()
        
        # Search UKSI database with smart ranking
        try:
            if hasattr(self.uksi, 'search_species'):
                results = self.uksi.search_species(search_term, limit=8, obs_db_conn=obs_db)
            else:
                # Fallback if method signature different
                results = self.uksi.search_species(search_term, limit=8)
        except Exception as e:
            logger.error(f"Error searching species: {e}")
            return
        
        if not results:
            self._close_autocomplete()
            return
        
        # Close existing autocomplete window
        if self.autocomplete_window:
            self._close_autocomplete()
        
        # Create toplevel window
        self.autocomplete_window = tk.Toplevel(self.parent)
        self.autocomplete_window.wm_overrideredirect(True)
        
        # Position below entry widget
        x = self.species_entry.winfo_rootx()
        y = self.species_entry.winfo_rooty() + self.species_entry.winfo_height()
        self.autocomplete_window.wm_geometry(f"+{x}+{y}")
        
        # Bind global click to detect clicks outside dropdown
        def on_global_click(event):
            # Check if click was in entry field (don't close if typing)
            if event.widget == self.species_entry:
                return
            
            # Check if click was outside the autocomplete window
            widget = event.widget
            # Walk up widget hierarchy to see if we're inside autocomplete
            while widget:
                if widget == self.autocomplete_window:
                    return  # Click was inside, don't close
                try:
                    widget = widget.master
                except:
                    break
            # Click was outside, close autocomplete
            self._close_autocomplete()
        
        # Bind to root window for global click detection
        self.parent.winfo_toplevel().bind('<Button-1>', on_global_click, add='+')
        
        # Store binding so we can remove it later
        self._global_click_binding = on_global_click
        
        # Create Text widget (supports mixed fonts) instead of Listbox
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
            scientific = species.get('scientific_name', 'Unknown')
            common_names = species.get('common_names', '')
            
            # Insert scientific name in italic
            text_widget.insert(tk.END, scientific, "scientific")
            
            # Insert common names in bold (if available)
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
        
        logger.debug(f"Autocomplete shown with {len(results)} results")
    
    def _close_autocomplete(self):
        """Close autocomplete window if open"""
        if self.autocomplete_window:
            # Remove global click binding if it exists
            if hasattr(self, '_global_click_binding'):
                try:
                    self.parent.winfo_toplevel().unbind('<Button-1>', self._global_click_binding)
                except:
                    pass  # Binding may not exist
                delattr(self, '_global_click_binding')
            
            # Destroy window
            try:
                self.autocomplete_window.destroy()
            except:
                pass  # Window may already be destroyed
            self.autocomplete_window = None
            self.autocomplete_results = None
    
    def _open_search_dialog(self):
        """
        Open species search dialog (button-based search)
        
        Fallback method for users who prefer clicking over typing
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
            if hasattr(self.uksi, 'search_species'):
                results = self.uksi.search_species(search_term, limit=50, obs_db_conn=obs_conn)
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
        dialog.geometry("700x400")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Title
        ttk.Label(
            dialog,
            text=f"Found {len(results)} species:",
            font=('TkDefaultFont', 10, 'bold')
        ).pack(pady=10)
        
        # Create frame with scrollbar
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Use Text widget for formatting support
        text_widget = tk.Text(
            frame,
            yscrollcommand=scrollbar.set,
            font=('TkDefaultFont', 9),
            cursor="hand2",
            wrap=tk.WORD
        )
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Configure tags for formatting
        text_widget.tag_configure("scientific", font=('TkDefaultFont', 9, 'italic'))
        text_widget.tag_configure("common", font=('TkDefaultFont', 9, 'bold'))
        
        # Populate with formatted species
        line_to_species = {}
        for idx, species in enumerate(results):
            scientific = species.get('scientific_name', 'Unknown')
            common_names = species.get('common_names', '')
            
            # Insert scientific name in italic
            text_widget.insert(tk.END, scientific, "scientific")
            
            # Insert common names in bold
            if common_names:
                text_widget.insert(tk.END, f" {common_names}", "common")
            
            text_widget.insert(tk.END, "\n")
            line_to_species[idx + 1] = species
        
        # Make read-only
        text_widget.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        selected_species = [None]  # Use list to modify in nested function
        
        def on_click(event):
            # Get clicked line
            index = text_widget.index(f"@{event.x},{event.y}")
            line = int(index.split('.')[0])
            
            if line in line_to_species:
                selected_species[0] = line_to_species[line]
        
        def on_select():
            if selected_species[0]:
                self._select_species(selected_species[0])
                dialog.destroy()
        
        text_widget.bind('<Button-1>', on_click)
        text_widget.bind('<Double-Button-1>', lambda e: (on_click(e), on_select()))
        
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
        Format species for display (text-only version for compatibility)
        
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
            common = species.get('common_names', '')
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