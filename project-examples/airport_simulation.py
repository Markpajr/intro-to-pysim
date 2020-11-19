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

# Variables for Output Analysis
boarding_check_wait_times = []
personal_check_wait_times = []
time_in_system = []
total_passengers = 0


class AirPort:
    def __init__(self, env):
        self.env = env
        self.boarding_check = simpy.Resource(env, capacity=BOARDING_CHECK_WORKERS)
        self.personal_check_scanner = [simpy.Resource(env, capacity=1) for _ in range(PERSONAL_CHECK_SCANNERS + 1)]

    def boarding_check_service_time(self):
        yield self.env.timeout(np.random.exponential(1 / BOARDING_CHECK_SERVICE_RATE))

    def personal_check_service_time(self):
        yield self.env.timeout(np.random.uniform(PERSONAL_CHECK_SERVICE_RATE["min_scan"],
                                                 PERSONAL_CHECK_SERVICE_RATE["max_scan"]))


class Passenger:
    global boarding_check_wait_times
    global personal_check_wait_times
    global time_in_system

    def __init__(self, name, airport):
        self.name = name
        self.airport = airport
        self.arrival_time = round(self.airport.env.now, 2)

    def go_to_airport(self):
        yield from self._create_process_dispose(self.airport.boarding_check)
        available_scanner = self._decision_block  # Decision block to determine which scanner to go to
        yield from self._create_process_dispose(self.airport.personal_check_scanner[available_scanner])

    def _create_process_dispose(self, resource):
        service_name, service_time = self._determine_resource(resource)
        print(f"ARRIVAL: Passenger {self.name} Arrives to {service_name} @ {self.arrival_time} minutes")
        with resource.request() as request:  # Automatically Disposes Entity, Releases Resource when Finished (dispose)
            yield request  # Entity Requests Resource (create)
            if service_name == "Personal Check Scanner":
                personal_check_wait_times.append(self.airport.env.now - self.arrival_time)
            else:
                boarding_check_wait_times.append(self.airport.env.now - self.arrival_time)
            print(f"SERVICED: Passenger {self.name} is being served @ {round(self.airport.env.now, 2)} minutes")
            yield env.process(service_time)  # Resource is Serving the Entity (process)
            print(f"DEPARTURE: Passenger {self.name} Departs {service_name} @ {round(self.airport.env.now, 2)} minutes")
            if service_name == "Personal Check Scanner":
                time_in_system.append(self.airport.env.now - self.arrival_time)

    def _determine_resource(self, resource):
        service_name = "Personal Check Scanner"
        service_time = self.airport.personal_check_service_time()
        if resource == self.airport.boarding_check:
            service_name = "Boarding Check"
            service_time = self.airport.boarding_check_service_time()
        return service_name, service_time

    @property
    def _decision_block(self):
        minq = 0
        for i in range(1, PERSONAL_CHECK_SCANNERS + 1):
            if len(self.airport.personal_check_scanner[i].queue) < len(self.airport.personal_check_scanner[minq].queue):
                minq = i
        return minq


def passenger_generator(env):
    global total_passengers
    passenger_name = 1
    airport = AirPort(env)
    while True:
        yield env.timeout(np.random.exponential(1/PASSENGERS_PER_MINUTE))
        passenger = Passenger(passenger_name, airport)
        env.process(passenger.go_to_airport())
        passenger_name += 1
        total_passengers += 1


for i in range(1, REPLICATIONS + 1):
    print(f"REPLICATION {i}")

    np.random.seed(i + 1)
    env = simpy.Environment()
    env.process(passenger_generator(env))
    env.run(until=RUN_TIME_MINUTES)

    # print(f"REPLICATION {i} Boarding Check Wait Time: {np.mean(boarding_check_wait_times) / REPLICATIONS, 2)} Minutes")
    # print(f"Average Personal Check Wait Time: {round(np.mean(personal_check_wait_times) / REPLICATIONS, 2)} Minutes")
    # print(f"Average Time in System: {round(np.mean(time_in_system) / REPLICATIONS, 2)} Minutes")

print("---------------------Output Analysis-----------------------")
average_wait_times = (np.mean(boarding_check_wait_times) + np.mean(personal_check_wait_times)) / 2
print(f"Average Boarding Check Wait Time: {round(np.mean(boarding_check_wait_times)/REPLICATIONS, 2)} Minutes")
print(f"Average Personal Check Wait Time: {round(np.mean(personal_check_wait_times)/REPLICATIONS, 2)} Minutes")
print(f"Average Total Wait Time: {round(average_wait_times / REPLICATIONS, 2)} Minutes")
print(f"Average Time in System: {round(np.mean(time_in_system)/REPLICATIONS, 2)} Minutes")
