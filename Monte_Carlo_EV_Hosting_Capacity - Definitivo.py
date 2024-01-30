import py_dss_interface
import pandas as pd
import EV_profiles
import matplotlib.pyplot as plt
import random
import numpy as np

dss = py_dss_interface.DSSDLL()

dss_file = r"C:\Users\Particular\Desktop\TCC\37Bus\ieee37.dss"

dss.text(f"compile [{dss_file}]")

v_threshold = 0.95
kva_to_kw = 1
pf = 1
ol_max = 0
num_phases = 0
is_in = 0
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
charging = list()
discharging = list()
idling = list()
init_time_vect = pd.DataFrame(columns=['A'])
init_time_vect_drop = pd.DataFrame(columns=['A'])
dss.lines_first()
k = 0
options = dss.circuit_all_bus_names()
options.remove('sourcebus')
options.remove('799')

df_tensao = pd.DataFrame()
df_overload = pd.DataFrame()
df_active_losses = pd.DataFrame()

for _ in range(dss.lines_count()):
    dss.circuit_set_active_class('line')
    num_phases = dss.cktelement_num_phases()
    for phase in range(1, num_phases + 1):
        lines_names.append(f"{dss.cktelement_name()}.{dss.cktelement_node_order()[phase-1]}")
    dss.lines_next()

total_daily_losses_kw = 0

BESS_centralizado = True
BESS_distribuido = False
BESS_control = True
RegV = True

ev_penetration = 0
Mont_C = 0
# while not Subtensao and not Sobretensao and not Sobrecarga:
while ev_penetration < 500:

    j += 50
    Mont_C = 0
    # print(j)

    while Mont_C < 5:

        soc = list()
        power_bat = list()
        ckt_power = list()
        ckt_power_var = list()
        stg_list = list()
        v_min_list = list()
        v_max_list = list()
        max_overload = 0
        flag_ol = 0
        flag_uv = 0
        flag_ov = 0
        total_daily_losses_kw = 0
        
        # print("MC=",Mont_C)

        dss_file = r"C:\Users\Particular\Desktop\TCC\37Bus\ieee37.dss"

        dss.text(f"compile [{dss_file}]")

        dss.text(f"Set mode = daily")
        dss.text(f"Set stepsize = 0.25h")
        dss.text(f"Set number = 1")

        # dss.text("Batchedit Load..* daily=residencial")

        w = 0
        for bus in options:

            dss.text(f"New Transformer.trafo{w} Phases=3 Windings=2 Xhl=5 "
                    f"wdg=1 bus={bus} conn=Delta kv=4.8  kva=150 "
                    f"wdg=2 bus={w} conn=Wye kv=0.22  kva=150")
            
            if BESS_centralizado == True and bus == '701':
                dss.text(f"New Transformer.trafoBESS Phases=3 Windings=2 Xhl=5 "
                        f"wdg=1 bus={bus} conn=Delta kv=4.8  kva=800 "
                        f"wdg=2 bus=BESS conn=Wye kv=0.22  kva=800")
                for i in range(35):
                    nodes = list([1, 2, 3])
                    node1 = np.random.choice(nodes, size=1) # type: ignore
                    nodes.remove(node1) # type: ignore
                    node2 = np.random.choice(nodes, size=1) # type: ignore
                    dss.text(f"New Storage.Stg{i} kwrated=20 kwhrated=80 kv=0.22 phases=2 conn=wye kvarMaxAbs=0 "
                             f"bus1=BESS.{int(node1)}.{int(node2)} state=idling %stored=30 %reserve=20 dispmode=external")
            elif BESS_distribuido == True:
                nodes = list([1, 2, 3])
                node1 = np.random.choice(nodes, size=1) # type: ignore
                nodes.remove(node1) # type: ignore
                node2 = np.random.choice(nodes, size=1) # type: ignore
                dss.text(f"New Storage.Stg{w} kwrated=20 kwhrated=80 kv=0.22 phases=2 conn=wye kvarMaxAbs=0 "
                        f"bus1={w}.{int(node1)}.{int(node2)} state=idling %stored=30 %reserve=20 dispmode=external")
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

        EV_list = list()
        dss.circuit_set_active_class('Storage')
        for stg in dss.active_class_all_names():
                if 'stg' in stg:
                    stg_list.append(stg)
        for stg in dss.active_class_all_names():
                if 'ev' in stg:
                    EV_list.append(stg)

        dss.circuit_set_active_class('storage')
        print("")
        print(f"EVs={len(EV_list)}/MC={Mont_C}")
        num_ev = len(EV_list)
        
        dss.text(f"New StorageController.Stg_control element=Transformer.SubXF elementlist={stg_list} "
                 f"%reserve=20 modecharge=peakshavelow kwtargetlow=2200 modedischarge=peakshave kwtarget=2200 enabled={BESS_control} monphase=avg")

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
                    if max(dss.cktelement_currents()[0:12:2]) > dss.cktelement_read_norm_amps():
                        Sobrecarga = True
                        if max(dss.cktelement_currents()[0:12:2]) / dss.cktelement_read_norm_amps() > max_overload:
                            print(dss.cktelement_name())
                            max_overload = max(dss.cktelement_currents()[0:12:2]) / dss.cktelement_read_norm_amps()
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
                        if phase_current > dss.cktelement_read_norm_amps():
                            Sobrecarga = True
                            if phase_current / dss.cktelement_read_norm_amps() > max_overload:
                                max_overload = phase_current / dss.cktelement_read_norm_amps()
                            if flag_ol == 0:
                                print(f"Hora de sobrecorrente: {i*15/60}")
                                print(f"Element = {dss.cktelement_name()}")
                                print(f"Potência do circuito =", dss.circuit_total_power()[0])
                                flag_ol = 1

            trafos_current[i] = pd.Series(currents)
            # print("")

        # hour_vect = np.arange(1, len(ckt_power)+1)
        # hour_vect = hour_vect*15/60

        # print("Perdas totais =", total_daily_losses_kw)
        # print("Tamanho da lista de espera =", len(waiting_list))
        # print("Lista de espera =", waiting_list)

        # dss.circuit_set_active_class("Storage")
        # plt.subplot(2, 2, 1)
        # plt.plot(hour_vect, ckt_power, label='Active Power', color='green')
        # plt.title(f"Equilíbrio de Potência do Sistema - {dss.active_class_num_elements()-35} EVs")
        # plt.xlabel("Hora [h]")
        # plt.legend(loc='upper left')
        # plt.ylabel("Potência [kW]")
        # plt.grid()

        # plt.subplot(3, 2, 2)
        # plt.plot(hour_vect, v_min_list, label='Tensão Mínima', color='blue')
        # plt.plot(hour_vect, v_max_list, label='Tensão Máxima', color='red')
        # plt.title(f"Tensões máximas e mínimas do sistema")
        # plt.xlabel("Hora [h]")
        # plt.legend(loc='upper left')
        # plt.ylabel("Tensão [pu]")
        # plt.grid()
        
        # soc_total = dss.text("? StorageController.Stg_control.kwhtotal")
        # plt.subplot(2, 2, 3)
        # plt.plot(hour_vect, soc, label='SOC', color='green')
        # plt.title(f"SOC Geral das Baterias de Suporte - {soc_total} kWh TOTAL")
        # plt.xlabel("Hora [h]")
        # plt.legend(loc='upper left')
        # plt.ylabel("SOC [%]")
        # plt.grid()

        # pot_total = dss.text("? StorageController.Stg_control.kwtotal")
        # plt.subplot(2, 2, 4)
        # plt.plot(hour_vect, power_bat, label='Battery Power', color='green')
        # plt.title(f"Potência Total das Baterias de Suporte - {pot_total} kW TOTAL")
        # plt.xlabel("Hora [h]")
        # plt.legend(loc='upper right')
        # plt.ylabel("Potência [kW]")
        # plt.grid()

        # plt.show()
        
        ######################### FIM DO DIA ####################################
        if Mont_C == 0:
            df_tensao[k] = pd.Series(min(v_min_list))
            if max_overload != 0:
                df_overload[k] = pd.Series((max_overload-1)*100)
            else:
                df_overload[k] = pd.Series(max_overload)
            df_active_losses[k] = pd.Series(total_daily_losses_kw)
        else:
            df_tensao.loc[Mont_C, k] = min(v_min_list)
            if max_overload != 0:
                df_overload.loc[Mont_C, k] = (max_overload-1)*100
            else:
                df_overload.loc[Mont_C, k] = max_overload
            df_active_losses.loc[Mont_C, k] = total_daily_losses_kw
        Mont_C += 1
        
    ev_penetration += 50

df_tensao.to_csv("dados_tensao.csv")
df_overload.to_csv("dados_sobrecarga.csv")
df_active_losses.to_csv("dados_perdas.csv")

df_overload.boxplot()
plt.title("Sobrecarga")
plt.xlabel("Quantidade de VEs")
# plt.legend(loc='upper left')
plt.ylabel("Sobrecarga [%]")
plt.yticks(np.array([0, 10, 20, 30, 40, 50]))
plt.show()

df_tensao.boxplot()
plt.title("Tensão")
plt.xlabel("Quantidade de VEs")
# plt.legend(loc='upper right')
plt.ylabel("Tensão [pu]")
plt.yticks(np.array([0.85, 0.87, 0.89, 0.91, 0.93, 0.95]))
plt.show()

df_active_losses.boxplot()
plt.title("Perdas")
plt.xlabel("Quantidade de VEs")
plt.yticks(np.array([4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500]))
# plt.legend(loc='upper left')
plt.ylabel("Perdas [kW]")
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
