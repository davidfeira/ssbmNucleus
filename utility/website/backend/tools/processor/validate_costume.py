#!/usr/bin/env python3
import subprocess
import shutil
import sys
import os
import hashlib
from pathlib import Path

def validate_dat_file(dat_path, auto_fix=False, create_backup=True):
    """
    Validate a DAT file for Slippi compatibility.

    Args:
        dat_path: Path to the DAT file to validate
        auto_fix: If True, automatically apply fixes. If False, just check.
        create_backup: If True and auto_fix is True, create a backup before fixing

    Returns:
        dict with keys:
            - is_valid: True if file is Slippi-safe (or was made safe)
            - needs_fix: True if file needed fixes
            - fix_applied: True if fixes were applied
            - backup_path: Path to backup if created
            - output: Validator output message
    """
    dat_path = Path(dat_path).resolve()
    if not dat_path.exists():
        return {
            'is_valid': False,
            'needs_fix': False,
            'fix_applied': False,
            'backup_path': None,
            'output': f"Error: File {dat_path} not found"
        }

    # Use appropriate path based on platform
    # Get the validator path relative to this script
    script_dir = Path(__file__).parent
    validator_exe = script_dir / "CostumeValidator" / "SlippiCostumeValidator.exe"
    validator_exe = str(validator_exe.resolve())

    # Get hash before validation to detect if file was modified
    with open(dat_path, 'rb') as f:
        original_hash = hashlib.md5(f.read()).hexdigest()

    # Run validator using timeout to prevent hanging
    try:
        # Run from the file's directory using relative path - this is key!
        file_dir = dat_path.parent
        file_name = dat_path.name

        # Use appropriate echo command based on platform
        if sys.platform == "win32":
            cmd = f'echo. | "{validator_exe}" "{file_name}"'
        else:
            cmd = f'echo | "{validator_exe}" "{file_name}"'

        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(file_dir),
            capture_output=True,
            text=True,
            timeout=10  # 10 second timeout should be enough
        )

        # Check if validator failed to run
        if result.returncode != 0:
            error_msg = f"Validator failed with return code {result.returncode}\n"
            error_msg += f"stdout: {result.stdout}\n"
            error_msg += f"stderr: {result.stderr}\n"
            error_msg += f"command: {cmd}\n"
            error_msg += f"cwd: {file_dir}"
            return {
                'is_valid': False,
                'needs_fix': False,
                'fix_applied': False,
                'backup_path': None,
                'output': error_msg
            }

    except subprocess.TimeoutExpired:
        return {
            'is_valid': False,
            'needs_fix': False,
            'fix_applied': False,
            'backup_path': None,
            'output': f"ERROR: Validator timed out after 10 seconds\nCommand: {cmd}\nCwd: {file_dir}"
        }
    except Exception as e:
        return {
            'is_valid': False,
            'needs_fix': False,
            'fix_applied': False,
            'backup_path': None,
            'output': f"ERROR: Validator exception: {str(e)}\nCommand: {cmd}\nCwd: {file_dir}"
        }

    output = result.stdout.strip()
    debug_info = f"stdout: {result.stdout}\nstderr: {result.stderr}\nreturncode: {result.returncode}"

    # Get hash after validation to see if it changed
    with open(dat_path, 'rb') as f:
        after_hash = hashlib.md5(f.read()).hexdigest()

    # If hash changed, the file needed fixing and was fixed
    needs_fix = original_hash != after_hash
    is_already_valid = not needs_fix

    result_dict = {
        'is_valid': is_already_valid,  # Was it valid BEFORE any fixes?
        'needs_fix': needs_fix,         # Did it need fixes?
        'fix_applied': False,
        'backup_path': None,
        'output': f"Hash before: {original_hash}\nHash after: {after_hash}\nHash changed: {needs_fix}\n{debug_info}"
    }

    # If it needs fixing and auto_fix is enabled
    if needs_fix and auto_fix:
        backup_path = None

        # Create backup if requested
        if create_backup:
            backup_path = dat_path.with_suffix('.dat.backup')
            # Find unique backup name if it already exists
            counter = 1
            while backup_path.exists():
                backup_path = dat_path.with_suffix(f'.dat.backup{counter}')
                counter += 1

            shutil.copy2(dat_path, backup_path)
            result_dict['backup_path'] = backup_path
            print(f"Created backup: {backup_path}")

        # The validator already fixed the file when we ran it above
        result_dict['fix_applied'] = True
        result_dict['is_valid'] = True

    return result_dict

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_costume.py <dat_file> [options]")
        print("\nOptions:")
        print("  --check-only    Only check if file is Slippi-safe, don't fix")
        print("  --auto-fix      Automatically fix issues (default: ask user)")
        print("  --no-backup     Don't create backup when fixing")
        print("\nExamples:")
        print("  python validate_costume.py PlMsLv.dat --check-only")
        print("  python validate_costume.py PlMsLv.dat --auto-fix")
        print("  python validate_costume.py PlMsLv.dat --auto-fix --no-backup")
        sys.exit(1)

    dat_file = sys.argv[1]
    check_only = "--check-only" in sys.argv
    auto_fix = "--auto-fix" in sys.argv
    create_backup = "--no-backup" not in sys.argv

    print(f"Validating: {dat_file}")
    print("-" * 50)

    if check_only:
        # Make a temporary copy to check without modifying original
        temp_file = Path(dat_file).with_suffix('.dat.temp')
        shutil.copy2(dat_file, temp_file)

        try:
            result = validate_dat_file(temp_file, auto_fix=False)

            print("Validation Result:")
            if result['is_valid'] and not result['needs_fix']:
                print("✓ File is Slippi-safe!")
            elif result['needs_fix']:
                print("✗ File needs fixes to be Slippi-safe")
                print(f"Issues found: {result['output']}")
            else:
                print(result['output'])
        finally:
            # Clean up temp file
            if temp_file.exists():
                os.remove(temp_file)

    else:
        # First check what needs to be done
        temp_file = Path(dat_file).with_suffix('.dat.temp')
        shutil.copy2(dat_file, temp_file)

        try:
            check_result = validate_dat_file(temp_file, auto_fix=False)

            if check_result['is_valid'] and not check_result['needs_fix']:
                print("✓ File is already Slippi-safe! No fixes needed.")
                return

            if check_result['needs_fix']:
                print("✗ File needs fixes to be Slippi-safe")
                print(f"Issues found: {check_result['output']}")

                if not auto_fix:
                    # Ask user what to do
                    print("\nOptions:")
                    print("1. Apply fixes (original will be backed up)")
                    print("2. Apply fixes without backup")
                    print("3. Cancel (keep original)")

                    choice = input("\nEnter choice (1/2/3): ").strip()

                    if choice == "1":
                        auto_fix = True
                        create_backup = True
                    elif choice == "2":
                        auto_fix = True
                        create_backup = False
                    else:
                        print("Cancelled. File unchanged.")
                        return

                if auto_fix:
                    # Apply fixes to the actual file
                    result = validate_dat_file(dat_file, auto_fix=True, create_backup=create_backup)

                    if result['fix_applied']:
                        print("\n✓ Fixes applied successfully!")
                        if result['backup_path']:
                            print(f"Original backed up to: {result['backup_path']}")
                            print(f"\nTo restore original: cp \"{result['backup_path']}\" \"{dat_file}\"")
                    else:
                        print("\n✗ Failed to apply fixes")
                        print(result['output'])
        finally:
            # Clean up temp file
            if temp_file.exists():
                os.remove(temp_file)

if __name__ == "__main__":
    main()