from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse, HttpResponse
from datetime import datetime
from .models import CategoriaReporte, Reporte
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import connections
from django.contrib.auth.hashers import make_password
import pyodbc

def home(request):
    sidebar_categories = CategoriaReporte.objects.filter(activo=True).prefetch_related('reportes')
    return render(request, 'dashboard.html', {'sidebar_categories': sidebar_categories})

class ReporteExecutorView(View):
    def get(self, request):
        sidebar_categories = CategoriaReporte.objects.filter(activo=True).prefetch_related('reportes')
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
def get_sidebar_context():
    return CategoriaReporte.objects.filter(activo=True).prefetch_related('reportes')

# --- CRUD Reportes ---
def reporte_list(request):
    reportes = Reporte.objects.select_related('categoria').all()
    return render(request, 'reporte/list.html', {
        'reportes': reportes, 
        'sidebar_categories': get_sidebar_context()
    })

def reporte_create(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        sp_nombre = request.POST.get('sp_nombre')
        categoria_id = request.POST.get('categoria')
        activo = request.POST.get('activo') == 'on'
        
        Reporte.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            sp_nombre=sp_nombre,
            categoria_id=categoria_id,
            activo=activo
        )
        messages.success(request, 'Reporte creado exitosamente.')
        return redirect('reporte_list')
        
    categorias = CategoriaReporte.objects.filter(activo=True)
    # Check if we have pre-filled data from the Wizard
    initial_sp = request.GET.get('sp', '')
    
    return render(request, 'reporte/form.html', {
        'sidebar_categories': get_sidebar_context(),
        'categorias': categorias,
        'action': 'Crear',
        'initial_sp': initial_sp
    })

def reporte_update(request, pk):
    reporte = get_object_or_404(Reporte, pk=pk)
    if request.method == 'POST':
        reporte.nombre = request.POST.get('nombre')
        reporte.descripcion = request.POST.get('descripcion')
        reporte.sp_nombre = request.POST.get('sp_nombre')
        reporte.categoria_id = request.POST.get('categoria')
        reporte.activo = request.POST.get('activo') == 'on'
        reporte.save()
        messages.success(request, 'Reporte actualizado exitosamente.')
        return redirect('reporte_list')

    categorias = CategoriaReporte.objects.filter(activo=True)
    return render(request, 'reporte/form.html', {
        'sidebar_categories': get_sidebar_context(),
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
        'sidebar_categories': get_sidebar_context()
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
        'sidebar_categories': get_sidebar_context()
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
        'sidebar_categories': get_sidebar_context()
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
        'sidebar_categories': get_sidebar_context()
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

    return render(request, 'usuario/form.html', {'action': 'Crear', 'sidebar_categories': get_sidebar_context()})

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
        'sidebar_categories': get_sidebar_context()
    })

def usuario_delete(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado.')
    return redirect('usuario_list')

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
        
    return render(request, 'reporte/wizard_connection.html', {'sidebar_categories': get_sidebar_context()})

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
        # Using ODBC Driver 18 which is installed in Docker (msodbcsql18)
        # TrustServerCertificate=yes is required for self-signed certs (dev/docker)
        conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={host};DATABASE={dbname};UID={user};PWD={password};TrustServerCertificate=yes;'
        
        # We need to rely on 'mssql-django' or 'pyodbc' being installed.
        # Assuming pyodbc for direct raw query in this wizard context.
        with pyodbc.connect(conn_str, timeout=10) as conn:
            with conn.cursor() as cursor:
                # Query to get Stored Procedures
                # Exclusion of system SPs (dt_, sp_, etc) if needed, but user said "sp a los que tengo acceso"
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

    return render(request, 'reporte/wizard_discovery.html', {
        'sp_list': sp_list,
        'error_msg': error_msg,
        'sidebar_categories': get_sidebar_context()
    })
