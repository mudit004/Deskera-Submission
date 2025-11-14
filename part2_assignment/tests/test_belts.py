import os
import json
import subprocess
import pytest

BELTS_CMD = os.environ.get("BELTS_CMD", "python belts/main.py")

def run_solver(input_data):
    """Helper to run the belts solver with given data and return parsed JSON output."""
    input_json_str = json.dumps(input_data)
    command_result = subprocess.run(
        BELTS_CMD,
        input=input_json_str,
        capture_output=True,
        text=True,
        shell=True,
        timeout=2
    )
    assert command_result.returncode == 0, f"Solver exited with an error: {command_result.stderr}"
    return json.loads(command_result.stdout)

def test_feasible_belt_network():
    """Tests a feasible belt network configuration."""
    input_data = {
        "nodes": ["source_1", "junction_a", "sink"],
        "edges": [
            {"from": "source_1", "to": "junction_a", "hi": 100},
            {"from": "junction_a", "to": "sink", "hi": 100}
        ],
        "sources": [{"name": "source_1", "supply": 50}],
        "sink": {"name": "sink"}
    }
    
    output = run_solver(input_data)
    
    assert output["status"] == "ok"
    assert output["max_flow_per_min"] == pytest.approx(50.0)
    assert len(output["flows"]) == 2

def test_infeasible_belt_network():
    """Tests an infeasible belt network with a bottleneck."""
    input_data = {
        "nodes": ["source_1", "junction_a", "sink"],
        "edges": [
            {"from": "source_1", "to": "junction_a", "hi": 100},
            {"from": "junction_a", "to": "sink", "hi": 20}  # Bottleneck edge
        ],
        "sources": [{"name": "source_1", "supply": 50}],
        "sink": {"name": "sink"}
    }
    
    output = run_solver(input_data)
    
    assert output["status"] == "infeasible"
    assert "cut_reachable" in output
    assert "source_1" in output["cut_reachable"]
    assert "junction_a" in output["cut_reachable"]
    assert "sink" not in output["cut_reachable"]
    assert output["deficit"]["demand_balance"] == pytest.approx(30.0)
