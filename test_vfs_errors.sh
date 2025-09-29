#!/bin/bash

echo "=== Comprehensive VFS Error Handling Tests ==="
echo ""

mkdir -p vfs_error_tests

echo "=== Phase 1: File Not Found Errors ==="
timeout 2s python emulator.py --vfs-csv ./nonexistent_vfs.csv || true
echo ""

echo "=== Phase 2: Invalid Format Errors ==="
cat > vfs_error_tests/completely_invalid.csv << 'EOF'
This is not a CSV file at all!
Just some random text here...
No structure, no headers, nothing!
Maybe some "quotes" and , commas, but not CSV.
EOF
timeout 2s python emulator.py --vfs-csv vfs_error_tests/completely_invalid.csv || true
echo ""

echo "=== Phase 3: Mixed Valid and Invalid Data ==="
cat > vfs_error_tests/mixed_data.csv << 'EOF'
path,type,perms,content
/home,directory,755,
/home/user,directory,755,
/home/user/file1.txt,file,644,SGVsbG8gV29ybGQ=  # Valid
/home/user/invalid,,755,                        # Missing type
,file,644,                                      # Missing path
/home/user/file2.txt,file,644,0J/RgNC40LLQtdGC  # Valid: "Test"
/home/user/bad_type,invalid_type,755,           # Invalid type
EOF
timeout 2s python emulator.py --vfs-csv vfs_error_tests/mixed_data.csv || true
echo ""

echo "=== Phase 4: Testing with Script ==="
cat > vfs_error_tests/test_script.vfs << 'EOF'
ls
cd home
ls
pwd
exit
EOF

echo "Running with problematic VFS and script..."
python emulator.py --vfs-csv vfs_error_tests/mixed_data.csv --script vfs_error_tests/test_script.vfs
echo ""

echo "=== All VFS Error Tests Completed ==="

rm -rf vfs_error_tests