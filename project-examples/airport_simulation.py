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

    def get_resources(self):
        resources = {
            "boarding_check": {
                "wait_times": boarding_check_wait_times,
                "service_rate": self.boarding_check_service_time(),
                "service_times": boarding_check_service_times
            },
            "personal_check": {
                "wait_times": personal_check_wait_times,
                "service_rate": self.personal_check_service_time(),
                "service_times": personal_check_service_times
            }
        }
        return resources


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
        yield from self._create_process_dispose(self.airport.boarding_check,
                                                "boarding_check", self.airport_arrival_time)

        available_scanner = self._decision_block()  # Decision Block to Determine Available Scanner
        yield from self._create_process_dispose(self.airport.personal_check_scanner[available_scanner],
                                                "personal_check", round(self.airport.env.now, 2))

        departed_airport = self.airport.env.now
        time_in_system.append(departed_airport - self.airport_arrival_time)  # Calculate Time in System

    def _create_process_dispose(self, resource, name, arrival_time):
        resources = self.airport.get_resources()
        with resource.request() as request:  # Automatically Disposes Entity, Releases Resource when Finished (Dispose)
            yield request  # Entity Requests Resource (Create)
            time_in = self.airport.env.now
            resources[name]["wait_times"].append(round(time_in, 2) - arrival_time)
            yield env.process(resources[name]["service_rate"])  # Resource is Serving the Entity (Process)
            resources[name]["service_times"].append(self.airport.env.now - time_in)  # Calculate Service Rates

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
average_wait_times = np.mean([np.mean(boarding_check_wait_times), np.mean(personal_check_wait_times)])

table = [
    ['Avg Boarding Check Wait', round(np.mean(boarding_check_wait_times), 2)],
    ['Avg Personal Check Wait', round(np.mean(personal_check_wait_times), 2)],
    ['Avg Boarding Check Service Rate', round(np.mean(boarding_check_service_times), 2)],
    ['Avg Personal Check Service Rate', round(np.mean(personal_check_service_times), 2)],
    ['Avg Wait Time', round(average_wait_times, 2)],
    ['Avg Time in System', round(np.mean(time_in_system), 2)]
]

headers = ["", "Total (Minutes)"]

print(tabulate(table, headers, tablefmt="fancy_grid"))
