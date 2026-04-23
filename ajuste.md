# Ajustes y Suavizado de Datos - Explicación Completa

## ¿Por qué hacer ajustes después de rotar?

Después de rotar los puntos (transformar de píxeles a metros), necesitas:

1. **Interpolar** → Tener una función continua, no solo puntos sueltos
2. **Suavizar** → Eliminar ruido de medición
3. **Cerrar el dominio** → Asegurar que la función sea 0 en los bordes (x=0 y x=20)
4. **Facilitar integración** → Simpson necesita una función suave y evaluable en puntos equiespaciados

---

## PUENTE 1: Enfoque con Spline + Márgenes Lineales

### ¿Qué es?
Después de rotar y transformar tus puntos a metros, tienes un conjunto de puntos que representan el **perfil de profundidad**. Pero estos puntos:
- Pueden ser ruidosos o tener oscilaciones
- Están apenas en 10-15 puntos (no es mucho)
- No cubren suavemente toda la sección

### ¿Qué hace `construir_p1`?

```python
def construir_p1(puntos_metros):
    # 1. Extrae los puntos del CENTRO del cauce (donde hay más precisión)
    mask_centro = (x1 > 7.0) & (x1 < 19.8) & (y1 > 5.0)
    x_c = x1[mask_centro]
    y_c = y1[mask_centro]
    
    # 2. Crea un Spline SOLO con esos puntos limpios
    f_central = PchipInterpolator(x_c, y_c)
    
    # 3. Crea TRES TRAMOS:
    #    - Recta diagonal izquierda (x=0 a inicio del cauce)
    #    - Spline suave en el medio (centro del cauce)
    #    - Recta diagonal derecha (fin del cauce a x=20)
    
    # 4. Devuelve una función PARTIDA que cambia según donde estés
```

### Pasos detallados:

**Paso 1: Filtro Anti-Oscilación**
- Ignora puntos fuera del rango 7m-20m (márgenes inciertas)
- Ignora puntos con y < 5m (errores de medición)
- Resultado: Solo los puntos más confiables del cauce central

**Paso 2: Interpolación PCHIP**
- PCHIP = "Piecewise Cubic Hermite Interpolating Polynomial"
- Es como conectar puntos con curvas suaves, sin oscilaciones
- Mejor que Lagrange para datos reales

**Paso 3: Tramos Lineales en Márgenes**
```
Recta izquierda: (0,0) → primer punto del spline
    Pendiente = y_inicio / x_inicio
    
Recta derecha: último punto del spline → (20,0)
    Pendiente = (0 - y_fin) / (20 - x_fin)
```

**Paso 4: Función Partida Final**
```
f(x) = {
    recta_izq(x)      si x ≤ x_inicio
    spline(x)         si x_inicio < x ≤ x_fin
    recta_der(x)      si x_fin < x ≤ 20
    0                 si x > 20
}
```

### Visualización:
```
        *  *              ← Puntos ruidosos originales
      /    \
    /        \            ← Spline suave (PCHIP)
   /          \
  /___________\          ← Rectas en las márgenes
0            20 metros
```

### ¿Por qué es mejor?
- ✅ Elimina el ruido de las márgenes (donde hay incertidumbre)
- ✅ Mantiene los datos reales del cauce central
- ✅ Crea una función **suave y continua** para Simpson
- ✅ Simula mejor la física real del río
- ✅ Garantiza que profundidad = 0 en los apoyos (x=0 y x=20)

---

## PUENTE 2: Enfoque Polinomial (Cuadráticas)

Tu código implementa **DOS modelos competidores**:

### **Modelo A: 2 Cuadráticas + 1 Recta**

```
Tramo 1: Cuadrática P1→P8  (0 a ~14.59 m)
         y = a₁x² + b₁x + c₁
         
Tramo 2: Cuadrática P8→P18 (14.59 a ~17.12 m)
         y = a₂x² + b₂x + c₂
         
Tramo 3: Recta lineal P18→P20 (17.12 a 20 m)
         y = mx + n
```

**Idea**: El río no es simétrico. La parte izquierda tiene diferente curvatura que la derecha, así que necesitamos 2 parábolas diferentes.

**Ventajas**:
- Más flexible (adapta mejor a cambios de curvatura)
- Captura mejor la geometría real

**Desventajas**:
- Más complejo (más parámetros)
- Puede overfitting si hay ruido

### **Modelo B: 1 Cuadrática + 1 Recta** (MÁS SIMPLE)

```
Tramo 1: Una sola cuadrática (0 a ~17.12 m)
         y = ax² + bx + c
         
Tramo 2: Recta lineal (~17.12 a 20 m)
         y = mx + n
```

**Idea**: Ajustamos UNA SOLA parábola a todo el cauce principal, luego una recta en la zona de desagüe.

**Ventajas**:
- Más simple (menos parámetros)
- Menos riesgo de overfitting
- Más robusto ante ruido

**Desventajas**:
- Menos flexible

### ¿Cómo elige el mejor modelo?

El código calcula el **Error Cuadrático Medio (RMSE)** para cada modelo:

```python
# RMSE mide cuánto se desvían nuestras predicciones de los puntos reales
rmse_a = √(suma((y_real - y_modelo_a)²) / n)
rmse_b = √(suma((y_real - y_modelo_b)²) / n)

if rmse_a < rmse_b:
    print("Ganador: Modelo A")
    usar_modelo_a()
else:
    print("Ganador: Modelo B")
    usar_modelo_b()
```

**Ejemplo:**
```
RMSE Modelo A (2 cuadráticas): 0.234
RMSE Modelo B (1 cuadrática):  0.189
            ↓
Ganador: Modelo B (más preciso)
```

---

## Comparación: Puente 1 vs Puente 2

| Aspecto | Puente 1 | Puente 2 |
|---------|----------|----------|
| **Tipo** | Spline suave + rectas | Polinomios cuadráticos |
| **Flexibilidad** | Muy flexible (sigue datos exactos) | Menos flexible (forma parabólica fija) |
| **Suavidad** | Muy suave (PCHIP) | Suave pero más rígida |
| **Para Simpson 3/8** | ✅ Excelente | ✅ Bueno |
| **Interpretación física** | "Vamos a filtrar el ruido de medición" | "El río sigue forma parabólica" |
| **Ventaja principal** | Adaptabilidad a formas irregulares | Simplicidad matemática |

---

## Fórmulas de Simpson 3/8

Ambos modelos se integran usando **Simpson 3/8**, que requiere:
- Función continua ✓ (ambos modelos la tienen)
- Puntos **equiespaciados** en X ✓ (se generan con `linspace`)
- Número de intervalos múltiplo de 3 ✓ (21 intervalos)

```python
def calcular_area_simpson38(f, b, h=1):
    n = 21  # 21 intervalos (múltiplo de 3)
    x_nodos = np.linspace(0, n, n + 1)  # Equiespaciados
    y_nodos = [f(xi) for xi in x_nodos]
    
    suma = y_nodos[0] + y_nodos[-1]
    for i in range(1, n):
        if i % 3 == 0:
            suma += 2 * y_nodos[i]   # Cada 3er punto
        else:
            suma += 3 * y_nodos[i]   # Otros puntos
            
    area = (3 * h / 8) * suma
    return area
```

**¿Por qué funciona?**
- Simpson 3/8 usa paneles de 3 subintervalos (por eso el nombre)
- Los pesos son: 3, 3, 2, 3, 3, 2, 3, 3, 2...
- Fórmula: Área ≈ (3h/8) × (suma ponderada)
- Es exacta para polinomios hasta grado 3

---

## Diagrama de Flujo

```
Puntos rotados en píxeles
        ↓
    Transformar a metros
        ↓
    ├── PUENTE 1 ──────────────────┐
    │   - Filtro ruido            │
    │   - Spline PCHIP            │
    │   - Rectas en márgenes      │
    │   → Función partida suave    │
    │                              │
    └─────────────────────────────┤
                                   ↓
    ├── PUENTE 2 ──────────────────┐
    │   - Modelo A: 2 cuadráticas │
    │   - Modelo B: 1 cuadrática  │
    │   - Compara errores (RMSE)  │
    │   → Elige modelo ganador     │
    │                              │
    └─────────────────────────────┤
                                   ↓
                        Evaluar en 21 puntos
                        equiespaciados
                                   ↓
                        Simpson 3/8
                                   ↓
                            ÁREA (m²)
```

---

## Verificación de Calidad

Para asegurar que todo está bien hecho:

1. **¿Simpson 3/8 está correctamente aplicado?**
   - ✅ Puntos equiespaciados: `linspace(0, 21, 22)`
   - ✅ Número de intervalos = 21 (múltiplo de 3)
   - ✅ Pesos correctos: 3, 3, 2 repeating

2. **¿La función es suave?**
   - ✅ Puente 1: PCHIP es suave por definición
   - ✅ Puente 2: Parábola + recta (ambas suaves)

3. **¿Cubre todo el dominio [0, 20]?**
   - ✅ Ambas funciones retornan 0 para x > 20
   - ✅ Ambas son continuas

---

## Conclusión

Ambos ajustes están **bien fundamentados matemáticamente**:

- **Puente 1** es más flexible y captura mejor irregularidades
- **Puente 2** es más simple y basado en física (forma parabólica típica de ríos)

La elección depende de tu objetivo:
- Si quieres máxima precisión en los datos → Puente 1
- Si quieres modelo simple y robusto → Puente 2
