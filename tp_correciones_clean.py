"""
TRABAJO PRÁCTICO - MODELACIÓN NUMÉRICA
Análisis de Puentes: Interpolación, Ajuste e Integración
VERSIÓN CORREGIDA - Mayo 2026
"""

import csv
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from sklearn.metrics import mean_squared_error


# ============================================================================
# 1. LECTURA Y TRANSFORMACIÓN DE DATOS
# ============================================================================

def leer_csv(ruta):
    """Lee puntos desde archivo CSV."""
    puntos = []
    with open(ruta, "r") as f:
        for linea in f:
            x, y = linea.strip().split(",")
            puntos.append((float(x), float(y)))
    return puntos


def limpiar_y_transformar(puntos, idx_p1, idx_p2):
    """
    Transforma puntos en píxeles a metros.
    
    CORRECCIÓN: La distancia de 20m es entre P1 y P2 (índices 0 y 1).
    Mantiene TODOS los puntos, incluidos los atípicos.
    """
    p1_x, p1_y = puntos[idx_p1]
    p2_x, p2_y = puntos[idx_p2]

    distancia_px = math.sqrt((p2_x - p1_x)**2 + (p2_y - p1_y)**2)
    factor = 20.0 / distancia_px

    puntos_metros = []
    for x, y in puntos:
        nuevo_x = (x - p1_x) * factor
        nuevo_y = (p1_y - y) * factor
        puntos_metros.append((nuevo_x, nuevo_y))

    puntos_metros.sort(key=lambda p: p[0])
    return puntos_metros


# Lectura de datos
puntos_tabla1 = leer_csv("Tabla1.csv")
puntos_tabla2 = leer_csv("Tabla2.csv")

# CORRECCIÓN: Usar índices 0,1 (P1 a P2) para escala de 20m
p1 = limpiar_y_transformar(puntos_tabla1, 0, 1)
p2 = limpiar_y_transformar(puntos_tabla2, 0, 1)


# ============================================================================
# 2. VISUALIZACIÓN INICIAL
# ============================================================================

def graficar_puntos(puntos1, puntos2):
    """Gráfico de puntos en píxeles (datos crudos)."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    x_t1, y_t1 = zip(*puntos1)
    axes[0].scatter(x_t1, y_t1, color='blue', s=50)
    axes[0].set_title("Tabla 1 — Datos crudos (píxeles)")
    axes[0].set_xlabel("x (px)"); axes[0].set_ylabel("y (px)")
    axes[0].grid(True)

    x_t2, y_t2 = zip(*puntos2)
    axes[1].scatter(x_t2, y_t2, color='red', s=50)
    axes[1].set_title("Tabla 2 — Datos crudos (píxeles)")
    axes[1].set_xlabel("x (px)"); axes[1].set_ylabel("y (px)")
    axes[1].grid(True)

    plt.tight_layout()
    plt.savefig("grafico_puntos.png")
    plt.show()


def graficar_transformacion(puntos_t1_metros, puntos_t2_metros):
    """Gráfico de puntos transformados a metros."""
    print("Coordenada X de P10:", puntos_t2_metros[9][0])
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    x_r1, y_r1 = zip(*puntos_t1_metros)
    axes[0].scatter(x_r1, y_r1, color='green', s=60, zorder=5)
    for i, (x, y) in enumerate(zip(x_r1, y_r1)):
        axes[0].annotate(f'idx{i}', (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7)

    axes[0].set_title("Puente 1 — Perfil de Profundidad (transformado)")
    axes[0].set_xlabel("Distancia horizontal (m)")
    axes[0].set_ylabel("Altura relativa (m)")
    axes[0].axhline(0, color='gray', ls='--', alpha=0.5, label='Nivel del puente')
    axes[0].legend()
    axes[0].grid(True)

    x_r2, y_r2 = zip(*puntos_t2_metros)
    axes[1].scatter(x_r2, y_r2, color='orange', s=60, zorder=5)
    for i, (x, y) in enumerate(zip(x_r2, y_r2)):
        lbl = f'P{i+1}'
        axes[1].annotate(lbl, (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7)

    axes[1].set_title("Puente 2 — Perfil de Profundidad (transformado)")
    axes[1].set_xlabel("Distancia horizontal (m)")
    axes[1].set_ylabel("Altura relativa (m)")
    axes[1].axhline(0, color='gray', ls='--', alpha=0.5, label='Nivel del puente')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    plt.savefig("grafico_puentes.png")
    plt.show()


graficar_puntos(puntos_tabla1, puntos_tabla2)
graficar_transformacion(p1, p2)


# ============================================================================
# 3. INTERPOLADOR DE HERMITE CÚBICO (método programado en clase)
# ============================================================================

class InterpoladorHermiteManual:
    """
    Interpolador de Hermite Cúbico programado manualmente.
    Usa polinomios cúbicos de Hermite: h00, h10, h01, h11
    """
    def __init__(self, x, y):
        self.x = np.array(x)
        self.y = np.array(y)
        self.n = len(x)
        self.m = np.zeros(self.n)
        self._calcular_pendientes()

    def _calcular_pendientes(self):
        """Calcula las pendientes de Hermite en cada nodo."""
        d = np.zeros(self.n - 1)
        for i in range(self.n - 1):
            d[i] = (self.y[i+1] - self.y[i]) / (self.x[i+1] - self.x[i])

        for i in range(1, self.n - 1):
            if d[i-1] * d[i] <= 0:
                self.m[i] = 0.0
            else:
                w1 = 2 * (self.x[i+1] - self.x[i]) + (self.x[i] - self.x[i-1])
                w2 = (self.x[i+1] - self.x[i]) + 2 * (self.x[i] - self.x[i-1])
                self.m[i] = (w1 + w2) / (w1 / d[i-1] + w2 / d[i])

        self.m[0] = d[0]
        self.m[-1] = d[-1]

    def __call__(self, xi):
        """Evalúa el interpolador en punto(s) xi."""
        if isinstance(xi, (list, np.ndarray)):
            return np.array([self._evaluar_punto(val) for val in xi])
        return self._evaluar_punto(xi)

    def _evaluar_punto(self, xi):
        """Evalúa en un punto específico usando polinomios de Hermite."""
        for i in range(self.n - 1):
            if self.x[i] <= xi <= self.x[i+1]:
                h = self.x[i+1] - self.x[i]
                t = (xi - self.x[i]) / h

                # Polinomios base de Hermite
                h00 = 2*t**3 - 3*t**2 + 1
                h10 = t**3 - 2*t**2 + t
                h01 = -2*t**3 + 3*t**2
                h11 = t**3 - t**2

                return (h00 * self.y[i] +
                        h10 * h * self.m[i] +
                        h01 * self.y[i+1] +
                        h11 * h * self.m[i+1])
        return 0.0


# ============================================================================
# 4. PUENTE 1 - INTERPOLACIÓN CON HERMITE
# ============================================================================

def construir_p1(puntos_metros):
    """
    Construye la función partida para Puente 1.
    
    CORRECCIÓN: 
    - Mantiene TODOS los puntos (incluido P11 atípico) visibles en gráficos
    - EXCLUYE P11 solo de la interpolación de Hermite
    - Calcula el área del trapecio formado por P11 para restarlo luego
    """
    x1 = np.array([p[0] for p in puntos_metros])
    y1 = np.array([p[1] for p in puntos_metros])

    orden = np.argsort(x1)
    x1 = x1[orden]
    y1 = y1[orden]

    # IDENTIFICAR Y SEPARAR EL PUNTO 11 (ATÍPICO)
    idx_p11 = np.argmax(y1)  # El punto más alto es el atípico
    x_p11 = x1[idx_p11]
    y_p11 = y1[idx_p11]
    
    print(f"\n{'='*60}")
    print(f"PUENTE 1 - INFORMACIÓN DE PUNTO 11")
    print(f"{'='*60}")
    print(f"Punto 11 identificado en x={x_p11:.4f} m, y={y_p11:.4f} m")
    
    # Crear máscara para EXCLUIR el punto 11 de la interpolación
    mask_sin_p11 = np.abs(x1 - x_p11) > 0.1
    x_sin_p11 = x1[mask_sin_p11]
    y_sin_p11 = y1[mask_sin_p11]

    # Filtro anti-oscilación: puntos del cauce con y > 5.0
    mask_centro = (x_sin_p11 >= 5.0) & (x_sin_p11 <= 15.0) & (y_sin_p11 > 5.0)
    x_c = x_sin_p11[mask_centro]
    y_c = y_sin_p11[mask_centro]

    # INTERPOLADOR DE HERMITE (método programado en clase, sin librerías externas)
    f_central = InterpoladorHermiteManual(x_c, y_c)
    x_inicio_cauce = x_c[0]
    x_fin_cauce = x_c[-1]

    print(f"Rango de interpolación Hermite: x=[{x_inicio_cauce:.4f}, {x_fin_cauce:.4f}] m")

    # Márgenes izquierda y derecha
    candidatos_der = (x_sin_p11 > x_fin_cauce) & (y_sin_p11 <= 1.0)
    x_base_der = x_sin_p11[candidatos_der][0] if candidatos_der.any() else x_fin_cauce + 1.0

    candidatos_izq = (x_sin_p11 < x_inicio_cauce) & (y_sin_p11 <= 1.0)
    x_base_izq = x_sin_p11[candidatos_izq][-1] if candidatos_izq.any() else 0.0

    def tramo_izq(x):
        y_objetivo = f_central(x_inicio_cauce)
        pendiente = (y_objetivo - 0.0) / (x_inicio_cauce - x_base_izq)
        return pendiente * (x - x_base_izq)

    def tramo_der(x):
        y_inicio = f_central(x_fin_cauce)
        pendiente = (0.0 - y_inicio) / (x_base_der - x_fin_cauce)
        return y_inicio + pendiente * (x - x_fin_cauce)

    def f_puente1_final(x):
        if x < x_base_izq:
            return 0.0
        elif x <= x_inicio_cauce:
            return float(tramo_izq(x))
        elif x <= x_fin_cauce:
            return float(f_central(x))
        elif x <= x_base_der:
            return float(tramo_der(x))
        else:
            return 0.0

    # Calcular el área del trapecio del punto 11
    x_izq = x1[idx_p11 - 1] if idx_p11 > 0 else x_p11 - 0.5
    x_der = x1[idx_p11 + 1] if idx_p11 < len(x1) - 1 else x_p11 + 0.5
    y_izq = y1[idx_p11 - 1] if idx_p11 > 0 else 0.0
    y_der = y1[idx_p11 + 1] if idx_p11 < len(x1) - 1 else 0.0
    
    # Área del trapecio compuesto
    area_trapecio = ((y_izq + y_p11) / 2) * (x_p11 - x_izq) + ((y_p11 + y_der) / 2) * (x_der - x_p11)
    print(f"Área del trapecio (punto 11): {area_trapecio:.4f} m²")
    print(f"{'='*60}\n")

    return f_puente1_final, x1, y1, x_inicio_cauce, x_fin_cauce, x_base_der, area_trapecio


f1, x1, y1, xi, xf, xb, area_trap_p1 = construir_p1(p1)


def graficar_puente1(x, y, f, x_ini, x_fin, x_base_der):
    """Gráfica el perfil corregido del Puente 1 con Hermite."""
    xp = np.linspace(0, x_base_der, 500)
    yp = [f(val) for val in xp]

    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, color='black', label='Todos los puntos medidos', zorder=5, s=60)
    plt.plot(xp, yp, 'r-', lw=2, label='Interpolación Hermite (sin P11)')
    plt.axvline(x_ini, color='orange', ls='--', label='Inicio interpolación')
    plt.axvline(x_fin, color='purple', ls='--', label='Fin interpolación')

    plt.title("Puente 1: Perfil corregido (Interpolación Hermite)")
    plt.xlabel("Distancia horizontal (m)")
    plt.ylabel("Altura relativa (m)")
    plt.xlim(0, x_base_der + 2)
    plt.ylim(-2, max(y) + 5)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig("punto_c_i.jpg", bbox_inches='tight', dpi=150)
    plt.show()


graficar_puente1(x1, y1, f1, xi, xf, xb)


# ============================================================================
# 5. PUENTE 2 - AJUSTE CON FUNCIONES CUADRÁTICAS
# ============================================================================

def cuadratica_neg(x, a, b, c):
    """Función cuadrática con coeficiente a negativo."""
    return -abs(a) * x**2 + b * x + c


def construir_p2(puntos_metros):
    """
    Construye la función partida para Puente 2.
    Compara dos modelos usando curve_fit con funciones cuadráticas.
    """
    x2 = np.array([p[0] for p in puntos_metros])
    y2 = np.array([p[1] for p in puntos_metros])

    idx_p8 = 7
    idx_p10 = 9
    idx_p18 = 17

    x_p8 = x2[idx_p8]
    x_p10 = x2[idx_p10]
    y_p10 = y2[idx_p10]
    x_p18 = x2[idx_p18]
    y_p18 = y2[idx_p18]

    # Datos para Modelo A (2 cuadráticas)
    x_tab1 = x2[:idx_p8 + 1]
    y_tab1 = y2[:idx_p8 + 1]

    indices_tab2 = [i for i in range(idx_p8, idx_p18 + 1) if i != idx_p10]
    x_tab2 = x2[indices_tab2]
    y_tab2 = y2[indices_tab2]

    # Datos para Modelo B (1 cuadrática)
    indices_comp = [i for i in range(idx_p18 + 1) if i != idx_p10]
    x_comp = x2[indices_comp]
    y_comp = y2[indices_comp]

    # Ajuste de Modelo A (2 cuadráticas)
    coef_a1, _ = curve_fit(cuadratica_neg, x_tab1, y_tab1)
    coef_a2, _ = curve_fit(cuadratica_neg, x_tab2, y_tab2)
    
    print(f"\n{'='*60}")
    print(f"PUENTE 2 - ECUACIONES OBTENIDAS POR AJUSTE")
    print(f"{'='*60}")
    print(f"Modelo A (2 cuadráticas):")
    print(f"  Tramo 1 (P1 a P8): y(x) = {coef_a1[0]:.8f}·x² + {coef_a1[1]:.8f}·x + {coef_a1[2]:.8f}")
    print(f"  Tramo 2 (P8 a P18): y(x) = {coef_a2[0]:.8f}·x² + {coef_a2[1]:.8f}·x + {coef_a2[2]:.8f}")

    def modelo_a_tablero(x):
        if x <= x_p8:
            return float(cuadratica_neg(x, *coef_a1))
        else:
            return float(cuadratica_neg(x, *coef_a2))

    # Ajuste de Modelo B (1 cuadrática)
    coef_b, _ = curve_fit(cuadratica_neg, x_comp, y_comp)
    
    print(f"\nModelo B (1 cuadrática):")
    print(f"  Tablero: y(x) = {coef_b[0]:.8f}·x² + {coef_b[1]:.8f}·x + {coef_b[2]:.8f}")

    def modelo_b_tablero(x):
        return float(cuadratica_neg(x, *coef_b))

    def funcion_lineal_tirante(x):
        pendiente = (y_p18 - y_p10) / (x_p18 - x_p10)
        return y_p10 + pendiente * (x - x_p10)

    # Comparación de errores
    y_pred_a = np.array([modelo_a_tablero(xi) for xi in x_comp])
    y_pred_b = np.array([modelo_b_tablero(xi) for xi in x_comp])

    error_a = np.sum((y_comp - y_pred_a)**2)
    error_b = np.sum((y_comp - y_pred_b)**2)

    print(f"\nError cuadrático Modelo A: {error_a:.4f}")
    print(f"Error cuadrático Modelo B: {error_b:.4f}")

    if error_a < error_b:
        print("✓ Ganador: Modelo A (2 cuadráticas)")
        modelo_ganador = np.vectorize(modelo_a_tablero)
    else:
        print("✓ Ganador: Modelo B (1 cuadrática)")
        modelo_ganador = np.vectorize(modelo_b_tablero)
    print(f"{'='*60}\n")

    return modelo_ganador, funcion_lineal_tirante, x_comp, y_comp, x_p8, x_p10, x_p18


f_tab, f_tir, x_val, y_val, xc, xp10, xp18 = construir_p2(p2)


def graficar_puente2(x_datos, y_datos, f_tablero, f_tirante, x_corte, x_p10, x_p18):
    """Gráfica el perfil ajustado del Puente 2."""
    plt.figure(figsize=(10, 5))

    x_tablero_plot = np.linspace(0, x_p18, 500)
    y_tablero_plot = f_tablero(x_tablero_plot)
    plt.plot(x_tablero_plot, y_tablero_plot, 'orange', lw=2, label='Tablero (Modelo Ganador)')

    x_tirante_plot = np.linspace(x_p10, x_p18, 100)
    y_tirante_plot = f_tirante(x_tirante_plot)
    plt.plot(x_tirante_plot, y_tirante_plot, 'blue', lw=2, label='Tirante Lineal')

    plt.scatter(x_datos, y_datos, color='black', s=40, zorder=5, label='Puntos medidos')
    plt.scatter([x_p10], [0], color='red', s=60, marker='s', zorder=6, label='Apoyo P10')
    plt.axvline(x_corte, ls='--', color='gray', alpha=0.5)

    plt.title('Puente 2 - Perfil de Profundidad (Ajustado)')
    plt.xlabel('Distancia horizontal (m)')
    plt.ylabel('Altura relativa (m)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig('ajuste_p2_corregido.png', bbox_inches='tight', dpi=150)
    plt.show()


graficar_puente2(x_val, y_val, f_tab, f_tir, xc, xp10, xp18)


# ============================================================================
# 6. MÉTODOS DE INTEGRACIÓN NUMÉRICA
# ============================================================================

def simpson_38_final(f, a, b, h=1):
    """Integración numérica mediante Simpson 3/8."""
    n = int((b - a) / h)

    if n % 3 != 0:
        raise ValueError("n debe ser múltiplo de 3")

    x_nodos = np.linspace(a, b, n + 1)
    y_nodos = [abs(f(xi)) for xi in x_nodos]

    suma = y_nodos[0] + y_nodos[-1]

    for i in range(1, n):
        if i % 3 == 0:
            suma += 2 * y_nodos[i]
        else:
            suma += 3 * y_nodos[i]

    area = (3 * h / 8) * suma
    return area


def cuadratura_gaussiana_3p(f, a, b):
    """Cuadratura Gaussiana de 3 puntos en intervalo [a,b]."""
    nodos = np.array([-np.sqrt(0.6), 0.0, np.sqrt(0.6)])
    pesos = np.array([5/9, 8/9, 5/9])
    x_transformado = ((b - a) / 2) * nodos + ((a + b) / 2)

    suma = np.sum(pesos * np.array([abs(f(xi)) for xi in x_transformado]))
    return ((b - a) / 2) * suma


def cuadratura_gaussiana(f, a, b, h=1):
    """Cuadratura Gaussiana compuesta (subintervalos de ancho h)."""
    n = int((b - a) / h)
    area_total = 0

    for i in range(n):
        ai = a + i * h
        bi = ai + h
        area_total += cuadratura_gaussiana_3p(f, ai, bi)

    return area_total


# Cálculo de áreas
print(f"\n{'='*60}")
print(f"CÁLCULO DE ÁREAS - MÉTODO SIMPSON 3/8")
print(f"{'='*60}")

area_simpson_p1 = simpson_38_final(f1, 0, 21)
area_simpson_p1_corregida = area_simpson_p1 - area_trap_p1
area_simpson_p2 = simpson_38_final(f_tab, 0, 21)

print(f"Puente 1 (área bruta):        {area_simpson_p1:.4f} m²")
print(f"Puente 1 (área trapecio):     {area_trap_p1:.4f} m²")
print(f"Puente 1 (área CORREGIDA):    {area_simpson_p1_corregida:.4f} m²")
print(f"Puente 2:                     {area_simpson_p2:.4f} m²")
print(f"{'='*60}\n")

print(f"{'='*60}")
print(f"CÁLCULO DE ÁREAS - CUADRATURA GAUSSIANA (3 puntos)")
print(f"{'='*60}")

area_gauss_p1 = cuadratura_gaussiana(f1, 0, 21)
area_gauss_p1_corregida = area_gauss_p1 - area_trap_p1
area_gauss_p2 = cuadratura_gaussiana(f_tab, 0, 21)

print(f"Puente 1 (área bruta):        {area_gauss_p1:.4f} m²")
print(f"Puente 1 (área trapecio):     {area_trap_p1:.4f} m²")
print(f"Puente 1 (área CORREGIDA):    {area_gauss_p1_corregida:.4f} m²")
print(f"Puente 2:                     {area_gauss_p2:.4f} m²")
print(f"{'='*60}\n")

# Tabla de resumen
print(f"{'='*60}")
print(f"TABLA RESUMEN DE ÁREAS OBTENIDAS")
print(f"{'='*60}")
print(f"{'Método':<30} {'Puente 1 (m²)':<20} {'Puente 2 (m²)':<20}")
print("-" * 70)
print(f"{'Simpson 3/8':<30} {area_simpson_p1_corregida:<20.4f} {area_simpson_p2:<20.4f}")
print(f"{'Cuadratura Gaussiana':<30} {area_gauss_p1_corregida:<20.4f} {area_gauss_p2:<20.4f}")
print("=" * 70 + "\n")


# ============================================================================
# 7. APLICACIÓN: CÁLCULO DE CAMIONES NECESARIOS
# ============================================================================

def calcular_camiones(area):
    """Calcula cantidad de camiones necesarios para transportar sedimento."""
    espesor = 0.40  # metros
    densidad = 800  # kg/m³
    capacidad_volumen = 18  # m³
    capacidad_peso = 12000  # kg

    volumen = area * espesor
    masa = volumen * densidad

    camiones_volumen = volumen / capacidad_volumen
    camiones_peso = masa / capacidad_peso

    camiones_necesarios = math.ceil(max(camiones_volumen, camiones_peso))
    return {
        "total_camiones": camiones_necesarios,
        "camiones_volumen": camiones_volumen,
        "camiones_peso": camiones_peso
    }


# Usar las áreas corregidas
resultado_p1 = calcular_camiones(area_simpson_p1_corregida)
resultado_p2 = calcular_camiones(area_simpson_p2)

print(f"{'='*60}")
print(f"APLICACIÓN: TRANSPORTE DE SEDIMENTO")
print(f"{'='*60}")
print(f"Puente 1: {resultado_p1['total_camiones']} camiones necesarios")
print(f"Puente 2: {resultado_p2['total_camiones']} camiones necesarios")
print(f"{'='*60}\n")
