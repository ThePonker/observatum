"""
Settings Tab for Observatum
Configuration and user preferences

Allows users to configure:
- Default values for data entry fields (Recorder, Determiner, Certainty)
- Application preferences
- Database settings
- Display options
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
from typing import Dict, Any

try:
    from tabs.base_tab import BaseTab
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from tabs.base_tab import BaseTab


class SettingsTab(BaseTab):
    """Settings and configuration tab"""
    
    def __init__(self, parent, app_instance, **kwargs):
        """Initialize the settings tab"""
        self.config_file = Path(__file__).parent.parent / 'data' / 'config.json'
        self.settings = self._load_settings()
        super().__init__(parent, app_instance, **kwargs)
        
    def setup_ui(self):
        """Create the settings interface"""
        # Main container
        main_container = ttk.Frame(self, padding="20")
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_container,
            text="Settings",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Create notebook for different settings categories
        self.settings_notebook = ttk.Notebook(main_container)
        self.settings_notebook.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        main_container.rowconfigure(1, weight=1)
        
        # Create settings pages
        self._create_data_entry_defaults_page()
        self._create_display_settings_page()
        self._create_database_settings_page()
        
        # Buttons at bottom
        button_frame = ttk.Frame(main_container)
        button_frame.grid(row=2, column=0, sticky="ew")
        
        ttk.Button(
            button_frame,
            text="Save Settings",
            command=self.save_settings
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults
        ).pack(side=tk.LEFT)
        
    def _create_data_entry_defaults_page(self):
        """Create page for data entry default values"""
        page = ttk.Frame(self.settings_notebook, padding="20")
        self.settings_notebook.add(page, text="Data Entry Defaults")
        
        # Description
        desc_label = ttk.Label(
            page,
            text="Set default values that will be pre-filled in the Add Single Record dialog:",
            wraplength=500,
            justify=tk.LEFT
        )
        desc_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
        
        # Default Recorder
        ttk.Label(page, text="Default Recorder:").grid(row=1, column=0, sticky="w", pady=5)
        self.recorder_var = tk.StringVar(value=self.settings.get('default_recorder', ''))
        recorder_entry = ttk.Entry(page, textvariable=self.recorder_var, width=40)
        recorder_entry.grid(row=1, column=1, sticky="w", pady=5, padx=(10, 0))
        
        # Default Determiner
        ttk.Label(page, text="Default Determiner:").grid(row=2, column=0, sticky="w", pady=5)
        self.determiner_var = tk.StringVar(value=self.settings.get('default_determiner', ''))
        determiner_entry = ttk.Entry(page, textvariable=self.determiner_var, width=40)
        determiner_entry.grid(row=2, column=1, sticky="w", pady=5, padx=(10, 0))
        
        # Default Certainty
        ttk.Label(page, text="Default Certainty:").grid(row=3, column=0, sticky="w", pady=5)
        self.certainty_var = tk.StringVar(value=self.settings.get('default_certainty', 'Certain'))
        certainty_combo = ttk.Combobox(
            page,
            textvariable=self.certainty_var,
            values=['Certain', 'Likely', 'Uncertain'],
            width=37,
            state='readonly'
        )
        certainty_combo.grid(row=3, column=1, sticky="w", pady=5, padx=(10, 0))
        
        # Default Sample Method
        ttk.Label(page, text="Default Sample Method:").grid(row=4, column=0, sticky="w", pady=5)
        self.sample_method_var = tk.StringVar(value=self.settings.get('default_sample_method', ''))
        sample_method_entry = ttk.Entry(page, textvariable=self.sample_method_var, width=40)
        sample_method_entry.grid(row=4, column=1, sticky="w", pady=5, padx=(10, 0))
        
        # Default Observation Type
        ttk.Label(page, text="Default Observation Type:").grid(row=5, column=0, sticky="w", pady=5)
        self.obs_type_var = tk.StringVar(value=self.settings.get('default_observation_type', ''))
        obs_type_entry = ttk.Entry(page, textvariable=self.obs_type_var, width=40)
        obs_type_entry.grid(row=5, column=1, sticky="w", pady=5, padx=(10, 0))
        
    def _create_display_settings_page(self):
        """Create page for display settings"""
        page = ttk.Frame(self.settings_notebook, padding="20")
        self.settings_notebook.add(page, text="Display Settings")
        
        # Description
        desc_label = ttk.Label(
            page,
            text="Customize the appearance and behavior of the application:",
            wraplength=500,
            justify=tk.LEFT
        )
        desc_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
        
        # Theme (placeholder for future implementation)
        ttk.Label(page, text="Theme:").grid(row=1, column=0, sticky="w", pady=5)
        self.theme_var = tk.StringVar(value=self.settings.get('theme', 'Default'))
        theme_combo = ttk.Combobox(
            page,
            textvariable=self.theme_var,
            values=['Default', 'Dark', 'Light'],
            width=37,
            state='readonly'
        )
        theme_combo.grid(row=1, column=1, sticky="w", pady=5, padx=(10, 0))
        
        # Font size
        ttk.Label(page, text="Font Size:").grid(row=2, column=0, sticky="w", pady=5)
        self.font_size_var = tk.StringVar(value=self.settings.get('font_size', 'Medium'))
        font_combo = ttk.Combobox(
            page,
            textvariable=self.font_size_var,
            values=['Small', 'Medium', 'Large'],
            width=37,
            state='readonly'
        )
        font_combo.grid(row=2, column=1, sticky="w", pady=5, padx=(10, 0))
        
        # Show grid lines
        self.show_grid_var = tk.BooleanVar(value=self.settings.get('show_grid_lines', True))
        grid_check = ttk.Checkbutton(
            page,
            text="Show grid lines in data tables",
            variable=self.show_grid_var
        )
        grid_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=10)
        
        # Confirm deletions
        self.confirm_delete_var = tk.BooleanVar(value=self.settings.get('confirm_deletions', True))
        delete_check = ttk.Checkbutton(
            page,
            text="Confirm before deleting records",
            variable=self.confirm_delete_var
        )
        delete_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
        
        # Auto-save
        self.auto_save_var = tk.BooleanVar(value=self.settings.get('auto_save', False))
        autosave_check = ttk.Checkbutton(
            page,
            text="Auto-save changes every 5 minutes",
            variable=self.auto_save_var
        )
        autosave_check.grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
        
    def _create_database_settings_page(self):
        """Create page for database settings"""
        page = ttk.Frame(self.settings_notebook, padding="20")
        self.settings_notebook.add(page, text="Database Settings")
        
        # Description
        desc_label = ttk.Label(
            page,
            text="Database location and backup settings:",
            wraplength=500,
            justify=tk.LEFT
        )
        desc_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))
        
        # Database location (read-only for now)
        ttk.Label(page, text="Database Location:").grid(row=1, column=0, sticky="nw", pady=5)
        db_path = Path(__file__).parent.parent / 'data'
        db_label = ttk.Label(
            page,
            text=str(db_path.absolute()),
            foreground="gray"
        )
        db_label.grid(row=1, column=1, sticky="w", pady=5, padx=(10, 0))
        
        # Backup settings
        ttk.Label(page, text="Automatic Backups:").grid(row=2, column=0, sticky="w", pady=5)
        self.backup_var = tk.StringVar(value=self.settings.get('backup_frequency', 'Weekly'))
        backup_combo = ttk.Combobox(
            page,
            textvariable=self.backup_var,
            values=['Never', 'Daily', 'Weekly', 'Monthly'],
            width=37,
            state='readonly'
        )
        backup_combo.grid(row=2, column=1, sticky="w", pady=5, padx=(10, 0))
        
        # Manual backup button
        backup_button = ttk.Button(
            page,
            text="Create Backup Now",
            command=self.create_backup
        )
        backup_button.grid(row=3, column=0, columnspan=2, sticky="w", pady=20)
        
        # Database statistics
        stats_frame = ttk.LabelFrame(page, text="Database Statistics", padding="10")
        stats_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        
        stats_text = "Database statistics will be displayed here:\n"
        stats_text += "• Total observations: (to be implemented)\n"
        stats_text += "• Total species: (to be implemented)\n"
        stats_text += "• Database size: (to be implemented)"
        
        ttk.Label(
            stats_frame,
            text=stats_text,
            foreground="gray",
            justify=tk.LEFT
        ).pack(anchor=tk.W)
        
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from config file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
                return self._get_default_settings()
        return self._get_default_settings()
        
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings"""
        return {
            'default_recorder': '',
            'default_determiner': '',
            'default_certainty': 'Certain',
            'default_sample_method': '',
            'default_observation_type': '',
            'theme': 'Default',
            'font_size': 'Medium',
            'show_grid_lines': True,
            'confirm_deletions': True,
            'auto_save': False,
            'backup_frequency': 'Weekly'
        }
        
    def save_settings(self):
        """Save current settings to file"""
        try:
            # Gather all settings
            self.settings = {
                'default_recorder': self.recorder_var.get(),
                'default_determiner': self.determiner_var.get(),
                'default_certainty': self.certainty_var.get(),
                'default_sample_method': self.sample_method_var.get(),
                'default_observation_type': self.obs_type_var.get(),
                'theme': self.theme_var.get(),
                'font_size': self.font_size_var.get(),
                'show_grid_lines': self.show_grid_var.get(),
                'confirm_deletions': self.confirm_delete_var.get(),
                'auto_save': self.auto_save_var.get(),
                'backup_frequency': self.backup_var.get()
            }
            
            # Ensure data directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
                
            self.update_status("Settings saved successfully")
            messagebox.showinfo("Settings Saved", "Your settings have been saved successfully.")
            self.clear_modified()
            
        except Exception as e:
            self.update_status(f"Error saving settings: {e}")
            messagebox.showerror("Save Error", f"Could not save settings:\n{e}")
            
    def reset_to_defaults(self):
        """Reset all settings to default values"""
        response = messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?"
        )
        
        if response:
            defaults = self._get_default_settings()
            
            # Update all variables
            self.recorder_var.set(defaults['default_recorder'])
            self.determiner_var.set(defaults['default_determiner'])
            self.certainty_var.set(defaults['default_certainty'])
            self.sample_method_var.set(defaults['default_sample_method'])
            self.obs_type_var.set(defaults['default_observation_type'])
            self.theme_var.set(defaults['theme'])
            self.font_size_var.set(defaults['font_size'])
            self.show_grid_var.set(defaults['show_grid_lines'])
            self.confirm_delete_var.set(defaults['confirm_deletions'])
            self.auto_save_var.set(defaults['auto_save'])
            self.backup_var.set(defaults['backup_frequency'])
            
            self.update_status("Settings reset to defaults")
            self.mark_modified()
            
    def create_backup(self):
        """Create a manual database backup"""
        # TODO: Implement actual backup functionality
        self.update_status("Backup functionality to be implemented")
        messagebox.showinfo(
            "Backup",
            "Database backup functionality will be implemented in a future version."
        )
        
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a specific setting value
        
        Args:
            key: Setting key
            default: Default value if key doesn't exist
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
