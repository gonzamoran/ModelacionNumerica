import numpy as np
import matplotlib.pyplot as plt


def graficar_puntos(puntos1, puntos2):
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
    print("Coordenada X de P10:", puntos_t2_metros[9][0])
    # 3. Graficación
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # --- Lógica Puente 1 ---
    x_r1, y_r1 = zip(*puntos_t1_metros)
    axes[0].scatter(x_r1, y_r1, color='green', s=60, zorder=5)
    for i, (x, y) in enumerate(zip(x_r1, y_r1)):
        axes[0].annotate(f'idx{i}', (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7)

    axes[0].set_title("Puente 1 — Perfil de Profundidad")
    axes[0].set_xlabel("Distancia horizontal (m)")
    axes[0].set_ylabel("Altura relativa (m)")
    axes[0].axhline(0, color='gray', ls='--', alpha=0.5, label='Nivel del puente')
    axes[0].legend()
    axes[0].grid(True)

    # --- Lógica Puente 2 ---
    x_r2, y_r2 = zip(*puntos_t2_metros)
    axes[1].scatter(x_r2, y_r2, color='orange', s=60, zorder=5)
    for i, (x, y) in enumerate(zip(x_r2, y_r2)):
        # Mantengo tu lógica de etiquetas
        lbl = f'P{i+1}'
        axes[1].annotate(lbl, (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7)

    axes[1].set_title("Puente 2 — Perfil de Profundidad")
    axes[1].set_xlabel("Distancia horizontal (m)")
    axes[1].set_ylabel("Altura relativa (m)")
    axes[1].axhline(0, color='gray', ls='--', alpha=0.5, label='Nivel del puente')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    plt.savefig("grafico_puentes.png")
    #plt.show()

def graficar_puente1(x, y, f, x_ini, x_fin):
    xp = np.linspace(0, 20, 500)
    yp = [f(val) for val in xp]

    plt.figure(figsize=(12, 6))
    plt.scatter(x, y, color='black', label='Puntos medidos', zorder=5)
    plt.plot(xp, yp, 'r-', lw=2, label='Función Partida Estable')
    plt.axvline(x_ini, color='orange', ls='--', label='Inicio Spline')
    plt.axvline(x_fin, color='purple', ls='--', label='Fin Spline')
    plt.title("Puente 1: Perfil corregido para Integración")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig("punto_c_i.jpg")

def graficar_puente2(x, y, f, x_corte):
    plt.figure(figsize=(10, 5))
    x_p2_plot = np.linspace(0, 21, 500)
    y_p2_plot = [f(v) for v in x_p2_plot]
    plt.plot(x_p2_plot, y_p2_plot, 'orange', label='Modelo Ganador (2 tramos)')
    plt.scatter(x, y, color='black', s=10)
    plt.axvline(x_corte, ls='--', color='red', label='Cambio de función')
    plt.legend()
    plt.savefig('ajuste_p2.png')
    plt.show()