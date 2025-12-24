import json
import os
import shutil

def reset_all_data():
    """Reset all data files to initial state"""
    data_dir = 'data'
    uploads_dir = 'uploads'
    
    # Delete and recreate data directory
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)
    os.makedirs(data_dir)
    
    # Delete uploads directory
    if os.path.exists(uploads_dir):
        shutil.rmtree(uploads_dir)
    
    # Create empty data files
    data_files = {
        'users.json': [],
        'userlogs.json': {},
        'projects.json': {},
        'contact_inquiries.json': [],
        'floor_plans.json': {}
    }
    
    for filename, data in data_files.items():
        with open(f'{data_dir}/{filename}', 'w') as f:
            json.dump(data, f, indent=2)
    
    print("=" * 50)
    print("ALL DATA HAS BEEN RESET!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Start the app: python app.py")
    print("2. Go to http://localhost:5000")
    print("3. Click 'Login'")
    print("4. Click 'New Architect? Register' to create an account")
    print("5. Login with your new credentials")
    print("=" * 50)

if __name__ == '__main__':
    confirm = input("This will delete ALL data. Are you sure? (yes/no): ")
    if confirm.lower() == 'yes':
        reset_all_data()
    else:
        print("Operation cancelled.")