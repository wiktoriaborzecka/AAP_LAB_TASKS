import queue
import threading

POISON = None  # sentinel kończący konsumenta


def producer(even_q, odd_q, count):
    for n in range(1, count + 1):
        if n % 2 == 0:
            even_q.put(n)
        else:
            odd_q.put(n)
    # po wyprodukowaniu wszystkiego — sygnał końca dla każdego konsumenta
    even_q.put(POISON)
    odd_q.put(POISON)


def consumer(q, name):
    while True:
        item = q.get()
        try:
            if item is POISON:
                break
            print(f"{name}: {item}")
        finally:
            q.task_done()


if __name__ == "__main__":
    COUNT = 20
    even_q = queue.Queue()
    odd_q = queue.Queue()

    threads = [
        threading.Thread(target=producer, args=(even_q, odd_q, COUNT)),
        threading.Thread(target=consumer, args=(even_q, "Konsument-parzyste"), name="even"),
        threading.Thread(target=consumer, args=(odd_q, "Konsument-nieparzyste"), name="odd"),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("Zakończono — wszystkie liczby przetworzone.")