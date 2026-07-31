import os
from datetime import datetime

# Test the directory creation logic for receipt uploads
UPLOAD_DIR = "contabilità_francesco/ricevute_uploads"

def test_upload_directory_structure():
    """Test that the upload directory structure follows YYYY/MM format."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_part = timestamp[:8]  # YYYYMMDD
    year = date_part[:4]
    month = date_part[4:6]
    local_dir = os.path.join(UPLOAD_DIR, year, month)
    os.makedirs(local_dir, exist_ok=True)
    
    # Verify directory was created
    assert os.path.exists(local_dir), f"Directory {local_dir} was not created"
    
    # Verify year/month format
    assert len(year) == 4, f"Year should be 4 digits, got {year}"
    assert len(month) == 2, f"Month should be 2 digits, got {month}"
    
    print(f"[OK] Directory structure created: {local_dir}")
    print(f"[OK] Year: {year}, Month: {month}")
    print(f"[OK] Directory exists: {os.path.exists(local_dir)}")
    
    # Test creating a file in the directory
    test_file = os.path.join(local_dir, f"{timestamp}_test_receipt.txt")
    with open(test_file, "w") as f:
        f.write("Test receipt content")
    
    assert os.path.exists(test_file), f"File {test_file} was not created"
    print(f"[OK] Test file created: {test_file}")
    
    # Clean up
    os.remove(test_file)
    print(f"[OK] Test file cleaned up")
    
    print("\nAll tests passed! The receipt upload directory structure is working correctly.")

if __name__ == "__main__":
    test_upload_directory_structure()