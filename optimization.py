import numpy as np
from datetime import timedelta, datetime

from functions import P_sol, P_level, dE_bat_dt
from power_time import plot_results


# Aircraft and environmental parameters

lat = 46.7   #latitude of flight(degrees)
h = 820      #altitude(M)
date_time = datetime(2027, 6, 15, 7, 0) #date, Y-M-D-H-M
normal = np.array([0,0,-1])   #North-East-Down normal vector

C_L = 0.8            #Coeff of lift
C_D = 0.017          #(Y)Coeff of drag, need to add parasitic and induced drag



Eta_prop = 1.0       #(X)Prop, Esc, Motor effiency, need to test
Eta_mppt = 0.97      #(X)Mppt efficency, model later?

m_rest = 2.0         #(X)Estimate fusulage + tail weight(Kg)
m_L = 0.5            #(X)Mass of layup, per meter, without batteries(Kg)
P_av = 2.0           #(X)Power consumption of avionics(servos, flight controller ect) (W)
P_pld = 0.0          #(X)Power consuption  of payload(Remote id, leds, fpv ect) (W)


Ch = 0.3             #Chord(M)

L = 5.0              #Length of wing(M)         This will be a variable that will be optimized
L_min = 4.0          # Minimum wingspan (M)
L_max = 6.0          # Maximum wingspan (M)
L_step = 1.0

m_bat = 2.5         #Weight of batteries(Kg)   This will be a veriable that will be optimized 
m_bat_min = 1.0
m_bat_max = 3.0
m_bat_step = 1.0
e_bat = 250.0        #Specific energy (Wh/kg)
f_usable = 0.90      #Fraction of rated energy usable
reserve_fraction = 0.10  # Fraction of the battery we want available by morning

# Simulation parameters
dt_hours = 1.0 / 5.0   #5-minute time steps
simulation_hours = 48  # wo days to examine repeatability
n_steps = int(simulation_hours / dt_hours)

n_steps = int(round(simulation_hours / dt_hours))

times = [
    date_time + timedelta(hours=k * dt_hours)
    for k in range(n_steps + 1)
]

# Index for comparing the same time on consecutive days
steps_per_day = int(round(24.0 / dt_hours))


def battery_limits(m_bat):
    E_max = m_bat * e_bat * f_usable
    E_min = reserve_fraction * E_max
    return E_min, E_max



def simulate_battery(L, m_bat, solar_power):

    E_min, E_max = battery_limits(m_bat)

    motor_power = P_level(
        L, m_bat, C_D, C_L, m_L, m_rest, h, Ch
    ) / Eta_prop

    load = motor_power + P_av + P_pld

    # Positive = charging; negative = discharging
    battery_power = solar_power - load

    energy = np.zeros(len(times))
    energy[0] = E_max

    for k in range(n_steps):
        E_next = (
            energy[k] + battery_power[k] * dt_hours
        )
        energy[k + 1] = min(E_next, E_max)

    # Must maintain the required reserve at every timestep
    reserve_ok = np.all(energy >= E_min)

    # Compare energy at the same clock time on days 1 and 2
    repeatability_ok = (
        energy[-1] >= energy[-1 - steps_per_day]
    )

    feasible = reserve_ok and repeatability_ok

    return (
        energy,
        battery_power,
        load,
        motor_power,
        feasible
    )


L_values = np.round(
    np.arange(
        L_min,
        L_max + L_step / 2,
        L_step
    ),
    3
)

battery_values = np.round(
    np.arange(
        m_bat_min,
        m_bat_max + m_bat_step / 2,
        m_bat_step
    ),
    3
)

print("Precomputing solar power profiles...")

solar_profiles = {}

for L_test in L_values:
    solar_profiles[L_test] = np.array([
        P_sol(
            L_test, lat, h, t,
            normal, Ch, Eta_mppt
        )
        for t in times
    ])


print("Searching candidate designs...")

feasible_designs = []
all_designs = []

for L_test in L_values:
    solar_power = solar_profiles[L_test]

    for m_bat_test in battery_values:

        (
            energy,
            battery_power,
            load,
            motor_power,
            feasible
        ) = simulate_battery(
            L_test, m_bat_test, solar_power
        )

        E_min, E_max = battery_limits(m_bat_test)

        result = {
            "L": L_test,
            "m_bat": m_bat_test,
            "motor_power": motor_power,
            "load": load,
            "min_energy": float(energy.min()),
            "final_energy": float(energy[-1]),
            "day1_end_energy": float(
                energy[steps_per_day]
            ),
            "E_max": E_max,
            "E_min": E_min,
            "feasible": feasible,
        }

        all_designs.append(result)

        if feasible:
            feasible_designs.append(result)


if not feasible_designs:
    print("\nNo feasible design found within the search bounds.")

else:
    # minimum battery mass.
    best = min(
        feasible_designs,
        key=lambda d: (d["m_bat"], d["L"])
    )

    L = best["L"]
    m_bat = best["m_bat"]

    print("\n========== OPTIMAL DESIGN ==========")
    print(f"Wingspan:              {L:.2f} m")
    print(f"Battery mass:          {m_bat:.2f} kg")
    print(f"Battery capacity:      {best['E_max']:.1f} Wh")
    print(f"Minimum reserve:       {best['E_min']:.1f} Wh")
    print(f"Motor power:           {best['motor_power']:.2f} W")
    print(f"Total electrical load: {best['load']:.2f} W")
    print(f"Minimum energy:        {best['min_energy']:.1f} Wh")
    print(f"Energy after 24 h:     {best['day1_end_energy']:.1f} Wh")
    print(f"Energy after 48 h:     {best['final_energy']:.1f} Wh")
    print(f"Feasible designs:      {len(feasible_designs)}")
    print(f"Designs tested:        {len(all_designs)}")


    P_solar = solar_profiles[L]

    (
        E_battery,
        P_battery,
        P_load,
        P_motor,
        feasible
    ) = simulate_battery(L, m_bat, P_solar)

    plot_results(
        times=times,
        P_solar=P_solar,
        P_motor=P_motor,
        P_load=P_load,
        P_battery=P_battery,
        E_battery=E_battery,
        E_max=best["E_max"],
        reserve_fraction=reserve_fraction
    )
