from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# Configuración de la base de datos MySQL
db_config = {
    'host': '11.168.103.252',
    'user': 'joseastelllo',
    'password': 'cH@70FIs7B4E',
    'database': 'control_unidades'
}

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

# Configuración de la base de datos MySQL
db_config = {
    'host': '11.168.103.252',
    'user': 'joseastelllo',
    'password': 'cH@70FIs7B4E',
    'database': 'control_unidades'
}

def get_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener listado de unidades con sus estados
    cursor.execute("""
        SELECT u.*, e.color as estado_color
        FROM unidades u
        LEFT JOIN estados e ON BINARY u.estado = BINARY e.nombre
        ORDER BY u.tipo, u.marca, u.serie
    """)
    unidades = cursor.fetchall()

    # Obtener conteo de unidades por estado
    cursor.execute("""
        SELECT
            COUNT(*) as total_unidades,
            COALESCE(SUM(CASE WHEN u.estado = 'Funcional' THEN 1 ELSE 0 END), 0) as funcionales,
            COALESCE(SUM(CASE WHEN u.estado = 'En Reparación' THEN 1 ELSE 0 END), 0) as en_reparacion,
            COALESCE(SUM(CASE WHEN u.estado = 'Sin Reparación' THEN 1 ELSE 0 END), 0) as sin_reparacion
        FROM unidades u
    """)
    resumen = cursor.fetchone() or {}

    # Asegurarse de que los valores no sean None
    resumen['total_unidades'] = resumen.get('total_unidades', 0)
    resumen['funcionales'] = resumen.get('funcionales', 0)
    resumen['en_reparacion'] = resumen.get('en_reparacion', 0)
    resumen['sin_reparacion'] = resumen.get('sin_reparacion', 0)

    # Obtener lista de estados disponibles
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
    estado = data.get("estado", "Funcional")  # Default to "Funcional" if not provided

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
        "id": nuevo_id,
        "serie": serie,
        "modelo": modelo,
        "marca": marca,
        "numero_economico": numero_economico,
        "tipo": tipo,
        "estado": estado
    })


@app.route('/agregar_combustible', methods=['POST'])
def agregar_combustible_antigua():
    """
    Función obsoleta para compatibilidad con formularios antiguos.
    Se recomienda usar /combustible/agregar/<unidad_id> en su lugar.
    """
    datos = (
        request.form['unidad_id'],
        request.form['fecha'],
        request.form['litros'],
        request.form.get('kilometraje'),
        request.form.get('observaciones')
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
        request.form['unidad_id'],
        request.form['fecha'],
        request.form['descripcion'],
        request.form.get('costo'),
        request.form.get('taller'),
        request.form.get('kilometraje')
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

        # Eliminar registros relacionados en otras tablas
        cursor.execute("DELETE FROM combustible WHERE unidad_id = %s", (unidad_id,))
        cursor.execute("DELETE FROM mantenimientos WHERE unidad_id = %s", (unidad_id,))

        # Finalmente, eliminar la unidad
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
        # Obtener todas las unidades con su último registro de combustible
        cursor.execute("""
            SELECT
                u.id,
                u.serie,
                u.marca,
                u.tipo,
                c.fecha as ultima_fecha,
                c.litros as ultimos_litros,
                c.precio as ultimo_precio,
                c.total as ultimo_total,
                DATE_FORMAT(c.fecha, '%Y-%m') as mes_anio
            FROM unidades u
            LEFT JOIN (
                SELECT
                    unidad_id,
                    MAX(fecha) as max_fecha
                FROM combustible
                GROUP BY unidad_id
            ) ultimo ON u.id = ultimo.unidad_id
            LEFT JOIN combustible c ON c.unidad_id = ultimo.unidad_id AND c.fecha = ultimo.max_fecha
            ORDER BY u.tipo, u.marca, u.serie
        """)

        unidades = cursor.fetchall()

        # Obtener totales por mes para cada unidad
        for unidad in unidades:
            if unidad['id']:
                cursor.execute("""
                    SELECT
                        DATE_FORMAT(fecha, '%Y-%m') as mes_anio,
                        SUM(litros) as total_litros,
                        SUM(total) as total_importe
                    FROM combustible
                    WHERE unidad_id = %s
                    GROUP BY DATE_FORMAT(fecha, '%Y-%m')
                    ORDER BY mes_anio DESC
                """, (unidad['id'],))
                unidad['meses'] = cursor.fetchall()

                # Calcular total general
                unidad['total_general_litros'] = sum(mes['total_litros'] or 0 for mes in unidad['meses'])
                unidad['total_general_importe'] = sum(float(mes['total_importe'] or 0) for mes in unidad['meses'])

        return render_template('combustibles.html',
                           unidades=unidades,
                           now=datetime.now().strftime('%Y-%m-%dT%H:%M'))

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
        cursor.execute("""
            SELECT kilometraje
            FROM combustible
            WHERE unidad_id = %s
            ORDER BY fecha DESC, id DESC
            LIMIT 1
        """, (unidad_id,))

        resultado = cursor.fetchone()
        if resultado and 'kilometraje' in resultado:
            return jsonify({"kilometraje": resultado['kilometraje']})
        return jsonify({"kilometraje": ""})
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
        # Validar que la unidad existe y obtener sus datos
        cursor.execute("SELECT id, serie, marca, tipo FROM unidades WHERE id = %s", (unidad_id,))
        unidad = cursor.fetchone()
        if not unidad:
            return jsonify({"error": "Unidad no encontrada"}), 404

        # Obtener datos del formulario
        fecha = request.form.get('fecha')
        litros = request.form.get('litros')
        precio = request.form.get('precio')
        kilometraje = request.form.get('kilometraje')
        observaciones = request.form.get('observaciones', '')

        # Validar campos requeridos
        if not all([fecha, litros, precio]):
            return jsonify({"error": "Fecha, litros y precio son campos requeridos"}), 400

        # Convertir y validar valores numéricos
        try:
            litros_float = float(litros.replace(',', '.'))
            precio_float = float(precio.replace(',', '.'))
            total = litros_float * precio_float

            if litros_float <= 0 or precio_float <= 0:
                return jsonify({"error": "Los valores deben ser mayores a cero"}), 400

        except ValueError:
            return jsonify({"error": "Los valores de litros y precio deben ser números válidos"}), 400

        # Insertar en la base de datos
        cursor.execute("""
            INSERT INTO combustible
            (unidad_id, fecha, litros, precio, total, kilometraje, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (unidad_id, fecha, litros_float, precio_float, total, kilometraje, observaciones))

        # Actualizar el kilometraje de la unidad si se proporcionó
        if kilometraje:
            try:
                kilometraje_int = int(kilometraje.replace('.', ''))
                cursor.execute("""
                    UPDATE unidades
                    SET kilometraje = %s
                    WHERE id = %s
                """, (kilometraje_int, unidad_id))
            except ValueError:
                pass  # Si el kilometraje no es un número válido, lo ignoramos

        conn.commit()

        # Obtener los datos formateados para la respuesta
        cursor.execute("""
            SELECT
                DATE_FORMAT(fecha, '%%d/%%m/%%Y %%H:%%i') as fecha_formateada,
                litros,
                precio,
                total,
                observaciones
            FROM combustible
            WHERE id = LAST_INSERT_ID()
        """)
        registro = cursor.fetchone()

        return jsonify({
            "success": True,
            "mensaje": "Carga de combustible registrada correctamente",
            "registro": {
                "fecha": registro['fecha_formateada'],
                "litros": f"{float(registro['litros']):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                "precio": f"{float(registro['precio']):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                "total": f"{float(registro['total']):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                "observaciones": registro['observaciones'] or ''
            },
            "unidad": {
                "id": unidad_id,
                "serie": unidad['serie'],
                "marca": unidad['marca'],
                "tipo": unidad['tipo']
            }
        })

    except Exception as e:
        conn.rollback()
        print(f"Error al registrar combustible: {str(e)}")
        return jsonify({"success": False, "error": f"Error al registrar la carga: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

# Rutas para mantenimientos
@app.route('/mantenimientos')
def ver_mantenimientos():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Obtener parámetros de filtrado
        unidad_id = request.args.get('unidad_id')
        tipo = request.args.get('tipo')
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')

        # Construir la consulta base
        query = """
            SELECT m.*, u.serie, u.marca, u.modelo
            FROM mantenimientos m
            JOIN unidades u ON m.unidad_id = u.id
            WHERE 1=1
        """
        params = []

        # Aplicar filtros
        if unidad_id:
            query += " AND m.unidad_id = %s"
            params.append(unidad_id)

        if tipo:
            query += " AND m.tipo = %s"
            params.append(tipo)

        if fecha_desde:
            query += " AND DATE(m.fecha) >= %s"
            params.append(fecha_desde)

        if fecha_hasta:
            query += " AND DATE(m.fecha) <= %s"
            params.append(fecha_hasta)

        # Ordenar por fecha descendente por defecto
        query += " ORDER BY m.fecha DESC"

        cursor.execute(query, params)
        all_mantenimientos = cursor.fetchall() # Fetch all results first

        # Paginación logic
        page = request.args.get('page', 1, type=int)
        PER_PAGE = 10  # Define how many items per page

        total_items = len(all_mantenimientos)
        start_index = (page - 1) * PER_PAGE
        end_index = start_index + PER_PAGE
        mantenimientos_paginados = all_mantenimientos[start_index:end_index]

        total_pages = (total_items + PER_PAGE - 1) // PER_PAGE if PER_PAGE > 0 else 0

        # Create a pagination object to pass to the template
        pagination_obj = {
            'page': page,
            'per_page': PER_PAGE,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'prev_num': page - 1 if page > 1 else None,
            'has_next': page < total_pages,
            'next_num': page + 1 if page < total_pages else None,
            'iter_pages': [p for p in range(1, total_pages + 1)]
        }

        # Obtener lista de unidades para el filtro
        cursor.execute("SELECT id, serie, marca, modelo FROM unidades ORDER BY marca, modelo")
        unidades = cursor.fetchall()

        # Pass current request arguments to the template for persistent filter links in pagination
        current_request_args = request.args.to_dict()
        if 'page' in current_request_args: # Remove old page from args for new links
            del current_request_args['page']

        return render_template('mantenimientos.html',
                             mantenimientos=mantenimientos_paginados, # Pass paginated data
                             unidades=unidades,
                             pagination=pagination_obj, # Pass pagination object
                             request_args=current_request_args) # Pass current filters

    except Exception as e:
        print(f"Error en ver_mantenimientos: {str(e)}")
        return render_template('error.html', error="Ocurrió un error al cargar los mantenimientos"), 500
    finally:
        cursor.close()
        conn.close()

# API para obtener un mantenimiento específico
@app.route('/api/mantenimientos/<int:mantenimiento_id>', methods=['GET'])
def obtener_mantenimiento(mantenimiento_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT m.*, u.serie, u.marca, u.modelo
            FROM mantenimientos m
            JOIN unidades u ON m.unidad_id = u.id
            WHERE m.id = %s
        """, (mantenimiento_id,))

        mantenimiento = cursor.fetchone()

        if not mantenimiento:
            return jsonify({"success": False, "message": "Mantenimiento no encontrado"}), 404

        # Formatear fechas para el formulario
        if mantenimiento['fecha']:
            mantenimiento['fecha'] = mantenimiento['fecha'].strftime('%Y-%m-%dT%H:%M')

        if mantenimiento.get('proximo_mantenimiento_fecha'):
            mantenimiento['proximo_mantenimiento_fecha'] = mantenimiento['proximo_mantenimiento_fecha'].strftime('%Y-%m-%d')

        return jsonify({"success": True, "data": mantenimiento})

    except Exception as e:
        print(f"Error al obtener mantenimiento: {str(e)}")
        return jsonify({"success": False, "message": "Error al obtener el mantenimiento"}), 500
    finally:
        cursor.close()
        conn.close()

# API para crear o actualizar un mantenimiento
@app.route('/api/mantenimientos', methods=['POST'])
@app.route('/api/mantenimientos/<int:mantenimiento_id>', methods=['PUT'])
def guardar_mantenimiento(mantenimiento_id=None):
    try:
        data = request.form.to_dict()

        # Validar datos requeridos
        required_fields = ['unidad_id', 'fecha', 'tipo', 'descripcion']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"success": False, "message": f"El campo {field} es requerido"}), 400

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Extract 'observaciones' and 'completado' from data
        observaciones = data.get('observaciones')
        # FormData sends checkbox value as string 'true' or 'false' if set via JS .checked
        # If field is not in form data at all (e.g. not sent), default to False.
        completado_str = data.get('completado', 'false')
        completado = completado_str.lower() == 'true'


        if request.method == 'POST':
            # Crear nuevo mantenimiento
            query = """
                INSERT INTO mantenimientos
                (unidad_id, fecha, tipo, descripcion, costo, proveedor,
                 kilometraje, proximo_mantenimiento_km, proximo_mantenimiento_fecha,
                 observaciones, completado, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            params = (
                data['unidad_id'],
                data['fecha'],
                data['tipo'],
                data['descripcion'],
                float(data.get('costo')) if data.get('costo') else None,
                data.get('proveedor'),
                int(data.get('kilometraje')) if data.get('kilometraje') else None,
                int(data.get('proximo_mantenimiento_km')) if data.get('proximo_mantenimiento_km') else None,
                data.get('proximo_mantenimiento_fecha') if data.get('proximo_mantenimiento_fecha') else None,
                observaciones,
                completado
            )
            cursor.execute(query, params)
            mensaje = "Mantenimiento creado correctamente"
        else:
            # Actualizar mantenimiento existente
            query = """
                UPDATE mantenimientos
                SET unidad_id = %s, fecha = %s, tipo = %s, descripcion = %s,
                    costo = %s, proveedor = %s, kilometraje = %s,
                    proximo_mantenimiento_km = %s, proximo_mantenimiento_fecha = %s,
                    observaciones = %s, completado = %s, updated_at = NOW()
                WHERE id = %s
            """
            params = (
                data['unidad_id'],
                data['fecha'],
                data['tipo'],
                data['descripcion'],
                float(data.get('costo')) if data.get('costo') else None,
                data.get('proveedor'),
                int(data.get('kilometraje')) if data.get('kilometraje') else None,
                int(data.get('proximo_mantenimiento_km')) if data.get('proximo_mantenimiento_km') else None,
                data.get('proximo_mantenimiento_fecha') if data.get('proximo_mantenimiento_fecha') else None,
                observaciones,
                completado,
                mantenimiento_id
            )
            cursor.execute(query, params)
            mensaje = "Mantenimiento actualizado correctamente"

        conn.commit()
        return jsonify({"success": True, "message": mensaje})

    except Exception as e:
        if 'conn' in locals() and conn.is_connected():
            conn.rollback()
        return jsonify({"success": False, "message": f"Error al guardar el mantenimiento: {str(e)}"}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

# API para eliminar un mantenimiento
@app.route('/api/mantenimientos/<int:mantenimiento_id>', methods=['DELETE'])
def eliminar_mantenimiento(mantenimiento_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM mantenimientos WHERE id = %s", (mantenimiento_id,))

        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"success": False, "message": "Mantenimiento no encontrado"}), 404

        conn.commit()
        return jsonify({"success": True, "message": "Mantenimiento eliminado correctamente"})

    except Exception as e:
        if conn and conn.is_connected():
            conn.rollback()
        return jsonify({"success": False, "message": f"Error al eliminar el mantenimiento: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

@app.route("/actualizar_estado/<int:unidad_id>", methods=["POST"])
def actualizar_estado(unidad_id):
    data = request.get_json()
    nuevo_estado = data.get('estado')

    if not nuevo_estado:
        return jsonify({"success": False, "error": "Estado no proporcionado"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Verificar si el estado existe (using BINARY for case-sensitive comparison)
        cursor.execute("""
            SELECT id, color
            FROM estados
            WHERE BINARY nombre = %s
        """, (nuevo_estado,))
        estado_info = cursor.fetchone()

        if not estado_info:
            return jsonify({"success": False, "error": "El estado especificado no existe"}), 400

        # Update the unit's state
        cursor.execute(
            "UPDATE unidades SET estado = %s WHERE id = %s",
            (nuevo_estado, unidad_id)
        )

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "estado": nuevo_estado,
            "color": estado_info[0] if estado_info else "#9CA3AF"
        })

    except Exception as e:
        print(f"Error al actualizar el estado: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/agregar_estado", methods=["POST"])
def agregar_estado():
    data = request.get_json()
    nombre = data.get('nombre')
    color = data.get('color', '#9CA3AF')

    if not nombre:
        return jsonify({"success": False, "error": "El nombre del estado es requerido"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Verificar si el estado ya existe (using BINARY for case-sensitive comparison)
        cursor.execute("""
            SELECT id FROM estados
            WHERE BINARY nombre = %s
        """, (nombre,))
        if cursor.fetchone():
            return jsonify({"success": False, "error": "Ya existe un estado con este nombre"}), 400

        # Insertar el nuevo estado
        cursor.execute(
            "INSERT INTO estados (nombre, color, es_predeterminado) VALUES (%s, %s, %s)",
            (nombre, color, 0)  # 0 para estados personalizados
        )

        conn.commit()
        nuevo_estado_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "estado": {
                "id": nuevo_estado_id,
                "nombre": nombre,
                "color": color
            }
        })

    except Exception as e:
        print(f"Error al agregar el estado: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/obtener_estados", methods=["GET"])
def obtener_estados():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, nombre, color, es_predeterminado
            FROM estados
            ORDER BY es_predeterminado DESC, BINARY nombre
        """)

        estados = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "estados": estados})

    except Exception as e:
        print(f"Error al obtener los estados: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/obtener_unidades')
def obtener_unidades():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Obtener listado de unidades con sus estados
        cursor.execute("""
            SELECT u.*, e.color as estado_color
            FROM unidades u
            LEFT JOIN estados e ON BINARY u.estado = BINARY e.nombre
            ORDER BY u.tipo, u.marca, u.serie
        """)
        unidades = cursor.fetchall()

        # Obtener datos para el resumen
        cursor.execute("""
            SELECT
                COUNT(*) as total_unidades,
                COALESCE(SUM(CASE WHEN u.estado = 'Funcional' THEN 1 ELSE 0 END), 0) as funcionales,
                COALESCE(SUM(CASE WHEN u.estado = 'En Reparación' THEN 1 ELSE 0 END), 0) as en_reparacion,
                COALESCE(SUM(CASE WHEN u.estado = 'Inactivo' THEN 1 ELSE 0 END), 0) as inactivas
            FROM unidades u
        """)
        resumen = cursor.fetchone() or {}

        # Asegurarse de que los valores no sean None
        resumen['total_unidades'] = resumen.get('total_unidades', 0)
        resumen['funcionales'] = resumen.get('funcionales', 0)
        resumen['en_reparacion'] = resumen.get('en_reparacion', 0)
        resumen['inactivas'] = resumen.get('inactivas', 0)

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'unidades': unidades,
            'resumen': resumen
        })

    except Exception as e:
        print(f"Error al obtener unidades: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error al cargar los datos'
        }), 500

@app.route('/unidad/<int:unidad_id>/estado', methods=['POST'])
def actualizar_estado_unidad(unidad_id):
    try:
        data = request.get_json()
        nuevo_estado = data.get('estado')
        comentario = data.get('comentario', '')

        if not nuevo_estado:
            return jsonify({"error": "El estado es requerido"}), 400

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Actualizar el estado de la unidad
        cursor.execute(
            "UPDATE unidades SET estado = %s WHERE id = %s",
            (nuevo_estado, unidad_id)
        )

        # Registrar el cambio de estado en el historial
        if comentario:
            cursor.execute(
                """
                INSERT INTO historial_estados (unidad_id, estado_anterior, estado_nuevo, comentario, fecha_cambio)
                SELECT %s, estado, %s, %s, NOW()
                FROM unidades
                WHERE id = %s
                """,
                (unidad_id, nuevo_estado, comentario, unidad_id)
            )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Estado actualizado correctamente",
            "nuevo_estado": nuevo_estado
        })

    except Exception as e:
        print(f"Error al actualizar el estado: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({"error": "Error al actualizar el estado"}), 500

@app.route('/iframe')
def iframe_view():
    return render_template('iframe.html')

if __name__ == '__main__':
    app.run(debug=True)
