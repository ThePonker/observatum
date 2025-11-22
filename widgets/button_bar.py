"""
Button Bar Widget for Observatum
Reusable button bar component for consistent UI across tabs

Provides standardized button bars with common actions like Import, Export,
Add Record, and Stats. Can be customized per tab while maintaining consistency.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List, Dict


class ButtonBar(ttk.Frame):
    """
    Reusable button bar widget
    
    Provides a horizontal bar of buttons with consistent styling and spacing.
    Commonly used in Data, Longhorns, and Insect Collection tabs.
    """
    
    def __init__(self, parent, buttons: Optional[List[Dict]] = None, **kwargs):
        """
        Initialize the button bar
        
        Args:
            parent: Parent widget
            buttons: List of button specifications, each dict containing:
                - 'text': Button text
                - 'command': Callback function
                - 'state': Optional button state ('normal', 'disabled')
                - 'width': Optional button width
            **kwargs: Additional arguments passed to ttk.Frame
        """
        super().__init__(parent, **kwargs)
        
        self.buttons = {}
        self.button_specs = buttons or []
        
        self._create_buttons()
        
    def _create_buttons(self):
        """Create all buttons in the button bar"""
        for i, button_spec in enumerate(self.button_specs):
            btn = ttk.Button(
                self,
                text=button_spec.get('text', 'Button'),
                command=button_spec.get('command', lambda: None),
                state=button_spec.get('state', 'normal'),
                width=button_spec.get('width', None)
            )
            
            # Pack with padding between buttons
            btn.pack(side=tk.LEFT, padx=(0, 5) if i < len(self.button_specs) - 1 else 0)
            
            # Store reference using button text as key
            self.buttons[button_spec['text']] = btn
            
    def get_button(self, text: str) -> Optional[ttk.Button]:
        """
        Get a button by its text
        
        Args:
            text: Button text
            
        Returns:
            Button widget or None if not found
        """
        return self.buttons.get(text)
        
    def enable_button(self, text: str):
        """
        Enable a button
        
        Args:
            text: Button text
        """
        btn = self.get_button(text)
        if btn:
            btn.config(state='normal')
            
    def disable_button(self, text: str):
        """
        Disable a button
        
        Args:
            text: Button text
        """
        btn = self.get_button(text)
        if btn:
            btn.config(state='disabled')
            
    def set_button_command(self, text: str, command: Callable):
        """
        Update a button's command
        
        Args:
            text: Button text
            command: New callback function
        """
        btn = self.get_button(text)
        if btn:
            btn.config(command=command)


class DataTabButtonBar(ButtonBar):
    """
    Specialized button bar for data tabs
    
    Provides the standard Import, Export, Add Record, and Stats buttons
    used in Data, Longhorns, and Insect Collection tabs.
    """
    
    def __init__(
        self, 
        parent, 
        tab_name: str = "Data",
        on_import: Optional[Callable] = None,
        on_export: Optional[Callable] = None,
        on_add_record: Optional[Callable] = None,
        on_stats: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize the data tab button bar
        
        Args:
            parent: Parent widget
            tab_name: Name of the tab (used for Stats button label)
            on_import: Callback for Import Data button
            on_export: Callback for Export Data button
            on_add_record: Callback for Add Single Record button
            on_stats: Callback for Stats button
            **kwargs: Additional arguments passed to ButtonBar
        """
        self.tab_name = tab_name
        
        # Define standard buttons
        buttons = [
            {
                'text': 'Import Data',
                'command': on_import or self._placeholder_import
            },
            {
                'text': 'Export Data',
                'command': on_export or self._placeholder_export
            },
            {
                'text': 'Add Single Record',
                'command': on_add_record or self._placeholder_add_record
            },
            {
                'text': f'{tab_name} Stats',
                'command': on_stats or self._placeholder_stats
            }
        ]
        
        super().__init__(parent, buttons=buttons, **kwargs)
        
    def _placeholder_import(self):
        """Placeholder for import function"""
        print(f"{self.tab_name}: Import Data clicked")
        
    def _placeholder_export(self):
        """Placeholder for export function"""
        print(f"{self.tab_name}: Export Data clicked")
        
    def _placeholder_add_record(self):
        """Placeholder for add record function"""
        print(f"{self.tab_name}: Add Single Record clicked")
        
    def _placeholder_stats(self):
        """Placeholder for stats function"""
        print(f"{self.tab_name}: Stats clicked")


class SimpleButtonBar(ButtonBar):
    """
    Simple button bar with custom buttons
    
    For tabs that need a button bar but not the standard data tab layout.
    """
    
    def __init__(self, parent, button_configs: List[tuple], **kwargs):
        """
        Initialize simple button bar
        
        Args:
            parent: Parent widget
            button_configs: List of (text, command) tuples
            **kwargs: Additional arguments passed to ButtonBar
        """
        buttons = [
            {'text': text, 'command': command}
            for text, command in button_configs
        ]
        
        super().__init__(parent, buttons=buttons, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    # Create test window
    root = tk.Tk()
    root.title("Button Bar Test")
    root.geometry("800x400")
    
    # Test DataTabButtonBar
    def test_import():
        print("Import clicked!")
        
    def test_export():
        print("Export clicked!")
        
    def test_add():
        print("Add Record clicked!")
        
    def test_stats():
        print("Stats clicked!")
    
    label1 = ttk.Label(root, text="DataTabButtonBar Example:", font=("Arial", 12, "bold"))
    label1.pack(pady=(20, 10))
    
    data_button_bar = DataTabButtonBar(
        root,
        tab_name="Observation Database",
        on_import=test_import,
        on_export=test_export,
        on_add_record=test_add,
        on_stats=test_stats
    )
    data_button_bar.pack(padx=20, pady=10, anchor=tk.W)
    
    # Test SimpleButtonBar
    label2 = ttk.Label(root, text="SimpleButtonBar Example:", font=("Arial", 12, "bold"))
    label2.pack(pady=(30, 10))
    
    simple_buttons = [
        ("Refresh", lambda: print("Refresh clicked!")),
        ("Settings", lambda: print("Settings clicked!")),
        ("Help", lambda: print("Help clicked!"))
    ]
    
    simple_button_bar = SimpleButtonBar(root, button_configs=simple_buttons)
    simple_button_bar.pack(padx=20, pady=10, anchor=tk.W)
    
    # Test button control
    label3 = ttk.Label(root, text="Button Control Example:", font=("Arial", 12, "bold"))
    label3.pack(pady=(30, 10))
    
    control_bar = DataTabButtonBar(root, tab_name="Test")
    control_bar.pack(padx=20, pady=10, anchor=tk.W)
    
    # Control buttons
    control_frame = ttk.Frame(root)
    control_frame.pack(padx=20, pady=10)
    
    ttk.Button(
        control_frame,
        text="Disable Import",
        command=lambda: control_bar.disable_button("Import Data")
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        control_frame,
        text="Enable Import",
        command=lambda: control_bar.enable_button("Import Data")
    ).pack(side=tk.LEFT, padx=5)
    
    root.mainloop()
