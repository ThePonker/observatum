"""
iRecord Sync Dialog
Sync verification status from iRecord CSV exports
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from datetime import datetime

from utils.irecord_mapper import iRecordMapper
from database.db_manager import get_db_manager

logger = logging.getLogger(__name__)


class iRecordSyncDialog(tk.Toplevel):
    """Dialog for syncing verification status with iRecord"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Sync with iRecord")
        self.geometry("600x450")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        # Variables
        self.filepath = tk.StringVar()
        self.sync_verification = tk.BooleanVar(value=True)
        self.sync_comments = tk.BooleanVar(value=False)
        
        self.preview_data = None
        
        self._create_widgets()
        
        # Position center of parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets"""
        
        # Main frame
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Sync Verification Status with iRecord",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 10))
        
        # Instructions
        instructions = ttk.Label(
            main_frame,
            text="1. Download your records from iRecord and save as CSV\n"
                 "2. Select the CSV file below\n"
                 "3. Review the preview and click Sync",
            justify=tk.LEFT
        )
        instructions.pack(pady=(0, 15), anchor=tk.W)
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="iRecord CSV File", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        file_entry_frame = ttk.Frame(file_frame)
        file_entry_frame.pack(fill=tk.X)
        
        self.file_entry = ttk.Entry(
            file_entry_frame,
            textvariable=self.filepath,
            state='readonly'
        )
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = ttk.Button(
            file_entry_frame,
            text="Browse...",
            command=self._browse_file
        )
        browse_btn.pack(side=tk.RIGHT)
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Sync Options", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Checkbutton(
            options_frame,
            text="Update verification status and verifier info",
            variable=self.sync_verification
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            options_frame,
            text="Update comments (will overwrite Observatum comments)",
            variable=self.sync_comments
        ).pack(anchor=tk.W, pady=2)
        
        # Preview
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.preview_text = tk.Text(
            preview_frame,
            height=8,
            width=70,
            wrap=tk.WORD,
            state='disabled',
            font=('Courier', 9)
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        self.sync_btn = ttk.Button(
            button_frame,
            text="Sync Now",
            command=self._do_sync,
            state='disabled'
        )
        self.sync_btn.pack(side=tk.RIGHT)
    
    def _browse_file(self):
        """Browse for iRecord CSV file"""
        filename = filedialog.askopenfilename(
            parent=self,
            title="Select iRecord CSV Export",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.filepath.set(filename)
            self._analyze_file()
    
    def _analyze_file(self):
        """Analyze selected CSV file for sync"""
        filepath = self.filepath.get()
        if not filepath:
            return
        
        try:
            # Read iRecord CSV
            irecord_records = iRecordMapper.read_irecord_csv(filepath)
            
            if not irecord_records:
                messagebox.showerror(
                    "Empty File",
                    "The selected CSV file contains no records."
                )
                return
            
            # Get existing records from database
            db_manager = get_db_manager()
            obs_conn = db_manager.get_observations_connection()
            cursor = obs_conn.cursor()
            
            cursor.execute("""
                SELECT id, irecord_key, irecord_external_key, uuid, 
                       verification_status, species_name, date
                FROM records
            """)
            
            existing_records = cursor.fetchall()
            
            # Build lookup dictionaries
            by_irecord_key = {
                r['irecord_key']: r 
                for r in existing_records 
                if r['irecord_key']
            }
            
            by_uuid = {
                r['uuid']: r 
                for r in existing_records 
                if r['uuid']
            }
            
            by_external_key = {
                r['irecord_external_key']: r 
                for r in existing_records 
                if r['irecord_external_key']
            }
            
            # Analyze what will be updated
            matches = []
            verification_updates = []
            no_match = []
            
            for irecord_row in irecord_records:
                record_key = irecord_row.get('RecordKey')
                external_key = irecord_row.get('External key')
                
                existing = None
                match_type = None
                
                # Try to match by RecordKey
                if record_key and record_key in by_irecord_key:
                    existing = by_irecord_key[record_key]
                    match_type = 'RecordKey'
                
                # Try to match by External key (UUID)
                elif external_key and external_key in by_uuid:
                    existing = by_uuid[external_key]
                    match_type = 'UUID'
                
                elif external_key and external_key in by_external_key:
                    existing = by_external_key[external_key]
                    match_type = 'External Key'
                
                if existing:
                    matches.append({
                        'irecord_row': irecord_row,
                        'existing': existing,
                        'match_type': match_type
                    })
                    
                    # Check if verification changed
                    new_status = irecord_row.get('Verification status 1', '')
                    old_status = existing['verification_status'] or ''
                    
                    if new_status != old_status:
                        verification_updates.append({
                            'species': existing['species_name'],
                            'date': existing['date'],
                            'old_status': old_status,
                            'new_status': new_status
                        })
                else:
                    no_match.append(irecord_row)
            
            self.preview_data = {
                'irecord_records': irecord_records,
                'matches': matches,
                'verification_updates': verification_updates,
                'no_match': no_match
            }
            
            # Update preview
            self._update_preview()
            
            # Enable sync button
            self.sync_btn['state'] = 'normal'
            
        except Exception as e:
            logger.error(f"Error analyzing file: {e}")
            messagebox.showerror(
                "Error",
                f"Error analyzing file:\n{str(e)}"
            )
    
    def _update_preview(self):
        """Update preview text"""
        if not self.preview_data:
            return
        
        total_irecord = len(self.preview_data['irecord_records'])
        matched = len(self.preview_data['matches'])
        verification_updates = len(self.preview_data['verification_updates'])
        no_match = len(self.preview_data['no_match'])
        
        preview_text = f"""Sync Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Records in iRecord file:   {total_irecord:>6}
Matched in Observatum:     {matched:>6}
Not found in Observatum:   {no_match:>6}

Verification updates:      {verification_updates:>6}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if verification_updates > 0:
            preview_text += "\nRecent verification updates:\n"
            for update in self.preview_data['verification_updates'][:5]:
                preview_text += f"• {update['species']} ({update['date']})\n"
                preview_text += f"  {update['old_status']} → {update['new_status']}\n"
            
            if verification_updates > 5:
                preview_text += f"\n...and {verification_updates - 5} more\n"
        
        self.preview_text['state'] = 'normal'
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', preview_text)
        self.preview_text['state'] = 'disabled'
    
    def _do_sync(self):
        """Perform the sync"""
        if not self.preview_data:
            return
        
        updates_count = len(self.preview_data['verification_updates'])
        
        if updates_count == 0:
            messagebox.showinfo(
                "No Updates",
                "No verification status updates found."
            )
            return
        
        # Confirm
        response = messagebox.askyesno(
            "Confirm Sync",
            f"Update verification status for {updates_count} records?"
        )
        
        if not response:
            return
        
        try:
            db_manager = get_db_manager()
            obs_conn = db_manager.get_observations_connection()
            cursor = obs_conn.cursor()
            
            updated = 0
            
            for match in self.preview_data['matches']:
                irecord_row = match['irecord_row']
                existing = match['existing']
                
                # Update verification status
                if self.sync_verification.get():
                    new_status = irecord_row.get('Verification status 1', 'Not reviewed')
                    old_status = existing['verification_status'] or ''
                    
                    if new_status != old_status:
                        update_fields = {
                            'verification_status': new_status,
                            'verification_substatus': irecord_row.get('Verification status 2'),
                            'verified_by': irecord_row.get('Verifier'),
                            'verified_on': irecord_row.get('Verified on'),
                            'last_synced_with_irecord': datetime.now().isoformat()
                        }
                        
                        # Update iRecord keys if missing
                        if not existing.get('irecord_key'):
                            update_fields['irecord_key'] = irecord_row.get('RecordKey')
                        if not existing.get('irecord_id'):
                            update_fields['irecord_id'] = irecord_row.get('ID')
                        if not existing.get('irecord_external_key'):
                            update_fields['irecord_external_key'] = irecord_row.get('External key')
                        
                        # Build UPDATE query
                        set_clause = ', '.join([f"{k} = ?" for k in update_fields.keys()])
                        values = list(update_fields.values()) + [existing['id']]
                        
                        cursor.execute(f"""
                            UPDATE records
                            SET {set_clause}
                            WHERE id = ?
                        """, values)
                        
                        updated += 1
            
            obs_conn.commit()
            
            # Show success
            messagebox.showinfo(
                "Sync Complete",
                f"Successfully updated {updated} records."
            )
            
            logger.info(f"iRecord sync complete: {updated} records updated")
            
            # Close dialog
            self.destroy()
            
        except Exception as e:
            logger.error(f"Sync error: {e}")
            obs_conn.rollback()
            messagebox.showerror(
                "Sync Error",
                f"Error during sync:\n{str(e)}"
            )
