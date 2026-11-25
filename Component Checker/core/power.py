"""Power-supply sizing rule.

IMPORTANT: this is a simple *heuristic* defined by this project, not a
manufacturer figure:

    load      = CPU TDP + GPU board power + 100 W (motherboard, RAM, drives, fans)
    required  = load x 1.2                       (20% headroom for power spikes)
    rating    = the next standard PSU rating that is >= required
"""
from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass

STANDARD_PSU_RATINGS_W = [450, 500, 550, 650, 750, 850, 1000, 1200]
SYSTEM_OVERHEAD_W = 100  # everything that is not the CPU or the GPU


@dataclass(frozen=True)
class PowerEstimate:
    cpu_tdp_w: int
    gpu_power_w: int
    overhead_w: int
    load_w: int             # CPU + GPU + overhead
    with_headroom_w: int    # load x 1.2, rounded up to a whole watt
    required_rating_w: int  # next standard PSU rating


def round_up_to_standard_rating(watts: int) -> int:
    """Next standard PSU rating that is >= watts (multiples of 50 above the list)."""
    index = bisect_left(STANDARD_PSU_RATINGS_W, watts)
    if index < len(STANDARD_PSU_RATINGS_W):
        return STANDARD_PSU_RATINGS_W[index]
    return -(-watts // 50) * 50


def estimate_power(cpu_tdp_w: float, gpu_power_w: float) -> PowerEstimate:
    cpu = int(round(cpu_tdp_w))
    gpu = int(round(gpu_power_w))
    load = cpu + gpu + SYSTEM_OVERHEAD_W
    # load x 1.2 rounded UP, written with integers so there is no floating-point error:
    # ceil(load * 6 / 5)
    with_headroom = (load * 6 + 4) // 5
    return PowerEstimate(
        cpu_tdp_w=cpu,
        gpu_power_w=gpu,
        overhead_w=SYSTEM_OVERHEAD_W,
        load_w=load,
        with_headroom_w=with_headroom,
        required_rating_w=round_up_to_standard_rating(with_headroom),
    )
