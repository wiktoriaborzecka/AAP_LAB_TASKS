import multiprocessing
import time
from lab2_functions import calculate_power_sum

if __name__ == "__main__":
    numbers = range(1, 10_001)

    # Wersja sekwencyjna (do porównania)
    start = time.perf_counter()
    seq_results = [calculate_power_sum(n) for n in numbers]
    seq_time = time.perf_counter() - start
    print(f"Sekwencyjnie: {seq_time:.2f} s")

    # Wersja wieloprocesowa
    start = time.perf_counter()
    with multiprocessing.Pool() as pool:
        par_results = pool.map(calculate_power_sum, numbers)
    par_time = time.perf_counter() - start
    print(f"Wieloprocesowo: {par_time:.2f} s")

    speedup = seq_time / par_time if par_time else float("inf")
    print(f"Przyspieszenie: {speedup:.1f}x (rdzeni: {multiprocessing.cpu_count()})")

    assert seq_results == par_results  # weryfikacja zgodności wyników