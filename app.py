from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import mysql.connector
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración de la base de datos MySQL
db_config = {
    'host': '11.168.103.252',
    'user': 'joseastelllo',
    'password': 'cH@70FIs7B4E',
    'database': 'control_unidades'
}

# Configuration for File Uploads
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads', 'mantenimientos')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Optional: 16MB max upload size

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


def get_connection():
    return mysql.connector.connect(**db_config)

# Agregar filtro number_format a Jinja2
@app.template_filter('number_format')
def number_format(value, decimals=0, decimal_point='.', thousands_sep=','):
    try:
        value = float(value)
        format_string = "%0.{0}f".format(decimals)
        number = format_string % value
        if thousands_sep:
            parts = number.split('.')
            parts[0] = "{:,}".format(int(parts[0])).replace(",", thousands_sep)
            number = decimal_point.join(parts)
        return number
    except (ValueError, TypeError):
        return value

@app.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.*, e.color as estado_color
        FROM unidades u
        LEFT JOIN estados e ON BINARY u.estado = BINARY e.nombre
        ORDER BY u.tipo, u.marca, u.serie
    """)
    unidades = cursor.fetchall()

    cursor.execute("""
        SELECT
            COUNT(*) as total_unidades,
            COALESCE(SUM(CASE WHEN u.estado = 'Funcional' THEN 1 ELSE 0 END), 0) as funcionales,
            COALESCE(SUM(CASE WHEN u.estado = 'En Reparación' THEN 1 ELSE 0 END), 0) as en_reparacion,
            COALESCE(SUM(CASE WHEN u.estado = 'Sin Reparación' THEN 1 ELSE 0 END), 0) as sin_reparacion
        FROM unidades u
    """)
    resumen = cursor.fetchone() or {}

    resumen['total_unidades'] = resumen.get('total_unidades', 0)
    resumen['funcionales'] = resumen.get('funcionales', 0)
    resumen['en_reparacion'] = resumen.get('en_reparacion', 0)
    resumen['sin_reparacion'] = resumen.get('sin_reparacion', 0)

    cursor.execute("SELECT nombre, color FROM estados ORDER BY es_predeterminado DESC, nombre")
    estados = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('index.html',
                         unidades=unidades,
                         resumen=resumen,
                         estados=estados)

@app.route("/agregar_unidad", methods=["POST"])
def agregar_unidad():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos no válidos"}), 400

    serie = data.get("serie")
    modelo = data.get("modelo")
    marca = data.get("marca")
    descripcion = data.get("descripcion")
    numero_economico = data.get("numero_economico")
    tipo = data.get("tipo")
    estado = data.get("estado", "Funcional")

    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO unidades (serie, modelo, marca, descripcion, numero_economico, tipo, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (serie, modelo, marca, descripcion, numero_economico, tipo, estado))
    conexion.commit()
    nuevo_id = cursor.lastrowid
    cursor.close()
    conexion.close()

    return jsonify({
        "id": nuevo_id, "serie": serie, "modelo": modelo, "marca": marca,
        "numero_economico": numero_economico, "tipo": tipo, "estado": estado
    })

@app.route('/agregar_combustible', methods=['POST'])
def agregar_combustible_antigua():
    datos = (
        request.form['unidad_id'], request.form['fecha'], request.form['litros'],
        request.form.get('kilometraje'), request.form.get('observaciones')
    )
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO combustible (unidad_id, fecha, litros, kilometraje, observaciones)
        VALUES (%s, %s, %s, %s, %s)
    """, datos)
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

# DEPRECATED: This route is for older form submissions or direct HTML form posts.
# Prefer using the POST /api/mantenimientos endpoint for new integrations
# as it offers more features and a consistent JSON response.
@app.route('/agregar_mantenimiento', methods=['POST'])
def agregar_mantenimiento():
    datos = (
        request.form['unidad_id'], request.form['fecha'], request.form['descripcion'],
        request.form.get('costo'), request.form.get('taller'), request.form.get('kilometraje')
    )
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mantenimientos (unidad_id, fecha, descripcion, costo, taller, kilometraje)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, datos)
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route("/eliminar_unidad/<int:unidad_id>", methods=["POST"])
def eliminar_unidad(unidad_id):
    try:
        if not unidad_id:
            return jsonify({"success": False, "error": "ID de unidad no proporcionado"}), 400
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM combustible WHERE unidad_id = %s", (unidad_id,))
        cursor.execute("DELETE FROM mantenimientos WHERE unidad_id = %s", (unidad_id,))
        cursor.execute("DELETE FROM unidades WHERE id = %s", (unidad_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Unidad eliminada correctamente"})
    except Exception as e:
        print(f"Error al eliminar la unidad: {e}")
        return jsonify({"success": False, "error": "Error al eliminar la unidad"}), 500

@app.route('/combustibles')
def combustibles():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.id, u.serie, u.marca, u.tipo, c.fecha as ultima_fecha,
                   c.litros as ultimos_litros, c.precio as ultimo_precio, c.total as ultimo_total,
                   DATE_FORMAT(c.fecha, '%Y-%m') as mes_anio
            FROM unidades u
            LEFT JOIN (
                SELECT unidad_id, MAX(fecha) as max_fecha FROM combustible GROUP BY unidad_id
            ) ultimo ON u.id = ultimo.unidad_id
            LEFT JOIN combustible c ON c.unidad_id = ultimo.unidad_id AND c.fecha = ultimo.max_fecha
            ORDER BY u.tipo, u.marca, u.serie
        """)
        unidades = cursor.fetchall()
        for unidad in unidades:
            if unidad['id']:
                cursor.execute("""
                    SELECT DATE_FORMAT(fecha, '%Y-%m') as mes_anio, SUM(litros) as total_litros,
                           SUM(total) as total_importe
                    FROM combustible WHERE unidad_id = %s GROUP BY DATE_FORMAT(fecha, '%Y-%m')
                    ORDER BY mes_anio DESC
                """, (unidad['id'],))
                unidad['meses'] = cursor.fetchall()
                unidad['total_general_litros'] = sum(mes['total_litros'] or 0 for mes in unidad['meses'])
                unidad['total_general_importe'] = sum(float(mes['total_importe'] or 0) for mes in unidad['meses'])
        return render_template('combustibles.html', unidades=unidades, now=datetime.now().strftime('%Y-%m-%dT%H:%M'))
    except Exception as e:
        print(f"Error en ruta /combustibles: {str(e)}")
        return render_template('error.html', error=str(e)), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/ultimo-kilometraje/<int:unidad_id>')
def obtener_ultimo_kilometraje(unidad_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT kilometraje FROM combustible WHERE unidad_id = %s ORDER BY fecha DESC, id DESC LIMIT 1", (unidad_id,))
        resultado = cursor.fetchone()
        return jsonify({"kilometraje": resultado['kilometraje'] if resultado and 'kilometraje' in resultado else ""})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/combustible/agregar/<int:unidad_id>', methods=['POST'])
def agregar_combustible_nuevo(unidad_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, serie, marca, tipo FROM unidades WHERE id = %s", (unidad_id,))
        unidad = cursor.fetchone()
        if not unidad: return jsonify({"error": "Unidad no encontrada"}), 404

        data = request.form
        fecha, litros_str, precio_str = data.get('fecha'), data.get('litros'), data.get('precio')
        kilometraje, observaciones = data.get('kilometraje'), data.get('observaciones', '')

        if not all([fecha, litros_str, precio_str]):
            return jsonify({"error": "Fecha, litros y precio son campos requeridos"}), 400

        try:
            litros, precio = float(litros_str.replace(',', '.')), float(precio_str.replace(',', '.'))
            if litros <= 0 or precio <= 0: return jsonify({"error": "Los valores deben ser mayores a cero"}), 400
            total = litros * precio
        except ValueError:
            return jsonify({"error": "Los valores de litros y precio deben ser números válidos"}), 400

        cursor.execute("""
            INSERT INTO combustible (unidad_id, fecha, litros, precio, total, kilometraje, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (unidad_id, fecha, litros, precio, total, kilometraje, observaciones))

        if kilometraje:
            try: cursor.execute("UPDATE unidades SET kilometraje = %s WHERE id = %s", (int(kilometraje.replace('.', '')), unidad_id))
            except ValueError: pass

        conn.commit()
        cursor.execute("SELECT DATE_FORMAT(fecha, '%%d/%%m/%%Y %%H:%%i') as fecha_formateada, litros, precio, total, observaciones FROM combustible WHERE id = LAST_INSERT_ID()")
        registro = cursor.fetchone()

        return jsonify({
            "success": True, "mensaje": "Carga de combustible registrada correctamente",
            "registro": {
                "fecha": registro['fecha_formateada'],
                "litros": f"{float(registro['litros']):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                "precio": f"{float(registro['precio']):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                "total": f"{float(registro['total']):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                "observaciones": registro['observaciones'] or ''
            }, "unidad": unidad
        })
    except Exception as e:
        conn.rollback()
        print(f"Error al registrar combustible: {str(e)}")
        return jsonify({"success": False, "error": f"Error al registrar la carga: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/mantenimientos')
def ver_mantenimientos():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        filtros = {k: v for k, v in request.args.items() if v} # Collect non-empty args
        page = int(filtros.pop('page', 1)) # Pop page from filters, default to 1

        query = "SELECT m.*, u.serie, u.marca, u.modelo FROM mantenimientos m JOIN unidades u ON m.unidad_id = u.id WHERE 1=1"
        params = []

        if filtros.get('unidad_id'): query += " AND m.unidad_id = %s"; params.append(filtros['unidad_id'])
        if filtros.get('tipo'): query += " AND m.tipo = %s"; params.append(filtros['tipo'])
        if filtros.get('fecha_desde'): query += " AND DATE(m.fecha) >= %s"; params.append(filtros['fecha_desde'])
        if filtros.get('fecha_hasta'): query += " AND DATE(m.fecha) <= %s"; params.append(filtros['fecha_hasta'])
        query += " ORDER BY m.fecha DESC"

        cursor.execute(query, tuple(params))
        all_mantenimientos = cursor.fetchall()

        PER_PAGE = 10
        total_items = len(all_mantenimientos)
        start_index, end_index = (page - 1) * PER_PAGE, page * PER_PAGE
        mantenimientos_paginados = all_mantenimientos[start_index:end_index]
        total_pages = (total_items + PER_PAGE - 1) // PER_PAGE if PER_PAGE > 0 else 0

        pagination_obj = {
            'page': page, 'per_page': PER_PAGE, 'total_items': total_items, 'total_pages': total_pages,
            'has_prev': page > 1, 'prev_num': page - 1 if page > 1 else None,
            'has_next': page < total_pages, 'next_num': page + 1 if page < total_pages else None,
            'iter_pages': list(range(1, total_pages + 1))
        }

        cursor.execute("SELECT id, serie, marca, modelo FROM unidades ORDER BY marca, modelo")
        unidades = cursor.fetchall()

        return render_template('mantenimientos.html',
                             mantenimientos=mantenimientos_paginados, unidades=unidades,
                             pagination=pagination_obj, request_args=filtros)
    except Exception as e:
        print(f"Error en ver_mantenimientos: {str(e)}")
        return render_template('error.html', error="Ocurrió un error al cargar los mantenimientos"), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/mantenimientos/<int:mantenimiento_id>', methods=['GET'])
def obtener_mantenimiento(mantenimiento_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT m.*, u.serie, u.marca, u.modelo FROM mantenimientos m JOIN unidades u ON m.unidad_id = u.id WHERE m.id = %s", (mantenimiento_id,))
        mantenimiento = cursor.fetchone()
        if not mantenimiento: return jsonify({"success": False, "message": "Mantenimiento no encontrado"}), 404
        if mantenimiento.get('fecha'): mantenimiento['fecha'] = mantenimiento['fecha'].strftime('%Y-%m-%dT%H:%M')
        if mantenimiento.get('proximo_mantenimiento_fecha'): mantenimiento['proximo_mantenimiento_fecha'] = mantenimiento['proximo_mantenimiento_fecha'].strftime('%Y-%m-%d')
        return jsonify({"success": True, "data": mantenimiento})
    except Exception as e:
        print(f"Error al obtener mantenimiento: {str(e)}")
        return jsonify({"success": False, "message": "Error al obtener el mantenimiento"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/mantenimientos', methods=['POST'])
@app.route('/api/mantenimientos/<int:mantenimiento_id>', methods=['PUT'])
def guardar_mantenimiento(mantenimiento_id=None):
    try:
        data = request.form.to_dict()
        required_fields = ['unidad_id', 'fecha', 'tipo', 'descripcion']
        for field in required_fields:
            if not data.get(field): return jsonify({"success": False, "message": f"El campo {field} es requerido"}), 400

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        trabajos_realizados_detalle = data.get('trabajos_realizados_detalle')
        costo_db = float(data.get('costo')) if data.get('costo') and data.get('costo').strip() else None
        kilometraje_db = int(data.get('kilometraje')) if data.get('kilometraje') and data.get('kilometraje').strip() else None
        proximo_km_db = int(data.get('proximo_mantenimiento_km')) if data.get('proximo_mantenimiento_km') and data.get('proximo_mantenimiento_km').strip() else None
        proximo_fecha_db = data.get('proximo_mantenimiento_fecha') if data.get('proximo_mantenimiento_fecha') and data.get('proximo_mantenimiento_fecha').strip() else None
        observaciones = data.get('observaciones')
        completado = data.get('completado', 'false').lower() == 'true'

        if request.method == 'POST':
            query = """
                INSERT INTO mantenimientos (unidad_id, fecha, tipo, descripcion, trabajos_realizados_detalle, costo, proveedor,
                                         kilometraje, proximo_mantenimiento_km, proximo_mantenimiento_fecha,
                                         observaciones, completado, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            params = (data['unidad_id'], data['fecha'], data['tipo'], data['descripcion'], trabajos_realizados_detalle,
                      costo_db, data.get('proveedor'), kilometraje_db, proximo_km_db, proximo_fecha_db,
                      observaciones, completado)
            mensaje = "Mantenimiento creado correctamente"
        else: # PUT
            query = """
                UPDATE mantenimientos SET unidad_id = %s, fecha = %s, tipo = %s, descripcion = %s,
                                       trabajos_realizados_detalle = %s, costo = %s, proveedor = %s,
                                       kilometraje = %s, proximo_mantenimiento_km = %s, proximo_mantenimiento_fecha = %s,
                                       observaciones = %s, completado = %s, updated_at = NOW()
                WHERE id = %s
            """
            params = (data['unidad_id'], data['fecha'], data['tipo'], data['descripcion'], trabajos_realizados_detalle,
                      costo_db, data.get('proveedor'), kilometraje_db, proximo_km_db, proximo_fecha_db,
                      observaciones, completado, mantenimiento_id)
            mensaje = "Mantenimiento actualizado correctamente"

        cursor.execute(query, params)
        conn.commit()
        return jsonify({"success": True, "message": mensaje})
    except Exception as e:
        if 'conn' in locals() and conn.is_connected(): conn.rollback()
        return jsonify({"success": False, "message": f"Error al guardar el mantenimiento: {str(e)}"}), 500
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'conn' in locals() and conn.is_connected(): conn.close()

@app.route('/api/mantenimientos/<int:mantenimiento_id>/archivos', methods=['POST'])
def agregar_archivo_mantenimiento(mantenimiento_id):
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No se encontró el archivo (file part missing)"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No se seleccionó ningún archivo (filename empty)"}), 400

    if file:
        try:
            original_filename = secure_filename(file.filename)
            file_ext = os.path.splitext(original_filename)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"

            mantenimiento_specific_folder_name = str(mantenimiento_id)
            storable_path = os.path.join(mantenimiento_specific_folder_name, unique_filename).replace("\\", "/")

            mantenimiento_upload_target_abs_path = os.path.join(app.config['UPLOAD_FOLDER'], mantenimiento_specific_folder_name)
            if not os.path.exists(mantenimiento_upload_target_abs_path):
                os.makedirs(mantenimiento_upload_target_abs_path)

            filepath_on_disk = os.path.join(mantenimiento_upload_target_abs_path, unique_filename)
            file.save(filepath_on_disk)

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                INSERT INTO mantenimiento_archivos (mantenimiento_id, nombre_archivo, ruta_archivo, tipo_mime)
                VALUES (%s, %s, %s, %s)
            """, (mantenimiento_id, original_filename, storable_path, file.mimetype))
            conn.commit()
            new_file_id = cursor.lastrowid

            cursor.execute("SELECT id, nombre_archivo, ruta_archivo, tipo_mime, DATE_FORMAT(fecha_subida, '%Y-%m-%d %H:%i:%s') as fecha_subida FROM mantenimiento_archivos WHERE id = %s", (new_file_id,))
            new_file_details = cursor.fetchone()

            cursor.close()
            conn.close()

            return jsonify({"success": True, "message": "Archivo subido correctamente", "file": new_file_details }), 201
        except Exception as e:
            app.logger.error(f"Error al subir el archivo para mantenimiento {mantenimiento_id}: {str(e)}")
            return jsonify({"success": False, "message": f"Error al subir el archivo: {str(e)}"}), 500
    return jsonify({"success": False, "message": "Error desconocido al procesar el archivo"}), 500

@app.route('/api/mantenimientos/<int:mantenimiento_id>/archivos', methods=['GET'])
def listar_archivos_mantenimiento(mantenimiento_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nombre_archivo, ruta_archivo, tipo_mime, DATE_FORMAT(fecha_subida, '%Y-%m-%d %H:%i:%s') as fecha_subida
            FROM mantenimiento_archivos WHERE mantenimiento_id = %s ORDER BY fecha_subida DESC
        """, (mantenimiento_id,))
        archivos = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "archivos": archivos})
    except Exception as e:
        app.logger.error(f"Error al listar archivos para mantenimiento {mantenimiento_id}: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/archivos/<int:archivo_id>', methods=['GET'])
def descargar_archivo(archivo_id):
    conn = None; cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT ruta_archivo, nombre_archivo FROM mantenimiento_archivos WHERE id = %s", (archivo_id,))
        archivo_info = cursor.fetchone()

        if cursor: cursor.close(); cursor = None
        if conn: conn.close(); conn = None

        if archivo_info and archivo_info['ruta_archivo']:
            # Ensure path separators are correct for send_from_directory (expects relative path using OS separator from UPLOAD_FOLDER)
            # The storable_path was saved with "/", so os.path.join will handle it if UPLOAD_FOLDER is absolute.
            # If UPLOAD_FOLDER itself might have mixed separators, this is more robust:
            directory_part, filename_part = os.path.split(archivo_info['ruta_archivo'].replace("/", os.sep).replace("\\", os.sep))
            full_directory_path = os.path.join(app.config['UPLOAD_FOLDER'], directory_part)

            return send_from_directory(
                full_directory_path,
                filename_part,
                as_attachment=True,
                download_name=archivo_info['nombre_archivo']
            )
        else:
            return jsonify({"success": False, "message": "Archivo no encontrado o ruta no válida"}), 404
    except FileNotFoundError:
        app.logger.error(f"Archivo físico no encontrado para el archivo ID {archivo_id}.")
        return jsonify({"success": False, "message": "Archivo no encontrado en el servidor."}), 404
    except Exception as e:
        app.logger.error(f"Error al descargar archivo {archivo_id}: {str(e)}")
        return jsonify({"success": False, "message": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

@app.route('/api/archivos/<int:archivo_id>', methods=['DELETE'])
def eliminar_archivo(archivo_id):
    conn = None; cursor = None
    try:
        conn = get_connection()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT ruta_archivo, mantenimiento_id FROM mantenimiento_archivos WHERE id = %s", (archivo_id,))
        archivo_info = cursor.fetchone()

        if not archivo_info or not archivo_info['ruta_archivo']:
            conn.rollback()
            return jsonify({"success": False, "message": "Archivo no encontrado en la base de datos o ruta no válida"}), 404

        # Construct path using os.sep for the current OS from the stored relative path
        ruta_relativa_os_corrected = archivo_info['ruta_archivo'].replace("/", os.sep).replace("\\", os.sep)
        full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], ruta_relativa_os_corrected)

        cursor.execute("DELETE FROM mantenimiento_archivos WHERE id = %s", (archivo_id,))
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"success": False, "message": "Error al eliminar el registro de la base de datos (no se encontró el ID)"}), 404

        if os.path.exists(full_file_path):
            try:
                os.remove(full_file_path)
                mantenimiento_folder_name = str(archivo_info['mantenimiento_id'])
                mantenimiento_folder_abs_path = os.path.join(app.config['UPLOAD_FOLDER'], mantenimiento_folder_name)
                if os.path.exists(mantenimiento_folder_abs_path) and not os.listdir(mantenimiento_folder_abs_path):
                    os.rmdir(mantenimiento_folder_abs_path)
            except OSError as e:
                conn.rollback()
                app.logger.error(f"Error de OS al eliminar archivo/directorio: {full_file_path}. Error: {str(e)}")
                return jsonify({"success": False, "message": f"Error de OS al eliminar archivo/directorio: {str(e)}"}), 500
        else:
            app.logger.warning(f"Archivo no encontrado en el sistema de archivos para eliminar (pero se eliminó de la BD): {full_file_path}")

        conn.commit()
        return jsonify({"success": True, "message": "Archivo eliminado correctamente"})
    except Exception as e:
        if conn and conn.is_connected(): conn.rollback()
        app.logger.error(f"Error general al eliminar archivo {archivo_id}: {str(e)}")
        return jsonify({"success": False, "message": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

@app.route("/actualizar_estado/<int:unidad_id>", methods=["POST"])
def actualizar_estado(unidad_id):
    data = request.get_json()
    nuevo_estado = data.get('estado')
    if not nuevo_estado: return jsonify({"success": False, "error": "Estado no proporcionado"}), 400
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True) # Changed to dictionary=True
        cursor.execute("SELECT id, color FROM estados WHERE BINARY nombre = %s", (nuevo_estado,))
        estado_info = cursor.fetchone()
        if not estado_info: return jsonify({"success": False, "error": "El estado especificado no existe"}), 400
        cursor.execute("UPDATE unidades SET estado = %s WHERE id = %s", (nuevo_estado, unidad_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "estado": nuevo_estado, "color": estado_info['color'] }) # Use dict access
    except Exception as e:
        print(f"Error al actualizar el estado: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/agregar_estado", methods=["POST"])
def agregar_estado():
    data = request.get_json()
    nombre = data.get('nombre')
    color = data.get('color', '#9CA3AF')
    if not nombre: return jsonify({"success": False, "error": "El nombre del estado es requerido"}), 400
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True) # Changed
        cursor.execute("SELECT id FROM estados WHERE BINARY nombre = %s", (nombre,))
        if cursor.fetchone(): return jsonify({"success": False, "error": "Ya existe un estado con este nombre"}), 400
        cursor.execute("INSERT INTO estados (nombre, color, es_predeterminado) VALUES (%s, %s, %s)", (nombre, color, 0))
        conn.commit()
        nuevo_estado_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"success": True, "estado": {"id": nuevo_estado_id, "nombre": nombre, "color": color}})
    except Exception as e:
        print(f"Error al agregar el estado: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/obtener_estados", methods=["GET"])
def obtener_estados():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, color, es_predeterminado FROM estados ORDER BY es_predeterminado DESC, BINARY nombre")
        estados = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "estados": estados})
    except Exception as e:
        print(f"Error al obtener los estados: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/obtener_unidades')
def obtener_unidades_json(): # Renamed to avoid conflict if you have another obtener_unidades
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT u.*, e.color as estado_color FROM unidades u LEFT JOIN estados e ON BINARY u.estado = BINARY e.nombre ORDER BY u.tipo, u.marca, u.serie")
        unidades = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) as total_unidades, COALESCE(SUM(CASE WHEN u.estado = 'Funcional' THEN 1 ELSE 0 END), 0) as funcionales, COALESCE(SUM(CASE WHEN u.estado = 'En Reparación' THEN 1 ELSE 0 END), 0) as en_reparacion, COALESCE(SUM(CASE WHEN u.estado = 'Inactivo' THEN 1 ELSE 0 END), 0) as inactivas FROM unidades u")
        resumen = cursor.fetchone() or {}
        resumen = {k: resumen.get(k, 0) for k in ['total_unidades', 'funcionales', 'en_reparacion', 'inactivas']}
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'unidades': unidades, 'resumen': resumen})
    except Exception as e:
        print(f"Error al obtener unidades: {str(e)}")
        return jsonify({'success': False, 'error': 'Error al cargar los datos'}), 500

@app.route('/unidad/<int:unidad_id>/estado', methods=['POST'])
def actualizar_estado_unidad(unidad_id):
    try:
        data = request.get_json()
        nuevo_estado, comentario = data.get('estado'), data.get('comentario', '')
        if not nuevo_estado: return jsonify({"error": "El estado es requerido"}), 400
        conn = get_connection()
        cursor = conn.cursor(dictionary=True) # Assuming you might want to return unidad info later
        # Fetch old state for history (optional, if historial_estados table expects it)
        # cursor.execute("SELECT estado FROM unidades WHERE id = %s", (unidad_id,))
        # old_state_record = cursor.fetchone()
        # estado_anterior = old_state_record['estado'] if old_state_record else None

        cursor.execute("UPDATE unidades SET estado = %s WHERE id = %s", (nuevo_estado, unidad_id))
        if comentario: # Simplified history insertion
            cursor.execute("INSERT INTO historial_estados (unidad_id, estado_nuevo, comentario, fecha_cambio) VALUES (%s, %s, %s, NOW())", (unidad_id, nuevo_estado, comentario))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Estado actualizado correctamente", "nuevo_estado": nuevo_estado})
    except Exception as e:
        print(f"Error al actualizar el estado: {str(e)}")
        if 'conn' in locals() and conn.is_connected(): conn.rollback()
        return jsonify({"error": "Error al actualizar el estado"}), 500

@app.route('/iframe')
def iframe_view():
    return render_template('iframe.html')

if __name__ == '__main__':
    app.run(debug=True)
