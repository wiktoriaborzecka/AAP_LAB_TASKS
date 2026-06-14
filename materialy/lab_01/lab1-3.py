def prime_generator():
    primes = []
    candidate = 2
    while True:
        if all(candidate % p != 0 for p in primes if p * p <= candidate):
            primes.append(candidate)
            yield candidate
        candidate += 1


primes_ending_7 = (p for p in prime_generator() if p % 10 == 7)

for _ in range(10):
    print(next(primes_ending_7))