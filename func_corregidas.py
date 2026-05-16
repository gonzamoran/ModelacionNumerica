"""
TRABAJO PRÁCTICO - MODELACIÓN NUMÉRICA
Solución final: Interpolación, ajuste e integración de perfiles de puentes
"""

import os
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Crear carpeta para gráficos si no existe
if not os.path.exists("graficos"):
    os.makedirs("graficos")


# ============================================================================
# LECTURA Y TRANSFORMACIÓN DE DATOS
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
    """Transforma puntos en píxeles a metros (0-20m)."""
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

p1 = limpiar_y_transformar(puntos_tabla1, 0, 1)
p2 = limpiar_y_transformar(puntos_tabla2, 0, 1)


# ============================================================================
# GRÁFICO 1: DATOS CRUDOS EN PÍXELES (SIN TRANSFORMAR)
# ============================================================================

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

x_t1, y_t1 = zip(*puntos_tabla1)
axes[0].scatter(x_t1, y_t1, color='blue', s=50)
axes[0].set_title("Datos crudos - Puente 1 (píxeles)", fontsize=11, fontweight='bold')
axes[0].set_xlabel("x (píxeles)")
axes[0].set_ylabel("y (píxeles)")
axes[0].grid(True, alpha=0.3)

x_t2, y_t2 = zip(*puntos_tabla2)
axes[1].scatter(x_t2, y_t2, color='red', s=50)
axes[1].set_title("Datos crudos - Puente 2 (píxeles)", fontsize=11, fontweight='bold')
axes[1].set_xlabel("x (píxeles)")
axes[1].set_ylabel("y (píxeles)")
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("graficos/01_puntos_sin_transformar.png", dpi=150, bbox_inches='tight')
plt.close()


# ============================================================================
# GRÁFICO 2: DATOS TRANSFORMADOS A METROS
# ============================================================================

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

x_r1, y_r1 = zip(*p1)
axes[0].scatter(x_r1, y_r1, color='green', s=60, zorder=5)
for i, (x, y) in enumerate(zip(x_r1, y_r1)):
    axes[0].annotate(f'P{i+1}', (x, y), textcoords="offset points", 
                     xytext=(4, 4), fontsize=8)

axes[0].set_title("Puente 1 - Transformación: Píxeles a Metros", fontsize=11, fontweight='bold')
axes[0].set_xlabel("Distancia horizontal (m)")
axes[0].set_ylabel("Altura relativa (m)")
axes[0].axhline(0, color='gray', ls='--', alpha=0.5)
axes[0].grid(True, alpha=0.3)

x_r2, y_r2 = zip(*p2)
axes[1].scatter(x_r2, y_r2, color='orange', s=60, zorder=5)
for i, (x, y) in enumerate(zip(x_r2, y_r2)):
    axes[1].annotate(f'P{i+1}', (x, y), textcoords="offset points", 
                     xytext=(4, 4), fontsize=8)

axes[1].set_title("Puente 2 - Transformación: Píxeles a Metros", fontsize=11, fontweight='bold')
axes[1].set_xlabel("Distancia horizontal (m)")
axes[1].set_ylabel("Altura relativa (m)")
axes[1].axhline(0, color='gray', ls='--', alpha=0.5)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("graficos/02_puntos_transformados.png", dpi=150, bbox_inches='tight')
plt.close()


# ============================================================================
# INTERPOLADOR DE LAGRANGE (CODIFICADO A MANO)
# ============================================================================

class InterpoladorLagrange:
    """
    Interpolador polinomial de Lagrange.
    Interpola exactamente a través de todos los puntos proporcionados.
    """
    
    def __init__(self, x_data, y_data):
        """Construye el interpolador de Lagrange."""
        self.x = np.array(x_data, dtype=float)
        self.y = np.array(y_data, dtype=float)
        self.n = len(x_data)
    
    def __call__(self, xi):
        if isinstance(xi, (list, np.ndarray)):
            return np.array([self._evaluar_lagrange(val) for val in xi])
        return self._evaluar_lagrange(xi)
    
    def _evaluar_lagrange(self, xi):
        """Evalúa el polinomio de Lagrange en xi."""
        resultado = 0.0
        
        for i in range(self.n):
            # Calcular base de Lagrange L_i(x)
            L_i = 1.0
            for j in range(self.n):
                if i != j:
                    L_i *= (xi - self.x[j]) / (self.x[i] - self.x[j])
            resultado += self.y[i] * L_i
        
        return resultado


# ============================================================================
# PUENTE 1: INTERPOLACIÓN CON LAGRANGE (PUNTOS DEL CAUCE - REGIÓN SUAVE)
# ============================================================================

def construir_puente1_lagrange(puntos_metros):
    """
    Construye interpolación de Lagrange para Puente 1 usando los puntos del cauce
    (región suave bien comportada) excepto P11 (punto atípico - máximo relativo).
    Los márgenes se cierran con rectas para evitar oscilaciones de Runge.
    """
    x1 = np.array([p[0] for p in puntos_metros])
    y1 = np.array([p[1] for p in puntos_metros])

    orden = np.argsort(x1)
    x1 = x1[orden]
    y1 = y1[orden]

    # Identificar y excluir P11 (punto atípico - máximo relativo)
    idx_p11 = np.argmax(y1)
    x_p11 = x1[idx_p11]
    y_p11 = y1[idx_p11]
    
    # Excluir P11 de la interpolación
    mask_sin_p11 = np.abs(x1 - x_p11) > 0.1
    x_sin_p11 = x1[mask_sin_p11]
    y_sin_p11 = y1[mask_sin_p11]

    # Filtrar puntos del cauce (región suave y bien comportada)
    # Eliminar márgenes planos (y ~ 0) que causan oscilaciones de Runge
    mask_centro = (y_sin_p11 > 1.0)
    x_c = x_sin_p11[mask_centro]
    y_c = y_sin_p11[mask_centro]

    # Interpolador de Lagrange en el cauce
    f_central = InterpoladorLagrange(x_c, y_c)
    x_inicio = x_c[0]
    x_fin = x_c[-1]

    # Márgenes con interpolación lineal simple
    y_inicio = f_central(x_inicio)
    y_fin = f_central(x_fin)

    def f_puente1(x):
        if x < x_inicio:
            # Margen izquierdo: recta desde 0 hasta el inicio
            pendiente = y_inicio / x_inicio if x_inicio > 0 else 0
            return pendiente * x
        elif x <= x_fin:
            # Centro: interpolación Lagrange
            return float(f_central(x))
        else:
            # Margen derecho: recta descendente
            x_final = x_sin_p11[-1]
            if x_final > x_fin:
                pendiente = -y_fin / (x_final - x_fin)
                return y_fin + pendiente * (x - x_fin)
            else:
                return 0.0

    # Área del trapecio de P11 (se suma por separado)
    x_izq = x1[idx_p11 - 1] if idx_p11 > 0 else x_p11 - 0.5
    x_der = x1[idx_p11 + 1] if idx_p11 < len(x1) - 1 else x_p11 + 0.5
    y_izq = y1[idx_p11 - 1] if idx_p11 > 0 else 0.0
    y_der = y1[idx_p11 + 1] if idx_p11 < len(x1) - 1 else 0.0

    area_trapecio_p11 = (
        ((y_izq + y_p11) / 2) * (x_p11 - x_izq) +
        ((y_p11 + y_der) / 2) * (x_der - x_p11)
    )

    return f_puente1, x1, y1, x_inicio, x_fin, x_p11, y_p11, area_trapecio_p11


f1, x1, y1, x_min1, x_max1, x_p11, y_p11, area_trap_p1 = construir_puente1_lagrange(p1)


# ============================================================================
# GRÁFICO 3: PUENTE 1 - INTERPOLACIÓN CON LAGRANGE
# ============================================================================

x_plot = np.linspace(x_min1, x_max1, 800)
y_plot = np.array([f1(val) for val in x_plot])

x_max_grafico = max(x1) + 1.5  # Eje X extendido para ver todos los puntos

plt.figure(figsize=(12, 6))

# Curva interpolada
plt.plot(x_plot, y_plot, 'r-', lw=2.5, label='Interpolación Lagrange', zorder=3)

# Todos los puntos medidos
plt.scatter(x1, y1, color='black', s=70, zorder=5, label='Todos los puntos medidos')

# Destacar P11 (excluido de la interpolación)
plt.scatter([x_p11], [y_p11], color='red', s=120, marker='*', zorder=6,
            label=f'P11 excluido (x={x_p11:.1f}m, y={y_p11:.1f}m)')

# Líneas de inicio y fin de interpolación
plt.axvline(x_min1, color='orange', ls='--', alpha=0.8, linewidth=2,
            label=f'Inicio interp. (x={x_min1:.1f}m)')
plt.axvline(x_max1, color='purple', ls='--', alpha=0.8, linewidth=2,
            label=f'Fin interp. (x={x_max1:.1f}m)')

plt.title("Puente 1: Interpolación con Lagrange (cauce + márgenes lineales)", fontsize=13, fontweight='bold')
plt.xlabel("Distancia horizontal (m)", fontsize=11)
plt.ylabel("Altura relativa (m)", fontsize=11)
plt.xlim(0, x_max_grafico)
plt.ylim(-5, max(y1) + 5)
plt.legend(fontsize=9, loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("graficos/03_puente1_interpolacion_lagrange.png", dpi=150, bbox_inches='tight')
plt.close()


# ============================================================================
# PUENTE 2: AJUSTE CON FUNCIONES CUADRÁTICAS
# ============================================================================

def cuadratica_neg(x, a, b, c):
    """Función cuadrática con coeficiente a negativo."""
    return -abs(a) * x**2 + b * x + c


def construir_puente2(puntos_metros):
    """Construye función partida para Puente 2 usando curve_fit."""
    x2 = np.array([p[0] for p in puntos_metros])
    y2 = np.array([p[1] for p in puntos_metros])

    idx_p8  = 7
    idx_p10 = 9
    idx_p18 = 17

    x_p8  = x2[idx_p8]
    x_p10 = x2[idx_p10]
    y_p10 = y2[idx_p10]
    x_p18 = x2[idx_p18]
    y_p18 = y2[idx_p18]

    # Modelo A: 2 cuadráticas
    x_tab1 = x2[:idx_p8 + 1]
    y_tab1 = y2[:idx_p8 + 1]

    indices_tab2 = [i for i in range(idx_p8, idx_p18 + 1) if i != idx_p10]
    x_tab2 = x2[indices_tab2]
    y_tab2 = y2[indices_tab2]

    coef_a1, _ = curve_fit(cuadratica_neg, x_tab1, y_tab1)
    coef_a2, _ = curve_fit(cuadratica_neg, x_tab2, y_tab2)

    def modelo_a(x):
        if x <= x_p8:
            return float(cuadratica_neg(x, *coef_a1))
        else:
            return float(cuadratica_neg(x, *coef_a2))

    # Modelo B: 1 cuadrática
    indices_comp = [i for i in range(idx_p18 + 1) if i != idx_p10]
    x_comp = x2[indices_comp]
    y_comp = y2[indices_comp]

    coef_b, _ = curve_fit(cuadratica_neg, x_comp, y_comp)

    def modelo_b(x):
        return float(cuadratica_neg(x, *coef_b))

    # Comparar errores
    y_pred_a = np.array([modelo_a(xi) for xi in x_comp])
    y_pred_b = np.array([modelo_b(xi) for xi in x_comp])

    error_a = np.sum((y_comp - y_pred_a)**2)
    error_b = np.sum((y_comp - y_pred_b)**2)

    if error_a < error_b:
        modelo_ganador = np.vectorize(modelo_a)
        modelo_nombre = "Modelo A (2 cuadráticas)"
    else:
        modelo_ganador = np.vectorize(modelo_b)
        modelo_nombre = "Modelo B (1 cuadrática)"

    def f_tirante(x):
        pendiente = (y_p18 - y_p10) / (x_p18 - x_p10)
        return y_p10 + pendiente * (x - x_p10)

    return modelo_ganador, f_tirante, x_comp, y_comp, x_p8, x_p10, x_p18, modelo_nombre


f_tab, f_tir, x_val, y_val, xc, xp10, xp18, modelo_nombre = construir_puente2(p2)


# ============================================================================
# GRÁFICO 4: PUENTE 2 - AJUSTE CON FUNCIONES CUADRÁTICAS
# ============================================================================

x_tablero_plot = np.linspace(0, xp18, 500)
y_tablero_plot = f_tab(x_tablero_plot)

x_tirante_plot = np.linspace(xp10, xp18, 100)
y_tirante_plot = f_tir(x_tirante_plot)

plt.figure(figsize=(11, 5))
plt.plot(x_tablero_plot, y_tablero_plot, 'orange', lw=2.5,
         label=f'Tablero ({modelo_nombre})')
plt.plot(x_tirante_plot, y_tirante_plot, 'blue', lw=2.5, label='Tirante Lineal')
plt.scatter(x_val, y_val, color='black', s=50, zorder=5, label='Puntos medidos')
plt.scatter([xp10], [0], color='red', s=100, marker='s', zorder=6, label='Apoyo')
plt.axvline(xc, ls='--', color='gray', alpha=0.5, linewidth=1)

plt.title('Puente 2: Ajuste con Funciones Cuadráticas', fontsize=12, fontweight='bold')
plt.xlabel('Distancia horizontal (m)', fontsize=11)
plt.ylabel('Altura relativa (m)', fontsize=11)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=10, loc='best')
plt.tight_layout()
plt.savefig('graficos/04_puente2_ajuste_cuadratico.png', dpi=150, bbox_inches='tight')
plt.close()


# ============================================================================
# MÉTODOS DE INTEGRACIÓN NUMÉRICA
# ============================================================================

def simpson_38(f, a, b, n=300):
    """
    Integración Simpson 3/8 compuesto.
    n debe ser múltiplo de 3.
    """
    # Asegurar que n sea múltiplo de 3
    n = n - (n % 3)
    h = (b - a) / n
    x_nodos = np.linspace(a, b, n + 1)
    y_nodos = np.array([abs(f(xi)) for xi in x_nodos])

    suma = y_nodos[0] + y_nodos[-1]
    for i in range(1, n):
        if i % 3 == 0:
            suma += 2 * y_nodos[i]
        else:
            suma += 3 * y_nodos[i]

    return (3 * h / 8) * suma


def cuadratura_gaussiana(f, a, b, n_intervalos=100):
    """Cuadratura Gaussiana de 3 puntos sobre n_intervalos subintervalos."""
    nodos = np.array([-np.sqrt(0.6), 0.0, np.sqrt(0.6)])
    pesos = np.array([5/9, 8/9, 5/9])

    area_total = 0.0
    h = (b - a) / n_intervalos

    for i in range(n_intervalos):
        ai = a + i * h
        bi = ai + h
        x_transformado = ((bi - ai) / 2) * nodos + ((ai + bi) / 2)
        suma = np.sum(pesos * np.array([abs(f(xi)) for xi in x_transformado]))
        area_total += ((bi - ai) / 2) * suma

    return area_total


# ============================================================================
# CÁLCULO DE ÁREAS — usando el rango completo de cada puente
# ============================================================================

# Puente 1: integrar sobre todo el rango [x_min1, x_max1]
# P11 ya está excluido de f1, su área se suma por separado (trapecio)
area_simpson_p1  = simpson_38(f1,   x_min1, x_max1) + area_trap_p1
area_gauss_p1    = cuadratura_gaussiana(f1, x_min1, x_max1) + area_trap_p1

# Puente 2: integrar sobre el rango del tablero [0, xp18]
area_simpson_p2  = simpson_38(f_tab,   0, xp18)
area_gauss_p2    = cuadratura_gaussiana(f_tab, 0, xp18)


# ============================================================================
# TABLA RESUMEN
# ============================================================================

print("\n" + "="*70)
print("TABLA RESUMEN DE ÁREAS OBTENIDAS")
print("="*70)
print(f"{'Método':<30} {'Puente 1 (m²)':<20} {'Puente 2 (m²)':<20}")
print("-" * 70)
print(f"{'Simpson 3/8':<30} {area_simpson_p1:<20.4f} {area_simpson_p2:<20.4f}")
print(f"{'Cuadratura Gaussiana':<30} {area_gauss_p1:<20.4f} {area_gauss_p2:<20.4f}")
print("=" * 70)

print(f"\nDetalles Puente 1:")
print(f"  Rango integración:  [{x_min1:.2f} m, {x_max1:.2f} m]")
print(f"  Área trapecio P11:  {area_trap_p1:.4f} m²")
print(f"\nDetalles Puente 2:")
print(f"  Rango integración:  [0.00 m, {xp18:.2f} m]")
print(f"  Modelo seleccionado: {modelo_nombre}")
