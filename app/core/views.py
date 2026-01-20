from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse, HttpResponse
from datetime import datetime
from .models import CategoriaReporte, Reporte, ConsultaAuditoria
from core.utils_ad import get_ad_users
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connections
from django.contrib.auth.hashers import make_password
import pyodbc

def home(request):
    sidebar_categories = get_sidebar_context(request)
    return render(request, 'dashboard.html', {'sidebar_categories': sidebar_categories})

class ReporteExecutorView(View):
    def get(self, request):
        sidebar_categories = get_sidebar_context(request)
        return render(request, 'dashboard.html', {'sidebar_categories': sidebar_categories})

    def post(self, request):
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_val = request.POST.get('search[value]', '').lower()
        sucursal = request.POST.get('sucursal')
        
        all_data = []
        status_opts = ["Atendido", "Pendiente", "Cancelado", "En Proceso"]
        
        for i in range(1, 56):
            estado = status_opts[i % 4]
            nombre = f"Paciente {i} - {sucursal or 'Central'}"
            if search_val and search_val not in nombre.lower():
                continue
            all_data.append({
                "id": i,
                "nombre": nombre,
                "estado": estado,
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "acciones": f'<button class="btn btn-xs btn-info"><i class="fas fa-eye"></i></button>'
            })

        total_records = len(all_data)
        data_slice = all_data[start : start + length]
        formatted_data = []
        for item in data_slice:
            badge_class = "success" if item['estado'] == "Atendido" else "warning" if item['estado'] == "Pendiente" else "danger"
            status_html = f'<span class="badge bg-{badge_class}">{item["estado"]}</span>'
            formatted_data.append([
                item['id'],
                item['nombre'],
                status_html,
                item['fecha'],
                item['acciones']
            ])

        return JsonResponse({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_records,
            "data": formatted_data
        })

# --- Helper for Sidebar ---
from django.db.models import Prefetch

# --- Helper for Sidebar ---
def get_sidebar_context(request=None):
    if not request or not request.user.is_authenticated:
        return []
        
    if request.user.is_superuser:
        return CategoriaReporte.objects.filter(activo=True).prefetch_related(
            Prefetch('reportes', queryset=Reporte.objects.filter(activo=True))
        )
    
    # Filter Reports first: User sees reports they are assigned to
    reportes_visible = Reporte.objects.filter(activo=True, usuarios=request.user)
    
    # User sees categories they are assigned to
    # AND we fetch related reports that are also visible
    # Logic: Only show category if user is assigned to it? Or if they have at least one report?
    # Requirement: "asignar a cada usuario... qué menús puede ver" implies Category permission.
    
    return CategoriaReporte.objects.filter(activo=True, usuarios=request.user).prefetch_related(
        Prefetch('reportes', queryset=reportes_visible)
    )

# --- CRUD Reportes ---
def reporte_list(request):
    reportes = Reporte.objects.select_related('categoria').all()
    return render(request, 'reporte/list.html', {
        'reportes': reportes, 
        'sidebar_categories': get_sidebar_context(request)
    })

def reporte_create(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        sp_nombre = request.POST.get('sp_nombre')
        categoria_id = request.POST.get('categoria')
        activo = request.POST.get('activo') == 'on'
        
        # Capture selected parameters
        config_params = []
        selected_params = request.POST.getlist('parametros_seleccionados')
        
        for p_name in selected_params:
             # We expect metadata in a hidden field named 'param_meta_<p_name>'
             meta = request.POST.get(f'param_meta_{p_name}', '')
             tipo = ''
             length = ''
             if '|' in meta:
                 tipo, length = meta.split('|', 1)
                 
             config_params.append({
                 'nombre': p_name, 
                 'tipo': tipo, 
                 'longitud': length,
                 'label': p_name.replace('@', '').capitalize() # Default label
             })

        Reporte.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            sp_nombre=sp_nombre,
            categoria_id=categoria_id,
            configuracion_parametros=config_params,
            activo=activo,
            horario_inicio=request.POST.get('horario_inicio') or None,
            horario_fin=request.POST.get('horario_fin') or None
        )
        messages.success(request, 'Reporte creado exitosamente.')
        return redirect('reporte_list')
        
    categorias = CategoriaReporte.objects.filter(activo=True)
    # Check if we have pre-filled data from the Wizard
    initial_sp = request.GET.get('sp', '')
    parametros_sp = []
    
    if initial_sp:
        # Try to fetch parameters from MSSQL using session credentials from Wizard
        host = request.session.get('db_host')
        user = request.session.get('db_user')
        password = request.session.get('db_pass')
        dbname = request.session.get('db_name')
        
        if host and user and dbname:
            try:
                # We reuse the connection logic
                # Extract schema and name from initial_sp (Format: Schema.Name) ??
                # The wizard passed just 'name' (ROUTINE_NAME) or Schema.Name?
                # Wizard list: <td>{{ sp.schema }}</td> <td>{{ sp.name }}</td>... ?sp={{ sp.name }}
                # Ah, we only passed the NAME. We should probably pass schema too or search by name.
                # Assuming simple name search for now or schema is dbo.
                # Use query checking SPECIFIC_NAME = initial_sp
                
                with get_raw_connection(host, dbname, user, password, timeout=10) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT PARAMETER_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, PARAMETER_MODE
                            FROM INFORMATION_SCHEMA.PARAMETERS 
                            WHERE SPECIFIC_NAME = ?
                            ORDER BY ORDINAL_POSITION
                        """, (initial_sp,))
                        for row in cursor.fetchall():
                            parametros_sp.append({
                                'nombre': row[0],
                                'tipo': row[1],
                                'longitud': row[2],
                                'modo': row[3]
                            })
            except Exception as e:
                messages.warning(request, f"No se pudieron cargar los parámetros del SP: {e}")

    return render(request, 'reporte/form.html', {
        'sidebar_categories': get_sidebar_context(request),
        'categorias': categorias,
        'action': 'Crear',
        'initial_sp': initial_sp,
        'parametros_sp': parametros_sp
    })

def reporte_update(request, pk):
    reporte = get_object_or_404(Reporte, pk=pk)
    if request.method == 'POST':
        reporte.nombre = request.POST.get('nombre')
        reporte.descripcion = request.POST.get('descripcion')
        reporte.sp_nombre = request.POST.get('sp_nombre')
        reporte.categoria_id = request.POST.get('categoria')
        reporte.activo = request.POST.get('activo') == 'on'
        reporte.horario_inicio = request.POST.get('horario_inicio') or None
        reporte.horario_fin = request.POST.get('horario_fin') or None
        reporte.save()
        messages.success(request, 'Reporte actualizado exitosamente.')
        return redirect('reporte_list')

    categorias = CategoriaReporte.objects.filter(activo=True)
    return render(request, 'reporte/form.html', {
        'sidebar_categories': get_sidebar_context(request),
        'reporte': reporte,
        'categorias': categorias,
        'action': 'Editar'
    })

def reporte_delete(request, pk):
    reporte = get_object_or_404(Reporte, pk=pk)
    if request.method == 'POST':
        reporte.delete()
        messages.success(request, 'Reporte eliminado.')
    return redirect('reporte_list')

# --- CRUD Categories (Menus) ---
def categoria_list(request):
    categorias = CategoriaReporte.objects.all()
    return render(request, 'categoria/list.html', {
        'categorias': categorias,
        'sidebar_categories': get_sidebar_context(request)
    })

def categoria_create(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        orden = request.POST.get('orden', 0)
        icono = request.POST.get('icono', 'fas fa-folder')
        activo = request.POST.get('activo') == 'on'
        
        CategoriaReporte.objects.create(nombre=nombre, orden=orden, icono=icono, activo=activo)
        messages.success(request, 'Categoría creada.')
        return redirect('categoria_list')

    return render(request, 'categoria/form.html', {
        'action': 'Crear',
        'sidebar_categories': get_sidebar_context(request)
    })

def categoria_update(request, pk):
    categoria = get_object_or_404(CategoriaReporte, pk=pk)
    if request.method == 'POST':
        categoria.nombre = request.POST.get('nombre')
        categoria.orden = request.POST.get('orden')
        categoria.icono = request.POST.get('icono')
        categoria.activo = request.POST.get('activo') == 'on'
        categoria.save()
        messages.success(request, 'Categoría actualizada.')
        return redirect('categoria_list')

    return render(request, 'categoria/form.html', {
        'categoria': categoria,
        'action': 'Editar',
        'sidebar_categories': get_sidebar_context(request)
    })

def categoria_delete(request, pk):
    categoria = get_object_or_404(CategoriaReporte, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoría eliminada.')
    return redirect('categoria_list')

# --- CRUD Users ---
def usuario_list(request):
    usuarios = User.objects.all()
    return render(request, 'usuario/list.html', {
        'usuarios': usuarios,
        'sidebar_categories': get_sidebar_context(request)
    })

def usuario_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe.')
        else:
            User.objects.create_user(
                username=username, email=email, password=password,
                is_staff=is_staff, is_superuser=is_superuser
            )
            messages.success(request, 'Usuario creado.')
            return redirect('usuario_list')

    return render(request, 'usuario/form.html', {'action': 'Crear', 'sidebar_categories': get_sidebar_context(request)})

def usuario_update(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        usuario.username = request.POST.get('username')
        usuario.email = request.POST.get('email')
        usuario.is_staff = request.POST.get('is_staff') == 'on'
        usuario.is_superuser = request.POST.get('is_superuser') == 'on'
        
        new_password = request.POST.get('password')
        if new_password:
            usuario.set_password(new_password)
            
        usuario.save()
        messages.success(request, 'Usuario actualizado.')
        return redirect('usuario_list')

    return render(request, 'usuario/form.html', {
        'usuario': usuario, 
        'action': 'Editar',
        'sidebar_categories': get_sidebar_context(request)
    })

def usuario_delete(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado.')
    return redirect('usuario_list')

def usuario_asignar(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        reportes_ids = request.POST.getlist('reportes')
        categorias_ids = request.POST.getlist('categorias')
        
        usuario.reportes_permitidos.set(reportes_ids)
        usuario.categorias_permitidas.set(categorias_ids)
        
        messages.success(request, f'Asignaciones actualizadas para {usuario.username}')
        return redirect('usuario_list')
        
    reportes = Reporte.objects.filter(activo=True)
    categorias = CategoriaReporte.objects.filter(activo=True)
    
    return render(request, 'usuario/asignar.html', {
        'usuario': usuario,
        'reportes': reportes,
        'categorias': categorias,
        'asignados_reportes': usuario.reportes_permitidos.all(),
        'asignados_categorias': usuario.categorias_permitidas.all(),
        'sidebar_categories': get_sidebar_context(request)
    })

# --- Report Wizard Steps ---

def reporte_wizard_connection(request):
    """ Step 1: Input DB Credentials """
    if request.method == 'POST':
        # Store in session
        request.session['db_host'] = request.POST.get('host')
        request.session['db_name'] = request.POST.get('database')
        request.session['db_user'] = request.POST.get('user')
        request.session['db_pass'] = request.POST.get('password')
        return redirect('reporte_wizard_discovery')
        
    return render(request, 'reporte/wizard_connection.html', {'sidebar_categories': get_sidebar_context(request)})

from core.utils import get_raw_connection

def reporte_wizard_discovery(request):
    """ Step 2: List SPs """
    host = request.session.get('db_host')
    user = request.session.get('db_user')
    password = request.session.get('db_pass')
    dbname = request.session.get('db_name')
    
    if not host or not user:
        messages.error(request, "Faltan credenciales de conexión.")
        return redirect('reporte_wizard_connection')

    error_msg = None
    sp_list = []

    try:
        # Use centralized connection logic with correct timeout/encryption settings
        # Including explicit timeout=30 to allow for initial handshake delays
        # We need to import get_raw_connection if not imported at top
        # from core.utils import get_raw_connection # Already imported
        
        with get_raw_connection(host, dbname, user, password, timeout=30) as conn:
            with conn.cursor() as cursor:
                # Query to get Stored Procedures
                cursor.execute("""
                    SELECT ROUTINE_SCHEMA, ROUTINE_NAME 
                    FROM INFORMATION_SCHEMA.ROUTINES 
                    WHERE ROUTINE_TYPE = 'PROCEDURE' 
                    ORDER BY ROUTINE_NAME
                """)
                for row in cursor.fetchall():
                    sp_list.append({'schema': row[0], 'name': row[1]})
                    
    except Exception as e:
        error_msg = str(e)
        # Log error for better debugging if needed
        print(f"Wizard Connection Error: {e}")

    return render(request, 'reporte/wizard_discovery.html', {
        'sp_list': sp_list,
        'error_msg': error_msg,
        'sidebar_categories': get_sidebar_context(request)
    })

def reporte_execute(request, pk):
    reporte = get_object_or_404(Reporte, pk=pk)
    
    # Validacion: Matriz de Accesos
    if not request.user.is_superuser and not reporte.usuarios.filter(pk=request.user.pk).exists():
        messages.error(request, 'No tienes permiso para acceder a este reporte.')
        return redirect('home')
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Execute SP for DataTables/AJAX
        params = []
        try:
            # Collect Parameters
            if reporte.configuracion_parametros:
                for conf in reporte.configuracion_parametros:
                    val = request.POST.get(conf['nombre'])
                    params.append(val) 

            # DB Credentials (Default SIGH)
            import os
            server = os.getenv('SQL_SERVER', 'sqlserver')
            database = os.getenv('SQL_DATABASE', 'SIGH')
            user = os.getenv('SQL_USER', 'sa')
            password = os.getenv('SQL_PASSWORD', 'YourStrong!Passw0rd')
            
            data = []
            headers = []
            
            with get_raw_connection(server, database, user, password) as conn:
                with conn.cursor() as cursor:
                    placeholders = ', '.join(['?'] * len(params))
                    sql = f"EXEC {reporte.sp_nombre} {placeholders}"
                    
                    cursor.execute(sql, params)
                    
                    if cursor.description:
                        headers = [col[0] for col in cursor.description]
                        rows = cursor.fetchall()
                        
                        for row in rows:
                            row_dict = {}
                            for idx, col in enumerate(headers):
                                cell = row[idx]
                                if isinstance(cell, datetime):
                                    cell = cell.strftime('%Y-%m-%d %H:%M:%S')
                                row_dict[col] = cell if cell is not None else ""
                            data.append(row_dict)

            # Audit Success
            ConsultaAuditoria.objects.create(
                 usuario=request.user.username,
                 sp_ejecutado=reporte.sp_nombre,
                 parametros=str(params),
                 ip_origen=request.META.get('REMOTE_ADDR'),
                 exitoso=True
             )

            return JsonResponse({
                "data": data,
                "columns": headers,
                "success": True
            })
            
        except Exception as e:
            # Audit Failure
            ConsultaAuditoria.objects.create(
                 usuario=request.user.username,
                 sp_ejecutado=reporte.sp_nombre,
                 parametros=str(params),
                 ip_origen=request.META.get('REMOTE_ADDR'),
                 exitoso=False,
                 mensaje_error=str(e)
             )
            return JsonResponse({'success': False, 'error': str(e)})

    # GET Renders the wrapper page
    locked = False
    if reporte.horario_inicio and reporte.horario_fin:
        now = datetime.now().time()
        if not (reporte.horario_inicio <= now <= reporte.horario_fin):
            locked = True

    return render(request, 'reporte/execute.html', {
        'reporte': reporte,
        'sidebar_categories': get_sidebar_context(request),
        'locked': locked
    })

def usuario_ad_sync(request):
    if request.method == 'POST':
        selected_users = request.POST.getlist('ad_users')
        count = 0
        for username in selected_users:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(username=username, password='DefaultPassword123')
                count += 1
        messages.success(request, f"{count} usuarios importados desde AD.")
        return redirect('usuario_list')
        
    ad_users = get_ad_users()
    return render(request, 'usuario/ad_sync.html', {
        'ad_users': ad_users,
        'sidebar_categories': get_sidebar_context(request)
    })

