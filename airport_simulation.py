import simpy
import numpy as np

# Defining Resources
BOARDING_CHECK_WORKERS = 1
PERSONAL_CHECK_SCANNERS = 1

# Defining Arrival Rate
PASSENGERS_PER_MINUTE = 5

# Defining Service Rates
BOARDING_CHECK_SERVICE_RATE = 0.75
PERSONAL_CHECK_SERVICE_RATE = {"min_scan": 0.5, "max_scan": 1}

# Defining Simulation Variables
RUN_TIME_MINUTES = 10
REPLICATIONS = 1


class AirPort(object):
    def __init__(self, env):
        self.env = env
        self.boarding_check = simpy.Resource(env, capacity=BOARDING_CHECK_WORKERS)
        self.personal_check_scanner = [simpy.Resource(env, capacity=1)for _ in range(PERSONAL_CHECK_SCANNERS + 1)]
        self.passenger_wait_times = []

    def boarding_check_service_time(self):
        yield self.env.timeout(np.random.exponential(1 / BOARDING_CHECK_SERVICE_RATE))

    def personal_check_service_time(self):
        yield self.env.timeout(np.random.uniform(PERSONAL_CHECK_SERVICE_RATE["min_scan"],
                                                 PERSONAL_CHECK_SERVICE_RATE["max_scan"]))

    def store_wait_times(self, wait_time):
        self.passenger_wait_times.append(wait_time)


def passenger(env, name, airport):
    arrival_time = round(airport.env.now, 2)
    print(f'Passenger {name} Arrives to Boarding Check at {arrival_time} minutes')
    with airport.boarding_check.request() as request:
        print(f"Boarding Check QUEUE SIZE:", len(airport.boarding_check.queue))
        yield request
        yield env.process(airport.boarding_check_service_time())
        boarding_departure_time = round(airport.env.now, 2)
        print(f'Passenger {name} Departs Boarding Check at {boarding_departure_time} minutes')
    personal_check_arrival_time = round(airport.env.now, 2)
    print(f'Passenger {name} Arrives to Personal Check at {personal_check_arrival_time} minutes')

    minq = 0
    for i in range(1, PERSONAL_CHECK_SCANNERS + 1):
        if len(airport.personal_check_scanner[i].queue) < len(airport.personal_check_scanner[minq].queue):
            minq = i
    with airport.personal_check_scanner[minq].request() as request:
        yield request
        yield env.process(airport.personal_check_service_time())
        personal_check_departure_time = round(airport.env.now, 2)
        print(f'Passenger {name} Departs Personal Check at {personal_check_departure_time} minutes')
        wait_time = (personal_check_departure_time - arrival_time)
        airport.store_wait_times(round(wait_time, 2))


def passenger_generator(env):
    passenger_name = 1
    airport = AirPort(env)
    while True:
        yield env.timeout(np.random.exponential(PASSENGERS_PER_MINUTE))
        env.process(passenger(env, passenger_name, airport))
        passenger_name += 1


for i in range(1, REPLICATIONS + 1):
    np.random.seed(i)
    env = simpy.Environment()
    env.process(passenger_generator(env))
    env.run(until=RUN_TIME_MINUTES)
