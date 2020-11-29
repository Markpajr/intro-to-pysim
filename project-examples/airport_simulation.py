import simpy
import numpy as np
from tabulate import tabulate

# Defining Resources
BOARDING_CHECK_WORKERS = 1
PERSONAL_CHECK_SCANNERS = 1

# Defining Arrival Rate
PASSENGERS_PER_MINUTE = 5

# Defining Service Rates
BOARDING_CHECK_SERVICE_RATE = 0.75
PERSONAL_CHECK_SERVICE_RATE = {"min_scan": 0.5, "max_scan": 1}

# Defining Simulation Variables
RUN_TIME_MINUTES = 720
REPLICATIONS = 1

# Variables for Output Analysis
boarding_check_wait_times = []
personal_check_wait_times = []
boarding_check_service_times = []
personal_check_service_times = []
time_in_system = []


class AirPort:
    def __init__(self, env):
        self.env = env
        self.boarding_check = simpy.Resource(env, capacity=BOARDING_CHECK_WORKERS)
        self.personal_check_scanner = [simpy.Resource(env, capacity=1) for _ in range(PERSONAL_CHECK_SCANNERS + 1)]

    def boarding_check_service_time(self):
        yield self.env.timeout(np.random.exponential(BOARDING_CHECK_SERVICE_RATE))

    def personal_check_service_time(self):
        yield self.env.timeout(np.random.uniform(PERSONAL_CHECK_SERVICE_RATE["min_scan"],
                                                 PERSONAL_CHECK_SERVICE_RATE["max_scan"]))


class Passenger:
    global boarding_check_wait_times
    global boarding_check_service_times
    global personal_check_wait_times
    global personal_check_service_times
    global time_in_system

    def __init__(self, name, airport):
        self.name = name
        self.airport = airport
        self.airport_arrival_time = round(self.airport.env.now, 2)

    def go_to_airport(self):
        with self.airport.boarding_check.request() as request:  # Automatically Disposes Entity, Releases Resource when Finished (dispose)
            yield request  # Entity Requests Resource (create)
            time_in = self.airport.env.now
            boarding_check_wait_times.append(round(time_in, 2) - self.airport_arrival_time)
            yield env.process(self.airport.boarding_check_service_time())  # Resource is Serving the Entity (process)
            boarding_check_service_times.append(self.airport.env.now - time_in)  # calculate total time for passenger to be checked

        available_scanner = self._decision_block()  # Decision block to determine which scanner to go to
        personal_check_arrival = round(self.airport.env.now, 2)
        with self.airport.personal_check_scanner[available_scanner].request() as request:  # Automatically Disposes Entity, Releases Resource when Finished (dispose)
            yield request  # Entity Requests Resource (create)
            time_in = self.airport.env.now
            personal_check_wait_times.append(round(time_in, 2) - personal_check_arrival)
            yield env.process(self.airport.personal_check_service_time())  # Resource is Serving the Entity (process)
            personal_check_service_times.append(self.airport.env.now - time_in)  # calculate total time for passenger to be checked

        left_airport = self.airport.env.now
        time_in_system.append(left_airport - self.airport_arrival_time)  # calculate total time in system for passenger

    def _decision_block(self):
        minq = 1
        for i in range(1, PERSONAL_CHECK_SCANNERS + 1):
            if len(self.airport.personal_check_scanner[i].queue) < len(self.airport.personal_check_scanner[minq].queue):
                minq = i
        return minq


def passenger_generator(env):
    passenger_name = 1
    airport = AirPort(env)
    while True:
        yield env.timeout(np.random.exponential(1 / PASSENGERS_PER_MINUTE))
        passenger = Passenger(passenger_name, airport)
        env.process(passenger.go_to_airport())
        passenger_name += 1


for i in range(1, REPLICATIONS + 1):
    np.random.seed(i)
    env = simpy.Environment()
    env.process(passenger_generator(env))
    env.run(until=RUN_TIME_MINUTES)


print("---------------------Output Analysis-----------------------")
headers = ['Avg Boarding Check Wait',
           'Avg Personal Check Wait',
           'Avg Boarding Check Service Rate',
           'Avg Personal Check Service Rate',
           'Avg Wait Time',
           'Avg Time in System']

average_wait_times = (np.mean(boarding_check_wait_times) + np.mean(personal_check_wait_times)) / 2
data = np.array([
    round(np.mean(boarding_check_wait_times), 2),
    round(np.mean(personal_check_wait_times), 2),
    round(np.mean(boarding_check_service_times), 2),
    round(np.mean(personal_check_service_times), 2),
    round(average_wait_times, 2),
    round(np.mean(time_in_system), 2)
])

print(tabulate([data], headers, tablefmt="fancy_grid"))
