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
RUN_TIME_MINUTES = 15
REPLICATIONS = 1


class AirPort:
    def __init__(self, env):
        self.env = env
        self.boarding_check = simpy.Resource(env, capacity=BOARDING_CHECK_WORKERS)
        self.personal_check_scanner = [simpy.Resource(env, capacity=1) for _ in range(PERSONAL_CHECK_SCANNERS + 1)]
        self.boarding_check_wait_times = []
        self.personal_check_wait_times = []
        self.wait_times = []
        self.system_wait_times = []

    def boarding_check_service_time(self):
        yield self.env.timeout(np.random.exponential(1 / BOARDING_CHECK_SERVICE_RATE))

    def personal_check_service_time(self):
        yield self.env.timeout(np.random.uniform(PERSONAL_CHECK_SERVICE_RATE["min_scan"],
                                                 PERSONAL_CHECK_SERVICE_RATE["max_scan"]))


class Passenger:
    def __init__(self, name, airport):
        self.name = name
        self.airport = airport

    def go_to_airport(self):
        boarding_check_arrival = round(self.airport.env.now, 2)
        print(f'Passenger {self.name} Arrives to Boarding Check at {boarding_check_arrival} minutes')
        yield from self._create_process_dispose(self.airport.boarding_check)
        boarding_check_wait_time = round(self.airport.env.now, 2) - boarding_check_arrival
        self.airport.boarding_check_wait_times.append(boarding_check_wait_time)

        personal_check_arrival = round(self.airport.env.now, 2)
        print(f'Passenger {self.name} Arrives to Personal Check Scanner at {personal_check_arrival} minutes')
        available_scanner = self._decision_block()  # Decision block to determine which scanner to go to
        yield from self._create_process_dispose(self.airport.personal_check_scanner[available_scanner])
        personal_check_wait_time = round(self.airport.env.now, 2) - personal_check_arrival
        self.airport.personal_check_wait_times.append(personal_check_wait_time)

        self.airport.wait_times.append(boarding_check_wait_time + personal_check_wait_time)
        self.airport.system_wait_times.append(round(self.airport.env.now, 2) - boarding_check_arrival)

    def _create_process_dispose(self, resource):
        service_name, service_time = self._determine_resource(resource)
        with resource.request() as request:  # Automatically Disposes Entity, Releases Resource when Finished (dispose)
            print(f"{service_name} QUEUE SIZE:", len(resource.queue))
            yield request  # Entity Requests Resource (create)
            yield env.process(service_time)  # Resource is Serving the Entity (process)
            print(f'Passenger {self.name} Departs {service_name} at {round(self.airport.env.now, 2)} minutes')

    def _determine_resource(self, resource):
        service_name = "Personal Check Scanner"
        service_time = self.airport.personal_check_service_time()
        if resource == self.airport.boarding_check:
            service_name = "Boarding Check"
            service_time = self.airport.boarding_check_service_time()
        return service_name, service_time

    def _decision_block(self):
        minq = 0
        for i in range(1, PERSONAL_CHECK_SCANNERS + 1):
            if len(self.airport.personal_check_scanner[i].queue) < len(self.airport.personal_check_scanner[minq].queue):
                minq = i
        return minq


total_boarding_check_wait_times = 0
total_personal_check_wait_times = 0
total_wait_times = 0
total_system_wait_times = 0
total_passengers = 0


def passenger_generator(env):
    global total_boarding_check_wait_times
    global total_personal_check_wait_times
    global total_wait_times
    global total_system_wait_times
    global total_passengers

    passenger_name = 1
    airport = AirPort(env)
    while True:
        yield env.timeout(np.random.exponential(PASSENGERS_PER_MINUTE))
        passenger = Passenger(passenger_name, airport)
        env.process(passenger.go_to_airport())
        passenger_name += 1
        total_boarding_check_wait_times = np.sum(airport.boarding_check_wait_times)
        total_personal_check_wait_times = np.sum(airport.personal_check_wait_times)
        total_wait_times = np.sum(airport.wait_times)
        total_system_wait_times = np.sum(airport.system_wait_times)
        total_passengers = len(airport.boarding_check_wait_times)


for i in range(1, REPLICATIONS + 1):
    np.random.seed(i+1)
    env = simpy.Environment()
    env.process(passenger_generator(env))
    env.run(until=RUN_TIME_MINUTES)

print("---------------------Output Analysis-----------------------")
print(f"Average Boarding Check Wait Time: {round(total_boarding_check_wait_times/total_passengers,2)} Minutes")
print(f"Average Personal Check Wait Time: {round(total_personal_check_wait_times/total_passengers, 2)} Minutes")
print(f"Average Wait Time: {round(total_wait_times/total_passengers,2)} Minutes")
print(f"Average Time in System: {round(total_system_wait_times/total_passengers,2)} Minutes")
