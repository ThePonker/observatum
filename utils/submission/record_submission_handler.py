"""
Record Submission Handler for Observatum
Handles validation and database submission of observation records

Extracted from add_record_widget.py to separate business logic from UI.
This makes the code testable, reusable, and easier to maintain.
"""

import uuid
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class RecordSubmissionHandler:
    """
    Handles validation and submission of observation records
    
    Responsibilities:
    - Validate form data
    - Generate UUIDs
    - Insert records into database
    - Trigger UI updates (stats refresh)
    """
    
    def __init__(self, app_instance):
        """
        Initialize the submission handler
        
        Args:
            app_instance: Reference to main application for stats refresh
        """
        self.app = app_instance
    
    def validate_record_data(self, field_values, selected_species):
        """
        Validate observation record data
        
        Args:
            field_values: Dict of form field values
            selected_species: Selected species dict with TVK
            
        Returns:
            tuple: (is_valid: bool, errors: list of str)
        """
        errors = []
        
        # Check species selection first
        if not selected_species or 'tvk' not in selected_species:
            errors.append("Species Search (must select a species with TVK)")
        
        # Check mandatory fields
        if not field_values.get('site_name', '').strip():
            errors.append("Site Name")
        
        if not field_values.get('grid_reference', '').strip():
            errors.append("Grid Ref")
        
        if not field_values.get('date', '').strip():
            errors.append("Date")
        
        if not field_values.get('recorder', '').strip():
            errors.append("Recorder")
        
        if not field_values.get('determiner', '').strip():
            errors.append("Determiner")
        
        if not field_values.get('certainty', '').strip():
            errors.append("Certainty")
        
        # Return validation result
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def prepare_record_data(self, field_values, selected_species):
        """
        Prepare record data dict for database insertion
        
        Args:
            field_values: Dict of form field values
            selected_species: Selected species dict with TVK and name
            
        Returns:
            dict: Prepared record data ready for database insertion
        """
        # Generate UUID for this record
        record_uuid = str(uuid.uuid4())
        
        # Build record data dict
        record_data = {
            'uuid': record_uuid,
            'species_name': selected_species['scientific_name'],
            'taxon_id': selected_species['tvk'],
            'site_name': field_values['site_name'].strip(),
            'grid_reference': field_values['grid_reference'].strip(),
            'date': field_values['date'].strip(),
            'recorder': field_values['recorder'].strip(),
            'determiner': field_values['determiner'].strip(),
            'certainty': field_values['certainty'],
            
            # Optional fields (with None for empty values)
            'sex': field_values.get('sex') if field_values.get('sex') else None,
            'quantity': self._parse_quantity(field_values.get('quantity', '')),
            'sample_method': field_values.get('sample_method', '').strip() or None,
            'observation_type': field_values.get('observation_type', '').strip() or None,
            'sample_comment': field_values.get('sample_comment', '').strip() or None,
            
            # Default values
            'verification_status': 'Not reviewed',
            'submitted_to_irecord': 0
        }
        
        return record_data
    
    def _parse_quantity(self, quantity_str):
        """
        Parse quantity string to integer
        
        Args:
            quantity_str: String value from quantity field
            
        Returns:
            int or None
        """
        if not quantity_str:
            return None
        
        quantity_clean = quantity_str.strip()
        if quantity_clean.isdigit():
            return int(quantity_clean)
        
        return None
    
    def save_record(self, record_data):
        """
        Save record to database
        
        Args:
            record_data: Dict of record data prepared by prepare_record_data()
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Get database connection
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            obs_conn = db_manager.get_observations_connection()
            cursor = obs_conn.cursor()
            
            # Insert record
            cursor.execute("""
                INSERT INTO records (
                    uuid, species_name, taxon_id, site_name, grid_reference, date,
                    recorder, determiner, certainty, sex, quantity,
                    sample_method, observation_type, sample_comment,
                    verification_status, submitted_to_irecord
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_data['uuid'],
                record_data['species_name'],
                record_data['taxon_id'],
                record_data['site_name'],
                record_data['grid_reference'],
                record_data['date'],
                record_data['recorder'],
                record_data['determiner'],
                record_data['certainty'],
                record_data['sex'],
                record_data['quantity'],
                record_data['sample_method'],
                record_data['observation_type'],
                record_data['sample_comment'],
                record_data['verification_status'],
                record_data['submitted_to_irecord']
            ))
            
            # Commit transaction
            obs_conn.commit()
            
            # Refresh UI stats
            self._refresh_stats()
            
            # Build success message
            success_message = (
                f"Observation record for {record_data['species_name']} "
                f"has been saved successfully!\n\n"
                f"TVK: {record_data['taxon_id']}"
            )
            
            logger.info(
                f"Saved record: {record_data['species_name']} "
                f"(TVK: {record_data['taxon_id']}, UUID: {record_data['uuid']})"
            )
            
            return True, success_message
            
        except Exception as e:
            error_message = f"Failed to save record:\n\n{str(e)}"
            logger.error(f"Error saving record: {e}", exc_info=True)
            return False, error_message
    
    def _refresh_stats(self):
        """
        Refresh Home tab statistics after record save
        
        This triggers UI update to show new record counts
        """
        try:
            if hasattr(self.app, 'tabs') and 'Home' in self.app.tabs:
                home_tab = self.app.tabs['Home']
                if hasattr(home_tab, '_update_stats'):
                    home_tab._update_stats()
                    # Force UI update
                    if hasattr(self.app, 'root'):
                        self.app.root.update()
        except Exception as e:
            logger.warning(f"Failed to refresh stats: {e}")
    
    def submit_record(self, field_values, selected_species):
        """
        Complete submission workflow: validate, prepare, and save
        
        This is a convenience method that combines all steps.
        
        Args:
            field_values: Dict of form field values
            selected_species: Selected species dict with TVK
            
        Returns:
            tuple: (success: bool, message: str, errors: list or None)
        """
        # Step 1: Validate
        is_valid, errors = self.validate_record_data(field_values, selected_species)
        
        if not is_valid:
            error_message = "The following mandatory fields are missing:\n\n• " + "\n• ".join(errors)
            return False, error_message, errors
        
        # Step 2: Prepare data
        record_data = self.prepare_record_data(field_values, selected_species)
        
        # Step 3: Save
        success, message = self.save_record(record_data)
        
        return success, message, None
