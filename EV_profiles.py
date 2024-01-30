import numpy as np
import matplotlib.pyplot as plt

charg_start_time_prob = np.array([1.32, 1.15, 0.982, 0.635, 0.0867, 0.144, 0.115, 0.0867, 0.0578, 0, 0.0867, 0.115,
                                  0.115, 0.0578, 0, 0.0578,
                                  0.0578, 0.0578, 0.0578, 0, 0.0578, 0, 0, 0.0578, 0.115, 0.202, 0.231, 0.231, 0.433,
                                  0.404, 0.491, 0.606, 0.433, 0.606, 0.578, 1.09, 0.982, 0.783, 0.783, 0.664, 0.664,
                                  0.693, 0.606, 0.838, 0.693, 0.78, 0.953, 0.780, 0.780, 0.780, 1.01, 0.867, 1.04,
                                  0.895, 1.069, 1.01, 0.751, 0.924, 1.04, 0.924, 1.01, 1.01, 1.27, 1.38, 1.18, 1.41,
                                  1.76, 1.82, 2.34, 2.63, 3.06, 3.41, 3.21, 3.06, 2.54, 2.34, 2.57, 2.83, 2.39, 2.6,
                                  2.48, 2.22, 2.51, 2.37, 2.63, 2.83, 1.79, 2.22, 2.42, 2.05, 1.70, 1.21])

charg_duration_prob = np.array([0.1443678, 0.2206897, 0.275862, 0.1848277, 0.0845977, 0.03954016, 0.03402294, 0.0229885,
                                0.01747126, 0.01103448, 0.00367816])

charg_duration_prob = np.array([0.1443678, 0.2206897, 0.275862, 0.1848277, 0.0845977, 0.03954016, 0.03402294, 0.0229885,
                                0.01747126, 0.01103448, 0.00367816])


# res = np.array([0.25, 0.20, 0.18, 0.18, 0.18, 0.24, 0.41, 0.61, 0.63, 0.63, 0.67, 0.60, 0.72, 0.65, 0.56, 0.49, 0.46,    
#                 0.64, 0.80, 0.91, 0.81, 0.60, 0.56, 0.38, 0.38])
# plt.plot(list(range(0, len(res))), res)
# plt.title("Distribuição de probabilidade para início do carregamento")
# plt.show()


# plt.plot(list(range(1, len(charg_duration_prob)+1)), charg_duration_prob)
# plt.title("Distribuição de probabilidade para tempo de carregamento")
# plt.show()

# np.random.seed(17)

normalized_st_prob = charg_start_time_prob/np.sum(charg_start_time_prob)
normalized_cd_prob = charg_duration_prob/np.sum(charg_duration_prob)

# Capacidade da bateria (kWh)
C = 44.9

# Potência do carregador (kW)
P_charg = 6.6

def new_EV(dss, i):
    start_time = np.random.choice(list(range(1, 93)), p=normalized_st_prob, size=1) # type: ignore
    charg_duration = np.random.choice(list(range(1, len(charg_duration_prob)+1)), p=normalized_cd_prob, size=1) # type: ignore
    # print(f"Inicio do carregamento ={start_time}")
    # print(f"Duração do carregamento: {charg_duration}")
    init_time = start_time * 15 / 60
    SOC = 1 - (charg_duration * P_charg * 0.8) / C
    SOC_init = SOC
    if SOC < 0.2:
        SOC = 0.2

    lv_buses = list()
    buses = dss.circuit_all_bus_names()
    for bus in buses:
        dss.circuit_set_active_bus(bus)
        if bus == "sourcebus":
            pass
        elif bus == "799":
            pass
        elif bus == "bess":
            pass
        elif dss.bus_kv_base() <= 1:
            lv_buses.append(bus)

    nodes = list([1, 2, 3])
    bus = np.random.choice(lv_buses, size=1)
    node1 = np.random.choice(nodes, size=1) # type: ignore
    nodes.remove(node1)
    node2 = np.random.choice(nodes, size=1) # type: ignore

    dss.text(f"New Storage.EV{i} kwrated=6.6 kwhrated=44.9 kv=0.22 phases=2 conn=wye "
             f"bus1={int(bus)}.{int(node1)}.{int(node2)} %stored={int(SOC_init*100)} state=idling dispmode=external pf=0.98")

    return start_time

def new_reg_control(dss, bus1, bus2, bus3, i):
    dss.text(f"New Transformer.reg{i}a phases=1 xhl=0.1 kVAs=(500 500) buses=({bus1}.1 {bus1}r.1) "
             f"kVs=({4.8/1.732} {4.8/1.732}) %loadloss=0.01 conns=(wye wye)")
    dss.text(f"New RegControl.Regc{i}a transformer=reg{i}a winding=2 band=2 vreg=45.5 ptratio=60 bus={bus3}")

    dss.text(f"New Transformer.reg{i}b phases=1 xhl=0.1 kVAs=(500 500) buses=({bus1}.2 {bus1}r.2) "
             f"kVs=({4.8/1.732} {4.8/1.732}) "
             f"%loadloss=0.01 conns=(wye wye)")
    dss.text(f"New RegControl.Regc{i}b transformer=reg{i}b winding=2 band=2 vreg=45.5 ptratio=60 bus={bus3}")

    dss.text(f"New Transformer.reg{i}c phases=1 xhl=0.1 kVAs=(500 500) buses=({bus1}.3 {bus1}r.3) "
             f"kVs=({4.8/1.732} {4.8/1.732}) "
             f"%loadloss=0.01 conns=(wye wye)")
    dss.text(f"New RegControl.Regc{i}c transformer=reg{i}c winding=2 band=2 vreg=45.5 ptratio=60 bus={bus3}")

    dss.lines_first()
    for _ in range(dss.lines_count()):
        if dss.lines_read_phases() == 3:
            dss.circuit_set_active_element(f"line.{dss.lines_read_name()}")
            # print(dss.cktelement_read_bus_names())
        if dss.cktelement_read_bus_names() == [f"{bus1}.1.2.3", f"{bus2}.1.2.3"]:
            dss.text(f"BatchEdit {dss.cktelement_name()} bus1={bus1}r.1.2.3")
        dss.lines_next()

def volt_var(dss, lista):
    x_vv_curve = "[0.5 0.92 0.98 1.0 1.02 1.08 1.5]"
    y_vv_curve = "[1 1 0 0 0 -1 -1]"
    dss.text(f"new XYcurve.volt-var_catb_curve npts=7 yarray={y_vv_curve} xarray={x_vv_curve}")
    dss.text(f"new invcontrol.inv mode=voltvar voltage_curvex_ref=rated vvc_curve1=volt-var_catb_curve "
             f"RefReactivePower=VARMAX voltagechangetolerance=0.2 varchangetolerance=0.2 DERList={lista}")
