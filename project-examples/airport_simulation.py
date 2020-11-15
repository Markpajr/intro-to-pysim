import simpy
from numpy import random

# Defining Resources
BOARDING_CHECK_WORKERS = 1
PERSONAL_CHECK_QUEUES = 1

# Defining Rates
PASSENGERS_PER_MINUTE = 5

# Defining Simulation Reps
SIMULATION_RUN_TIME = 10
SIMULATION_REPS = 1

class AirPort(object):
    def __init__(self, env):
        self.env = env
        self.boarding_check = simpy.Resource(env, capacity=BOARDING_CHECK_WORKERS)
        self.personal_check = simpy.Resource(env, capacity=PERSONAL_CHECK_QUEUES)
        self.passenger_wait_times = []
        

    def boarding_check_service_time(self):
        yield self.env.timeout(random.exponential(1/0.75))


    def personal_check_service_time(self):
        yield self.env.timeout(random.uniform(0.5,1))


    def store_wait_times(self, wait_time):
        self.passenger_wait_times.append(wait_time)


def passenger(env, name, airport):  
    # arrives to boarding check
    arrival_time = round(airport.env.now,2)
    print(f'Passenger {name} Arriving to Boarding Check at {arrival_time} minutes')

    with airport.boarding_check.request() as request:
        # checks queue size
        print(f"Boarding Check QUEUE SIZE:",len(airport.boarding_check.queue))

        # requests service
        yield request

        # now serving
        print(f'Now Serving Passenger {name} at Boarding Check; {round(airport.env.now,2)} minutes')        
        yield env.process(airport.boarding_check_service_time())

        # passenger leaves
        boarding_departure_time = round(airport.env.now,2)
        print(f'Passenger {name} Leaves Boarding Check at {boarding_departure_time} minutes')

    # arrives to personal check  
    personal_check_arrival_time = round(airport.env.now,2)
    print(f'Passenger {name} Arriving to Personal Check at {personal_check_arrival_time} minutes')

    with airport.personal_check.request() as request:
        # checks queue size
        print(f"Personal Check QUEUE SIZE:", len(airport.personal_check.queue))

        # requests service
        yield request
        
        # now serving
        print(f'Now Serving Passenger {name} at Personal Check; {round(airport.env.now,2)} minutes')        
        yield env.process(airport.personal_check_service_time())        
       
        # passenger leaves
        personal_check_departure_time = round(airport.env.now,2)
        print(f'Passenger {name} Leaves Personal Check at {personal_check_departure_time} minutes')
        
        # storing wait times
        wait_time = (personal_check_departure_time - arrival_time)
        airport.store_wait_times(round(wait_time,2))


def passenger_generator(env, airport):
    for name in range(1, PASSENGERS_PER_MINUTE + 1):
        env.process(passenger(env, name, airport))
        yield env.timeout(round(random.exponential(1/0.2),2))        



wait_times = []
for i in range(1, SIMULATION_REPS + 1):
    random.seed(i)
    env = simpy.Environment()
    airport = AirPort(env)
    env.process(passenger_generator(env, airport))
    env.run(until=SIMULATION_RUN_TIME)
    wait_times.append(airport.passenger_wait_times)         


# calculate average wait times
minutes_waited_per_rep = [sum(wait_time) for wait_time in wait_times]
average_wait_time_per_rep = [minutes/PASSENGERS_PER_MINUTE for minutes in minutes_waited_per_rep]
average_wait_time_across_reps = sum(average_wait_time_per_rep)/SIMULATION_REPS    