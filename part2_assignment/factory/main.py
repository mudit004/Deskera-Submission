import sys
import json
import numpy as np
from scipy.optimize import linprog

class FactorySolver:
    """Solves the factory production optimization problem using linear programming."""
    
    def __init__(self, data):
        self.data = data
        
        self.recipe_list = sorted(list(self.data['recipes'].keys()))
        self.machine_type_list = sorted(list(self.data['machines'].keys()))
        
        self._identify_and_categorize_materials()
        
        self.material_index_map = {name: i for i, name in enumerate(self.all_materials)}
        self.recipe_index_map = {name: i for i, name in enumerate(self.recipe_list)}
        
        self.effective_crafts_per_min = self._calculate_effective_crafts()
        self.productivity_multipliers = self._get_productivity_multipliers()
        self.numerical_tolerance = 1e-6

    def solve(self):
        objective_coefficients = self._build_objective_function()

        inequality_matrix, inequality_bounds, constraint_info = self._build_inequality_constraints()
        equality_matrix, equality_bounds = self._build_equality_constraints()
        variable_bounds = (0, None)
        
        optimization_result = linprog(objective_coefficients, A_ub=inequality_matrix, b_ub=inequality_bounds, 
                                     A_eq=equality_matrix, b_eq=equality_bounds, bounds=variable_bounds, method='highs')

        if optimization_result.success:
            return self._format_success_output(optimization_result.x)
        
        maximization_info = self._maximize_target(inequality_matrix, inequality_bounds)
        if not maximization_info['success']:
            return {"status": "infeasible", "max_feasible_target_per_min": 0.0, "bottleneck_hint": []}
        
        bottleneck_hints = self._get_bottleneck_hints(maximization_info['result'], constraint_info, inequality_matrix, inequality_bounds)
        return {"status": "infeasible", "max_feasible_target_per_min": float(maximization_info['max_target']), "bottleneck_hint": bottleneck_hints}
    
    def _build_objective_function(self):
        """Builds the objective function coefficients (minimize total machine count)."""
        objective_coefficients = np.zeros(len(self.recipe_list))
        for recipe_idx, recipe_name in enumerate(self.recipe_list):
            objective_coefficients[recipe_idx] = 1.0 / self.effective_crafts_per_min[recipe_name]
        return objective_coefficients

    def _build_equality_constraints(self):
        """Builds matrices for material balance equations (intermediates and target)."""
        # Materials to be balanced: the target material plus all intermediates
        target_material = self.data['target']['item']
        materials_to_balance = self.intermediate_materials + [target_material]
        # Remove duplicates if target material is also an intermediate
        materials_to_balance = sorted(list(set(materials_to_balance)))
        
        num_equality_constraints = len(materials_to_balance)
        num_recipes = len(self.recipe_list)
        
        equality_matrix = np.zeros((num_equality_constraints, num_recipes))
        equality_bounds = np.zeros(num_equality_constraints)

        for constraint_idx, material_name in enumerate(materials_to_balance):
            for recipe_idx, recipe_name in enumerate(self.recipe_list):
                recipe = self.data['recipes'][recipe_name]
                # Net production = production - consumption
                output_amount = recipe['out'].get(material_name, 0) * self.productivity_multipliers[recipe_name]
                input_amount = recipe['in'].get(material_name, 0)
                equality_matrix[constraint_idx, recipe_idx] = output_amount - input_amount

            if material_name == target_material:
                equality_bounds[constraint_idx] = self.data['target']['rate_per_min']
            else:
                equality_bounds[constraint_idx] = 0
        
        return equality_matrix, equality_bounds

    def _build_inequality_constraints(self):
        """Builds matrices for machine capacity constraints and raw material constraints."""
        num_machine_constraints = len(self.machine_type_list)
        num_raw_supply_constraints = len(self.raw_materials)
        # Add a constraint per raw material to prevent net production
        num_raw_nonproduction_constraints = len(self.raw_materials)
        num_recipes = len(self.recipe_list)
        
        total_constraints = num_machine_constraints + num_raw_supply_constraints + num_raw_nonproduction_constraints
        inequality_matrix = np.zeros((total_constraints, num_recipes))
        inequality_bounds = np.zeros(total_constraints)
        constraint_info = []

        # Machine capacity constraints
        for machine_idx, machine_type in enumerate(self.machine_type_list):
            for recipe_idx, recipe_name in enumerate(self.recipe_list):
                if self.data['recipes'][recipe_name]['machine'] == machine_type:
                    inequality_matrix[machine_idx, recipe_idx] = 1.0 / self.effective_crafts_per_min[recipe_name]
            inequality_bounds[machine_idx] = self.data['limits']['max_machines'].get(machine_type, float('inf'))
            constraint_info.append({"type": "machine_cap", "name": machine_type})

        # Raw material supply constraints (net consumption <= cap) 
        for raw_idx, raw_material_name in enumerate(self.raw_materials):
            constraint_idx = num_machine_constraints + raw_idx
            for recipe_idx, recipe_name in enumerate(self.recipe_list):
                recipe = self.data['recipes'][recipe_name]
                # Net consumption = consumption - production
                input_amount = recipe['in'].get(raw_material_name, 0)
                output_amount = recipe['out'].get(raw_material_name, 0) * self.productivity_multipliers[recipe_name]
                inequality_matrix[constraint_idx, recipe_idx] = input_amount - output_amount
            inequality_bounds[constraint_idx] = self.data['limits']['raw_supply_per_min'].get(raw_material_name, float('inf'))
            constraint_info.append({"type": "raw_net_nonpos", "name": raw_material_name})

        # Raw material net production constraint (net production <= 0) 
        for raw_idx, raw_material_name in enumerate(self.raw_materials):
            constraint_idx = num_machine_constraints + num_raw_supply_constraints + raw_idx
            for recipe_idx, recipe_name in enumerate(self.recipe_list):
                recipe = self.data['recipes'][recipe_name]
                # Net production = production - consumption
                input_amount = recipe['in'].get(raw_material_name, 0)
                output_amount = recipe['out'].get(raw_material_name, 0) * self.productivity_multipliers[recipe_name]
                inequality_matrix[constraint_idx, recipe_idx] = output_amount - input_amount
            inequality_bounds[constraint_idx] = 0 # Net production must be <= 0
            constraint_info.append({"type": "raw_cap", "name": raw_material_name})
            
        return inequality_matrix, inequality_bounds, constraint_info
        
    def _identify_and_categorize_materials(self):
        """Finds all unique materials and categorizes them as raw, intermediate, or other."""
        all_input_materials = set()
        all_output_materials = set()
        for recipe in self.data['recipes'].values():
            all_input_materials.update(recipe.get('in', {}).keys())
            all_output_materials.update(recipe.get('out', {}).keys())
        
        # Raw materials are only ever inputs, never outputs
        self.raw_materials = sorted(list(all_input_materials - all_output_materials))
        # Intermediates appear as both inputs and outputs 
        self.intermediate_materials = sorted(list(all_input_materials.intersection(all_output_materials)))
        
        all_material_set = all_input_materials.union(all_output_materials)
        self.all_materials = sorted(list(all_material_set))

    def _calculate_effective_crafts(self):
        """Calculates effective crafts per minute for each recipe."""
        effective_crafts = {}
        for recipe_name, recipe_data in self.data['recipes'].items():
            machine_type = recipe_data['machine']
            base_speed = self.data['machines'][machine_type]['crafts_per_min']
            time_seconds = recipe_data['time_s']
            speed_modifier = self.data.get('modules', {}).get(machine_type, {}).get('speed', 0)
            effective_crafts[recipe_name] = base_speed * (1 + speed_modifier) * 60.0 / time_seconds
        return effective_crafts

    def _get_productivity_multipliers(self):
        """Gets the productivity multiplier for each recipe."""
        productivity_mult = {}
        for recipe_name, recipe_data in self.data['recipes'].items():
            machine_type = recipe_data['machine']
            productivity_modifier = self.data.get('modules', {}).get(machine_type, {}).get('prod', 0)
            productivity_mult[recipe_name] = 1 + productivity_modifier
        return productivity_mult
    
    def _maximize_target(self, inequality_matrix, inequality_bounds):
        """Maximizes target production when primary optimization is infeasible."""
        target_material = self.data.get('target', {}).get('item', None)
        if not target_material:
            return {"success": False}
        
        # Minimize negative of target production (i.e., maximize target production)
        objective_coefficients = []
        for recipe in self.recipe_list:
            recipe_data = self.data['recipes'][recipe]
            output_target = recipe_data.get('out', {}).get(target_material, 0.0) * self.productivity_multipliers.get(recipe, 1.0)
            input_target = recipe_data.get('in', {}).get(target_material, 0.0)
            objective_coefficients.append(- (output_target - input_target))
        
        # Equality constraints: all non-raw materials except target must be balanced
        equality_rows = []
        equality_rhs = []
        for material in self.all_materials:
            if material in self.raw_materials or material == target_material:
                continue
            row = []
            for recipe in self.recipe_list:
                recipe_data = self.data['recipes'][recipe]
                output_amount = recipe_data.get('out', {}).get(material, 0.0) * self.productivity_multipliers.get(recipe, 1.0)
                input_amount = recipe_data.get('in', {}).get(material, 0.0)
                row.append(output_amount - input_amount)
            equality_rows.append(row)
            equality_rhs.append(0.0)

        variable_bounds = [(0, None)] * len(self.recipe_list)
        optimization_result = linprog(c=objective_coefficients, A_ub=inequality_matrix, b_ub=inequality_bounds, 
                                     A_eq=equality_rows if equality_rows else None,
                                     b_eq=equality_rhs if equality_rhs else None, bounds=variable_bounds, method='highs')
        
        if not optimization_result.success:
            return {"success": False, "result": optimization_result}
        
        solution_vector = optimization_result.x
        achieved_target = 0.0
        for recipe_idx, recipe in enumerate(self.recipe_list):
            recipe_data = self.data['recipes'][recipe]
            output_target = recipe_data.get('out', {}).get(target_material, 0.0) * self.productivity_multipliers.get(recipe, 1.0)
            input_target = recipe_data.get('in', {}).get(target_material, 0.0)
            achieved_target += (output_target - input_target) * solution_vector[recipe_idx]
        
        return {"success": True, "max_target": float(achieved_target), "result": optimization_result}
    
    def _get_bottleneck_hints(self, optimization_result, constraint_info, inequality_matrix, inequality_bounds):
        """Generates hints about which constraints are bottlenecks in infeasible case."""
        hints = []
        if not hasattr(optimization_result, 'x') or optimization_result.x is None:
            return hints
        
        slack_values = getattr(optimization_result, 'slack', None)
        if slack_values is None:
            slack_values = []
            solution_vector = optimization_result.x
            for constraint_row, constraint_bound in zip(inequality_matrix, inequality_bounds):
                lhs = sum(constraint_row[i] * solution_vector[i] for i in range(len(solution_vector)))
                slack_values.append(constraint_bound - lhs)
        
        for slack_val, info in zip(slack_values, constraint_info):
            if slack_val is None:
                continue
            if slack_val <= max(self.numerical_tolerance, 1e-6):
                if info['type'] == 'machine_cap':
                    hints.append(f"{info['name']} cap")
                elif info['type'] == 'raw_cap':
                    hints.append(f"{info['name']} supply")
                elif info['type'] == 'raw_net_nonpos':
                    hints.append(f"{info['name']} production restriction")
                else:
                    hints.append(info.get('name', 'constraint'))
        
        # Remove duplicates while preserving order
        unique_hints = []
        seen = set()
        for hint in hints:
            if hint not in seen:
                unique_hints.append(hint)
                seen.add(hint)
        
        return unique_hints

    def _format_success_output(self, solution_vector):
        """Formats the LP solution into the required JSON structure."""
        per_recipe_crafts = {
            self.recipe_list[i]: val for i, val in enumerate(solution_vector)
        }
        
        per_machine_machine_counts = {mtype: 0.0 for mtype in self.machine_type_list}
        for recipe_idx, recipe_name in enumerate(self.recipe_list):
            machine_type = self.data['recipes'][recipe_name]['machine']
            machines_used = solution_vector[recipe_idx] / self.effective_crafts_per_min[recipe_name]
            per_machine_machine_counts[machine_type] += machines_used

        raw_material_consumption = {raw_material: 0.0 for raw_material in self.raw_materials}
        for raw_material_name in self.raw_materials:
            net_consumption = 0.0
            for recipe_idx, recipe_name in enumerate(self.recipe_list):
                recipe = self.data['recipes'][recipe_name]
                input_val = recipe.get('in', {}).get(raw_material_name, 0)
                output_val = recipe.get('out', {}).get(raw_material_name, 0) * self.productivity_multipliers[recipe_name]
                net_consumption += (input_val - output_val) * solution_vector[recipe_idx]
            raw_material_consumption[raw_material_name] = net_consumption

        return {
            "status": "ok",
            "per_recipe_crafts_per_min": per_recipe_crafts,
            "per_machine_counts": per_machine_machine_counts,
            "raw_consumption_per_min": raw_material_consumption
        }

def main():
    try:
        input_data = json.load(sys.stdin)
        solver = FactorySolver(input_data)
        solution = solver.solve()
        print(json.dumps(solution, indent=2))
    except Exception as e:
        error_output = {"status": "error", "message": str(e)}
        print(json.dumps(error_output, indent=2))

if __name__ == "__main__":
    main()