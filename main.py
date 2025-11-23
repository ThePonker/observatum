"""
Observatum - Biological Recording Application
Main application entry point with tabbed interface

This is the main window that coordinates all tabs and manages the application lifecycle.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import tabs
from tabs.home_tab import HomeTab
from tabs.settings_tab import SettingsTab
from tabs.data_tab import DataTab

# Import migrations (NEW)
from database.migrations import DatabaseMigrations


class ObservatumApp:
    """Main application class for Observatum"""

    def __init__(self, root):
        self.root = root
        self.root.title("Observatum")
        self.root.geometry("1200x800")

        # Set minimum window size
        self.root.minsize(1000, 600)

        # Configure root window
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Initialize variables
        self.current_file = None
        self.unsaved_changes = False

        # Run database migrations (NEW)
        self._run_migrations()

        # Create UI components
        self._create_menu_bar()
        self._create_main_container()
        self._create_status_bar()  # Create before notebook so tabs can update status
        self._create_notebook()

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _run_migrations(self):
        """Run database migrations to add iRecord integration fields (NEW)"""
        try:
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            obs_conn = db_manager.get_observations_connection()
            
            if DatabaseMigrations.run_all_migrations(obs_conn):
                logger.info("Database migrations completed successfully")
            else:
                logger.warning("Database migrations encountered issues")
                
        except Exception as e:
            logger.error(f"Migration error: {e}")
            # Don't crash on migration error - app can still function
            messagebox.showwarning(
                "Migration Warning",
                "Some database updates couldn't be applied.\n"
                "iRecord integration may have limited functionality.\n\n"
                f"Error: {str(e)}"
            )

    def _create_menu_bar(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu (UPDATED: Added iRecord submenu)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # iRecord submenu (NEW)
        irecord_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="iRecord", menu=irecord_menu)
        
        irecord_menu.add_command(
            label="Import from iRecord CSV...",
            command=self._import_from_irecord
        )
        irecord_menu.add_command(
            label="Export for iRecord (Unsubmitted)...",
            command=self._export_for_irecord
        )
        irecord_menu.add_command(
            label="Sync Verification Status...",
            command=self._sync_with_irecord
        )
        
        file_menu.add_separator()
        file_menu.add_command(label="Save & Exit", command=self.save_and_exit)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def _create_main_container(self):
        """Create main container frame"""
        self.main_container = ttk.Frame(self.root, padding="10")
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.rowconfigure(0, weight=1)

    def _create_notebook(self):
        """Create the tabbed notebook interface"""
        # Create notebook (tab container)
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Create placeholder frames for each tab
        # These will be replaced with actual tab implementations in later phases
        self.tabs = {}

        # Create tabs - mix of implemented and placeholder tabs
        tab_configs = [
            ("Home", "implemented"),
            ("Data", "implemented"),
            ("Stats", "placeholder"),
            ("Mapping", "placeholder"),
            ("Longhorns", "placeholder"),
            ("Settings", "implemented"),
            ("Insect Collection", "placeholder")
        ]

        for tab_name, tab_type in tab_configs:
            if tab_type == "implemented":
                # Create actual implemented tab
                if tab_name == "Home":
                    tab_frame = HomeTab(self.notebook, self)
                elif tab_name == "Settings":
                    tab_frame = SettingsTab(self.notebook, self)
                elif tab_name == "Data":
                    tab_frame = DataTab(self.notebook, self)
                # Add more elif blocks here as tabs are implemented
            else:
                # Create placeholder frame
                tab_frame = ttk.Frame(self.notebook)
                tab_frame.columnconfigure(0, weight=1)
                tab_frame.rowconfigure(0, weight=1)

                # Add placeholder label
                placeholder = ttk.Label(
                    tab_frame,
                    text=f"{tab_name} Tab\n(To be implemented)",
                    font=("Arial", 16),
                    foreground="gray"
                )
                placeholder.grid(row=0, column=0, sticky="nsew")

            # Add tab to notebook
            self.notebook.add(tab_frame, text=tab_name)
            self.tabs[tab_name] = tab_frame

        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def _create_status_bar(self):
        """Create status bar at bottom of window"""
        self.status_bar = ttk.Frame(self.main_container)
        self.status_bar.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        # Status label (left side)
        self.status_label = ttk.Label(
            self.status_bar,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Save & Exit button (right side)
        self.exit_button = ttk.Button(
            self.status_bar,
            text="Save & Exit",
            command=self.save_and_exit
        )
        self.exit_button.pack(side=tk.RIGHT)

    # ====== iRecord Integration Methods (NEW) ======

    def _import_from_irecord(self):
        """Import records from iRecord CSV"""
        try:
            from dialogs.irecord_import_dialog import iRecordImportDialog
            dialog = iRecordImportDialog(self.root)
            dialog.wait_window()
            
            # Refresh Data tab if open
            if hasattr(self, 'tabs') and 'Data' in self.tabs:
                if hasattr(self.tabs['Data'], 'refresh'):
                    self.tabs['Data'].refresh()
            
            # Refresh Home tab stats
            if hasattr(self, 'tabs') and 'Home' in self.tabs:
                if hasattr(self.tabs['Home'], '_update_stats'):
                    self.tabs['Home']._update_stats()
            
            self.update_status("iRecord import completed")
            
        except ImportError as e:
            logger.error(f"Import dialog not available: {e}")
            messagebox.showerror(
                "Error",
                "iRecord import dialog not found.\n"
                "Please ensure all dialog files are installed correctly."
            )
        except Exception as e:
            logger.error(f"Error opening import dialog: {e}")
            messagebox.showerror("Error", f"Error opening import dialog:\n{str(e)}")

    def _export_for_irecord(self):
        """Export records to iRecord format"""
        try:
            from dialogs.irecord_export_dialog import iRecordExportDialog
            dialog = iRecordExportDialog(self.root)
            dialog.wait_window()
            
            # Refresh Data tab if open (submission status may have changed)
            if hasattr(self, 'tabs') and 'Data' in self.tabs:
                if hasattr(self.tabs['Data'], 'refresh'):
                    self.tabs['Data'].refresh()
            
            self.update_status("iRecord export completed")
            
        except ImportError as e:
            logger.error(f"Export dialog not available: {e}")
            messagebox.showerror(
                "Error",
                "iRecord export dialog not found.\n"
                "Please ensure all dialog files are installed correctly."
            )
        except Exception as e:
            logger.error(f"Error opening export dialog: {e}")
            messagebox.showerror("Error", f"Error opening export dialog:\n{str(e)}")

    def _sync_with_irecord(self):
        """Sync verification status from iRecord"""
        try:
            from dialogs.irecord_sync_dialog import iRecordSyncDialog
            dialog = iRecordSyncDialog(self.root)
            dialog.wait_window()
            
            # Refresh Data tab if open (verification status may have changed)
            if hasattr(self, 'tabs') and 'Data' in self.tabs:
                if hasattr(self.tabs['Data'], 'refresh'):
                    self.tabs['Data'].refresh()
            
            self.update_status("iRecord sync completed")
            
        except ImportError as e:
            logger.error(f"Sync dialog not available: {e}")
            messagebox.showerror(
                "Error",
                "iRecord sync dialog not found.\n"
                "Please ensure all dialog files are installed correctly."
            )
        except Exception as e:
            logger.error(f"Error opening sync dialog: {e}")
            messagebox.showerror("Error", f"Error opening sync dialog:\n{str(e)}")

    # ====== End iRecord Integration Methods ======

    def on_tab_changed(self, event):
        """Handle tab change event"""
        selected_tab = self.notebook.select()
        tab_name = self.notebook.tab(selected_tab, "text")
        
        # Auto-refresh specific tabs when switched to
        if tab_name == "Data" and hasattr(self.tabs.get("Data"), 'refresh'):
            try:
                self.tabs["Data"].refresh()
            except Exception as e:
                logger.error(f"Error refreshing Data tab: {e}")
        
        elif tab_name == "Home" and hasattr(self.tabs.get("Home"), '_update_stats'):
            try:
                self.tabs["Home"]._update_stats()
            except Exception as e:
                logger.error(f"Error refreshing Home stats: {e}")
        
        self.update_status(f"Switched to {tab_name} tab")

    def update_status(self, message):
        """Update the status bar message"""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def save_and_exit(self):
        """Save any changes and exit the application"""
        # TODO: Implement actual save logic in later phases
        if self.unsaved_changes:
            response = messagebox.askyesnocancel(
                "Save Changes",
                "Do you want to save changes before exiting?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_data()

        self.root.quit()

    def save_data(self):
        """Save current data"""
        # TODO: Implement actual save logic
        self.update_status("Data saved successfully")
        self.unsaved_changes = False

    def on_closing(self):
        """Handle window close event"""
        if self.unsaved_changes:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before exiting?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_data()

        self.root.destroy()

    def show_about(self):
        """Show about dialog"""
        about_text = (
            "Observatum\n"
            "Biological Recording Application\n\n"
            "Version: 0.2.0 (Development)\n"
            "A modern application for recording wildlife observations\n\n"
            "Replacing legacy systems like MapMate and Recorder 6\n\n"
            "Features:\n"
            "• UKSI Integration (204,865 taxa)\n"
            "• iRecord Import/Export\n"
            "• Verification Status Tracking\n"
            "• NBN-Compatible Data Exchange"
        )
        messagebox.showinfo("About Observatum", about_text)


def main():
    """Main entry point for the application"""
    root = tk.Tk()
    app = ObservatumApp(root)

    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()


if __name__ == "__main__":
    main()