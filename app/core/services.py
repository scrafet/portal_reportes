from django.db import connections
from django.utils import timezone
from datetime import datetime, timedelta, time
from .models import ConsultaAuditoria
import json

class PolicyError(Exception):
    pass

class ReporteService:
    @staticmethod
    def validate_policies(start_date: datetime.date, end_date: datetime.date):
        """
        Validates business policies:
        1. Date range <= 31 days.
        2. Block check during critical load window.
        """
        # 1. Date Range Check
        if (end_date - start_date).days > 31:
            raise PolicyError("El rango de fechas no puede exceder los 31 días.")
        
        # 2. Load Window Check (Example: Block between 02:00 and 04:00 AM)
        # You can make this configurable via settings or DB
        now = timezone.localtime().time()
        RESTRICTED_START = time(2, 0) # 02:00 AM
        RESTRICTED_END = time(4, 0)   # 04:00 AM
        
        # Simple check crossing midnight handled if needed, assuming simple window
        if RESTRICTED_START <= now <= RESTRICTED_END:
            raise PolicyError(f"Sistema en ventana de mantenimiento/carga ({RESTRICTED_START} - {RESTRICTED_END}). Intente más tarde.")

    @staticmethod
    def execute_sp(user, sp_name, params, request_ip=None):
        """
        Executes a Stored Procedure in MSSQL and audits the call in PostgreSQL.
        
        params: list or tuple of parameters for the SP.
        """
        audit_entry = ConsultaAuditoria(
            usuario=user,
            sp_ejecutado=sp_name,
            parametros=json.dumps(params, default=str),
            ip_origen=request_ip
        )
        
        try:
            # Connect to MSSQL (read-only regarding the audit, but SP might do whatever)
            # We assume 'mssql' key in DATABASES from settings
            
            # Using a raw cursor
            with connections['mssql'].cursor() as cursor:
                # Construct query string. Be careful with SQL injection if params are strings directly.
                # However, with cursor.execute(sql, params), the driver handles escaping.
                # MSSQL syntax for SP often needs "{CALL sp_name (?,?)}" or "EXEC sp_name %s, %s" depending on driver
                # django-mssql-backend usually supports standard style.
                
                # A generic robust way for MSSQL with placeholders varies by driver. 
                # Assuming 'mssql-django' which accepts %s for params.
                sql = f"EXEC {sp_name} " + ",".join(["%s"] * len(params))
                
                cursor.execute(sql, params)
                
                # Fetch headers
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    # Fetch all rows
                    rows = cursor.fetchall()
                    data = [dict(zip(columns, row)) for row in rows]
                else:
                    data = []
            
            audit_entry.exitoso = True
            audit_entry.save()
            return data
            
        except Exception as e:
            audit_entry.exitoso = False
            audit_entry.mensaje_error = str(e)
            audit_entry.save()
            raise e

    @staticmethod
    def process_data(data, search_query=None, page=1, page_size=10):
        """
        Performs Python-side pagination and search.
        """
        filtered_data = data
        
        # 1. Search (Simple string match across all values)
        if search_query:
            query = search_query.lower()
            filtered_data = [
                row for row in data 
                if any(str(val).lower().find(query) != -1 for val in row.values() if val is not None)
            ]
        
        # 2. Pagination
        total_items = len(filtered_data)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        paginated_data = filtered_data[start_index:end_index]
        
        return {
            'data': paginated_data,
            'total': total_items,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_items + page_size - 1) // page_size
        }
