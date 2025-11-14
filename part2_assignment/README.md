# Factory & Belts Solver - Advanced Implementation

A comprehensive solution implementing linear programming and network flow algorithms to solve factory production optimization and belt transportation problems.

---

## Part A: Factory Steady State Optimization

The factory production problem is modeled as a **Linear Program (LP)** and solved using the `scipy.optimize.linprog` library from SciPy.

### Approach

**Conservation and Material Balance**
- Material conservation is enforced through a system of linear equations (`A_eq * x = b_eq`)
- For **intermediate materials** (those that are both produced and consumed), the net production (total effective output - total input) must equal exactly **0** for perfect steady state
- For the **target material**, the net production is constrained to equal the exact required `rate_per_min`

**Machine and Raw Material Constraints**
- Limits are enforced using inequality matrices (`A_ub * x <= b_ub`)
- **Machine Capacity Constraints**: For each machine type, total machines used (sum of `crafts_per_min / effective_crafts_per_min`) ≤ specified maximum
- **Raw Material Supply Constraints**: For each raw material, net consumption (total input - total effective output) ≤ supply cap
- An additional constraint ensures raw materials are never net-produced (net production ≤ 0)

**Module Application and Coefficients**
- Speed and productivity modules are applied as pre-calculated coefficients
- `effective_crafts_per_min`: Final craft rate after applying speed modules
- `productivity_multipliers`: Output multiplier applied to each recipe based on productivity modules
- These values are directly integrated into constraint matrices

**Handling Complex Scenarios**
- **Cycles**: Inherently resolved by steady-state balance equations for all intermediates
- **Byproducts**: Items produced but never consumed are correctly left out of balance equations, allowing surplus to accumulate
- **Infeasibility Detection**: Uses a two-phase process
  1. First attempts standard LP minimization
  2. If infeasible, formulates a second LP to maximize target production rate
  3. Computes bottleneck hints by inspecting slack variables (constraints with zero slack are binding)

**Tie-Breaking**
- Primary objective: **minimize total machine count** (serves as tie-breaker for multiple feasible solutions)

---

## Part B: Belts with Flow Bounds and Node Capacity

This problem is modeled as a **circulation problem with demands** and solved using max-flow algorithms from `networkx`.

### Approach

**Lower Bounds Transformation**
- Core of the model: transform flow constraints with lower and upper bounds
- **Imbalance Calculation**: For each node `B(v) = sum(incoming lo) - sum(outgoing lo)`
- **Node Requirement**: For each node `R(v) = B(v) + supply(v) - demand(v)`
- **Transformed Graph**: Edge capacity becomes `hi - lo`

**Node Capacity Handling (Node Splitting)**
- For any non-source/sink node `v` with capacity constraint:
  - Split into two internal nodes: `v__in` and `v__out`
  - Add internal edge `v__in -> v__out` with capacity = node's cap
  - Redirect all incoming edges to `v__in`
  - Redirect all outgoing edges to start from `v__out`

**Feasibility Verification**
- Add super-source `S*` and super-sink `T*` to the flow graph
- For each node `v`:
  - If `R(v) > 0` (demander): add edge `S* -> v` with capacity `R(v)`
  - If `R(v) < 0` (supplier): add edge `v -> T*` with capacity `-R(v)`
- **Feasible if and only if**: max-flow from `S*` to `T*` equals total demand

**Infeasibility Certificate**
- Computes **min-cut** when feasibility check fails
- Reports:
  - `cut_reachable`: Original nodes reachable from `S*` in residual graph
  - `tight_nodes`: Node capacity constraints that are saturated
  - `tight_edges`: Flow edges crossing the cut that are saturated
  - `deficit`: Unmet demand (total demand - max flow achieved)

---

## Numeric Reliability and Edge Cases

**Tolerance Handling**
- Numerical tolerance: `1e-9` for all floating-point comparisons
- Prevents precision issues inherent in computer arithmetic

**Determinism and Robustness**
- Uses deterministic `preflow_push` algorithm from NetworkX
- Prevents randomness in results across runs

**Edge Cases Handled**
- **Name Collisions**: Internal nodes use prefixes like `__in` and `__out` to prevent collisions
- **Parallel Edges**: Multiple edges between two nodes are aggregated correctly in transformed graph
- **Cycles and Disconnected Components**: Both solvers gracefully handle these scenarios
  - Factory LP assigns zero crafts to unused recipes
  - Belts max-flow correctly reports infeasibility for disconnected source-sink pairs

---

## Project Structure

```
part2_assignment/
├── belts/
│   └── main.py               # Belts solver implementation
├── factory/
│   └── main.py               # Factory solver implementation
├── tests/
│   ├── test_belts.py         # Unit tests for belts solver
│   ├── test_factory.py       # Unit tests for factory solver
│   └── samples/              # Sample JSON test cases
│       ├── factory_*.in.json
│       ├── factory_*.out.json
│       ├── belts_*.in.json
│       └── belts_*.out.json
├── run_samples.py            # Sample test runner
├── README.md                 # This file
├── RUN.md                    # Testing instructions
└── how_to_make_commands.txt  # Setup guide for global commands
```

---

## Key Improvements in This Version

### Code Quality & Maintainability
- **Descriptive Variable Names**:
  - `network_nodes` instead of `nodes`
  - `recipe_list` instead of `recipes`
  - `effective_crafts_per_min` instead of `eff_crafts_per_min`
  - `productivity_multipliers` instead of `prod_multipliers`
  
- **Improved Method Names**:
  - `_get_internal_node_maps()` (clearer than `_get_maps()`)
  - `_get_bottleneck_hints()` (clearer than `_bottleneck_hints()`)
  - `_format_success_output()` (explicit purpose)

### Robustness
- Enhanced error messages and validation
- Better handling of edge cases
- Improved numerical stability with explicit tolerance constants

### Documentation
- Comprehensive docstrings for all methods
- Clear comments explaining algorithmic choices
- Updated markdown files with structured formatting
