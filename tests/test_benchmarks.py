import time

import pytest

from autoenum import AutoEnum, alias, auto


class Animal(AutoEnum):
    Antelope = auto()
    Bandicoot = auto()
    Cat = alias("Feline")
    Dog = auto()


class City(AutoEnum):
    Atlanta = auto()
    Boston = auto()
    Chicago = auto()
    Denver = auto()
    El_Paso = auto()
    Fresno = auto()
    Greensboro = auto()
    Houston = auto()
    Indianapolis = auto()
    Jacksonville = auto()
    Kansas_City = auto()
    Los_Angeles = auto()
    Miami = auto()
    New_York_City = alias("New York", "NYC")
    Orlando = auto()
    Philadelphia = auto()
    Quincy = auto()
    Reno = auto()
    San_Francisco = auto()
    Tucson = auto()
    Union_City = auto()
    Virginia_Beach = auto()
    Washington = alias("Washington D.C.")
    Xenia = auto()
    Yonkers = auto()
    Zion = auto()


def measure_lookup_speed(enum_class, test_values, iterations=100_000):
    """Measure lookup speed for a given enum class and test values."""
    ## Warmup cache:
    for value in test_values:
        _ = enum_class(value)
    ## Measure lookup speed:
    start_time = time.perf_counter()
    for _ in range(iterations):
        for value in test_values:
            _ = enum_class(value)

    end_time = time.perf_counter()
    total_time = end_time - start_time
    lookups_per_second = (iterations * len(test_values)) / total_time

    return lookups_per_second


def test_enum_size_impact():
    """Test if enum size impacts lookup speed."""
    animal_speed = measure_lookup_speed(Animal, ["Cat", "Dog"])
    city_speed = measure_lookup_speed(City, ["Los_Angeles", "New_York_City"])

    # Calculate speed ratio
    speed_ratio = city_speed / animal_speed

    print(f"\nSpeed ratio (City/Animal) for same number of lookups: {speed_ratio:.4f}x")

    # Ensure the larger enum is at least 50% as fast as the smaller one
    assert speed_ratio > 0.5, f"Larger enum too slow: {speed_ratio:.2f}x speed ratio"


@pytest.mark.parametrize(
    "n,threshold",
    [
        (1_000_000, 1000),  # 1M lookups in <1000 ms
    ],
)
def test_from_str_lookup_speed(n, threshold):
    """Test from_str lookup speed with cache warmup."""
    # warm up cache
    Animal.from_str("Cat")
    start = time.perf_counter()
    for _ in range(n):
        Animal.from_str("Cat")
    duration = 1000 * (time.perf_counter() - start)
    print(
        f"[from_str_lookup] {n:,} iterations took {duration:.2f}ms (avg {1000 * duration / n:.2f}us per from_str lookup)"
    )
    assert duration < threshold, f"{n:,} lookups took {duration:.2f}ms, over {threshold}ms"


@pytest.mark.parametrize(
    "n,threshold",
    [
        (10_000, 1000),  # 10k lookups in <1000 ms
    ],
)
def test_no_cache_from_str_lookup_speed(n, threshold):
    """Test from_str lookup speed without cache warmup."""
    loop_times = []
    for _ in range(5):  # Run 5 times to get average
        start = time.perf_counter()
        for _ in range(n):
            Animal.from_str("Cat")
        duration = 1000 * (time.perf_counter() - start)
        loop_times.append(duration)

    avg_duration = sum(loop_times) / len(loop_times)
    print(
        f"[no_cache_from_str_lookup] {n:,} iterations took avg {avg_duration:.2f}ms (avg {1000 * avg_duration / n:.2f}us per from_str lookup)"
    )
    assert avg_duration < threshold, f"{n:,} lookups took avg {avg_duration:.2f}ms, over {threshold}ms"


@pytest.mark.parametrize(
    "n,threshold",
    [
        (1_000_000, 1000),  # 1M lookups in <1000 ms
    ],
)
def test_matches_any_lookup_speed(n, threshold):
    """Test matches_any lookup speed with cache warmup."""
    # warm up cache
    Animal.matches_any("Cat")
    start = time.perf_counter()
    for _ in range(n):
        Animal.matches_any("Cat")
    duration = 1000 * (time.perf_counter() - start)
    print(
        f"[matches_any_lookup] {n:,} iterations took {duration:.2f}ms (avg {1000 * duration / n:.2f}us per matches_any lookup)"
    )
    assert duration < threshold, f"{n:,} lookups took {duration:.2f}ms, over {threshold}ms"


@pytest.mark.parametrize(
    "n,threshold",
    [
        (10_000, 1000),  # 10k lookups in <1000 ms
    ],
)
def test_no_cache_matches_any_lookup_speed(n, threshold):
    """Test matches_any lookup speed without cache warmup."""
    loop_times = []
    for _ in range(5):  # Run 5 times to get average
        start = time.perf_counter()
        for _ in range(n):
            Animal.matches_any("Cat")
        duration = 1000 * (time.perf_counter() - start)
        loop_times.append(duration)

    avg_duration = sum(loop_times) / len(loop_times)
    print(
        f"[no_cache_matches_any_lookup] {n:,} iterations took avg {avg_duration:.2f}ms (avg {1000 * avg_duration / n:.2f}us per matches_any lookup)"
    )
    assert avg_duration < threshold, f"{n:,} lookups took avg {avg_duration:.2f}ms, over {threshold}ms"


@pytest.mark.parametrize(
    "n,threshold",
    [
        (1_000_000, 10_000),  # 1M iterations in <10,000 ms
    ],
)
def test_enum_iteration_speed(n, threshold):
    """Test enum iteration speed."""
    # warm up
    list(Animal)
    start = time.perf_counter()
    for _ in range(n):
        list(Animal)
    duration = 1000 * (time.perf_counter() - start)
    print(
        f"[enum_iteration] {n:,} iterations took {duration:.2f}ms (avg {1000 * duration / n:.2f}us per iteration)"
    )
    assert duration < threshold, f"{n:,} iterations took {duration:.2f}ms, over {threshold}ms"


@pytest.mark.parametrize(
    "n,threshold",
    [
        (1_000_000, 10_000),  # 1M conversions in <10,000 ms
    ],
)
def test_convert_list_speed(n, threshold):
    """Test list conversion speed."""
    test_list = ["Cat", "Dog", "Antelope", "Bandicoot"]
    # warm up
    Animal.convert_list(test_list)
    start = time.perf_counter()
    for _ in range(n):
        Animal.convert_list(test_list)
    duration = 1000 * (time.perf_counter() - start)
    print(
        f"[convert_list] {n:,} conversions took {duration:.2f}ms (avg {1000 * duration / n:.2f}us per conversion)"
    )
    assert duration < threshold, f"{n:,} conversions took {duration:.2f}ms, over {threshold}ms"


def test_lookup_throughput():
    """Test lookup throughput with and without caching for both enums."""
    # Test values that will be used for both enums
    test_values = [
        "value1",  # Exact match
        "value2",  # Exact match
        "Value1",  # Case variation
        "Value2",  # Case variation
        "value 1",  # Spacing variation
        "value 2",  # Spacing variation
    ]

    iterations = 100_000

    # Test with caching (warm cache)
    print("\nTesting with caching (warm cache):")
    print("----------------------------------")

    # Warm up cache for Animal enum
    for value in test_values:
        _ = Animal.from_str(value, raise_error=False)

    # Measure Animal enum with cache
    start_time = time.perf_counter()
    for _ in range(iterations):
        for value in test_values:
            _ = Animal.from_str(value, raise_error=False)
    animal_cached_time = time.perf_counter() - start_time
    animal_cached_throughput = (iterations * len(test_values)) / animal_cached_time

    # Warm up cache for City enum
    for value in test_values:
        _ = City.from_str(value, raise_error=False)

    # Measure City enum with cache
    start_time = time.perf_counter()
    for _ in range(iterations):
        for value in test_values:
            _ = City.from_str(value, raise_error=False)
    city_cached_time = time.perf_counter() - start_time
    city_cached_throughput = (iterations * len(test_values)) / city_cached_time

    print(f"Animal enum ({len(Animal)} members):")
    print(f"  - Throughput: {animal_cached_throughput:,.0f} lookups/second")
    print(f"  - Total time: {animal_cached_time:.3f}s")
    print(f"  - Time per lookup: {animal_cached_time * 1_000_000 / (iterations * len(test_values)):.3f}µs")

    print(f"\nCity enum ({len(City)} members):")
    print(f"  - Throughput: {city_cached_throughput:,.0f} lookups/second")
    print(f"  - Total time: {city_cached_time:.3f}s")
    print(f"  - Time per lookup: {city_cached_time * 1_000_000 / (iterations * len(test_values)):.3f}µs")

    # Test without caching (cold cache)
    print("\nTesting without caching (cold cache):")
    print("------------------------------------")

    # Clear the cache
    Animal._normalize.cache_clear()
    City._normalize.cache_clear()

    # Measure Animal enum without cache
    animal_uncached_time = 0.0
    for _ in range(iterations):
        for value in test_values:
            Animal._normalize.cache_clear()
            start_time = time.perf_counter()
            _ = Animal.from_str(value, raise_error=False)
            animal_uncached_time += time.perf_counter() - start_time
    animal_uncached_throughput = (iterations * len(test_values)) / animal_uncached_time

    # Clear the cache again
    Animal._normalize.cache_clear()
    City._normalize.cache_clear()

    # Measure City enum without cache
    city_uncached_time = 0.0
    for _ in range(iterations):
        for value in test_values:
            City._normalize.cache_clear()
            start_time = time.perf_counter()
            _ = City.from_str(value, raise_error=False)
            city_uncached_time += time.perf_counter() - start_time
    city_uncached_throughput = (iterations * len(test_values)) / city_uncached_time

    print(f"Animal enum ({len(Animal)} members):")
    print(f"  - Throughput: {animal_uncached_throughput:,.0f} lookups/second")
    print(f"  - Total time: {animal_uncached_time:.3f}s")
    print(f"  - Time per lookup: {animal_uncached_time * 1_000_000 / (iterations * len(test_values)):.3f}µs")

    print(f"\nCity enum ({len(City)} members):")
    print(f"  - Throughput: {city_uncached_throughput:,.0f} lookups/second")
    print(f"  - Total time: {city_uncached_time:.3f}s")
    print(f"  - Time per lookup: {city_uncached_time * 1_000_000 / (iterations * len(test_values)):.3f}µs")

    # Calculate speed ratios
    cached_ratio = city_cached_throughput / animal_cached_throughput
    uncached_ratio = city_uncached_throughput / animal_uncached_throughput

    print("\nSpeed ratios:")
    print(f"  - With caching: {cached_ratio:.2f}x (City/Animal)")
    print(f"  - Without caching: {uncached_ratio:.2f}x (City/Animal)")

    # Assertions
    # With caching, both should be very fast
    assert animal_cached_throughput > 100_000, (
        f"Animal enum cached throughput too slow: {animal_cached_throughput:,.0f} lookups/second"
    )
    assert city_cached_throughput > 100_000, (
        f"City enum cached throughput too slow: {city_cached_throughput:,.0f} lookups/second"
    )

    # Without caching, the larger enum should be slower
    assert uncached_ratio < 2.0, f"Larger enum is faster without caching: {uncached_ratio:.2f}x"
    assert uncached_ratio > 0.5, f"Larger enum is too slow without caching: {uncached_ratio:.2f}x"
