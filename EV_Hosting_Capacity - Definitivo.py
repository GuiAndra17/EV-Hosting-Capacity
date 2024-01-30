import py_dss_interface
import pandas as pd
import EV_profiles
import matplotlib.pyplot as plt
import numpy as np

dss = py_dss_interface.DSSDLL()

dss_file = r"C:\Users\Particular\Desktop\TCC\37Bus\ieee37.dss"

dss.text(f"compile [{dss_file}]")

j = 0
Sobretensao = False
Subtensao = False
Sobrecarga = False
tensao = pd.DataFrame()
corrente = pd.DataFrame()
trafos_current = pd.DataFrame()
lines_names = list()
trafos_names = list()
qtde_EVs = list()
ckt_power = list()
ckt_power_var = list()
stg_list = list()
init_time_vect = pd.DataFrame(columns=['A'])
init_time_vect_drop = pd.DataFrame(columns=['A'])

dss.lines_first()
k = 0
options = dss.circuit_all_bus_names()
options.remove('sourcebus')
options.remove('799')
node = list()

for _ in range(dss.lines_count()):
    dss.circuit_set_active_class('line')
    num_phases = dss.cktelement_num_phases()
    for phase in range(1, num_phases + 1):
        lines_names.append(f"{dss.cktelement_name()}.{dss.cktelement_node_order()[phase-1]}")
    dss.lines_next()


###################### DEFINIÇÃO DOS PARÂMETROS DA SIMULAÇÃO ####################################
BESS_centralizado = True
BESS_distribuido = False
BESS_control = True
RegV = False
#################################################################################################

while not Subtensao and not Sobretensao and not Sobrecarga:
# while j < 1000:
    
    soc = list()
    power_bat = list()
    ckt_power = list()
    ckt_power_var = list()
    stg_list = list()
    v_min_list = list()
    v_max_list = list()
    flag_ol = 0
    flag_uv = 0
    flag_ov = 0
    total_daily_losses_kw = 0
    max_overload = 0
    max_ov_daily = list()

    dss_file = r"C:\Users\Particular\Desktop\TCC\37Bus\ieee37.dss"

    dss.text(f"compile [{dss_file}]")

    dss.text(f"Set mode = daily")
    dss.text(f"Set stepsize = 0.25h")
    dss.text(f"Set number = 1")
   
    # dss.text("Batchedit Load..* daily=residencial")

    w = 0
    for bus in options:

        dss.text(f"New Transformer.trafo{w} Phases=3 Windings=2 Xhl=5 "
                 f"wdg=1 bus={bus} conn=Delta kv=4.8  kva=100 "
                 f"wdg=2 bus={w} conn=Wye kv=0.22  kva=100")
        
        if BESS_centralizado == True and bus == '701':
            dss.text(f"New Transformer.trafoBESS Phases=3 Windings=2 Xhl=5 "
                    f"wdg=1 bus={bus} conn=Delta kv=4.8  kva=800 "
                    f"wdg=2 bus=BESS conn=Wye kv=0.22  kva=800")
            for i in range(35):
                nodes = list([1, 2, 3])
                node1 = np.random.choice(nodes, size=1) # type: ignore
                nodes.remove(node1) # type: ignore
                node2 = np.random.choice(nodes, size=1) # type: ignore
                dss.text(f"New Storage.Stg{i} kwrated=20 kwhrated=80 kv=0.22 phases=2 conn=wye "
                         f"bus1=BESS.{int(node1)}.{int(node2)} state=idling %stored=20 %reserve=20 dispmode=external")
        elif BESS_distribuido == True:
            nodes = list([1, 2, 3])
            node1 = np.random.choice(nodes, size=1) # type: ignore
            nodes.remove(node1)  # type: ignore
            node2 = np.random.choice(nodes, size=1) # type: ignore
            dss.text(f"New Storage.Stg{w} kwrated=20 kwhrated=80 kv=0.22 phases=2 conn=wye kvarMaxAbs=0 "
                     f"bus1={w}.{int(node1)}.{int(node2)} state=idling %stored=20 %reserve=20 dispmode=external")
        w += 1

    if RegV == True:
        dss.text(f"New RegControl.Reg_suba bus=702.1 transformer=SubXF band=2 vreg=46.4 ptratio=60 "
                f"winding=2 debugtrace=no")
        dss.text(f"New RegControl.Reg_subb bus=702.2 transformer=SubXF band=2 vreg=46.4 ptratio=60 "
                f"winding=2 debugtrace=no")
        dss.text(f"New RegControl.Reg_subc bus=702.3 transformer=SubXF band=2 vreg=46.4 ptratio=60 "
                f"winding=2 debugtrace=no")

    dss.text("Set voltagebases = [230, 4.8, 0.22]")
    dss.text("CalcVoltageBases")
    dss.text("set maxcontroliter=1000")

    k = 0
    while k < j:
        init_time = EV_profiles.new_EV(dss, k)
        init_time_vect.loc[k] = init_time # type: ignore
        k += 1
    init_time_vect_drop = init_time_vect.copy()
    j += 50

    EV_list = list()
    dss.circuit_set_active_class('Storage')
    for stg in dss.active_class_all_names():
            if 'stg' in stg:
                stg_list.append(stg)
    for stg in dss.active_class_all_names():
            if 'ev' in stg:
                EV_list.append(stg)

    dss.text(f"New StorageController.Stg_control element=Transformer.SubXF elementlist={stg_list} "
             f"%reserve=20 modecharge=peakshavelow kwtargetlow=2200 modedischarge=peakshave kwtarget=2200 enabled={BESS_control} monphase=avg")

    dss.circuit_set_active_class('storage')
    print("")
    print(f"Num EVs = {len(EV_list)}")
    num_ev = len(EV_list)

    for i in range(1, 92):

        # print("")
        # print("Hora =", i)
        flag = 0
        while init_time_vect_drop['A'].isin([i]).any():
            EV = init_time_vect_drop.loc[init_time_vect_drop['A'] == i].index[0]
            init_time_vect_drop = init_time_vect_drop.drop(EV)
            dss.text(f"BatchEdit Storage.ev{EV} state=charging")
        
        dss.solution_solve()
        
        total_daily_losses_kw += dss.circuit_losses()[0]/10 ** 3

        pot_atual = dss.text("? StorageController.Stg_control.kwactual")
        pot_total = dss.text("? StorageController.Stg_control.kwtotal")

        power_bat.append(-float(pot_atual))

        soc_atual = dss.text("? StorageController.Stg_control.kwhactual")
        soc_total = dss.text("? StorageController.Stg_control.kwhtotal")

        soc_atual = (float(soc_atual)/float(soc_total))*100
        soc.append(soc_atual)

        ckt_power.append(-dss.circuit_total_power()[0])
        ckt_power_var.append(-dss.circuit_total_power()[1])

        # TENSÕES NAS BARRAS
        voltages = dss.circuit_all_bus_vmag_pu()
        
        tensao[i] = pd.Series(voltages)
        v_min_list.append(min(voltages))
        v_max_list.append(max(voltages))

        if min(voltages) < 0.93:
            Subtensao = True
            if flag_uv == 0:
                print(f"Hora de subtensão: {i * 15 / 60}")
                print(f"Bus {dss.circuit_all_node_names()[voltages.index(min(voltages))]} - {min(voltages)} V")
                bus_split = dss.circuit_all_node_names()[voltages.index(min(voltages))].split(".")[0]
                dss.circuit_set_active_bus(bus_split)
                flag_uv = 1
        if max(voltages) > 1.05:
            Sobretensao = True
            if flag_ov == 0:
                print(f"Hora de sobretensao: {i * 15 / 60}")
                print(f"Bus {dss.circuit_all_node_names()[voltages.index(max(voltages))]} - {max(voltages)} V")
                bus_split = dss.circuit_all_node_names()[voltages.index(max(voltages))].split(".")[0]
                dss.circuit_set_active_bus(bus_split)
                print(dss.bus_all_pce_active_bus())
            flag_ov = 1

        # CORRENTES NAS LINHAS
        dss.lines_first()
        currents = list()
        for _ in range(dss.lines_count()):
            if dss.lines_read_phases() == 3:
                dss.circuit_set_active_element(f"line.{dss.lines_read_name()}")
                num_phases = dss.cktelement_num_phases()
                for phase in range(1, num_phases + 1):
                    currents.append(dss.cktelement_currents_mag_ang()[2 * (phase - 1)])
                if max(dss.cktelement_currents()[0:12:2]) / dss.cktelement_read_norm_amps() > max_overload:
                    max_overload = max(dss.cktelement_currents()[0:12:2]) / dss.cktelement_read_norm_amps()
                if max(dss.cktelement_currents()[0:12:2]) > dss.cktelement_read_norm_amps():
                    Sobrecarga = True
                    if flag_ol == 0:
                        print(f"Hora de sobrecorrente: {i*15/60}")
                        print(f"Element = {dss.cktelement_name()}")
                        print(f"Potência do circuito =", dss.circuit_total_power()[0])
                        flag_ol = 1
            dss.lines_next()

        corrente[i] = pd.Series(currents)

        # CORRENTES NOS TRANSFORMADORES
        currents = list()
        for element in dss.circuit_all_element_names():
            if "Transformer" in element:
                dss.circuit_set_active_element(element)
                num_phases = dss.cktelement_num_phases()
                for phase in range(1, num_phases + 1):
                    currents.append(dss.cktelement_currents_mag_ang()[2 * (phase - 1)])
                    phase_current = dss.cktelement_currents_mag_ang()[2 * (phase - 1)]
                    if phase_current / dss.cktelement_read_norm_amps() > max_overload:
                                max_overload = phase_current / dss.cktelement_read_norm_amps()
                    if phase_current > dss.cktelement_read_norm_amps():
                        Sobrecarga = True
                        
                        if flag_ol == 0:
                            print(f"Hora de sobrecorrente: {i*15/60}")
                            print(f"Element = {dss.cktelement_name()}")
                            print(f"Potência do circuito =", dss.circuit_total_power()[0])
                            flag_ol = 1

        max_ov_daily.append((max_overload)*100)
        trafos_current[i] = pd.Series(currents)
        # print("")

    hour_vect = np.arange(1, len(ckt_power)+1)
    hour_vect = hour_vect*15/60

    print("Perdas totais =", total_daily_losses_kw)

    # dss.circuit_set_active_class("Storage")
    # plt.subplot(2, 2, 1)
    # plt.plot(hour_vect, ckt_power, label='Active Power', color='green')
    # plt.title(f"Equilíbrio de Potência do Sistema - {len(EV_list)} EVs")
    # plt.xlabel("Hora [h]")
    # plt.legend(loc='upper left')
    # plt.ylabel("Potência [kW]")
    # plt.grid()

    dss.circuit_set_active_class("Storage")
    plt.subplot(2, 2, 1)
    plt.plot(hour_vect, max_ov_daily, color='red')
    plt.title(f"Nível de Carga Máximo - {len(EV_list)} VEs")
    plt.xlabel("Hora [h]")
    plt.yticks([0, 20, 40, 60, 80, 100, 120, 140]) # type: ignore
    # plt.legend(loc='upper left')
    plt.ylabel("Carga Máxima [%]")
    plt.grid()

    plt.subplot(2, 2, 2)
    plt.plot(hour_vect, v_min_list, label='Tensão Mínima', color='blue')
    plt.plot(hour_vect, v_max_list, label='Tensão Máxima', color='red')
    plt.title(f"Tensões máximas e mínimas do sistema")
    plt.xlabel("Hora [h]")
    plt.legend(loc='upper right')
    plt.ylabel("Tensão [pu]")
    plt.yticks([0.91, 0.93, 0.95, 0.97, 0.99, 1.01, 1.03, 1.05]) # type: ignore
    plt.grid()
    print("Vmin =", min(v_min_list))
    
    soc_total = dss.text("? StorageController.Stg_control.kwhtotal")
    plt.subplot(2, 2, 3)
    plt.plot(hour_vect, soc, color='green')
    plt.title(f"SOC Geral das Baterias de Suporte - {soc_total} kWh TOTAL")
    plt.xlabel("Hora [h]")
    plt.yticks([0, 20, 40, 60, 80, 100]) # type: ignore
    # plt.legend(loc='upper left')
    plt.ylabel("SOC [%]")
    plt.grid()

    pot_total = dss.text("? StorageController.Stg_control.kwtotal")
    plt.subplot(2, 2, 4)
    plt.plot(hour_vect, power_bat, color='green')
    plt.title(f"Potência Total das Baterias de Suporte - {pot_total} kW TOTAL")
    plt.xlabel("Hora [h]")
    plt.yticks([-700, -500, -300, -100, 0, 100, 300, 500, 700]) # type: ignore
    # plt.legend(loc='upper right')
    plt.ylabel("Potência [kW]")
    plt.grid()

    plt.show()

node_names = dss.circuit_all_node_names()

dss.transformers_first()
for _ in range(dss.transformers_count()):
    num_phases = dss.cktelement_num_phases()
    if num_phases == 1:
        dss.circuit_set_active_element(f"transformer.{dss.transformers_read_name()}")
        read_bus = dss.cktelement_read_bus_names()[0]
        node_split = read_bus.split(".")[1]
        trafos_names.append(f"{dss.transformers_read_name()}.{node_split}")
    else:
        for phase in range(1, num_phases + 1):
            trafos_names.append(f"{dss.transformers_read_name()}.{phase}")
    dss.transformers_next()

dss.text("plot circuit Power max=2000 n n C1=$00FF0000")
tensao.index = node_names # type: ignore
corrente.index = lines_names  # type: ignore
trafos_current.index = trafos_names # type: ignore
