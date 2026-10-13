import numpy as np
from datetime import timedelta, datetime
import csv
from optimization import optimize
from functions import simulate_battery
from power_time import plot_results

# Loading technical parameters
with open('params.csv', newline='', mode='r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file)
    p = {row['param']:float(row['value']) for row in reader}


lat = 46.7   #latitude of flight(degrees)
h = 820      #altitude(M)
date_time = datetime(2027, 6, 11, 7, 0) #date, Y-M-D-H-M
normal = np.array([0,0,-1])   #North-East-Down normal vector


L  = 5.0
m_bat = 2.0
L_step = 0.1
m_bat_step = 0.1

# Simulation parameters
dt_hours = 1.0 / 5.0   #5-minute time steps
simulation_hours = 48  # wo days to examine repeatability
n_steps = int(simulation_hours / dt_hours)

(P_solar, L, m_bat, times, E_max,) = optimize(date_time, dt_hours, p, L_step, m_bat_step, normal, lat, h, n_steps, m_bat, L)

(
            E_battery,
            P_battery,
            P_load,
            P_motor,
            feasible
) = simulate_battery(P_solar, times, n_steps, dt_hours, int(round(24.0 / dt_hours)), p, m_bat, L, h)

plot_results(
            times=times,
            P_solar=P_solar,
            P_motor=P_motor,
            P_load=P_load,
            P_battery=P_battery,
            E_battery=E_battery,
            E_max=E_max,
            reserve_fraction=p['reserve_fraction']
        )
