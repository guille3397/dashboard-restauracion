
📄 README – Requisitos para Subir Archivos de Datos (Centro de KPIs para Restauración)

🧾 Formato de archivo admitido:
- .csv (separado por comas o punto y coma)
- .xlsx (Excel moderno)

📌 Estructura mínima requerida:

El archivo debe contener al menos las siguientes columnas:

| Columna       | Tipo de dato       | Descripción                                 |
|---------------|--------------------|---------------------------------------------|
| Fecha         | Fecha (YYYY-MM-DD) | Fecha de la transacción                     |
| Importe       | Número decimal     | Total de la venta (por ticket o factura)    |
| Comensales    | Número entero      | Personas atendidas en esa venta             |

✅ Ejemplo básico:
Fecha,Importe,Comensales
2025-01-01,120.50,4
2025-01-01,55.00,2
2025-01-02,220.00,6

📌 Columnas opcionales:

| Columna       | Tipo     | Propósito                                   |
|----------------|----------|---------------------------------------------|
| TipoServicio   | Texto    | Segmentación por tipo (Desayuno, Cena...)   |
| Hora           | HH:MM    | Análisis de ventas por franja horaria       |

📌 Recomendaciones importantes:

1. Formato de fecha:
   - Usa el formato YYYY-MM-DD (ej: 2025-07-15).
   - Evita formatos como 15/07/2025 o 07-15-2025.

2. Decimal con punto:
   - Usa punto (.) como separador decimal.
   - Correcto: 120.50 | Incorrecto: 120,50

3. Nombres de columnas exactos:
   - Sensibles a mayúsculas y acentos: 'Fecha', 'Importe', 'Comensales'

4. Sin filas vacías ni totales manuales:
   - No incluyas totales o subtotales como filas.

5. Hora en formato 24h:
   - Si se incluye, que sea tipo 13:30, 21:00, etc.

📥 ¿Dónde se sube?
Desde la página principal de la aplicación Flask (http://localhost:5000), usa el formulario para seleccionar y subir tu archivo. Se generará un dashboard automático con KPIs.

