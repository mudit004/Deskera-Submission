import os
import sys
import json
import subprocess
from pathlib import Path

def run_test_command(command, input_file_path):
    """Execute solver command with given input file and return parsed JSON output."""
    with open(input_file_path, 'r') as input_file:
        input_data = input_file.read()
    
    try:
        command_execution = subprocess.run(
            command,
            input=input_data,
            capture_output=True,
            text=True,
            shell=True,
            timeout=10
        )
        if command_execution.returncode != 0:
            print(f"Error running command. Stderr:\n{command_execution.stderr}")
            return None
        return json.loads(command_execution.stdout)
    except subprocess.TimeoutExpired:
        print("Command timed out after 10 seconds.")
        return None
    except json.JSONDecodeError:
        print(f"Failed to decode JSON from stdout:\n{command_execution.stdout}")
        return None
    except Exception as exception:
        print(f"An unexpected error occurred: {exception}")
        return None

def main(factory_command, belts_command):
    """Run sample tests for both factory and belts solvers."""
    samples_directory = Path("tests") / "samples"
    if not samples_directory.is_dir():
        print(f"Error: Sample directory not found at '{samples_directory}'")
        sys.exit(1)

    print("=" * 50)
    print("Running Factory Solver Samples")
    print("=" * 50)
    
    factory_input_files = sorted(list(samples_directory.glob("factory_*.in.json")))
    for input_file in factory_input_files:
        print(f"Testing {input_file.name}...")
        output_file = input_file.with_suffix('').with_suffix('.out.json')
        if not output_file.exists():
            print(f"  Warning: Corresponding output file {output_file.name} not found. Skipping verification.")
            continue
        
        with open(output_file, 'r') as expected_output_file:
            expected_output_data = json.load(expected_output_file)
        
        actual_output_data = run_test_command(factory_command, input_file)
        
        if actual_output_data:
            if actual_output_data.get("status") == expected_output_data.get("status"):
                print("  ✓ Status OK")
            else:
                print(f"  ✗ Status Mismatch: Expected '{expected_output_data.get('status')}', Got '{actual_output_data.get('status')}'")

    print("\n" + "=" * 50)
    print("Running Belts Solver Samples")
    print("=" * 50)
    
    belts_input_files = sorted(list(samples_directory.glob("belts_*.in.json")))
    for input_file in belts_input_files:
        print(f"Testing {input_file.name}...")
        output_file = input_file.with_suffix('').with_suffix('.out.json')
        if not output_file.exists():
            print(f"  Warning: Corresponding output file {output_file.name} not found. Skipping verification.")
            continue

        with open(output_file, 'r') as expected_output_file:
            expected_output_data = json.load(expected_output_file)

        actual_output_data = run_test_command(belts_command, input_file)
        
        if actual_output_data:
            if actual_output_data.get("status") == expected_output_data.get("status"):
                print("  ✓ Status OK")
            else:
                print(f"  ✗ Status Mismatch: Expected '{expected_output_data.get('status')}', Got '{actual_output_data.get('status')}'")

    print("\n" + "=" * 50)
    print("Sample Testing Complete")
    print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_samples.py \"<factory_command>\" \"<belts_command>\"")
        print("Example: python run_samples.py \"python factory/main.py\" \"python belts/main.py\"")
        sys.exit(1)
    
    main(sys.argv[1], sys.argv[2])
