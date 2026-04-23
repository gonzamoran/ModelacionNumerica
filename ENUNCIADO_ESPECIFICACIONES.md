# Enunciado del Trabajo Práctico

## Especificación del Dominio

Extraído del enunciado oficial:

> "Para cada una de las imágenes satelitales, y utilizando los puntos digitalizados, con la distancia de referencia:
> 
> ...Tomar un punto (P1) como centro de coordenadas y pasar las coordenadas de los puntos digitalizados a **unidades de distancia, sabiendo que los puentes tienen una luz de 20 m**."

## Implicaciones

- **Luz del puente** = 20 metros (distancia entre apoyos)
- **Dominio de integración** = [0, 20] metros
- **Coordenadas**: 
  - x = 0 m → Apoyo izquierdo (P1)
  - x = 20 m → Apoyo derecho (P2)
  - y > 0 → Profundidad bajo el puente

## Calibración

En `limpiar_y_transformar()`, se usa:
```python
# Los apoyos en píxeles
p1 = puntos[idx_p1]  # Primer apoyo
p2 = puntos[idx_p2]  # Segundo apoyo

# Distancia entre apoyos en píxeles
distancia_px = dist(p1, p2)

# Factor de conversión: 20 metros / distancia_en_pixeles
factor = 20.0 / distancia_px
```

Esto escala los datos de píxeles a metros, usando los apoyos del puente como referencia.

## Justificación para filtrar datos

Por lo tanto, los puntos fuera del rango [0, 20] están **fuera del puente** y no deben usarse para:
- Ajuste de modelos
- Cálculo de área bajo la curva (Simpson 3/8)
- Análisis de la sección transversal

Son datos de contaminación o medición de zonas adyacentes.
