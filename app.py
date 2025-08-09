from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import pandas as pd
from werkzeug.utils import secure_filename
from data_processing import kpi
from functools import wraps
from dotenv import load_dotenv
load_dotenv()
from data_processing.kpi import resumen_anual_yoy, rentabilidad_por_servicio, heatmap_por_dia_hora

# ─────────────── AUTH POR VARIABLES DE ENTORNO ─────────────── #
APP_USER = os.getenv("APP_USER", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "1234")

# ─────────────── LOGIN ─────────────── #
def login_requerido(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorada

# ─────────────── CONFIGURACIÓN ─────────────── #
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

app = Flask(__name__)
# Clave de sesión desde variable de entorno (con fallback para local)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecreto')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Opcionales de seguridad (bien para producción)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# Si usas HTTPS en producción, activa la siguiente línea:
# app.config['SESSION_COOKIE_SECURE'] = True

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ─────────────── RUTA DE LOGIN (ajustada a env vars) ─────────────── #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        clave = request.form.get('clave', '')

        if usuario == APP_USER and clave == APP_PASSWORD:
            session['usuario'] = usuario
            flash('✅ Login correcto', 'success')
            return redirect(url_for('index'))
        else:
            flash('❌ Credenciales incorrectas.', 'danger')

    return render_template('login.html')

# ─────────────── RUTA DE LOGOUT ─────────────── #
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash("🔒 Sesión cerrada.", "info")
    return redirect(url_for('login'))

# ─────────────── INICIO ─────────────── #
@app.route('/')
@login_requerido
def index():
    return render_template('index.html')

# ─────────────── SUBIDA DE ARCHIVO ─────────────── #
@app.route('/upload', methods=['POST'])
@login_requerido
def upload_file():
    if 'file' not in request.files:
        flash('No se seleccionó ningún archivo.', 'warning')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('Nombre de archivo vacío.', 'warning')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Comprobación básica de lectura (opcional, para feedback inmediato)
        try:
            if filename.lower().endswith('.csv'):
                _ = pd.read_csv(filepath)
            elif filename.lower().endswith('.xlsx'):
                _ = pd.read_excel(filepath)
        except Exception as e:
            flash(f"Error leyendo el archivo: {e}", "danger")
            return redirect(url_for('index'))

        return redirect(url_for('dashboard', filename=filename))

    flash('Archivo no permitido.', 'warning')
    return redirect(url_for('index'))


# ─────────────── DASHBOARD PRINCIPAL ─────────────── #
@app.route('/dashboard')
@login_requerido
def dashboard():
    filename = request.args.get('filename')
    if not filename:
        flash("Archivo no encontrado.")
        return redirect(url_for('index'))

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Leer archivo
    if filename.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)

    # Procesamiento principal
    df = kpi.preparar_datos(df)
    total_ventas = kpi.calcular_venta_total(df)
    comensales = kpi.comensales_totales(df)
    ticket_medio = kpi.ticket_medio(df)

    objetivo_mensual = request.args.get('objetivo_mensual', default=5000, type=float)
    objetivo_anual = request.args.get('objetivo_anual', default=60000, type=float)

    comparativa = kpi.comparar_con_objetivos(df, objetivo_mensual, objetivo_anual)
    top_dias = kpi.top_dias_facturacion(df).to_dict()

    ventas_mensuales = kpi.ventas_por_mes(df)
    labels = [str(mes) for mes in ventas_mensuales.index]
    valores = [float(valor) for valor in ventas_mensuales.values]

    ventas_tipo_servicio = kpi.ventas_por_tipo_servicio(df)
    servicios_labels = list(ventas_tipo_servicio.index)
    servicios_valores = list(ventas_tipo_servicio.values)

    ticket_mensual = kpi.ticket_medio_mensual(df)
    ticket_labels = [str(mes) for mes in ticket_mensual.index]
    ticket_valores = [round(valor, 2) for valor in ticket_mensual.values]

    objetivos = {
        'mensual': objetivo_mensual,
        'anual': objetivo_anual,
        'año': 2025
    }
    alertas = kpi.detectar_alertas(df, objetivos)
    tendencias = kpi.calcular_tendencias_mensuales(df)
    resumen_servicio = kpi.resumen_por_tipo_servicio(df)

    # 📆 Comparativa Año vs. Año (Punto 1)
    resumen_yoy = resumen_anual_yoy(
        df,
        col_fecha='Fecha',
        col_ventas='Importe',
        col_comensales='Comensales'
    ).to_dict(orient='records')

    # 💰 Rentabilidad por tipo de servicio (Punto 2)
    costes_estimados = {
        'Desayuno': 0.4,
        'Almuerzo': 0.55,
        'Cena': 0.5
    }
    rentabilidad_servicio = kpi.rentabilidad_por_servicio(df, costes_estimados)
# 🔥 Heatmap día-hora
    heatmap = heatmap_por_dia_hora(df, col_fecha='Fecha', col_hora='Hora', col_ventas='Importe')

    return render_template(
        'dashboard.html',
        filename=filename,
        total_ventas=total_ventas,
        comensales=comensales,
        ticket_medio=ticket_medio,
        comparativa=comparativa,
        top_dias=top_dias,
        labels=labels,
        valores=valores,
        servicios_labels=servicios_labels,
        servicios_valores=servicios_valores,
        ticket_labels=ticket_labels,
        ticket_valores=ticket_valores,
        objetivo_mensual=objetivo_mensual,
        objetivo_anual=objetivo_anual,
        alertas=alertas,
        tendencias=tendencias,
        resumen_servicio=resumen_servicio,
        resumen_yoy=resumen_yoy,                      # Punto 1
        rentabilidad_servicio=rentabilidad_servicio,   # Punto 2
        heatmap_days=heatmap['days'],
        heatmap_hours=heatmap['hours'],
        heatmap_matrix=heatmap['matrix'],
        heatmap_max=heatmap['vmax'],

    )

@app.route('/demo')
def demo():
    return render_template('demo.html')


# ─────────────── INICIAR APP ─────────────── #
if __name__ == '__main__':
    app.run(debug=True)
