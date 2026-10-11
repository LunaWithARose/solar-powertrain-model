import math
import numpy as np

from solarpy import irradiance_on_plane
from datetime import datetime

lat = 46.73   #latitude of flight(degrees)
h = 100       #altitude(M)
date_time = datetime(2027, 6, 15, 12, 0) #date, Y-M-D-H-M
normal = np.array([0,0,-1])   #North-East-Down normal vector
Ch = 0.3             #Chord(M)
Eta_mppt = 0.85      #(X)Mppt efficency, model later?
C_L = 0.8            #Coeff of lift
C_D = 0.17           #(Y)Coeff of drag, need to add parasitic and induced drag


Eta_stc_sm = 0.237   #(Y)Standard Testing Condition solar conversion efficency, need to look at data sheet
Ep_I_sm = 1.0        #(Y)Iradiance efficency, again data sheet, need to model
Ep_T_sm = 1.0        #(Y)Temperature efficency, need to model
Ep_cbr_sm = 0.97     #Wing Chamber Efficency, V1 results
Eta_prop = 1.0       #(X)Prop, Esc, Motor effiency, need to test

m_rest = 2.0         #(X)Estimate fusulage + tail weight(Kg)
m_L = 2.0            #(X)Mass of layup, per meter, without batteries(Kg)
P_av = 2.0           #(X)Power consumption of avionics(servos, flight controller ect) (W)
P_pld = 0.0          #(X)Power consuption  of payload(Remote id, leds, fpv ect) (W)

L = 6.0              #Length of wing(M)         This will be a variable that will be optimized
m_bat = 3.5          #Weight of batteries(Kg)   This will be a veriable that will be optimized 





def P_sol(L, lat, h, date_time, normal, Ch, Eta_mppt):
    """Calculate solar electrical power output (W)."""

    irradiance = irradiance_on_plane(
        lat, h, date_time, normal
    )

    panel_area = Ch * L * 0.85  # 85% of wing area covered by solar cells

    return irradiance * panel_area * Eta_sm() * Eta_mppt


def P_level(L, m_bat, C_D, C_L, m_L, m_rest, h, Ch):
    """Calculate minimum level-flight power (W)."""

    total_mass = (2 * (m_L * L)) + m_bat + m_rest
    wing_area = Ch * L

    return (
        C_D / (C_L ** (3 / 2))
        * (
            (total_mass * 9.81) ** 3
            / (rho(h) * wing_area)
            * 2
        ) ** (1 / 2)
    )


def Eta_sm():
    """Calculate combined solar-module efficiency."""

    return (
        Eta_stc_sm
        * Ep_I_sm
        * Ep_T_sm
        * Ep_cbr_sm
    )


def rho(h):
    """Calculate air density."""

    # Sea-level constants
    P0 = 101325.0       # Sea-level pressure (Pa)
    T0 = 288.15         # Sea-level temperature (K)
    lapse_rate = 0.0065  # Temperature lapse rate (K/m)
    R = 287.05          # Specific gas constant for dry air (J/(kg·K))
    g = 9.81            # Gravitational acceleration (m/s²)

    # Atmospheric temperature
    T = T0 - lapse_rate * h

    # Atmospheric pressure
    exponent = g / (lapse_rate * R)
    P = P0 * (1 - (lapse_rate * h / T0)) ** exponent

    # Air density
    air_density = P / (R * T)

    return air_density



dE_bat_dt = P_sol(L, lat, h, date_time, normal, Ch, Eta_mppt) - (P_level(L, m_bat, C_D, C_L, m_L, m_rest, h, Ch) / Eta_prop) - P_av - P_pld
