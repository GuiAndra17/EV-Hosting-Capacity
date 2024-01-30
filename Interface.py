import importlib
import matplotlib.pyplot as plt
import pandas as pd
from customtkinter import *
import py_dss_interface
import colorama as clm
import numpy as np

dss = py_dss_interface.DSSDLL()
dados = importlib.import_module('EV_Hosting_Capacity - Definitivo')

def highlight_value(value, parametro, set):
    if set == 1:
        if value > parametro:
            value = f' {clm.Fore.RED}{value}{clm.Style.RESET_ALL}'
            return value
        else:
            value = f'{clm.Style.RESET_ALL}{value}{clm.Style.RESET_ALL}'
            return value
    elif set == 2:
        if value < parametro:
            value = f' {clm.Fore.RED}{value}{clm.Style.RESET_ALL}'
            return value
        else:
            value = f'{clm.Style.RESET_ALL}{value}{clm.Style.RESET_ALL}'
            return value

def report(info, parametro, set):
    info_marked = info.applymap(lambda value: highlight_value(value, parametro, set))
    print(info_marked.to_string())
    print()


def plota(matriz, indice, nome, nodes, variavel, parametro, set):
    time = list(range(1, 92))
    time = np.array(time)*0.25
    info = pd.DataFrame()

    if variavel == "tensao":
        plt.figure()
        plt.title(f'Bus {nome}')
        plt.grid()
        plt.xlabel("Tempo [h]")
        plt.ylabel("Vmag [pu]")

    elif variavel == "corrente":
        plt.figure()
        plt.title(f'{nome} - normamps = {parametro}')
        plt.grid()
        plt.xlabel("Tempo [h]")
        plt.ylabel("Corrente [A]")

    for i in range(nodes):
        plt.plot(time, matriz.iloc[indice + i], label=i+1)
        plt.legend()
        info[i] = pd.Series(matriz.iloc[indice + i])

    # print(nome)
    # report(info, parametro, set)
    plt.show()


def show_volt(volt):
    m = 0
    n = 0

    janela = CTk()
    janela.title("Tensões nas Barras")

    frame1 = CTkFrame(master=janela)
    frame1.pack(pady=5, padx=60, fill="both", expand=True)

    for j in range(len(dss.circuit_all_bus_names())):
        dss.circuit_set_active_bus(dss.circuit_all_bus_names()[j])
        flag = 0

        num_phases = dss.bus_num_nodes()
        index = volt.index.get_loc(f'{dss.bus_name()}.{dss.bus_nodes()[0]}')

        for i in range(1, 92):
            for k in range(num_phases):
                if volt.iloc[index + k, i - 1] > 1.05:
                    flag = 1
                elif volt.iloc[index + k, i - 1] < 0.95:
                    flag = 2
            if flag == 1 or flag == 2:
                break

        if flag == 1:
            button = CTkButton(master=frame1, text=dss.bus_name(),
                               command=lambda idx=index, n_nodes=dss.bus_num_nodes(), nome=dss.bus_name(),
                                              parametro=1.05:
                               plota(volt, idx, nome, n_nodes, "tensao", parametro, 1), fg_color='red')
        elif flag == 2:
            button = CTkButton(master=frame1, text=dss.bus_name(),
                               command=lambda idx=index, n_nodes=dss.bus_num_nodes(), nome=dss.bus_name(),
                                              parametro=0.95:
                               plota(volt, idx, nome, n_nodes, "tensao", parametro, 2), fg_color='blue')
        else:
            button = CTkButton(master=frame1, text=dss.bus_name(),
                               command=lambda idx=index, n_nodes=dss.bus_num_nodes(), nome=dss.bus_name(),
                                              parametro=1.05:
                               plota(volt, idx, nome, n_nodes, "tensao", parametro, 1), fg_color='green')

        if j % 15 == 0:
            m += 1
            n = 0
        button.grid(row=n, column=m, pady=5, padx=5)
        n += 1

    janela.mainloop()


def show_currents(correntes):
    m = 0
    n = 0

    janela = CTk()
    janela.title("Correntes nas Linhas")

    frame1 = CTkFrame(master=janela)
    frame1.pack(pady=5, padx=60, fill="both", expand=True)

    dss.lines_first()
    for j in range(dss.lines_count()):
        dss.circuit_set_active_element(f'line.{dss.lines_read_name()}')
        flag = 0

        num_phases = dss.lines_read_phases()
        index = correntes.index.get_loc(f'Line.{dss.lines_read_name()}.{dss.cktelement_node_order()[0]}')

        for i in range(1, 92):
            for k in range(num_phases):
                if correntes.iloc[index + k, i - 1] > dss.lines_read_norm_amps():
                    flag = 1
            if flag == 1:
                break

        if flag == 1:
            button = CTkButton(master=frame1, text=dss.lines_read_name(),
                               command=lambda idx=index, n_nodes=dss.lines_read_phases(), nome=dss.lines_read_name(),
                                              parametro=dss.lines_read_norm_amps():
                               plota(correntes, idx, nome, n_nodes, "corrente", parametro, 1), fg_color='red')
        else:
            button = CTkButton(master=frame1, text=dss.lines_read_name(),
                               command=lambda idx=index, n_nodes=dss.lines_read_phases(), nome=dss.lines_read_name(),
                                              parametro=dss.lines_read_norm_amps():
                               plota(correntes, idx, nome, n_nodes, "corrente", parametro, 1))

        if j % 15 == 0:
            m += 1
            n = 0
        button.grid(row=n, column=m, pady=5, padx=5)
        n += 1
        dss.lines_next()

    janela.mainloop()


def show_trafo_current(correntes):
    m = 0
    n = 0
    flag = 0
    j = 0

    janela = CTk()
    janela.title("Correntes nos Trafos")

    frame1 = CTkFrame(master=janela)
    frame1.pack(pady=5, padx=90, fill="both", expand=True)

    for element in dss.circuit_all_element_names():
        flag = 0
        if "Transformer" in element:
            dss.circuit_set_active_element(element)
            num_phases = dss.cktelement_num_phases()
            asset = dss.cktelement_name().split('.')[1]
            index = correntes.index.get_loc(f'{asset}.{dss.cktelement_node_order()[0]}')

            for i in range(1, 92):
                for k in range(num_phases):
                    if correntes.iloc[index + k, i - 1] > dss.cktelement_read_norm_amps():
                        flag = 1
                if flag == 1:
                    break

            if flag == 1:
                button = CTkButton(master=frame1, text=dss.cktelement_name(),
                                   command=lambda idx=index, n_nodes=dss.cktelement_num_phases(),
                                                  nome=dss.cktelement_name(),
                                                  parametro=dss.cktelement_read_norm_amps():
                                   plota(correntes, idx, nome, n_nodes, "corrente", parametro, 1), fg_color='red')
            else:
                button = CTkButton(master=frame1, text=dss.cktelement_name(),
                                   command=lambda idx=index, n_nodes=dss.cktelement_num_phases(),
                                                  nome=dss.cktelement_name(),
                                                  parametro=dss.cktelement_read_norm_amps():
                                   plota(correntes, idx, nome, n_nodes, "corrente", parametro, 1))

            if j % 10 == 0:
                m += 1
                n = 0
            button.grid(row=n, column=m, pady=5, padx=5)
            n += 1
            j += 1

    janela.mainloop()


root = CTk()
root.title("Resultados de Tensão e Corrente")

frame = CTkFrame(master=root)
frame.pack(pady=5, padx=90, fill="both", expand=True)

bt1 = CTkButton(master=frame, text="Tensões nas Barras", command=lambda: show_volt(dados.tensao))
bt1.grid(row=1, column=1, pady=5, padx=5)

bt2 = CTkButton(master=frame, text="Correntes nas Linhas", command=lambda: show_currents(dados.corrente))
bt2.grid(row=2, column=1, pady=5, padx=5)

bt3 = CTkButton(master=frame, text="Correntes nos Trafos",
                command=lambda: show_trafo_current(dados.trafos_current))
bt3.grid(row=3, column=1, pady=5, padx=5)

root.mainloop()
