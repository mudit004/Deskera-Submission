#!/usr/bin/env python3
import sys
import json
import networkx as nx
from collections import defaultdict

NUMERICAL_TOLERANCE = 1e-9

class BeltsSolver:
    """Solves the network flow problem with lower bounds on edges and capacity constraints on nodes."""
    
    def __init__(self, data):
        self.data = data
        self.network_nodes = list(self.data.get('nodes', []))
        self.network_edges = [dict(edge) for edge in self.data.get('edges', [])]
        
        # Ensure all edges have lower bounds
        for edge in self.network_edges:
            if 'lo' not in edge:
                edge['lo'] = 0.0
        
        self.node_capacity_map = {nc['name']: float(nc['cap']) for nc in self.data.get('node_caps', [])}
        self.source_supply_map = {s['name']: float(s['supply']) for s in self.data.get('sources', [])}
        self.sink_node = self.data['sink']['name']
        self.total_supply_amount = sum(self.source_supply_map.values())

        self.SUPER_SOURCE = "__SUPER_SRC__"
        self.SUPER_SINK = "__SUPER_SNK__"

    def _get_internal_node_maps(self):
        """Maps each node to its internal representation (split for capacitated nodes)."""
        internal_node_map = {}
        external_node_map = {}
        for node in self.network_nodes:
            if (node in self.node_capacity_map) and (node not in self.source_supply_map) and (node != self.sink_node):
                internal_node_map[node] = f"{node}__in"
                external_node_map[node] = f"{node}__out"
            else:
                internal_node_map[node] = node
                external_node_map[node] = node
        return internal_node_map, external_node_map

    def solve(self):
        internal_node_map, external_node_map = self._get_internal_node_maps()

        # Build reduced capacities (hi - lo) and validate
        mapped_edge_pairs = defaultdict(list)
        for edge_idx, edge in enumerate(self.network_edges):
            source_node = edge['from']
            target_node = edge['to']
            lower_bound = float(edge.get('lo', 0.0))
            upper_bound = float(edge['hi'])
            if upper_bound + NUMERICAL_TOLERANCE < lower_bound:
                return {"status": "error", "message": f"edge {source_node}->{target_node} has hi < lo"}
            reduced_capacity = upper_bound - lower_bound
            mapped_source = external_node_map[source_node]
            mapped_target = internal_node_map[target_node]
            mapped_edge_pairs[(mapped_source, mapped_target)].append({
                "idx": edge_idx, "from": source_node, "to": target_node, "lo": lower_bound, "hi": upper_bound, "reduced": reduced_capacity
            })

        # Compute B(v) = sum lo_in - sum lo_out
        node_imbalance = defaultdict(float)
        for edge in self.network_edges:
            lower_bound = float(edge.get('lo', 0.0))
            node_imbalance[edge['to']] += lower_bound
            node_imbalance[edge['from']] -= lower_bound

        # R(v) = B(v) + supply(v) - demand(v)
        node_requirement = {}
        for node in self.network_nodes:
            supply = float(self.source_supply_map.get(node, 0.0))
            demand = float(self.total_supply_amount if node == self.sink_node else 0.0)
            node_requirement[node] = node_imbalance[node] + supply - demand

        flow_graph = nx.DiGraph()
        mapped_node_set = set(internal_node_map.values()) | set(external_node_map.values())
        for mapped_node in mapped_node_set:
            flow_graph.add_node(mapped_node)
        
        for node, capacity in self.node_capacity_map.items():
            if internal_node_map[node] != external_node_map[node]:
                flow_graph.add_edge(internal_node_map[node], external_node_map[node], capacity=float(capacity))
        
        for (mapped_source, mapped_target), edge_info_list in mapped_edge_pairs.items():
            total_reduced_cap = sum(item["reduced"] for item in edge_info_list)
            flow_graph.add_edge(mapped_source, mapped_target, capacity=float(total_reduced_cap))

        flow_graph.add_node(self.SUPER_SOURCE)
        flow_graph.add_node(self.SUPER_SINK)
        total_demand = 0.0
        for node in self.network_nodes:
            requirement = node_requirement[node]
            node_internal = internal_node_map[node]
            node_external = external_node_map[node]
            if requirement > NUMERICAL_TOLERANCE:
                flow_graph.add_edge(self.SUPER_SOURCE, node_internal, capacity=float(requirement))
                total_demand += requirement
            elif requirement < -NUMERICAL_TOLERANCE:
                flow_graph.add_edge(node_external, self.SUPER_SINK, capacity=float(-requirement))

        try:
            max_flow_value, flow_dict = nx.maximum_flow(flow_graph, self.SUPER_SOURCE, self.SUPER_SINK,
                                                  capacity='capacity',
                                                  flow_func=nx.algorithms.flow.preflow_push)
        except Exception as exc:
            return {"status": "error", "message": f"maxflow error: {exc}"}

        if abs(max_flow_value - total_demand) > 1e-9:
            return self._format_infeasible(flow_graph, max_flow_value, total_demand, flow_dict, internal_node_map, external_node_map, mapped_edge_pairs)

        original_edge_flows = [0.0] * len(self.network_edges)
        for (mapped_source, mapped_target), edge_info_list in mapped_edge_pairs.items():
            flow_on_mapped = float(flow_dict.get(mapped_source, {}).get(mapped_target, 0.0))
            total_reduced_cap = sum(item["reduced"] for item in edge_info_list)
            if total_reduced_cap > NUMERICAL_TOLERANCE:
                for item in edge_info_list:
                    share = (item["reduced"] / total_reduced_cap) * flow_on_mapped
                    original_edge_flows[item["idx"]] = share
            else:
                for item in edge_info_list:
                    original_edge_flows[item["idx"]] = 0.0

        final_flows = []
        for edge_idx, edge in enumerate(self.network_edges):
            flow_value = original_edge_flows[edge_idx] + float(edge.get('lo', 0.0))
            if flow_value > NUMERICAL_TOLERANCE:
                final_flows.append({"from": edge['from'], "to": edge['to'], "flow": float(flow_value)})

        final_flows.sort(key=lambda x: (x['from'], x['to']))
        return {"status": "ok", "max_flow_per_min": float(self.total_supply_amount), "flows": final_flows}

    def _format_infeasible(self, flow_graph, max_flow_value, required_demand, flow_dict, internal_node_map, external_node_map, mapped_edge_pairs):
        """Generates infeasibility report with min-cut information."""
        min_cut_value, (source_reachable, sink_reachable) = nx.minimum_cut(flow_graph, self.SUPER_SOURCE, self.SUPER_SINK,
                                                   capacity='capacity',
                                                   flow_func=nx.algorithms.flow.preflow_push)
        reachable_original_nodes = set()
        for mapped_node in source_reachable:
            if mapped_node in (self.SUPER_SOURCE, self.SUPER_SINK):
                continue
            if '__' in mapped_node:
                base_node = mapped_node.split('__', 1)[0]
            else:
                base_node = mapped_node
            reachable_original_nodes.add(base_node)
        cut_reachable_nodes = sorted(reachable_original_nodes)

        deficit_amount = float(required_demand - max_flow_value)

        tight_node_capacities = []
        for node in sorted(self.network_nodes):
            if node not in reachable_original_nodes:
                continue
            if internal_node_map[node] == external_node_map[node]:
                continue
            node_internal = internal_node_map[node]
            node_external = external_node_map[node]
            node_capacity = float(flow_graph[node_internal][node_external]['capacity']) if flow_graph.has_edge(node_internal, node_external) else 0.0
            flow_through_node = float(flow_dict.get(node_internal, {}).get(node_external, 0.0))
            if node_capacity - flow_through_node <= NUMERICAL_TOLERANCE:
                tight_node_capacities.append(node)

        tight_edge_list = []
        for (mapped_source, mapped_target), edge_info_list in mapped_edge_pairs.items():
            if (mapped_source in source_reachable) and (mapped_target not in source_reachable):
                edge_capacity = float(flow_graph[mapped_source][mapped_target]['capacity']) if flow_graph.has_edge(mapped_source, mapped_target) else 0.0
                flow_on_edge = float(flow_dict.get(mapped_source, {}).get(mapped_target, 0.0))
                if edge_capacity - flow_on_edge <= NUMERICAL_TOLERANCE:
                    for item in edge_info_list:
                        tight_edge_list.append({
                            "from": item["from"],
                            "to": item["to"],
                            "flow_needed": float(deficit_amount)
                        })

        return {
            "status": "infeasible",
            "cut_reachable": cut_reachable_nodes,
            "deficit": {
                "demand_balance": deficit_amount,
                "tight_nodes": sorted(tight_node_capacities),
                "tight_edges": tight_edge_list
            }
        }


def main():
    try:
        input_data = json.load(sys.stdin)
        solver = BeltsSolver(input_data)
        out = solver.solve()
        print(json.dumps(out, indent=2))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e), "type": type(e).__name__}, indent=2))


if __name__ == "__main__":
    main()
