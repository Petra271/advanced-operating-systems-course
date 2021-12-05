from time import sleep
import numpy as np
import multiprocessing as mp
import typing
import random
from queue import PriorityQueue
import os
import itertools


class Philosopher:
    def __init__(self, id, n):
        self.id = id
        self.n = n
        self.read = []  # za čitanje
        self.write = []  # za pisanje
        self.clock = random.randrange(1, random.randint(200, 10000))
        self.my_responeses = PriorityQueue()
        self.my_request = None

    def work(self):

        while True:
            sleep(np.random.uniform(1., 3.))  # razmišlja

            self.send_request()
            self.wait_ans()
            self.send_responses()

            sleep(np.random.uniform(1., 3.))

    def send_request(self):
        self.my_request = ("I'm hungry", self.clock, self.id)
        for conn, id in self.write:
            print(f'Filozof {self.id+1} šalje zahtjev ({id+1}, {self.clock})')
            conn.send(self.my_request)
        sleep(0.2)

    def eat(self):
        print(f"Filozof {self.id+1} jede.")
        sleep(random.uniform(3, 7.))  # filozof je za stolom
        print(f"Filozof {self.id+1} je gotov")

    def wait_ans(self):
        answers = 0
        while answers < 2:  # čeka dok mu svi ne odgovore
            for conn, id in self.read:
                message, clock, pid = conn.recv()
                if message == "OK":
                    answers += 1
                    print(
                        f'Filozof {self.id+1} prima odgovor ({pid+1}, {clock})')
                    if answers == 2:
                        self.eat()
                if message == "I'm hungry":
                    print(
                        f'Filozof {self.id+1} prima zahtjev ({pid+1}, {clock})')
                    self.manage_request(pid, clock)

    def manage_request(self, id, clock):
        if self.check_priority(id, clock):
            self.my_responeses.put(('OK', clock, self.id, id))
            self.clock = max(self.clock, clock) + 1
        else:
            for conn, id_num in self.write:
                if id_num == id:
                    conn.send(("OK", clock, self.id))
                    print(
                        f'Filozof {self.id+1} šalje odgovor ({self.id+1}, {clock})')
                    self.clock = max(self.clock, clock) + 1

    def send_responses(self):
        for conn, id in self.write:
            for res in self.my_responeses.queue:
                if id == res[3]:
                    conn.send(res[:3])
        self.my_responeses.queue.clear()

    def check_priority(self, id, clock):
        # true ako ovaj je ovaj proces ranije poslao zahtjev
        my_request_time = self.my_request[1]
        if my_request_time == clock:
            return self.id < id
        return my_request_time < clock


def create_pipelines(phils: typing.List[Philosopher]) -> typing.List[mp.Pipe]:
    n = len(philosophers)
    conns = []
    combos = set()
    for p1 in range(n):
        n1 = (p1-1) % n
        n2 = (p1+1) % n
        if (n1, p1) not in combos:
            combos.add((p1, n1))
        if (n2, p1) not in combos:
            combos.add((p1, n2))

    for p1, n in combos:
        conns = connect_neighbours(phils, p1, n, conns)
    return conns


def connect_neighbours(philosophers, p1, n, conns):
    p1_r, p2_w = mp.Pipe()
    p2_r, p1_w = mp.Pipe()
    philosophers[p1].read.append((p1_r, n))
    philosophers[p1].write.append((p1_w, n))
    philosophers[n].read.append((p2_r, p1))
    philosophers[n].write.append((p2_w, p1))
    conns.extend([p1_w, p1_r, p2_r, p2_w])
    return conns


if __name__ == "__main__":
    n = 5
    philosophers = []
    processes = []

    for i in range(n):
        philosophers.append(Philosopher(i, n))

    conns = create_pipelines(philosophers)

    for p in philosophers:
        process = mp.Process(target=p.work)
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    for conn in conns:
        conn.close()
