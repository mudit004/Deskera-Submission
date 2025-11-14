# Testing Guide: Factory & Belts Solvers

## Prerequisites

Before running tests, ensure you have installed the required dependencies:

```bash
pip install numpy scipy networkx pytest
```

---

## Testing Methods

### Method 1: Run Sample Tests (Recommended for Quick Verification)

This method runs pre-built sample test cases without requiring pytest:

```bash
python run_samples.py "python factory/main.py" "python belts/main.py"
```

**What it does:**
- Loads sample JSON files from `tests/samples/` directory
- Runs each through the appropriate solver
- Compares output status with expected results
- Displays pass/fail status for each sample

**Expected Output:**
```
==================================================
Running Factory Solver Samples
==================================================
Testing factory_0.in.json...
  ✓ Status OK

==================================================
Running Belts Solver Samples
==================================================
Testing belts_0.in.json...
  ✓ Status OK

==================================================
Sample Testing Complete
==================================================
```

---

### Method 2: Run Unit Tests with pytest

This method executes comprehensive unit tests with detailed assertions:

#### On Windows (PowerShell):
```powershell
$env:FACTORY_CMD = "python factory/main.py"
$env:BELTS_CMD = "python belts/main.py"
pytest -q
```

#### On Windows (Command Prompt):
```cmd
set FACTORY_CMD=python factory/main.py
set BELTS_CMD=python belts/main.py
pytest -q
```

#### On Unix/Linux/Mac:
```bash
FACTORY_CMD="python factory/main.py" BELTS_CMD="python belts/main.py" pytest -q
```

**What it does:**
- Runs all test functions in `tests/test_factory.py` and `tests/test_belts.py`
- Validates outputs with numerical precision checks
- Reports detailed test results and failures

**Expected Output:**
```
tests/test_factory.py::test_feasible_factory_scenario PASSED
tests/test_factory.py::test_infeasible_factory_scenario PASSED
tests/test_belts.py::test_feasible_belt_network PASSED
tests/test_belts.py::test_infeasible_belt_network PASSED

4 passed in 1.23s
```

---

### Method 3: Test Individual Solvers Manually

#### Test Factory Solver:

```bash
python factory/main.py < tests/samples/factory_0.in.json
```

#### Test Belts Solver:

```bash
python belts/main.py < tests/samples/belts_0.in.json
```

This directly pipes a JSON input file to the solver and displays the JSON output.

---

### Method 4: Run Tests with Coverage Report

Generate a coverage report to see how much code is tested:

```powershell
pytest --cov=factory --cov=belts --cov-report=html
```

This creates an HTML coverage report in the `htmlcov/` directory.

---

## Understanding Test Output

### Sample Test Output Format

Each test displays:
- **Test Name**: The input file being tested
- **Status**: ✓ for pass, ✗ for fail
- **Details**: Expected vs actual status comparison

### pytest Output Format

- **PASSED**: Test completed successfully
- **FAILED**: Test failed with error details
- **Summary**: Total tests run and results

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'scipy'"

**Solution**: Install required dependencies
```bash
pip install numpy scipy networkx pytest
```

### Issue: "pytest: command not found"

**Solution**: Install pytest
```bash
pip install pytest
```

### Issue: Tests fail with timeout errors

**Solution**: The solvers are timing out. Check that:
1. The input JSON files exist in `tests/samples/`
2. The solver scripts are executable and working
3. Your system has sufficient resources

### Issue: "Cannot find sample files"

**Solution**: Ensure you're running tests from the project root directory:
```bash
cd part2_assignment
python run_samples.py "python factory/main.py" "python belts/main.py"
```

---

## Test Structure

### Factory Solver Tests (`tests/test_factory.py`)

```python
def test_feasible_factory_scenario():
    # Tests: Basic iron gear production
    # Input: 1 recipe, 10 machines max, 200 plate supply
    # Expected: Successful solution producing 10 iron_gears/min

def test_infeasible_factory_scenario():
    # Tests: Insufficient machine capacity
    # Input: Limited to 1 machine, need 5000 gears/min
    # Expected: Infeasible status with bottleneck hints
```

### Belts Solver Tests (`tests/test_belts.py`)

```python
def test_feasible_belt_network():
    # Tests: Simple source -> junction -> sink network
    # Input: 50 unit supply, 100 capacity edges
    # Expected: Successful flow routing

def test_infeasible_belt_network():
    # Tests: Bottleneck edge with insufficient capacity
    # Input: 50 unit supply, bottleneck edge with 20 capacity
    # Expected: Infeasible with cut analysis
```

---

## Example Workflow

1. **Quick Verification** (takes ~5 seconds):
   ```bash
   python run_samples.py "python factory/main.py" "python belts/main.py"
   ```

2. **Detailed Testing** (takes ~10 seconds):
   ```powershell
   $env:FACTORY_CMD = "python factory/main.py"; $env:BELTS_CMD = "python belts/main.py"; pytest -q
   ```

3. **Test with Output** (for debugging):
   ```bash
   python factory/main.py < tests/samples/factory_0.in.json | python -m json.tool
   ```

---

## Running Tests Programmatically

You can also import and run tests in your own Python script:

```python
import subprocess
import json

# Run factory solver
result = subprocess.run(
    ["python", "factory/main.py"],
    input=open("tests/samples/factory_0.in.json").read(),
    capture_output=True,
    text=True
)

output = json.loads(result.stdout)
print(f"Status: {output['status']}")
```

