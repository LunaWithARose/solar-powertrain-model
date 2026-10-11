import math
import numpy as np

from solarpy import irradiance_on_plane
from datetime import datetime

lat = 46.73   #latitude of flight(degrees)
h = 100       #altitude(M)
date_time = datetime(2027, 6, 15, 12, 0) #date, Y-M-D-H-M
normal = np.array([0,0,-1])   #North-East-Down normal vector
Ch = 0.3             #Chord(M)
Eta_mppt = 0.85      #Mppt efficency, model later?
C_L = 0.8            #Coeff of lift
C_D = 0.17           #Coeff of drag, need to add parasitic and induced drag


Eta_stc_sm = 0.237   #Standard Testing Condition solar conversion efficency, need to look at data sheet
Ep_I_sm = 1.0        #Iradiance efficency, again data sheet, need to model
Ep_T_sm = 1.0        #Temperature efficency, need to model
Ep_cbr_sm = 0.97     #Wing Chamber Efficency, V1 results
Eta_prop = 1.0       #Prop, Esc, Motor effiency, need to test

m_rest = 2.0         #Estimate fusulage + tail weight(Kg)
m_L = 2.0            #Mass of layup, per meter, without batteries(Kg)
P_av = 2.0           #Power consumption of avionics(servos, flight controller ect) (W)
P_pld = 0.0          #Power consuption  of payload(Remote id, leds, fpv ect) (W)

L = 6.0              #Length of wing(M)
m_bat = 3.5          #Weight of batteries(Kg)




def P_sol(L, lat, h, date_time, normal, Ch, Eta_mppt):
    return irradiance_on_plane(lat, h, date_time, normal) * (Ch * L * 0.85) * Eta_sm() * Eta_mppt    #0.85 is percentage of area covered by solar cells

def P_level(L, m_bat, C_D, C_L, m_L, m_rest, h, Ch):
    return (C_D/(C_L ** (3/2))) * ((((((2 * (m_L * L)) + m_bat + m_rest) * 9.81) ** 3) / (rho(h) * Ch * L)) ** (1/2))

def Eta_sm():
    return Eta_stc_sm * Ep_I_sm * Ep_T_sm * Ep_cbr_sm

def rho(h):
    # Sea-level constants
    P0 = 101325.0       # Standard sea-level atmospheric pressure (Pa)
    T0 = 288.15         # Standard sea-level temperature (K)
    L = 0.0065          # Temperature lapse rate (K/m)
    R = 287.05          # Specific gas constant for dry air (J/(kg·K))

    T = T0 - L * h
    exponent = 9.81 / (L * R)
    P = P0 * (1.0 - (L * h) / T0) ** exponent
    rho = P / (R * T)
    
    return rho


dE_bat_dt = P_sol(L, lat, h, date_time, normal, Ch, Eta_mppt) - (P_level(L, m_bat, C_D, C_L, m_L, m_rest, h, Ch) / Eta_prop) - P_av - P_pld
