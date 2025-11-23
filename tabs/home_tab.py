"""
Home Tab for Observatum
Displays overview and quick access to key information

Contains three main components:
- Add Single Record: Embedded data entry form
- Quick Stats: 8 statistics boxes showing key metrics
- Taxon Viewer: Hierarchical taxonomy browser
- Recent Species List: Last 10 species entered
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path

try:
    from tabs.base_tab import BaseTab
    from widgets.forms.add_record_widget import AddRecordWidget
    from tabs.stats_calculator import StatsCalculator
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from tabs.base_tab import BaseTab
    from widgets.forms.add_record_widget import AddRecordWidget
    try:
        from tabs.stats_calculator import StatsCalculator
    except ImportError:
        StatsCalculator = None


class HomeTab(BaseTab):
    """Home tab showing overview and quick access"""
    
    def setup_ui(self):
        """Create the home tab interface"""
        # Main container with padding
        main_container = ttk.Frame(self, padding="10")
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.columnconfigure(0, weight=3)  # Add Record area gets more space
        main_container.columnconfigure(1, weight=2)  # Quick Stats area
        main_container.rowconfigure(0, weight=0)  # Top section - fixed height
        main_container.rowconfigure(1, weight=1)  # Bottom section - expandable
        
        # Top-Left: Add Single Record placeholder
        add_record_frame = self._create_add_record_placeholder(main_container)
        add_record_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 10))
        
        # Top-Right: Quick Stats (8 boxes in 2 columns x 4 rows)
        stats_frame = self._create_quick_stats_section(main_container)
        stats_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 10))
        
        # Bottom section: Split between Taxon Viewer (left) and Species List (right)
        bottom_frame = ttk.Frame(main_container)
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=1)
        bottom_frame.rowconfigure(0, weight=1)
        
        # Left: Taxon Viewer
        taxon_frame = self._create_taxon_viewer_section(bottom_frame)
        taxon_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Right: Recent Species List
        species_frame = self._create_species_list_section(bottom_frame)
        species_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
    def _create_add_record_placeholder(self, parent) -> AddRecordWidget:
        """
        Create Add Single Record form widget
        
        Args:
            parent: Parent widget
            
        Returns:
            AddRecordWidget instance
        """
        # Return the actual Add Record widget
        add_record_widget = AddRecordWidget(parent, self.app)
        return add_record_widget
        
    def _create_quick_stats_section(self, parent) -> ttk.Frame:
        """
        Create the quick stats section with 8 stat boxes in 2 columns x 4 rows
        
        Args:
            parent: Parent widget
            
        Returns:
            Frame containing stats boxes
        """
        stats_container = ttk.LabelFrame(parent, text="Quick Statistics", padding="10")
        
        # Configure grid for 4 rows x 2 columns
        for i in range(2):
            stats_container.columnconfigure(i, weight=1, uniform="stats")
        for i in range(4):
            stats_container.rowconfigure(i, weight=1, uniform="stats")
        
        # Store references to stat labels for updating
        self.stat_labels = {}
        
        # Define the 8 statistics with keys for updating
        stats_config = [
            ("total_records", "Total Records", "0", "📊"),
            ("this_year", "This Year", "0", "📅"),
            ("last_7_days", "Last 7 Days", "0", "📈"),
            ("last_recorded", "Last Recorded", "N/A", "⭐"),
            ("total_species", "Total Species", "0", "🦋"),
            ("this_month", "This Month", "0", "📆"),
            ("last_30_days", "Last 30 Days", "0", "📊"),
            ("unique_sites", "Unique Sites", "0", "📍")
        ]
        
        # Create stat boxes in 2 columns x 4 rows
        for idx, (key, label, value, icon) in enumerate(stats_config):
            row = idx // 2  # Divide by 2 for row
            col = idx % 2   # Remainder for column
            
            stat_box, value_label = self._create_stat_box(stats_container, label, value, icon)
            stat_box.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)
            
            # Store reference to value label for updating
            self.stat_labels[key] = value_label
        
        # Load initial stats
        self._update_stats()
            
        return stats_container
        
    def _create_stat_box(self, parent, label: str, value: str, icon: str) -> tuple:
        """
        Create a single statistics box (compact version for 2-column layout)
        
        Args:
            parent: Parent widget
            label: Stat label
            value: Stat value
            icon: Icon/emoji
            
        Returns:
            Tuple of (box frame, value label) for updating
        """
        box = ttk.Frame(parent, relief=tk.RIDGE, borderwidth=2)
        box.columnconfigure(0, weight=1)
        
        # Icon (smaller size)
        icon_label = ttk.Label(box, text=icon, font=("Arial", 18))
        icon_label.grid(row=0, column=0, pady=(5, 2))
        
        # Value (smaller size) - store reference
        value_label = ttk.Label(box, text=value, font=("Arial", 14, "bold"))
        value_label.grid(row=1, column=0, pady=2)
        
        # Label (smaller size)
        label_text = ttk.Label(box, text=label, font=("Arial", 8))
        label_text.grid(row=2, column=0, pady=(2, 5))
        
        return box, value_label
        
    def _create_taxon_viewer_section(self, parent) -> ttk.Frame:
        """
        Create the taxon viewer section
        
        Args:
            parent: Parent widget
            
        Returns:
            Frame containing taxon viewer
        """
        taxon_container = ttk.LabelFrame(parent, text="Taxon Viewer", padding="10")
        taxon_container.columnconfigure(0, weight=1)
        taxon_container.rowconfigure(1, weight=1)
        
        # Search bar at top
        search_frame = ttk.Frame(taxon_container)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 5))
        
        self.taxon_search_var = tk.StringVar()
        self.taxon_search_entry = ttk.Entry(search_frame, textvariable=self.taxon_search_var)
        self.taxon_search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        self.taxon_search_entry.bind('<Return>', lambda e: self._search_taxon())  # Enter key support
        self.taxon_search_entry.bind('<KeyRelease>', self._on_taxon_key_release)  # Autocomplete
        self.taxon_search_entry.bind('<FocusOut>', self._on_taxon_focus_out)  # Close autocomplete
        
        # Initialize autocomplete tracking
        self.taxon_autocomplete_window = None
        self.taxon_autocomplete_timer = None
        self._taxon_global_click_binding = None
        
        search_button = ttk.Button(search_frame, text="Search", command=self._search_taxon)
        search_button.grid(row=0, column=2)
        
        clear_button = ttk.Button(search_frame, text="Clear", command=self._clear_taxon_search)
        clear_button.grid(row=0, column=3, padx=(5, 0))
        
        # Hierarchy display
        hierarchy_frame = ttk.Frame(taxon_container)
        hierarchy_frame.grid(row=1, column=0, sticky="nsew")
        hierarchy_frame.columnconfigure(0, weight=1)
        hierarchy_frame.rowconfigure(0, weight=1)
        
        # Scrollable text widget for hierarchy
        hierarchy_scroll = ttk.Scrollbar(hierarchy_frame)
        hierarchy_scroll.grid(row=0, column=1, sticky="ns")
        
        self.hierarchy_text = tk.Text(
            hierarchy_frame,
            wrap=tk.WORD,
            yscrollcommand=hierarchy_scroll.set,
            font=("Courier", 10),
            state=tk.DISABLED,
            height=15
        )
        self.hierarchy_text.grid(row=0, column=0, sticky="nsew")
        hierarchy_scroll.config(command=self.hierarchy_text.yview)
        
        # Add placeholder text
        self._set_hierarchy_text("Search for a species to view its taxonomic hierarchy.\n\n"
                                 "Example: Search for 'Robin' or 'Oak' to see the full\n"
                                 "classification from Kingdom down to Species.")
        
        return taxon_container
        
    def _create_species_list_section(self, parent) -> ttk.Frame:
        """
        Create the recent species list section
        
        Args:
            parent: Parent widget
            
        Returns:
            Frame containing species list
        """
        species_container = ttk.LabelFrame(parent, text="Pan Species List (Last 10 Entries)", padding="10")
        species_container.columnconfigure(0, weight=1)
        species_container.rowconfigure(0, weight=1)
        
        # Create treeview for species list
        tree_frame = ttk.Frame(species_container)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.grid(row=0, column=1, sticky="ns")
        
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Treeview
        self.species_tree = ttk.Treeview(
            tree_frame,
            columns=("Species", "Date", "Site"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=15
        )
        self.species_tree.grid(row=0, column=0, sticky="nsew")
        
        vsb.config(command=self.species_tree.yview)
        hsb.config(command=self.species_tree.xview)
        
        # Configure columns
        self.species_tree.heading("Species", text="Species Name")
        self.species_tree.heading("Date", text="Date")
        self.species_tree.heading("Site", text="Site")
        
        self.species_tree.column("Species", width=200)
        self.species_tree.column("Date", width=100)
        self.species_tree.column("Site", width=150)
        
        # Add sample data (placeholder)
        self._populate_species_list()
        
        return species_container
        
    def _populate_species_list(self):
        """Populate the species list with recent entries"""
        # TODO: Get actual data from database
        # For now, show placeholder message
        self.species_tree.insert("", "end", values=("No records yet", "", ""))
    
    def _on_taxon_key_release(self, event):
        """Handle key release in taxon search - trigger autocomplete"""
        # Ignore navigation keys
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Return', 'Escape', 'Tab'):
            return
        
        search_term = self.taxon_search_var.get().strip()
        
        # Cancel any pending timer
        if self.taxon_autocomplete_timer:
            self.after_cancel(self.taxon_autocomplete_timer)
        
        if len(search_term) >= 2:
            # Debounce: wait 300ms before showing autocomplete
            self.taxon_autocomplete_timer = self.after(300, lambda: self._show_taxon_autocomplete(search_term))
        else:
            # Close autocomplete if search too short
            self._close_taxon_autocomplete()
    
    def _on_taxon_focus_out(self, event):
        """Handle focus out - close autocomplete after delay"""
        self.after(200, self._close_taxon_autocomplete)
    
    def _show_taxon_autocomplete(self, search_term):
        """Show autocomplete dropdown with species suggestions"""
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from database.handlers.uksi_handler import UKSIHandler
            from database.db_manager import get_db_manager
            
            # Get database connections
            db_manager = get_db_manager()
            uksi_path = db_manager.uksi_db_path
            obs_conn = db_manager.get_observations_connection()
            
            # Search UKSI database
            with UKSIHandler(uksi_path) as uksi:
                results = uksi.search_species(search_term, limit=8, obs_db_conn=obs_conn)
                
                if not results:
                    self._close_taxon_autocomplete()
                    return
                
                # Close existing autocomplete
                if self.taxon_autocomplete_window:
                    self._close_taxon_autocomplete()
                
                # Create toplevel window
                self.taxon_autocomplete_window = tk.Toplevel(self)
                self.taxon_autocomplete_window.wm_overrideredirect(True)
                
                # Position below entry widget
                x = self.taxon_search_entry.winfo_rootx()
                y = self.taxon_search_entry.winfo_rooty() + self.taxon_search_entry.winfo_height()
                width = self.taxon_search_entry.winfo_width()
                self.taxon_autocomplete_window.wm_geometry(f"+{x}+{y}")
                
                # Create Text widget for mixed formatting
                text_widget = tk.Text(
                    self.taxon_autocomplete_window,
                    width=width // 7,
                    height=min(len(results), 8),
                    font=('TkDefaultFont', 9),
                    cursor="hand2",
                    wrap=tk.NONE,
                    relief=tk.SOLID,
                    borderwidth=1
                )
                text_widget.pack()
                
                # Configure tags for formatting
                text_widget.tag_configure("scientific", font=('TkDefaultFont', 9, 'italic'))
                text_widget.tag_configure("common", font=('TkDefaultFont', 9, 'bold'))
                text_widget.tag_configure("hover", background="#e0e0e0")
                
                # Populate results
                line_to_species = {}
                for idx, species in enumerate(results):
                    scientific = species.get('scientific_name', 'Unknown')
                    common_names = species.get('common_names', '')
                    
                    # Insert scientific name in italic
                    text_widget.insert(tk.END, scientific, "scientific")
                    
                    # Insert common names in bold
                    if common_names:
                        text_widget.insert(tk.END, f" ({common_names})", "common")
                    
                    text_widget.insert(tk.END, "\n")
                    line_to_species[idx + 1] = species
                
                # Make read-only
                text_widget.config(state=tk.DISABLED)
                
                # Click handler
                def on_click(event):
                    index = text_widget.index(f"@{event.x},{event.y}")
                    line_num = int(index.split('.')[0])
                    if line_num in line_to_species:
                        species = line_to_species[line_num]
                        # Set the search field
                        self.taxon_search_var.set(species['scientific_name'])
                        self._close_taxon_autocomplete()
                        # Load species by TVK directly (don't search again!)
                        self._load_taxon_by_tvk(species['tvk'], species['scientific_name'])
                
                text_widget.bind('<Button-1>', on_click)
                
                # Hover effect
                def on_motion(event):
                    text_widget.config(state=tk.NORMAL)
                    text_widget.tag_remove("hover", "1.0", tk.END)
                    index = text_widget.index(f"@{event.x},{event.y}")
                    line_num = int(index.split('.')[0])
                    if line_num in line_to_species:
                        text_widget.tag_add("hover", f"{line_num}.0", f"{line_num}.end")
                    text_widget.config(state=tk.DISABLED)
                
                text_widget.bind('<Motion>', on_motion)
                
                # Global click handler to close on outside click
                def on_global_click(event):
                    if event.widget == self.taxon_search_entry:
                        return
                    widget = event.widget
                    while widget:
                        if widget == self.taxon_autocomplete_window:
                            return
                        try:
                            widget = widget.master
                        except:
                            break
                    self._close_taxon_autocomplete()
                
                self.winfo_toplevel().bind('<Button-1>', on_global_click, add='+')
                self._taxon_global_click_binding = on_global_click
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error showing taxon autocomplete: {e}")
            self._close_taxon_autocomplete()
    
    def _close_taxon_autocomplete(self):
        """Close the autocomplete window"""
        if self.taxon_autocomplete_window:
            # Remove global click binding
            if self._taxon_global_click_binding:
                try:
                    self.winfo_toplevel().unbind('<Button-1>', self._taxon_global_click_binding)
                except:
                    pass
                self._taxon_global_click_binding = None
            
            try:
                self.taxon_autocomplete_window.destroy()
            except:
                pass
            self.taxon_autocomplete_window = None
        
    def _search_taxon(self):
        """Search for a taxon and display its hierarchy"""
        search_term = self.taxon_search_var.get().strip()
        
        if not search_term:
            self.update_status("Please enter a search term")
            return
        
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from database.handlers.uksi_handler import UKSIHandler
            from database.db_manager import get_db_manager
            
            # Get database connections
            db_manager = get_db_manager()
            uksi_path = db_manager.uksi_db_path
            obs_conn = db_manager.get_observations_connection()
            
            # Search UKSI database
            with UKSIHandler(uksi_path) as uksi:
                # Search for the species (with obs_conn for smart ranking)
                results = uksi.search_species(search_term, limit=1, obs_db_conn=obs_conn)
                
                if not results:
                    hierarchy = f"No results found for: '{search_term}'\n\n"
                    hierarchy += "Try searching by:\n"
                    hierarchy += "  • Common name (e.g., 'Robin', 'Oak')\n"
                    hierarchy += "  • Scientific name (e.g., 'Erithacus rubecula')\n"
                    hierarchy += "  • Partial name (e.g., 'Quer' for Quercus species)"
                    self._set_hierarchy_text(hierarchy)
                    self.update_status(f"No results found for: {search_term}")
                    return
                
                # Get the top result
                species = results[0]
                
                # Get full species details by TVK
                full_species = uksi.get_species_by_tvk(species['tvk'])
                
                if not full_species:
                    self._set_hierarchy_text(f"Error retrieving details for: {species['scientific_name']}")
                    self.update_status("Error retrieving species details")
                    return
                
                # Debug: Log what data we received
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Species data keys: {full_species.keys()}")
                logger.info(f"Kingdom: '{full_species.get('kingdom')}'")
                logger.info(f"Phylum: '{full_species.get('phylum')}'")
                logger.info(f"Class: '{full_species.get('class')}'")
                
                # Build hierarchy display
                hierarchy = self._format_taxonomy_hierarchy(full_species)
                
                self._set_hierarchy_text(hierarchy)
                self.update_status(f"Found: {species['scientific_name']}")
                
        except FileNotFoundError as e:
            hierarchy = "═" * 60 + "\n"
            hierarchy += "⚠️  UKSI DATABASE NOT FOUND\n"
            hierarchy += "═" * 60 + "\n\n"
            hierarchy += "The UK Species Inventory database (uksi.db) is required\n"
            hierarchy += "for taxonomy searches.\n\n"
            hierarchy += "Expected location:\n"
            hierarchy += f"  {db_manager.uksi_db_path if 'db_manager' in locals() else '/data/uksi.db'}\n\n"
            hierarchy += "─" * 60 + "\n"
            hierarchy += "TO GENERATE THE DATABASE:\n\n"
            hierarchy += "1. Locate uksi_extractor.py in your project folder\n"
            hierarchy += "2. Run: python uksi_extractor.py\n"
            hierarchy += "3. This will create uksi.db with 204,865 UK species\n"
            hierarchy += "4. The process takes a few minutes\n\n"
            hierarchy += "Once generated, the Taxon Viewer will work automatically.\n"
            hierarchy += "─" * 60 + "\n"
            self._set_hierarchy_text(hierarchy)
            self.update_status("⚠️  UKSI database not found - see instructions")
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error searching taxon: {e}")
            hierarchy = f"Error searching for: '{search_term}'\n\n"
            hierarchy += f"Error details: {str(e)}"
            self._set_hierarchy_text(hierarchy)
            self.update_status(f"Error: {str(e)}")
    
    def _load_taxon_by_tvk(self, tvk: str, display_name: str):
        """
        Load species details directly by TVK (don't search again).
        
        This is called from autocomplete click handler to load the exact
        species the user clicked on, not the first search result.
        
        Args:
            tvk: The specific TVK to load
            display_name: Species name for status display
        """
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from database.handlers.uksi_handler import UKSIHandler
            from database.db_manager import get_db_manager
            
            # Get database path
            db_manager = get_db_manager()
            uksi_path = db_manager.uksi_db_path
            
            # Load species by TVK
            with UKSIHandler(uksi_path) as uksi:
                full_species = uksi.get_species_by_tvk(tvk)
                
                if not full_species:
                    self._set_hierarchy_text(f"Error retrieving details for: {display_name}")
                    self.update_status("Error retrieving species details")
                    return
                
                # Debug: Log what data we received
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Loaded by TVK: {tvk}")
                logger.info(f"Species: {full_species.get('scientific_name')}")
                logger.info(f"Kingdom: '{full_species.get('kingdom')}'")
                
                # Build hierarchy display
                hierarchy = self._format_taxonomy_hierarchy(full_species)
                
                self._set_hierarchy_text(hierarchy)
                self.update_status(f"Found: {display_name}")
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error loading taxon by TVK: {e}")
            hierarchy = f"Error loading: '{display_name}'\n\n"
            hierarchy += f"Error details: {str(e)}"
            self._set_hierarchy_text(hierarchy)
            self.update_status(f"Error: {str(e)}")
    
    def _format_taxonomy_hierarchy(self, species: dict) -> str:
        """
        Format taxonomic hierarchy for display
        
        Args:
            species: Dictionary with species information including taxonomy
            
        Returns:
            Formatted hierarchy string
        """
        hierarchy = ""
        
        # Species header
        scientific = species.get('scientific_name', 'Unknown')
        common_names = species.get('common_names', '')
        rank = species.get('rank', 'Unknown')
        
        hierarchy += "═" * 60 + "\n"
        hierarchy += f"SPECIES: {scientific}\n"
        if common_names:
            hierarchy += f"COMMON NAMES: {common_names}\n"
        hierarchy += f"RANK: {rank}\n"
        hierarchy += "═" * 60 + "\n\n"
        
        # Taxonomic hierarchy
        hierarchy += "TAXONOMIC HIERARCHY:\n"
        hierarchy += "─" * 60 + "\n\n"
        
        # Build hierarchy from kingdom down
        taxonomy_levels = [
            ('Kingdom', 'kingdom', 0),
            ('Phylum', 'phylum', 2),
            ('Class', 'class', 4),
            ('Order', 'order', 6),
            ('Family', 'family', 8),
            ('Genus', 'genus', 10),
        ]
        
        for label, key, indent in taxonomy_levels:
            value = species.get(key)
            if value and value.strip():
                hierarchy += " " * indent + f"{label}: {value}\n"
            else:
                hierarchy += " " * indent + f"{label}: (not specified)\n"
        
        # Add the species itself at the end
        hierarchy += " " * 12 + f"Species: {scientific}\n"
        
        hierarchy += "\n" + "─" * 60 + "\n"
        
        # Additional information
        hierarchy += "\nADDITIONAL INFORMATION:\n"
        hierarchy += f"TVK: {species.get('tvk', 'N/A')}\n"
        
        parent_tvk = species.get('parent_tvk')
        if parent_tvk and parent_tvk.strip():
            hierarchy += f"Parent TVK: {parent_tvk}\n"
        
        return hierarchy
        
    def _clear_taxon_search(self):
        """Clear the taxon search"""
        self.taxon_search_var.set("")
        self._set_hierarchy_text("Search cleared.\n\nEnter a species name to search.")
        self.update_status("Search cleared")
        
    def _set_hierarchy_text(self, text: str):
        """
        Set text in the hierarchy display
        
        Args:
            text: Text to display
        """
        self.hierarchy_text.config(state=tk.NORMAL)
        self.hierarchy_text.delete("1.0", tk.END)
        self.hierarchy_text.insert("1.0", text)
        self.hierarchy_text.config(state=tk.DISABLED)
    
    def _update_stats(self):
        """Update statistics from database"""
        if not StatsCalculator:
            return  # Stats calculator not available
        
        try:
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            obs_conn = db_manager.get_observations_connection()
            
            # Get all stats
            calculator = StatsCalculator(obs_conn)
            stats = calculator.get_all_stats()
            
            # Update each stat label
            for key, value in stats.items():
                if key in self.stat_labels:
                    self.stat_labels[key].config(text=value)
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error updating stats: {e}")
        
    def refresh(self):
        """Refresh the home tab data"""
        self._update_stats()
        # TODO: Refresh species list
        self.update_status("Home tab refreshed")