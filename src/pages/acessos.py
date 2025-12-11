from utils.requisicoes import buscarUsuarios, buscarMetricas
from utils.controlar_banco_de_dados import salvarUsuarios, salvarMetricas

usuarios = buscarUsuarios()
salvarUsuarios(usuarios)
metricas = buscarMetricas(usuarios)
salvarMetricas(metricas)
