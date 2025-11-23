"""
iRecord Field Mapper
Maps between iRecord CSV format and Observatum database format
"""

import csv
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class iRecordMapper:
    """Maps fields between iRecord CSV and Observatum database"""
    
    # iRecord CSV column names (from actual export)
    IRECORD_COLUMNS = {
        'ID': 'ID',
        'RecordKey': 'RecordKey',
        'External key': 'External key',
        'Taxon': 'Taxon',
        'Common name': 'Common name',
        'TaxonVersionKey': 'TaxonVersionKey',
        'Site name': 'Site name',
        'Original map ref': 'Original map ref',
        'Output map ref': 'Output map ref',
        'Latitude': 'Latitude',
        'Longitude': 'Longitude',
        'Date from': 'Date from',
        'Date to': 'Date to',
        'Recorder': 'Recorder',
        'Determiner': 'Determiner',
        'Recorder certainty': 'Recorder certainty',
        'Sex': 'Sex',
        'Stage': 'Stage',
        'Count of sex or stage': 'Count of sex or stage',
        'Sample method': 'Sample method',
        'Comment': 'Comment',
        'Sample comment': 'Sample comment',
        'Verification status 1': 'Verification status 1',
        'Verification status 2': 'Verification status 2',
        'Verifier': 'Verifier',
        'Verified on': 'Verified on',
        'Input on date': 'Input on date',
        'Last edited on date': 'Last edited on date'
    }
    
    @staticmethod
    def irecord_to_observatum(irecord_row):
        """
        Convert iRecord CSV row to Observatum database record
        
        Args:
            irecord_row (dict): Row from iRecord CSV
            
        Returns:
            dict: Observatum database record
        """
        # Combine Comment and Sample comment
        comment = irecord_row.get('Comment', '').strip()
        sample_comment = irecord_row.get('Sample comment', '').strip()
        combined_comment = ' | '.join(filter(None, [comment, sample_comment]))
        
        # Parse date (iRecord format: YYYY-MM-DD)
        date_from = irecord_row.get('Date from', '')
        
        # Parse count
        count_str = irecord_row.get('Count of sex or stage', '')
        try:
            count = int(count_str) if count_str else None
        except ValueError:
            count = None
        
        # Parse coordinates
        try:
            latitude = float(irecord_row.get('Latitude', '')) if irecord_row.get('Latitude') else None
        except (ValueError, TypeError):
            latitude = None
            
        try:
            longitude = float(irecord_row.get('Longitude', '')) if irecord_row.get('Longitude') else None
        except (ValueError, TypeError):
            longitude = None
        
        # Prefer Output map ref over Original map ref
        grid_ref = irecord_row.get('Output map ref') or irecord_row.get('Original map ref', '')
        
        record = {
            # iRecord identification
            'irecord_id': irecord_row.get('ID'),
            'irecord_key': irecord_row.get('RecordKey'),
            'irecord_external_key': irecord_row.get('External key'),
            
            # Species
            'species_name': irecord_row.get('Taxon', ''),
            'common_name': irecord_row.get('Common name'),
            'taxon_version_key': irecord_row.get('TaxonVersionKey'),
            
            # Location
            'site_name': irecord_row.get('Site name', ''),
            'grid_reference': grid_ref,
            'latitude': latitude,
            'longitude': longitude,
            
            # Observation details
            'date': date_from,
            'recorder': irecord_row.get('Recorder', ''),
            'determiner': irecord_row.get('Determiner'),
            'certainty': irecord_row.get('Recorder certainty'),
            'sex': irecord_row.get('Sex'),
            'stage': irecord_row.get('Stage'),
            'count': count,
            'sample_method': irecord_row.get('Sample method'),
            'observation_type': 'Field Observation',  # Default
            'comment': combined_comment,
            
            # Verification
            'verification_status': irecord_row.get('Verification status 1', 'Not reviewed'),
            'verification_substatus': irecord_row.get('Verification status 2'),
            'verified_by': irecord_row.get('Verifier'),
            'verified_on': irecord_row.get('Verified on'),
            
            # Submission tracking
            'submitted_to_irecord': True,  # Came from iRecord
            'submitted_date': irecord_row.get('Input on date'),
            'last_synced_with_irecord': datetime.now().isoformat()
        }
        
        return record
    
    @staticmethod
    def observatum_to_irecord(observatum_record):
        """
        Convert Observatum database record to iRecord CSV format
        
        Args:
            observatum_record (dict): Observatum database record
            
        Returns:
            dict: iRecord CSV row
        """
        # Format date (iRecord expects YYYY-MM-DD)
        date = observatum_record.get('date', '')
        
        # Handle count
        count = observatum_record.get('count')
        count_str = str(count) if count else ''
        
        irecord_row = {
            # Include External key (Observatum UUID) for round-trip
            'External key': observatum_record.get('uuid', ''),
            
            # Species
            'Taxon': observatum_record.get('species_name', ''),
            'Common name': observatum_record.get('common_name', ''),
            'TaxonVersionKey': observatum_record.get('taxon_version_key', ''),
            
            # Location
            'Site name': observatum_record.get('site_name', ''),
            'Original map ref': observatum_record.get('grid_reference', ''),
            'Latitude': observatum_record.get('latitude', ''),
            'Longitude': observatum_record.get('longitude', ''),
            
            # Date
            'Date from': date,
            'Date to': date,
            'Date type': 'D',  # Day precision
            
            # Observation details
            'Recorder': observatum_record.get('recorder', ''),
            'Determiner': observatum_record.get('determiner', ''),
            'Recorder certainty': observatum_record.get('certainty', ''),
            'Sex': observatum_record.get('sex', ''),
            'Stage': observatum_record.get('stage', ''),
            'Count of sex or stage': count_str,
            'Sample method': observatum_record.get('sample_method', ''),
            'Comment': observatum_record.get('comment', ''),
            
            # Don't include these - iRecord assigns them:
            # 'ID', 'RecordKey', 'Verification status', etc.
        }
        
        return irecord_row
    
    @staticmethod
    def read_irecord_csv(filepath):
        """
        Read iRecord CSV file
        
        Args:
            filepath (str): Path to CSV file
            
        Returns:
            list: List of iRecord records (dicts)
        """
        records = []
        
        try:
            # iRecord exports with UTF-8 BOM
            with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(row)
            
            logger.info(f"Read {len(records)} records from iRecord CSV: {filepath}")
            return records
            
        except Exception as e:
            logger.error(f"Error reading iRecord CSV: {e}")
            raise
    
    @staticmethod
    def write_irecord_csv(filepath, records):
        """
        Write iRecord-compatible CSV file
        
        Args:
            filepath (str): Path to output CSV
            records (list): List of records to export
            
        Returns:
            int: Number of records written
        """
        if not records:
            return 0
        
        try:
            # Define column order for iRecord import
            fieldnames = [
                'External key',
                'Taxon',
                'Common name',
                'TaxonVersionKey',
                'Site name',
                'Original map ref',
                'Latitude',
                'Longitude',
                'Date from',
                'Date to',
                'Date type',
                'Recorder',
                'Determiner',
                'Recorder certainty',
                'Sex',
                'Stage',
                'Count of sex or stage',
                'Sample method',
                'Comment'
            ]
            
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(records)
            
            logger.info(f"Wrote {len(records)} records to iRecord CSV: {filepath}")
            return len(records)
            
        except Exception as e:
            logger.error(f"Error writing iRecord CSV: {e}")
            raise
    
    @staticmethod
    def detect_duplicates(irecord_records, existing_records_by_key):
        """
        Detect which iRecord records already exist in Observatum
        
        Args:
            irecord_records (list): Records from iRecord CSV
            existing_records_by_key (dict): Existing records keyed by irecord_key
            
        Returns:
            tuple: (new_records, duplicate_records, updated_records)
        """
        new_records = []
        duplicate_records = []
        updated_records = []
        
        for irecord_row in irecord_records:
            record_key = irecord_row.get('RecordKey')
            external_key = irecord_row.get('External key')
            
            # Check if exists by RecordKey
            if record_key and record_key in existing_records_by_key:
                existing = existing_records_by_key[record_key]
                
                # Check if verification status changed
                new_status = irecord_row.get('Verification status 1', '')
                old_status = existing.get('verification_status', '')
                
                if new_status != old_status:
                    updated_records.append(irecord_row)
                else:
                    duplicate_records.append(irecord_row)
            else:
                new_records.append(irecord_row)
        
        return new_records, duplicate_records, updated_records
