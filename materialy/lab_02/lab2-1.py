import requests
import time
import concurrent.futures

CAT_API_URL = "https://catfact.ninja/fact"
N = 20


def fetch_fact():
    return requests.get(CAT_API_URL).json().get("fact")


# 1. Wersja sekwencyjna
def run_sequential():
    facts = []
    start = time.perf_counter()
    for _ in range(N):
        facts.append(fetch_fact())
    elapsed = time.perf_counter() - start
    return facts, elapsed


# 2. Wersja wielowątkowa
def run_threaded(max_workers=20):
    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        facts = list(executor.map(lambda _: fetch_fact(), range(N)))
    elapsed = time.perf_counter() - start
    return facts, elapsed


if __name__ == "__main__":
    seq_facts, seq_time = run_sequential()
    print(f"Sekwencyjnie: {seq_time:.2f} s")

    thr_facts, thr_time = run_threaded()
    print(f"Wielowątkowo: {thr_time:.2f} s")

    # 3. Porównanie
    speedup = seq_time / thr_time if thr_time else float("inf")
    print(f"Przyspieszenie: {speedup:.1f}x")

    print(f"\nPrzykładowy fakt: {thr_facts[0]}")