"""
Validators for Observatum
Validation functions for data entry fields

Includes:
- UK Grid Reference validation
- Date validation
- Numeric validation
"""

import re
from datetime import datetime
from typing import Tuple, Optional


class GridReferenceValidator:
    """Validator for UK National Grid References"""
    
    # UK National Grid square letters (100km squares)
    GRID_LETTERS = [
        ['SV', 'SW', 'SX', 'SY', 'SZ', 'TV', 'TW'],
        ['SQ', 'SR', 'SS', 'ST', 'SU', 'TQ', 'TR'],
        ['SL', 'SM', 'SN', 'SO', 'SP', 'TL', 'TM'],
        ['SF', 'SG', 'SH', 'SJ', 'SK', 'TF', 'TG'],
        ['SA', 'SB', 'SC', 'SD', 'SE', 'TA', 'TB'],
        ['NV', 'NW', 'NX', 'NY', 'NZ', 'OV', 'OW'],
        ['NQ', 'NR', 'NS', 'NT', 'NU', 'OQ', 'OR'],
        ['NL', 'NM', 'NN', 'NO', 'NP', 'OL', 'OM'],
        ['NF', 'NG', 'NH', 'NJ', 'NK', 'OF', 'OG'],
        ['NA', 'NB', 'NC', 'ND', 'NE', 'OA', 'OB'],
        ['HV', 'HW', 'HX', 'HY', 'HZ', 'JV', 'JW'],
        ['HQ', 'HR', 'HS', 'HT', 'HU', 'JQ', 'JR'],
        ['HL', 'HM', 'HN', 'HO', 'HP', 'JL', 'JM']
    ]
    
    # Flatten for quick lookup
    VALID_SQUARES = set()
    for row in GRID_LETTERS:
        VALID_SQUARES.update(row)
    
    @classmethod
    def validate(cls, grid_ref: str) -> Tuple[bool, str]:
        """
        Validate UK National Grid Reference
        
        Supports formats:
        - 2 letters + numbers (e.g., TQ123456, TQ12345678, TQ1234)
        - Tetrad: 2 letters + 2 numbers + letter (e.g., TQ12A)
        
        Args:
            grid_ref: Grid reference string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not grid_ref or not isinstance(grid_ref, str):
            return False, "Grid reference is required"
        
        # Remove spaces and convert to uppercase
        grid_ref = grid_ref.replace(' ', '').upper()
        
        # Check minimum length (2 letters + at least 2 digits)
        if len(grid_ref) < 4:
            return False, "Grid reference too short (minimum: 2 letters + 2 digits)"
        
        # Extract letters (first 2 characters)
        letters = grid_ref[:2]
        remainder = grid_ref[2:]
        
        # Validate letters are in UK grid
        if letters not in cls.VALID_SQUARES:
            return False, f"Invalid grid square '{letters}'. Must be valid UK National Grid square."
        
        # Check for Tetrad format (e.g., TQ12A)
        tetrad_match = re.match(r'^(\d{2})([A-Z])$', remainder)
        if tetrad_match:
            return True, ""
        
        # Standard format: even number of digits (2, 4, 6, 8, or 10)
        if not remainder.isdigit():
            return False, "Grid reference must contain only letters and numbers"
        
        if len(remainder) % 2 != 0:
            return False, "Grid reference must have even number of digits (e.g., 2, 4, 6, 8, or 10)"
        
        if len(remainder) < 2 or len(remainder) > 10:
            return False, "Grid reference must have 2-10 digits"
        
        return True, ""
    
    @classmethod
    def format(cls, grid_ref: str) -> str:
        """
        Format grid reference with space after letters
        
        Args:
            grid_ref: Grid reference string
            
        Returns:
            Formatted grid reference (e.g., "TQ 123 456")
        """
        if not grid_ref:
            return ""
        
        # Remove existing spaces and uppercase
        grid_ref = grid_ref.replace(' ', '').upper()
        
        # Validate first
        is_valid, _ = cls.validate(grid_ref)
        if not is_valid:
            return grid_ref  # Return as-is if invalid
        
        # Format: 2 letters, space, then numbers
        letters = grid_ref[:2]
        numbers = grid_ref[2:]
        
        # For standard format, add space in middle of numbers if 4+ digits
        if numbers.isdigit() and len(numbers) >= 4:
            mid = len(numbers) // 2
            numbers = f"{numbers[:mid]} {numbers[mid:]}"
        
        return f"{letters} {numbers}"


class DateValidator:
    """Validator for date fields"""
    
    @staticmethod
    def validate(date_str: str, allow_future: bool = False) -> Tuple[bool, str]:
        """
        Validate date string
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            allow_future: Whether to allow future dates
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not date_str:
            return False, "Date is required"
        
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Check if future date
            if not allow_future and date > datetime.now():
                return False, "Date cannot be in the future"
            
            # Check reasonable range (not before 1900)
            if date.year < 1900:
                return False, "Date must be after 1900"
            
            return True, ""
            
        except ValueError:
            return False, "Invalid date format (use YYYY-MM-DD)"


class QuantityValidator:
    """Validator for quantity fields"""
    
    @staticmethod
    def validate(quantity_str: str, allow_zero: bool = False) -> Tuple[bool, str]:
        """
        Validate quantity string
        
        Args:
            quantity_str: Quantity as string
            allow_zero: Whether to allow zero
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not quantity_str or not quantity_str.strip():
            return True, ""  # Optional field
        
        try:
            quantity = int(quantity_str)
            
            if quantity < 0:
                return False, "Quantity cannot be negative"
            
            if not allow_zero and quantity == 0:
                return False, "Quantity must be greater than zero"
            
            if quantity > 1000000:
                return False, "Quantity seems unreasonably large (max: 1,000,000)"
            
            return True, ""
            
        except ValueError:
            return False, "Quantity must be a whole number"


def validate_required_field(value: str, field_name: str) -> Tuple[bool, str]:
    """
    Validate a required field is not empty
    
    Args:
        value: Field value
        field_name: Name of field for error message
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value or not value.strip():
        return False, f"{field_name} is required"
    return True, ""


def validate_all_record_fields(record_data: dict) -> Tuple[bool, list]:
    """
    Validate all fields in a record
    
    Args:
        record_data: Dictionary of record fields
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields
    required = {
        'species_name': 'Species',
        'site_name': 'Site Name',
        'grid_reference': 'Grid Reference',
        'date': 'Date',
        'recorder': 'Recorder',
        'determiner': 'Determiner',
        'certainty': 'Certainty'
    }
    
    for field, label in required.items():
        is_valid, error = validate_required_field(record_data.get(field, ''), label)
        if not is_valid:
            errors.append(error)
    
    # Grid reference validation
    if record_data.get('grid_reference'):
        is_valid, error = GridReferenceValidator.validate(record_data['grid_reference'])
        if not is_valid:
            errors.append(f"Grid Reference: {error}")
    
    # Date validation
    if record_data.get('date'):
        is_valid, error = DateValidator.validate(record_data['date'])
        if not is_valid:
            errors.append(f"Date: {error}")
    
    # Quantity validation (optional field)
    if record_data.get('quantity'):
        is_valid, error = QuantityValidator.validate(str(record_data['quantity']))
        if not is_valid:
            errors.append(f"Quantity: {error}")
    
    return len(errors) == 0, errors
