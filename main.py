from tp import *
from graficos import *

p_tabla1 = leer_csv('Tabla1.csv')
p_tabla2 = leer_csv('Tabla2.csv')

graficar_puntos(p_tabla1, p_tabla2)

p1 = limpiar_y_transformar(p_tabla1, 0, 10)
p2 = limpiar_y_transformar(p_tabla2, 0, 1)

print(f"{'Índice':<8} | {'X (metros)':<12} | {'Y (metros)':<12}")
print("-" * 40)
for i, (x, y) in enumerate(p2):
    print(f"{i:<8} | {x:<12.2f} | {y:<12.2f}")

f1, x1, y1, xi, xf = construir_p1(p1)
f2, x2, y2, xc, rmse2, rmse1 = construir_p2(p2)

graficar_puente1(x1, y1, f1, xi, xf)
graficar_puente2(x2, y2, f2, xc)

area1 = simpson_38_final(f1, 21)
area2 = simpson_38_final(f2, 21)

area1_f2 = calcular_area_simpson38(f1, 21)
area2_f2 = calcular_area_simpson38(f2, 21)

print(area1, area1_f2, area2, area2_f2)

