import pandas as pd
import numpy as np
# ────────────── FUNCIONES DE KPI PARA RESTAURACIÓN ────────────── #

def preparar_datos(df):
    """Convierte 'Fecha' a datetime y extrae columnas auxiliares."""
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Mes'] = df['Fecha'].dt.to_period('M')
    df['Año'] = df['Fecha'].dt.year
    return df

def calcular_venta_total(df):
    """Calcula el total vendido."""
    return df['Importe'].sum()

def comensales_totales(df):
    """Cuenta total de comensales."""
    return df['Comensales'].sum()

def ticket_medio(df):
    """Calcula el ticket promedio por comensal."""
    total = calcular_venta_total(df)
    total_comensales = comensales_totales(df)
    return total / total_comensales if total_comensales > 0 else 0

def ventas_por_mes(df):
    """Suma las ventas por mes."""
    return df.groupby('Mes')['Importe'].sum().sort_index()

def ventas_por_anio(df):
    """Suma las ventas por año."""
    return df.groupby('Año')['Importe'].sum().sort_index()

def comparar_con_objetivos(df, objetivo_mensual=None, objetivo_anual=None):
    """Compara la venta acumulada contra los objetivos definidos."""
    ventas_mensuales = ventas_por_mes(df)
    ventas_anuales = ventas_por_anio(df)
    
    comparativa = {}

    if objetivo_mensual:
        comparativa['mensual'] = []
        for mes, venta in ventas_mensuales.items():
            estado = "✅ Cumplido" if venta >= objetivo_mensual else "⚠️ No cumplido"
            comparativa['mensual'].append((str(mes), venta, estado))

    if objetivo_anual:
        for anio, venta in ventas_anuales.items():
            estado = "✅ Cumplido" if venta >= objetivo_anual else "⚠️ No cumplido"
            comparativa['anual'] = (anio, venta, estado)

    return comparativa

def top_dias_facturacion(df, top_n=5):
    """Retorna los días con mayor facturación."""
    resumen = df.groupby('Fecha')['Importe'].sum()
    return resumen.sort_values(ascending=False).head(top_n)

def ventas_por_tipo_servicio(df):
    """Suma de ventas por tipo de servicio (desayuno, comida, cena...)."""
    if 'TipoServicio' in df.columns:
        return df.groupby('TipoServicio')['Importe'].sum().sort_values(ascending=False)
    return None

def rango_horario_mas_rentable(df):
    """Agrupa las ventas por hora del día."""
    if 'Hora' in df.columns:
        df['Hora'] = pd.to_datetime(df['Hora'], format='%H:%M').dt.hour
        return df.groupby('Hora')['Importe'].sum().sort_index()
    return None

def ticket_medio_mensual(df):
    """Calcula ticket medio por mes."""
    if 'Mes' not in df.columns:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df['Mes'] = df['Fecha'].dt.to_period('M')
    agrupado = df.groupby('Mes').agg({'Importe': 'sum', 'Comensales': 'sum'})
    agrupado['TicketMedio'] = agrupado['Importe'] / agrupado['Comensales']
    return agrupado['TicketMedio']

def detectar_alertas(df, objetivos):
    """
    Genera alertas si:
    - Hay una caída significativa (>10%) de ventas respecto al mes anterior.
    - No se cumple el objetivo mensual o anual de ventas.
    """
    alertas = []

    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Mes'] = df['Fecha'].dt.to_period('M')
    df['Año'] = df['Fecha'].dt.year

    ventas_mensuales = df.groupby('Mes')['Importe'].sum().sort_index()

    if len(ventas_mensuales) >= 2:
        mes_actual = ventas_mensuales.index[-1]
        mes_anterior = ventas_mensuales.index[-2]

        venta_actual = ventas_mensuales.iloc[-1]
        venta_anterior = ventas_mensuales.iloc[-2]

        if venta_anterior > 0:
            variacion = (venta_actual - venta_anterior) / venta_anterior * 100
            if variacion < -10:
                alertas.append({
                    "tipo": "caida",
                    "mensaje": f"📉 Caída del {abs(variacion):.1f}% en las ventas de {mes_actual} respecto a {mes_anterior}"
                })

    año_actual = objetivos.get('año', df['Año'].max())
    objetivo_mensual = objetivos.get('mensual', 0)
    objetivo_anual = objetivos.get('anual', 0)

    venta_total_mes_actual = ventas_mensuales.iloc[-1]
    venta_total_anual = df[df['Año'] == año_actual]['Importe'].sum()

    if venta_total_mes_actual < objetivo_mensual:
        alertas.append({
            "tipo": "objetivo_mensual",
            "mensaje": f"🎯 No se alcanzó el objetivo mensual de {objetivo_mensual:.2f}€ en {mes_actual}"
        })

    if venta_total_anual < objetivo_anual:
        alertas.append({
            "tipo": "objetivo_anual",
            "mensaje": f"🎯 Aún no se alcanza el objetivo anual de {objetivo_anual:.2f}€ en {año_actual}"
        })

    return alertas

def calcular_tendencias_mensuales(df):
    """
    Devuelve un resumen con la evolución mensual de:
    - Ventas totales
    - Ticket medio
    Con porcentaje de cambio respecto al mes anterior.
    """
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Mes'] = df['Fecha'].dt.to_period('M')

    ventas_por_mes = df.groupby('Mes')['Importe'].sum().sort_index()
    ticket_medio = df.groupby('Mes').apply(
        lambda x: x['Importe'].sum() / x['Comensales'].sum() if x['Comensales'].sum() > 0 else 0
    )

    resumen = []

    for i in range(1, len(ventas_por_mes)):
        mes_actual = ventas_por_mes.index[i]
        mes_anterior = ventas_por_mes.index[i - 1]

        venta_actual = ventas_por_mes.iloc[i]
        venta_anterior = ventas_por_mes.iloc[i - 1]
        variacion_ventas = ((venta_actual - venta_anterior) / venta_anterior) * 100 if venta_anterior > 0 else 0

        ticket_actual = ticket_medio.iloc[i]
        ticket_anterior = ticket_medio.iloc[i - 1]
        variacion_ticket = ((ticket_actual - ticket_anterior) / ticket_anterior) * 100 if ticket_anterior > 0 else 0

        resumen.append({
            "mes": str(mes_actual),
            "ventas": venta_actual,
            "ticket": round(ticket_actual, 2),
            "variacion_ventas": round(variacion_ventas, 2),
            "variacion_ticket": round(variacion_ticket, 2)
        })

    return resumen

def resumen_por_tipo_servicio(df):
    """
    Calcula ventas totales y ticket medio por tipo de servicio.
    Devuelve una lista de diccionarios con los resultados.
    """
    if 'TipoServicio' not in df.columns:
        return []

    df['Ticket'] = df.apply(lambda x: x['Importe'] / x['Comensales'] if x['Comensales'] > 0 else 0, axis=1)
    agrupado = df.groupby('TipoServicio').agg({
        'Importe': 'sum',
        'Comensales': 'sum',
        'Ticket': 'mean'
    }).reset_index()

    resultados = []
    for _, fila in agrupado.iterrows():
        resultados.append({
            "tipo": fila['TipoServicio'],
            "ventas": round(fila['Importe'], 2),
            "ticket_medio": round(fila['Ticket'], 2),
            "comensales": int(fila['Comensales'])
        })

    return resultados

def resumen_anual_yoy(df, col_fecha='Fecha', col_ventas='venta_total', col_comensales='comensales'):
    d = df.copy()

    # Fecha
    d[col_fecha] = pd.to_datetime(d[col_fecha], errors='coerce')
    d = d.dropna(subset=[col_fecha])
    d['anio'] = d[col_fecha].dt.year

    # Ventas
    d['ventas'] = pd.to_numeric(d[col_ventas], errors='coerce').fillna(0)

    # Ticket medio (si hay comensales)
    if col_comensales in d.columns:
        d[col_comensales] = pd.to_numeric(d[col_comensales], errors='coerce')
        d['ticket_medio'] = d['ventas'] / d[col_comensales].replace(0, np.nan)
    else:
        d['ticket_medio'] = np.nan

    agg = (d.groupby('anio', as_index=False)
             .agg(ventas=('ventas','sum'),
                  ticket_medio=('ticket_medio','mean'))
             .sort_values('anio'))

    agg['var_ventas'] = agg['ventas'].pct_change() * 100
    agg['var_ticket'] = agg['ticket_medio'].pct_change() * 100

    return agg.round(2)

def rentabilidad_por_servicio(df, costes_dict):
    d = df.copy()

    # Asegurar nombres correctos
    if 'TipoServicio' not in d.columns:
        raise KeyError("No se encontró la columna 'TipoServicio' en los datos.")

    # Convertir ventas a numérico
    if 'Importe' not in d.columns:
        raise KeyError("No se encontró la columna 'Importe' en los datos.")
    d['Importe'] = pd.to_numeric(d['Importe'], errors='coerce').fillna(0)

    resultados = []
    for servicio, datos in d.groupby('TipoServicio'):
        ventas = datos['Importe'].sum()
        coste_pct = costes_dict.get(servicio, 0)  # Si no está en el dict, coste=0
        coste = ventas * coste_pct
        rentabilidad = ventas - coste
        margen = (rentabilidad / ventas * 100) if ventas > 0 else 0

        resultados.append({
            'servicio': servicio,
            'ventas': round(ventas, 2),
            'coste': round(coste, 2),
            'rentabilidad': round(rentabilidad, 2),
            'margen': round(margen, 1)
        })

    return resultados

def heatmap_por_dia_hora(df, col_fecha='Fecha', col_hora='Hora', col_ventas='Importe'):
    d = df.copy()

    # Fecha → día de semana
    d[col_fecha] = pd.to_datetime(d[col_fecha], errors='coerce')
    d = d.dropna(subset=[col_fecha])
    d['dow'] = d[col_fecha].dt.dayofweek  # 0=Lun ... 6=Dom

    # Hora → 0..23 (acepta "HH", "HH:MM" o datetime/time)
    if np.issubdtype(d[col_hora].dtype, np.number):
        d['hour'] = pd.to_numeric(d[col_hora], errors='coerce')
    else:
        # intentar parsear "HH:MM"
        h1 = pd.to_datetime(d[col_hora], format='%H:%M', errors='coerce')
        h2 = pd.to_datetime(d[col_hora], errors='coerce')  # por si viene "HH"
        d['hour'] = np.where(h1.notna(), h1.dt.hour,
                     np.where(h2.notna(), h2.dt.hour,
                              pd.to_numeric(d[col_hora], errors='coerce')))
    d['hour'] = d['hour'].astype('float').round().astype('Int64')
    d = d.dropna(subset=['hour'])
    d['hour'] = d['hour'].astype(int).clip(0, 23)

    # Ventas numérico
    d[col_ventas] = pd.to_numeric(d[col_ventas], errors='coerce').fillna(0)

    days_order = [0,1,2,3,4,5,6]
    day_labels = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    hours = list(range(24))

    agg = (d.groupby(['dow','hour'])[col_ventas].sum()
             .reindex(pd.MultiIndex.from_product([days_order, hours], names=['dow','hour']), fill_value=0)
             .reset_index())

    mat = agg.pivot(index='dow', columns='hour', values=col_ventas).loc[days_order, hours].values
    mat = mat.astype(float)
    vmax = float(mat.max()) if mat.size else 0.0

    return {
        'days': day_labels,
        'hours': hours,
        'matrix': mat.tolist(),
        'vmax': vmax
    }
