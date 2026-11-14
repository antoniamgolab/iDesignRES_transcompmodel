"""
Shared heuristic charging function (Shoman et al. approach).

Distributes charging energy to mandatory break locations proportional
to the distance to the next stop. Starting SOC covers origin to first break.
Total energy is scaled to match the LP-optimal total per route.
"""
import numpy as np
from collections import defaultdict


def compute_heuristic_charging(od_id, path_id, total_energy_mwh,
                                od_path, path_seq, path_dist, breaks_by_path):
    """
    Shoman-style heuristic: charge at every mandatory break stop,
    energy proportional to distance to next stop. Scaled to match total.

    Parameters:
        od_id: OD pair ID
        path_id: path ID
        total_energy_mwh: total energy to distribute (MWh)
        od_path: dict {od_id: path_id}
        path_seq: dict {path_id: [geo_id, ...]}
        path_dist: dict {path_id: [dist_km, ...]}
        breaks_by_path: dict {path_id: [geo_id, ...]}

    Returns:
        dict {geo_id: MWh}
    """
    pid = od_path.get(od_id, path_id)
    seq = path_seq.get(pid, [])
    dist = path_dist.get(pid, [])
    break_set = set(breaks_by_path.get(pid, []))

    if not seq or not dist or len(seq) != len(dist):
        return {}

    break_indices = [i for i, g in enumerate(seq) if g in break_set]
    if not break_indices:
        # No breaks — distribute evenly
        n = len(seq)
        return {seq[i]: total_energy_mwh / n for i in range(n)} if n > 0 else {}

    cum_dist = np.cumsum(dist)
    total_dist = cum_dist[-1] if len(cum_dist) > 0 else 0
    if total_dist < 1e-3:
        return {}

    # At each break: energy proportional to distance to next break/destination
    charges = {}
    for j, bi in enumerate(break_indices):
        if j < len(break_indices) - 1:
            dist_to_next = cum_dist[break_indices[j + 1]] - cum_dist[bi]
        else:
            dist_to_next = total_dist - cum_dist[bi]

        if dist_to_next > 0:
            charges[seq[bi]] = charges.get(seq[bi], 0) + dist_to_next

    # Scale to match total energy
    raw_total = sum(charges.values())
    if raw_total < 1e-9:
        # All breaks at the destination (distance to next stop = 0):
        # charge the full route energy at the last break instead of dropping it
        return {seq[break_indices[-1]]: total_energy_mwh}
    scale = total_energy_mwh / raw_total
    return {g: v * scale for g, v in charges.items()}
