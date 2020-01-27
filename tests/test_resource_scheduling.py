from unittest import TestCase
import logging
import time
import tempfile
from distributed import Client, LocalCluster, Lock, get_client, progress, get_worker
from multiprocessing import Process, freeze_support



# class While():

#     def __init__(self, condition, body, max_iterations=-1):
#         self.condition = condition
#         self.body = body
#         self.max_iterations = max_iterations

#     def __call__(self):

#         client = get_client()

#         return_value = None

#         iteration = 0
#         while self.max_iterations == -1 or iteration < self.max_iterations:
#             condition = bool(client.submit(
#                 self.condition,
#                 previous=return_value,
#                 iteration=iteration,
#                 pure=False
#             ).result())

#             logging.warning("Iteration %d: condition is %s & previous result is %s", iteration, str(condition), str(return_value))

#             if not condition:
#                 break

#             return_value = client.submit(
#                 self.body,
#                 previous=return_value,
#                 iteration=iteration,
#                 pure=False
#             ).result()

#             iteration += 1

#         return return_value


if __name__ == '__main__':

    freeze_support()

    cluster = LocalCluster(
        processes=False,
        n_workers=2,
        threads_per_worker=2,
        resources={"memory": 10, "cpu": 2},
    )
    
    client = Client(cluster.scheduler.address)

    start = time.time()

    # def condition(iteration, previous=None):
    #     if previous is None:
    #         return True
    #     if previous < 20:
    #         return True
    #     return False

    # def body(iteration, previous=None):
    #     if previous == 1:
    #         return previous + 1
    #     if previous is not None:
    #         return previous + iteration
    #     return 0

    # while_node = While(condition, body, max_iterations=10)

    # futures = [client.submit(while_node)]

    # results = client.gather(futures)
    # print(results)

    def timestamp(delay, i):
        import time
        time.sleep(delay)
        worker = get_worker()
        return {
            "time": time.time(),
            "i": i,
            "worker": worker.address
        }

    futures = [
        client.submit(
            timestamp, 3, i, 
            # resources={"memory": 6},
            resources={"cpu": 2, "memory": 2},
            pure=False,
        )
        for i in range(20)
    ]
    progress(futures)
    print()
    
    results = client.gather(futures)
    for r in sorted(results, key=lambda r: r['i']):
        print(r['i'], r['worker'], r['time'] - start)
