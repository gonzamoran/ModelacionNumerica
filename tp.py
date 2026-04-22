import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import lagrange, CubicSpline, PchipInterpolator
import math
from scipy.optimize import curve_fit
from sklearn.metrics import mean_squared_error

# Lee de los archivos csv y guarda los puntos en un arreglo de tuplas.
def leer_csv(ruta):
    puntos = []
    with open(ruta, "r") as f:
        for linea in f:
            x, y = linea.strip().split(",")
            puntos.append((float(x), float(y)))
    return puntos



def limpiar_y_transformar(puntos, idx_p1, idx_p2):
    """
    Transforma puntos en píxeles a metros.
    
    El puente cubre 20 metros (de 0 a 20 m), medido entre los apoyos.
    Se usan los puntos en idx_p1 e idx_p2 como referencias para calibrar.
    """
    p1_x, p1_y = puntos[idx_p1]
    p2_x, p2_y = puntos[idx_p2]

    distancia_px = math.sqrt((p2_x - p1_x)**2 + (p2_y - p1_y)**2)
    factor = 20.0 / distancia_px  # 20 metros entre apoyos del puente

    puntos_metros = []

    for x, y in puntos:
        nuevo_x = (x - p1_x) * factor
        nuevo_y = (p1_y - y) * factor
        puntos_metros.append((nuevo_x, nuevo_y))

    puntos_metros.sort(key=lambda p: p[0])
    return puntos_metros


def construir_p1(puntos_metros):

    x1 = np.array([p[0] for p in puntos_metros])
    y1 = np.array([p[1] for p in puntos_metros])

    # 2. FILTRO ANTI-OSCILACIÓN: 
    # Tomamos los puntos del cauce (entre 7m y 20m) 
    # pero ignoramos los que valen 0 o casi 0 en el medio.
    mask_centro = (x1 > 7.0) & (x1 < 19.8) & (y1 > 5.0)
    x_c = x1[mask_centro]
    y_c = y1[mask_centro]

    # Creamos el Spline solo con esos puntos válidos
    f_central = PchipInterpolator(x_c, y_c)

    # 3. DEFINIMOS LOS LÍMITES REALES DE LOS DATOS
    # En lugar de usar 9.0 y 19.0 fijos, usamos el primer y último punto del cauce
    x_inicio_cauce = x_c[0]
    x_fin_cauce = x_c[-1]

    # --- TRAMOS LINEALES PARA LAS MÁRGENES ---
    def tramo_izq(x):
        # Recta desde (0,0) hasta el primer punto del spline
        y_target = f_central(x_inicio_cauce)
        return (y_target / x_inicio_cauce) * x

    def tramo_der(x):
        # Recta desde el último punto del spline hasta el apoyo P2 (20, 0)
        y_start = f_central(x_fin_cauce)
        pendiente = (0 - y_start) / (20.0 - x_fin_cauce)
        return y_start + pendiente * (x - x_fin_cauce)

    # --- FUNCIÓN PARTIDA FINAL ---
    def f_puente1_final(x):
        if x <= x_inicio_cauce:
            return float(tramo_izq(x))
        elif x <= x_fin_cauce:
            return float(f_central(x))
        else:
            # Si estamos entre el fin del cauce y el apoyo P2 (20m)
            if x <= 20.0:
                return float(tramo_der(x))
            else:
                return 0.0 # Fuera del puente
    return f_puente1_final, x1, y1, x_inicio_cauce, x_fin_cauce


# La función debe ser negativa (cóncava hacia abajo)
def cuadratica_neg(x, a, b, c):
    return a * x**2 + b * x + c

def construir_p2(puntos_metros):
    """
    Construye la función partida para el Puente 2.
    
    Solo considera puntos en [0, 20] m porque:
    - El puente tiene una luz de 20 m (especificado en el enunciado)
    - Dominio de integración con Simpson 3/8: [0, 20]
    - Puntos fuera de este rango están fuera del puente
    
    Compara dos modelos:
    - Modelo A: 2 cuadráticas + 1 recta lineal
    - Modelo B: 1 cuadrática + 1 recta lineal
    
    Elige el de menor RMSE.
    """
    x2 = np.array([p[0] for p in puntos_metros])
    y2 = np.array([p[1] for p in puntos_metros])
    
    # Identificamos puntos clave según tu tabla
    # x=0 (P1), x=14.59 (P8), x=17.12 (P9), x=20.0 (P10/Apoyo)
    idx_p8 = 7
    idx_p9 = 8
    x_p8 = x2[idx_p8]
    x_p9 = x2[idx_p9]
    y_p9 = y2[idx_p9]

    # --- MODELO A: 2 Cuadráticas + 1 Lineal ---
    popt_a1, _ = curve_fit(cuadratica_neg, x2[:8], y2[:8])      # P1 a P8
    popt_a2, _ = curve_fit(cuadratica_neg, x2[7:18], y2[7:18]) # P8 a P18
    
    def modelo_a(x):
        if x <= x_p8:
            return float(cuadratica_neg(x, *popt_a1))
        elif x <= x_p9:
            return float(cuadratica_neg(x, *popt_a2))
        else:
            # FUNCIÓN LINEAL INTERPOLADA: une P9 con el apoyo P2 (20, 0)
            pendiente = (0 - y_p9) / (20.0 - x_p9)
            return float(y_p9 + pendiente * (x - x_p9))

    # --- MODELO B: 1 Cuadrática + 1 Lineal ---
    popt_b, _ = curve_fit(cuadratica_neg, x2[:18], y2[:18]) # Una sola para todo
    
    def modelo_b(x):
        if x <= x_p9:
            return float(cuadratica_neg(x, *popt_b))
        else:
            pendiente = (0 - y_p9) / (20.0 - x_p9)
            return float(y_p9 + pendiente * (x - x_p9))

    # --- CÁLCULO DE ERRORES (Punto c.ii.3) ---
    # Evaluamos solo en los puntos dentro del puente (x <= 20)
    mask_puente = x2 <= 20
    x_eval = x2[mask_puente]
    y_eval = y2[mask_puente]
    
    rmse_a = np.sqrt(mean_squared_error(y_eval, [modelo_a(xi) for xi in x_eval]))
    rmse_b = np.sqrt(mean_squared_error(y_eval, [modelo_b(xi) for xi in x_eval]))
    
    print(f"RMSE Modelo A (2 cuadráticas): {rmse_a:.4f}")
    print(f"RMSE Modelo B (1 cuadrática): {rmse_b:.4f}")

    # Elegimos el de menor error
    # Devolvemos SOLO los puntos dentro del puente [0, 20]
    x2_filtrado = x2[mask_puente]
    y2_filtrado = y2[mask_puente]
    
    if rmse_a < rmse_b:
        print("Ganador: Modelo A")
        return modelo_a, x2_filtrado, y2_filtrado, x_p8, rmse_a, rmse_b
    else:
        print("Ganador: Modelo B")
        return modelo_b, x2_filtrado, y2_filtrado, x_p8, rmse_a, rmse_b

def simpson_38_final(f, limite_b, h=1):
    n = int(limite_b / h) # n = 21 si limite_b es 21
    x_nodos = np.linspace(0, limite_b, n + 1)
    # Evaluamos la función en cada metro
    y_nodos = [abs(f(xi)) for xi in x_nodos]
    
    suma = y_nodos[0] + y_nodos[-1]
    for i in range(1, n):
        if i % 3 == 0:
            suma += 2 * y_nodos[i] # Nodos multiples de 3
        else:
            suma += 3 * y_nodos[i] # Nodos intermedios
            
    area = (3 * h / 8) * suma
    return area

# Cálculo del área para el Puente 1
# area_final_p1 = simpson_38_final(f_puente1_final, 21)
# print(f"El área de la sección transversal (P1) es: {area_final_p1:.2f} m²")

def calcular_area_simpson38(f, b, h=1):
    # n debe ser múltiplo de 3. Para un puente de 20m, usamos n=21.
    n = 21 
    x_nodos = np.linspace(0, n, n + 1)
    
    # Evaluamos la función en cada nodo (usando valor absoluto para el área física)
    # Si x > 20, la función debe devolver 0.
    y_nodos = [abs(f(xi)) for xi in x_nodos]
    
    # Aplicación de la fórmula de Simpson 3/8
    suma = y_nodos[0] + y_nodos[-1]
    
    for i in range(1, n):
        if i % 3 == 0:
            suma += 2 * y_nodos[i] # Nodos múltiplos de 3
        else:
            suma += 3 * y_nodos[i] # Resto de los nodos
            
    area = (3 * h / 8) * suma
    print (area)
    return area



def cuadratura_gaussiana_3p(f, a, b):
    # Nodos y pesos para n=3
    nodos = np.array([-np.sqrt(0.6), 0.0, np.sqrt(0.6)])
    pesos = np.array([5/9, 8/9, 5/9])
    
    # Cambio de variable: de [-1, 1] a [a, b]
    x_transformado = ((b - a) / 2) * nodos + ((a + b) / 2)
    
    # Sumatoria ponderada
    suma = np.sum(pesos * np.array([f(xi) for xi in x_transformado]))
    
    return ((b - a) / 2) * suma

# --- APLICACIÓN A TUS PUENTES ---

# Puente 1: Integramos los 3 tramos (usando valores redondos)
# area_p1_gauss = (cuadratura_gaussiana_3p(f_puente1_final, 0, 7) + 
#                  cuadratura_gaussiana_3p(f_puente1_final, 7, 20) +
#                  cuadratura_gaussiana_3p(f_puente1_final, 20, 21))
# 
# # Puente 2: Integramos los 2 tramos del Modelo A (ganador)
# # Asumiendo cambio en x=15
# area_p2_gauss = (cuadratura_gaussiana_3p(f_puente2_final, 0, 15) + 
#                  cuadratura_gaussiana_3p(f_puente2_final, 15, 21))
# 
# print(f"Área P1 (Gauss): {area_p1_gauss:.4f} m²")
# print(f"Área P2 (Gauss): {area_p2_gauss:.4f} m²")