import logging
import tempfile
import time
from multiprocessing import Process, freeze_support
from unittest import TestCase

from distributed import (Client, LocalCluster, Lock, get_client, get_worker,
                         progress)

if __name__ == '__main__':

    freeze_support()

    cluster = LocalCluster(
        processes=False,
        n_workers=2,
        threads_per_worker=10,
        resources={"memory": 30, "cpu": 10},
    )
    
    client = Client(cluster.scheduler.address)

    start = time.time()

    def timestamp(i):
        import time
        time.sleep(5)
        worker = get_worker()
        return {
            "time": time.time(),
            "i": i,
            "worker": worker.address
        }

    futures = [
        client.submit(
            timestamp, i, 
            # resources={"memory": 6},
            resources={"cpu": 2, "memory": 10},
            pure=False,
        )
        for i in range(20)
    ]
    progress(futures)
    print()
    
    results = client.gather(futures)
    for r in sorted(results, key=lambda r: r['i']):
        print(r['i'], r['worker'], r['time'] - start)
