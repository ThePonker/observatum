"""
Observatum - Biological Recording Application
Main application entry point with tabbed interface

This is the main window that coordinates all tabs and manages the application lifecycle.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import tabs
from tabs.home_tab import HomeTab
from tabs.settings_tab import SettingsTab


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
        
        # Create UI components
        self._create_menu_bar()
        self._create_main_container()
        self._create_notebook()
        self._create_status_bar()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def _create_menu_bar(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
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
            ("Data", "placeholder"),
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
        
    def on_tab_changed(self, event):
        """Handle tab change event"""
        selected_tab = self.notebook.select()
        tab_name = self.notebook.tab(selected_tab, "text")
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
            "Version: 0.1.0 (Development)\n"
            "A modern application for recording wildlife observations\n\n"
            "Replacing legacy systems like MapMate and Recorder 6"
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
