"""
iRecord Import Dialog
Import records from iRecord CSV exports
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from pathlib import Path
import uuid

from utils.irecord_mapper import iRecordMapper
from database.db_manager import get_db_manager

logger = logging.getLogger(__name__)


class iRecordImportDialog(tk.Toplevel):
    """Dialog for importing records from iRecord CSV"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Import from iRecord")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        # Variables
        self.filepath = tk.StringVar()
        self.update_verification = tk.BooleanVar(value=True)
        self.skip_duplicates = tk.BooleanVar(value=True)
        self.preserve_comments = tk.BooleanVar(value=True)
        
        self.preview_data = None
        self.import_stats = {
            'total': 0,
            'new': 0,
            'existing': 0,
            'updates': 0
        }
        
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
            text="Import from iRecord CSV",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="CSV File", padding=10)
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
        options_frame = ttk.LabelFrame(main_frame, text="Import Options", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Checkbutton(
            options_frame,
            text="Update verification status for existing records",
            variable=self.update_verification
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            options_frame,
            text="Skip duplicate records",
            variable=self.skip_duplicates
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            options_frame,
            text="Preserve Observatum comments",
            variable=self.preserve_comments
        ).pack(anchor=tk.W, pady=2)
        
        # Preview
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.preview_text = tk.Text(
            preview_frame,
            height=10,
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
        
        self.import_btn = ttk.Button(
            button_frame,
            text="Import",
            command=self._do_import,
            state='disabled'
        )
        self.import_btn.pack(side=tk.RIGHT)
    
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
        """Analyze selected CSV file"""
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
                SELECT id, irecord_key, verification_status 
                FROM records 
                WHERE irecord_key IS NOT NULL
            """)
            
            existing_by_key = {
                row['irecord_key']: row 
                for row in cursor.fetchall()
            }
            
            # Detect duplicates
            new_records, duplicate_records, updated_records = iRecordMapper.detect_duplicates(
                irecord_records,
                existing_by_key
            )
            
            self.preview_data = {
                'all_records': irecord_records,
                'new_records': new_records,
                'duplicate_records': duplicate_records,
                'updated_records': updated_records
            }
            
            # Update preview
            self._update_preview()
            
            # Enable import button
            self.import_btn['state'] = 'normal'
            
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
        
        total = len(self.preview_data['all_records'])
        new = len(self.preview_data['new_records'])
        existing = len(self.preview_data['duplicate_records'])
        updates = len(self.preview_data['updated_records'])
        
        preview_text = f"""File Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total records in file:     {total:>6}

New records to import:     {new:>6}
Already in database:       {existing:>6}
Verification updates:      {updates:>6}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Actions that will be taken:
• Import {new} new records
"""
        
        if self.update_verification.get() and updates > 0:
            preview_text += f"• Update verification for {updates} records\n"
        
        if self.skip_duplicates.get():
            preview_text += f"• Skip {existing} duplicate records\n"
        
        self.preview_text['state'] = 'normal'
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', preview_text)
        self.preview_text['state'] = 'disabled'
    
    def _do_import(self):
        """Perform the import"""
        if not self.preview_data:
            return
        
        # Confirm
        total_changes = (
            len(self.preview_data['new_records']) +
            (len(self.preview_data['updated_records']) if self.update_verification.get() else 0)
        )
        
        if total_changes == 0:
            messagebox.showinfo(
                "No Changes",
                "No new records or updates to import."
            )
            return
        
        response = messagebox.askyesno(
            "Confirm Import",
            f"Import {len(self.preview_data['new_records'])} new records"
            f"{' and update ' + str(len(self.preview_data['updated_records'])) + ' existing records' if self.update_verification.get() else ''}?"
        )
        
        if not response:
            return
        
        try:
            db_manager = get_db_manager()
            obs_conn = db_manager.get_observations_connection()
            cursor = obs_conn.cursor()
            
            imported = 0
            updated = 0
            
            # Import new records
            for irecord_row in self.preview_data['new_records']:
                record = iRecordMapper.irecord_to_observatum(irecord_row)
                
                # Generate UUID if not present
                if not record.get('uuid'):
                    record['uuid'] = str(uuid.uuid4())
                
                # Insert record
                cursor.execute("""
                    INSERT INTO records (
                        uuid, irecord_id, irecord_key, irecord_external_key,
                        species_name, common_name, taxon_version_key,
                        site_name, grid_reference, latitude, longitude,
                        date, recorder, determiner, certainty,
                        sex, stage, quantity, sample_method, observation_type, sample_comment,
                        verification_status, verification_substatus, verified_by, verified_on,
                        submitted_to_irecord, submitted_date, last_synced_with_irecord
                    ) VALUES (
                        :uuid, :irecord_id, :irecord_key, :irecord_external_key,
                        :species_name, :common_name, :taxon_version_key,
                        :site_name, :grid_reference, :latitude, :longitude,
                        :date, :recorder, :determiner, :certainty,
                        :sex, :stage, :count, :sample_method, :observation_type, :comment,
                        :verification_status, :verification_substatus, :verified_by, :verified_on,
                        :submitted_to_irecord, :submitted_date, :last_synced_with_irecord
                    )
                """, record)
                imported += 1
            
            # Update verification status for existing records
            if self.update_verification.get():
                for irecord_row in self.preview_data['updated_records']:
                    record_key = irecord_row.get('RecordKey')
                    
                    cursor.execute("""
                        UPDATE records
                        SET verification_status = ?,
                            verification_substatus = ?,
                            verified_by = ?,
                            verified_on = ?,
                            last_synced_with_irecord = ?
                        WHERE irecord_key = ?
                    """, (
                        irecord_row.get('Verification status 1', 'Not reviewed'),
                        irecord_row.get('Verification status 2'),
                        irecord_row.get('Verifier'),
                        irecord_row.get('Verified on'),
                        datetime.now().isoformat(),
                        record_key
                    ))
                    updated += 1
            
            obs_conn.commit()
            
            # Show success
            messagebox.showinfo(
                "Import Complete",
                f"Successfully imported {imported} new records"
                f"{f' and updated {updated} existing records' if updated > 0 else ''}."
            )
            
            logger.info(f"iRecord import complete: {imported} new, {updated} updated")
            
            # Close dialog
            self.destroy()
            
        except Exception as e:
            logger.error(f"Import error: {e}")
            obs_conn.rollback()
            messagebox.showerror(
                "Import Error",
                f"Error during import:\n{str(e)}"
            )
