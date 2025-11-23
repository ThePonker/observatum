"""
COMPREHENSIVE FIX for data_tab.py
Fixes ALL issues from the reorganization in one go:
1. Updates all import paths to new folder structure
2. Separates FilterPanel and EditRecordDialog imports
3. Adds UPDATE statement to _on_record_saved method
"""

# Read the file
with open('tabs/data_tab.py', 'r', encoding='utf-8') as f:
    content = f.read()

print("🔧 Fixing data_tab.py...")
print()

# Fix 1: Update imports for reorganized folders
print("1️⃣ Updating imports to new folder structure...")
content = content.replace(
    'from widgets.record_table_widget import',
    'from widgets.tables.record_table_widget import'
)
content = content.replace(
    'from database.record_query_builder import',
    'from database.queries.record_query_builder import'
)
content = content.replace(
    'from widgets.filter_panel import',
    'from widgets.panels.filter_panel import'
)
print("   ✅ Updated import paths")

# Fix 2: Separate FilterPanel and EditRecordDialog imports
print("2️⃣ Separating FilterPanel and EditRecordDialog imports...")
old_imports = """try:
    from widgets.panels.filter_panel import FilterPanel
    from dialogs.edit_record_dialog import EditRecordDialog
except ImportError:
    FilterPanel = None
    EditRecordDialog = None"""

new_imports = """try:
    from widgets.panels.filter_panel import FilterPanel
except ImportError:
    FilterPanel = None

try:
    from dialogs.edit_record_dialog import EditRecordDialog
except ImportError:
    EditRecordDialog = None"""

if old_imports in content:
    content = content.replace(old_imports, new_imports)
    print("   ✅ Separated import try/except blocks")
else:
    print("   ⏭️  Already separated")

# Fix 3: Add UPDATE statement to _on_record_saved
print("3️⃣ Adding UPDATE statement to _on_record_saved...")

# Find the method
import re
pattern = r'def _on_record_saved\(self, updated_data: dict\):.*?(?=\n    def |\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    old_method = match.group(0)
    
    # New method with UPDATE
    new_method = '''def _on_record_saved(self, updated_data: dict):
        """
        Callback when record is saved from edit dialog
        
        Args:
            updated_data: Updated record data
        """
        try:
            # Get database connection
            from database.db_manager import get_db_manager
            db_manager = get_db_manager()
            conn = db_manager.get_observations_connection()
            cursor = conn.cursor()
            
            # Update the record
            cursor.execute("""
                UPDATE records SET
                    species_name = ?,
                    site_name = ?,
                    grid_reference = ?,
                    date = ?,
                    recorder = ?,
                    determiner = ?,
                    certainty = ?,
                    sex = ?,
                    quantity = ?,
                    sample_method = ?,
                    observation_type = ?,
                    sample_comment = ?
                WHERE id = ?
            """, (
                updated_data['species_name'],
                updated_data['site_name'],
                updated_data['grid_reference'],
                updated_data['date'],
                updated_data['recorder'],
                updated_data['determiner'],
                updated_data['certainty'],
                updated_data.get('sex'),
                updated_data.get('quantity'),
                updated_data.get('sample_method'),
                updated_data.get('observation_type'),
                updated_data.get('sample_comment'),
                updated_data['id']
            ))
            
            conn.commit()
            
            # Refresh table
            self._load_records()
            
            # Show success message
            messagebox.showinfo("Success", "Record updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating record: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to update record:\\n\\n{str(e)}")
    '''
    
    content = content.replace(old_method, new_method)
    print("   ✅ Added UPDATE statement to _on_record_saved")
else:
    print("   ❌ Could not find _on_record_saved method!")

# Write back
with open('tabs/data_tab.py', 'w', encoding='utf-8') as f:
    f.write(content)

print()
print("✅ ALL FIXES APPLIED!")
print()
print("Verification:")
if 'from widgets.tables.record_table_widget import' in content:
    print("✅ Import paths updated")
else:
    print("❌ Import paths NOT updated")
    
if 'UPDATE records SET' in content:
    print("✅ UPDATE statement added")
else:
    print("❌ UPDATE statement NOT added")

print()
print("🧪 Now test with: python main.py")
