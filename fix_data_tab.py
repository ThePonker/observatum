import re

# Read the file
with open('tabs/data_tab.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the _on_record_saved method
old_method = '''    def _on_record_saved(self, updated_data: dict):
        """
        Callback when record is saved from edit dialog

        Args:
            updated_data: Updated record data
        """
        # Refresh table
        self._load_records()

        # Show success message
        messagebox.showinfo("Success", "Record updated successfully")'''

new_method = '''    def _on_record_saved(self, updated_data: dict):
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
            messagebox.showerror("Error", f"Failed to update record:\n\n{str(e)}")'''

# Replace
if old_method in content:
    content = content.replace(old_method, new_method)
    print('✅ Found and replaced method')
else:
    print('❌ Could not find exact method match')
    print('Looking for partial match...')
    # Try to find it with regex
    pattern = r'def _on_record_saved\(self, updated_data: dict\):.*?(?=\n    def )'
    if re.search(pattern, content, re.DOTALL):
        print('Found method with regex')
        content = re.sub(pattern, new_method + '\n\n', content, flags=re.DOTALL)
        print('✅ Replaced with regex')

# Write back
with open('tabs/data_tab.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ File saved')

# Verify
if 'UPDATE records SET' in content:
    print('✅ UPDATE statement confirmed in file')
else:
    print('❌ UPDATE statement NOT in file')
