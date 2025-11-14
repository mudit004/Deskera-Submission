import os
import json
import subprocess
import pytest

FACTORY_CMD = os.environ.get("FACTORY_CMD", "python factory/main.py")

def run_solver(input_data):
    """Helper to run the solver with given data and return parsed JSON output."""
    input_json_str = json.dumps(input_data)
    command_result = subprocess.run(
        FACTORY_CMD,
        input=input_json_str,
        capture_output=True,
        text=True,
        shell=True,
        timeout=10
    )
    assert command_result.returncode == 0, f"Solver exited with an error: {command_result.stderr}"
    return json.loads(command_result.stdout)

def test_feasible_factory_scenario():
    """Tests a basic, solvable factory layout."""
    input_data = {
      "machines": {"assembler": {"crafts_per_min": 60}},
      "recipes": {
        "iron_gear": {
          "machine": "assembler", "time_s": 0.5,
          "in": {"iron_plate": 2}, "out": {"iron_gear": 1}
        }
      },
      "limits": {
        "raw_supply_per_min": {"iron_plate": 200},
        "max_machines": {"assembler": 10}
      },
      "target": {"item": "iron_gear", "rate_per_min": 10}
    }
    
    output = run_solver(input_data)
    
    assert output["status"] == "ok"
    assert output["per_recipe_crafts_per_min"]["iron_gear"] == pytest.approx(10.0)
    assert output["raw_consumption_per_min"]["iron_plate"] == pytest.approx(20.0)

def test_infeasible_factory_scenario():
    """Tests a layout that is impossible due to a machine capacity constraint."""
    input_data = {
      "machines": {"assembler": {"crafts_per_min": 60}},
      "recipes": {
        "iron_gear": {
          "machine": "assembler", "time_s": 0.5,
          "in": {"iron_plate": 2}, "out": {"iron_gear": 1}
        }
      },
      "limits": {
        "raw_supply_per_min": {"iron_plate": 5000},
        "max_machines": {"assembler": 1}
      },
      "target": {"item": "iron_gear", "rate_per_min": 5000}
    }

    output = run_solver(input_data)
    
    assert output["status"] == "infeasible"
    assert "max_feasible_target_per_min" in output
    assert output["max_feasible_target_per_min"] > 0
    assert "iron_plate production restriction" in output["bottleneck_hint"]
