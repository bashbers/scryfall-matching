import ctypes
import os
import tracemalloc
from ctypes import wintypes
from time import perf_counter

from scryfall_matching.cards.domain import CompactCard
from scryfall_matching.cards.repository import InMemoryCardRepository, SwappableCardProvider


def test_swappable_provider_replaces_the_active_snapshot() -> None:
    old_repository = InMemoryCardRepository(_cards("old", 5), dataset_version="old")
    provider = SwappableCardProvider(old_repository)
    new_repository = InMemoryCardRepository(_cards("new", 5), dataset_version="new")

    provider.replace(new_repository)

    assert provider.statistics().dataset_version == "new"
    assert {card.id for card in provider.get_random_batch(5)} == {
        card.id for card in _cards("new", 5)
    }


def test_random_batch_meets_the_in_memory_latency_boundary() -> None:
    repository = InMemoryCardRepository(
        _cards("performance", 10_000),
        dataset_version="performance",
    )
    timings = []

    for _ in range(200):
        started_at = perf_counter()
        batch = repository.get_random_batch(5)
        timings.append(perf_counter() - started_at)
        assert len({card.id for card in batch}) == 5

    p95 = sorted(timings)[int(len(timings) * 0.95)]
    assert p95 < 0.1


def test_in_memory_snapshot_stays_within_the_memory_budget() -> None:
    baseline_working_set = _working_set_bytes()
    tracemalloc.start()
    repository = InMemoryCardRepository(
        _cards("memory", 50_000),
        dataset_version="memory",
    )
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    working_set_growth = _working_set_bytes() - baseline_working_set

    assert repository.statistics().card_count == 50_000
    assert peak < 1_000_000_000
    assert working_set_growth < 1_000_000_000


def _working_set_bytes() -> int:
    if os.name != "nt":
        return 0

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("page_fault_count", ctypes.c_ulong),
            ("peak_working_set_size", ctypes.c_size_t),
            ("working_set_size", ctypes.c_size_t),
            ("quota_peak_paged_pool_usage", ctypes.c_size_t),
            ("quota_paged_pool_usage", ctypes.c_size_t),
            ("quota_peak_non_paged_pool_usage", ctypes.c_size_t),
            ("quota_non_paged_pool_usage", ctypes.c_size_t),
            ("pagefile_usage", ctypes.c_size_t),
            ("peak_pagefile_usage", ctypes.c_size_t),
        ]

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    get_current_process = ctypes.windll.kernel32.GetCurrentProcess
    get_current_process.restype = wintypes.HANDLE
    get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_process_memory_info.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    get_process_memory_info.restype = wintypes.BOOL
    success = get_process_memory_info(
        get_current_process(),
        ctypes.byref(counters),
        counters.cb,
    )
    if not success:
        raise OSError("Could not read the current process working set.")
    return counters.working_set_size


def _cards(prefix: str, count: int) -> tuple[CompactCard, ...]:
    return tuple(
        CompactCard(
            id=f"{prefix}-{index}",
            name=f"{prefix} {index}",
            front_image_url=f"https://images.example.test/{prefix}-{index}.jpg",
            back_image_url=None,
            is_double_sided=False,
            commander_legal=True,
            scryfall_url=f"https://scryfall.com/card/test/{prefix}-{index}",
        )
        for index in range(count)
    )
