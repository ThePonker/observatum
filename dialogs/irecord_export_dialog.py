"""
iRecord Export Dialog
Export records in iRecord-compatible CSV format
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from pathlib import Path
from datetime import datetime

from utils.irecord_mapper import iRecordMapper
from database.db_manager import get_db_manager

logger = logging.getLogger(__name__)


class iRecordExportDialog(tk.Toplevel):
    """Dialog for exporting records to iRecord format"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Export for iRecord")
        self.geometry("550x450")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        # Variables
        self.export_type = tk.StringVar(value='unsubmitted')
        self.mark_submitted = tk.BooleanVar(value=True)
        self.include_uuid = tk.BooleanVar(value=True)
        self.date_from = tk.StringVar()
        self.date_to = tk.StringVar()
        
        self.record_counts = {
            'total': 0,
            'unsubmitted': 0,
            'submitted': 0
        }
        
        self._create_widgets()
        self._load_counts()
        
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
            text="Export for iRecord Submission",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Export type
        type_frame = ttk.LabelFrame(main_frame, text="Export Type", padding=10)
        type_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.unsubmitted_radio = ttk.Radiobutton(
            type_frame,
            text="Unsubmitted records only (recommended)",
            variable=self.export_type,
            value='unsubmitted',
            command=self._update_preview
        )
        self.unsubmitted_radio.pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(
            type_frame,
            text="All records",
            variable=self.export_type,
            value='all',
            command=self._update_preview
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(
            type_frame,
            text="Records within date range:",
            variable=self.export_type,
            value='date_range',
            command=self._update_preview
        ).pack(anchor=tk.W, pady=2)
        
        date_frame = ttk.Frame(type_frame)
        date_frame.pack(anchor=tk.W, padx=(30, 0), pady=5)
        
        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(date_frame, textvariable=self.date_from, width=12).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(date_frame, textvariable=self.date_to, width=12).pack(side=tk.LEFT)
        
        ttk.Label(date_frame, text="(YYYY-MM-DD)", font=('Arial', 8)).pack(side=tk.LEFT, padx=(10, 0))
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Export Options", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Checkbutton(
            options_frame,
            text="Include Observatum UUID (enables round-trip sync)",
            variable=self.include_uuid
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            options_frame,
            text="Mark records as submitted after export",
            variable=self.mark_submitted
        ).pack(anchor=tk.W, pady=2)
        
        # Preview
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.preview_text = tk.Text(
            preview_frame,
            height=6,
            width=60,
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
        
        self.export_btn = ttk.Button(
            button_frame,
            text="Export",
            command=self._do_export
        )
        self.export_btn.pack(side=tk.RIGHT)
    
    def _load_counts(self):
        """Load record counts from database"""
        try:
            db_manager = get_db_manager()
            obs_conn = db_manager.get_observations_connection()
            cursor = obs_conn.cursor()
            
            # Total records
            cursor.execute("SELECT COUNT(*) FROM records")
            self.record_counts['total'] = cursor.fetchone()[0]
            
            # Unsubmitted records
            cursor.execute("""
                SELECT COUNT(*) FROM records 
                WHERE submitted_to_irecord = 0 OR submitted_to_irecord IS NULL
            """)
            self.record_counts['unsubmitted'] = cursor.fetchone()[0]
            
            # Submitted records
            cursor.execute("""
                SELECT COUNT(*) FROM records 
                WHERE submitted_to_irecord = 1
            """)
            self.record_counts['submitted'] = cursor.fetchone()[0]
            
            self._update_preview()
            
        except Exception as e:
            logger.error(f"Error loading counts: {e}")
    
    def _update_preview(self):
        """Update preview text based on selection"""
        export_type = self.export_type.get()
        
        if export_type == 'unsubmitted':
            count = self.record_counts['unsubmitted']
            description = f"{count} unsubmitted records"
        elif export_type == 'all':
            count = self.record_counts['total']
            description = f"{count} total records"
        else:  # date_range
            count = self._count_date_range()
            description = f"{count} records in date range"
        
        preview_text = f"""Records to export: {count}

Export will include:
• Species name and common name
• Site name and grid reference
• GPS coordinates (if available)
• Date, recorder, determiner
• Sex, stage, count
• Sample method and comments
"""
        
        if self.include_uuid.get():
            preview_text += "• Observatum UUID (for round-trip sync)\n"
        
        if self.mark_submitted.get() and export_type == 'unsubmitted':
            preview_text += f"\nAfter export, {count} records will be marked as submitted."
        
        self.preview_text['state'] = 'normal'
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', preview_text)
        self.preview_text['state'] = 'disabled'
        
        # Enable/disable export button
        self.export_btn['state'] = 'normal' if count > 0 else 'disabled'
    
    def _count_date_range(self):
        """Count records in date range"""
        try:
            date_from = self.date_from.get()
            date_to = self.date_to.get()
            
            if not date_from or not date_to:
                return 0
            
            db_manager = get_db_manager()
            obs_conn = db_manager.get_observations_connection()
            cursor = obs_conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM records 
                WHERE date BETWEEN ? AND ?
            """, (date_from, date_to))
            
            return cursor.fetchone()[0]
            
        except Exception as e:
            logger.error(f"Error counting date range: {e}")
            return 0
    
    def _get_records_to_export(self):
        """Get records based on export type"""
        db_manager = get_db_manager()
        obs_conn = db_manager.get_observations_connection()
        cursor = obs_conn.cursor()
        
        export_type = self.export_type.get()
        
        if export_type == 'unsubmitted':
            cursor.execute("""
                SELECT * FROM records 
                WHERE submitted_to_irecord = 0 OR submitted_to_irecord IS NULL
                ORDER BY date DESC
            """)
        elif export_type == 'all':
            cursor.execute("""
                SELECT * FROM records 
                ORDER BY date DESC
            """)
        else:  # date_range
            date_from = self.date_from.get()
            date_to = self.date_to.get()
            
            cursor.execute("""
                SELECT * FROM records 
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC
            """, (date_from, date_to))
        
        return cursor.fetchall()
    
    def _do_export(self):
        """Perform the export"""
        try:
            # Get records
            records = self._get_records_to_export()
            
            if not records:
                messagebox.showwarning(
                    "No Records",
                    "No records match the selected criteria."
                )
                return
            
            # Get save filename
            default_filename = f"observatum_irecord_export_{datetime.now().strftime('%Y%m%d')}.csv"
            
            filepath = filedialog.asksaveasfilename(
                parent=self,
                title="Save iRecord Export",
                defaultextension=".csv",
                initialfile=default_filename,
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("All files", "*.*")
                ]
            )
            
            if not filepath:
                return
            
            # Convert records to iRecord format
            irecord_records = []
            for record in records:
                irecord_row = iRecordMapper.observatum_to_irecord(dict(record))
                irecord_records.append(irecord_row)
            
            # Write CSV
            count = iRecordMapper.write_irecord_csv(filepath, irecord_records)
            
            # Mark as submitted if requested
            if self.mark_submitted.get() and self.export_type.get() == 'unsubmitted':
                db_manager = get_db_manager()
                obs_conn = db_manager.get_observations_connection()
                cursor = obs_conn.cursor()
                
                record_ids = [record['id'] for record in records]
                placeholders = ','.join('?' * len(record_ids))
                
                cursor.execute(f"""
                    UPDATE records 
                    SET submitted_to_irecord = 1,
                        submitted_date = ?
                    WHERE id IN ({placeholders})
                """, [datetime.now().isoformat()] + record_ids)
                
                obs_conn.commit()
            
            # Show success
            messagebox.showinfo(
                "Export Complete",
                f"Successfully exported {count} records to:\n{filepath}"
            )
            
            logger.info(f"iRecord export complete: {count} records to {filepath}")
            
            # Close dialog
            self.destroy()
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            messagebox.showerror(
                "Export Error",
                f"Error during export:\n{str(e)}"
            )
