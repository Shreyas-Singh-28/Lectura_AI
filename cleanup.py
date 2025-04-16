# cleanup.py
import os
import shutil
import atexit

def cleanup_on_exit():
    """Remove temporary directories when program exits"""
    print("\n🧹 Cleaning up temporary files...")
    
    # List of directories to clean
    dirs_to_remove = ['uploads', '__pycache__']
    
    for dir_name in dirs_to_remove:
        try:
            if os.path.exists(dir_name):
                if dir_name == '__pycache__':
                    # Only remove contents of __pycache__ (safer)
                    for root, dirs, files in os.walk(dir_name):
                        for file in files:
                            os.unlink(os.path.join(root, file))
                    print(f"  - Cleared {dir_name}/")
                else:
                    # Remove entire directory for uploads
                    shutil.rmtree(dir_name)
                    print(f"  - Removed {dir_name}/")
        except Exception as e:
            print(f"  ⚠️ Could not remove {dir_name}: {e}")

# Register cleanup function
atexit.register(cleanup_on_exit)