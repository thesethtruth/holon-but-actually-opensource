## RESULTS:
# ----> Numba vectorized + numpy array (including constrution)
# time elapsed: 0.7808222770690918

# ----> Numpy array (including constrution)
# time elapsed: 0.7821321487426758

# ----> Numpy array (without array construction)
# time elapsed: 0.7029914855957031

# ----> List comprehension
# time elapsed: 1.6260454654693604

# ----> Multiprocessing pool
# time elapsed: 2.8562045097351074

from multiprocessing import Pool
import time
import numpy as np
from numba import jit, int64, vectorize


def add_one_to_even(i):
    if i % 2 == 0:
        return i + 1
    else:
        return i


@vectorize
def add_one_to_even_vectorized(i):
    if i % 2 == 0:
        return i + 1
    else:
        return i


if __name__ == "__main__":

    llist = range(int(1e7))

    print("----> Numba vectorized + numpy array (including constrution)")
    t1 = time.time()
    arr = np.array(llist)
    add_one_to_even_vectorized(arr)
    t2 = time.time()
    print(f"time elapsed: {t2-t1}\n")

    print("----> Numpy array (including constrution)")
    t1 = time.time()
    arr = np.array(llist)
    t1a = time.time()
    arr = np.where(arr % 2 == 0, arr + 1, arr)
    t2 = time.time()
    print(f"time elapsed: {t2-t1}\n")

    print("----> Numpy array (without array construction)")
    print(f"time elapsed: {t1a-t1}\n")

    print("----> List comprehension")
    t1 = time.time()
    _ = [add_one_to_even(it) for it in llist]
    t2 = time.time()
    print(f"time elapsed: {t2-t1}\n")

    with Pool() as pool:
        print("----> Multiprocessing pool")
        t1 = time.time()
        result = pool.map(add_one_to_even, llist)
        t2 = time.time()

        print(f"time elapsed: {t2-t1}\n")
