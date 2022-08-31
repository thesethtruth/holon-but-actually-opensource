# from joblib import Parallel, delayed
import multiprocessing
import math
import time


t1 = time.time()
# def sqrt_func(i, j):
#     time.sleep(1)
#     return(str( math.sqrt(i**j)))

# j=2
# results = Parallel(n_jobs=2)(delayed(sqrt_func)(i, j) for i in range(10))
# t2=time.time()

# print("Elapsed time " + str(t2-t1) + "seconds")
# results


def sumall(value):
    return sum(range(1, value + 1))


pool_obj = multiprocessing.Pool(4)

answer = pool_obj.map(sumall, range(0, 5))
print(answer)
