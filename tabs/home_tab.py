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
            ("total_records", "Total Records", "0", "🔢"),
            ("this_year", "This Year", "0", "📅"),
            ("last_7_days", "Last 7 Days", "0", "📊"),
            ("last_recorded", "Last Recorded", "N/A", "⭐"),
            ("total_species", "Total Species", "0", "🦋"),
            ("this_month", "This Month", "0", "📆"),
            ("last_30_days", "Last 30 Days", "0", "📈"),
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
        search_entry = ttk.Entry(search_frame, textvariable=self.taxon_search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        
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
        
    def _search_taxon(self):
        """Search for a taxon and display its hierarchy"""
        search_term = self.taxon_search_var.get().strip()
        
        if not search_term:
            self.update_status("Please enter a search term")
            return
            
        # TODO: Search UKSI database for the taxon
        # For now, show placeholder
        hierarchy = f"Searching for: {search_term}\n\n"
        hierarchy += "Kingdom: (To be implemented)\n"
        hierarchy += "  Phylum: (To be implemented)\n"
        hierarchy += "    Class: (To be implemented)\n"
        hierarchy += "      Order: (To be implemented)\n"
        hierarchy += "        Family: (To be implemented)\n"
        hierarchy += "          Genus: (To be implemented)\n"
        hierarchy += "            Species: (To be implemented)\n"
        
        self._set_hierarchy_text(hierarchy)
        self.update_status(f"Searched for: {search_term}")
        
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
