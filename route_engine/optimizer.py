import math


class RouteOptimizer:
    """
    Greedy routing by priority score (fill, gas, distance).
    Metrics use distance-derived fuel/CO2 estimates only (no fabricated percentages).
    """

    def __init__(self):
        self.depot_pos = (23.24, 77.45)
        self.collection_time_per_bin = 12
        self.avg_speed_kmh = 30
        self.truck_capacity = 5
        # Literature-style diesel proxy: L/km * CO2 kg per liter (order-of-magnitude for reporting)
        self.liters_per_km = 0.15
        self.kg_co2_per_liter = 2.31

    def haversine_distance(self, coord1, coord2):
        R = 6371
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def calculate_priority_score(self, bin_data, current_pos):
        dist = self.haversine_distance(current_pos, (bin_data["lat"], bin_data["lon"]))
        score = bin_data["fill_level"] * 0.5
        score += bin_data.get("gas_level", 0) * 0.3
        score -= dist * 2
        if bin_data.get("gas_level", 0) > 85:
            score += 100
        return score

    def calculate_optimal_path(self, current_pos, bin_data):
        targets = [b for b in bin_data if b["fill_level"] >= 75 or b.get("gas_level", 0) > 80]
        if not targets:
            return []
        targets = targets[: self.truck_capacity]
        ordered_path = []
        last_pos = current_pos
        while targets:
            best_target = max(targets, key=lambda b: self.calculate_priority_score(b, last_pos))
            ordered_path.append(best_target)
            last_pos = (best_target["lat"], best_target["lon"])
            targets.remove(best_target)
        return ordered_path

    def get_eta_metrics(self, path):
        if not path:
            return {
                "distance": "0 km",
                "time": "0 mins",
                "fuel_liters_est": "0 L",
                "co2_kg_est": "0 kg",
            }
        total_dist = 0.0
        last_pos = self.depot_pos
        for b in path:
            total_dist += self.haversine_distance(last_pos, (b["lat"], b["lon"]))
            last_pos = (b["lat"], b["lon"])
        total_dist += self.haversine_distance(last_pos, self.depot_pos)

        travel_time = (total_dist / self.avg_speed_kmh) * 60
        collection_time = len(path) * self.collection_time_per_bin
        total_time = travel_time + collection_time

        fuel_l = total_dist * self.liters_per_km
        co2 = fuel_l * self.kg_co2_per_liter

        return {
            "distance": f"{total_dist:.1f} km",
            "time": f"{int(total_time)} mins",
            "fuel_liters_est": f"{fuel_l:.2f} L",
            "co2_kg_est": f"{co2:.2f} kg",
        }


optimizer = RouteOptimizer()
