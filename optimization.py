import numpy as np
from datetime import timedelta, datetime
import csv

from functions import P_sol, P_level, dE_bat_dt, simulate_battery, battery_limits
from power_time import plot_results
from battery_wingspan import plot_design_space



def optimize(date_time, dt_hours, p, L_step, m_bat_step, normal, lat, h, n_steps, m_bat, L):

    times = [
        date_time + timedelta(hours=k * dt_hours)
        for k in range(n_steps + 1)
    ]

    # Index for comparing the same time on consecutive days
    steps_per_day = int(round(24.0 / dt_hours))

    L_values = np.round(
        np.arange(
            p['L_min'],
            p['L_max'] + L_step / 2,
            L_step
        ),
        3
    )

    battery_values = np.round(
        np.arange(
            p['m_bat_min'],
            p['m_bat_max'] + m_bat_step / 2,
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
                normal, p
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
                    solar_power,
                    times,
                    n_steps,
                    dt_hours,
                    steps_per_day,
                    p,
                    m_bat_test,
                    L_test,
                    h
                )

            E_min, E_max = battery_limits(p, m_bat_test)

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

        E_max = best["E_max"]

        return (P_solar, L, m_bat, times, E_max)