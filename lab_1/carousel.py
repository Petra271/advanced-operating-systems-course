from time import sleep
import numpy as np
import multiprocessing as mp
import random
import os


class Message:
    def __init__(self, type: str, source, dest, sitting=None, finished=None):
        self.type = type
        self.source_id = source
        self.dest_id = dest
        self.sitting = sitting
        self.finished = finished


def visitor(K: int, req: mp.Queue(), res: mp.Queue(), n: int):
    ct = 0

    while ct < 3:
        ct += 1

        sleep_time = np.random.uniform(0.1, 2.0)
        sleep(sleep_time)
        req.put(Message("I want a ride", n, K))

        # cekaj dok ne primi poruku "Sit"
        while True:
            if wait_response(res, "Sit", K, n):
                break

        print("\033[95m" + f"Visitor {K+1} got on the carousel" + "\x1b[0m")

        # cekaj znacku
        while True:
            if wait_token(res, K, n, 1, 0):
                break

        # cekaj dok ne primi poruku "Stand up"
        while True:
            if wait_response(res, "Stand up", K, n):
                break

        print("\033[92m" + f"Visitor {K+1} got off the carousel" + "\x1b[0m")

        # cekaj znacku
        while True:
            if wait_token(res, K, n, -1, 0):
                break

    while 1:
        message = res.get()
        if message.type == "Token":
            message.finished.append(K)
            if message.dest_id == K:
                message.dest_id = update_dest_id(K, n, message.finished)
            res.put(message)
            break
        res.put(message)

    print(f"Visitor {K+1} finished.")


def wait_response(res, response, K, n):
    message = res.get()
    if message.type == "Token":
        if message.dest_id == K:
            message.dest_id = update_dest_id(K, n, message.finished)
    if message.type == response:
        return True
    else:
        res.put(message)
    return False


def wait_token(res, K, n, inc, type, num_vis=None):
    message = res.get()
    if message.type == "Token":
        if message.dest_id == K:
            message.sitting += inc
            message.dest_id = update_dest_id(K, n, message.finished)
            if type and message.sitting == num_vis or not type:
                res.put(message)
                return True
    res.put(message)


def update_dest_id(K, n, finished):
    new = (K+1) % n
    while new in finished:
        new = (new+1) % n
    return new


def carousel():
    req = mp.Queue()
    res = mp.Queue()
    max = 4
    start = 1
    visitors = []
    n = 8
    id_car = 8

    # stvori visitore
    for v in range(8):
        vis = mp.Process(target=visitor, args=(v, req, res, n+1))
        visitors.append(vis)
        vis.start()

    alive = len(visitors)
    res.put(Message("Token", source=id_car, dest=0, sitting=0, finished=[]))
    while True:  # dok ima dovoljno posjetitelja za voznju
        sitting = []
        end = 0
        current = 0

        while current < max:
            message = res.get()
            if message.type == "Token":
                if len(message.finished) == n:
                    end = 1
                    break
            res.put(message)

            current += 1
            mess = req.get()
            res.put(Message("Sit", source=id_car, dest=mess.source_id))
            sitting.append(mess.source_id)
        if end:
            break

        # cekaj znacku
        while 1:
            if wait_token(res, id_car, n+1,  0, 1, num_vis=4):
                break

        print("Carousel spinning")
        sleep(np.random.uniform(0.1, 3.0))
        print("Carousel stopped spinning")

        for i in sitting:
            res.put(Message("Stand up", source=id_car, dest=i))

        # cekaj znacku
        while 1:
            result = wait_token(res, id_car, n+1, 0, 1, num_vis=0)
            if result:
                break

        while (message := res.get()).type != "Token":
            res.put(message)
        if len(message.finished) == n:
            break
        res.put(message)

    for v in visitors:
        v.join()

    req.close()
    res.close()


if __name__ == "__main__":
    vrt = mp.Process(target=carousel)
    vrt.start()
    vrt.join()
