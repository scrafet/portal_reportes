import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User # type: ignore
from app.core.utils import get_raw_connection
# NOTE: app.core.utils must be importable. Since manage.py is in root and app is a package.

class Command(BaseCommand):
    help = 'Sync users from SIGH.Empleados and SIGH.Login to Django auth_user'

    def handle(self, *args, **options):
        self.stdout.write("Connecting to MSSQL...")
        
        server = os.getenv('SQL_SERVER', 'sqlserver')
        database = os.getenv('SQL_DATABASE', 'SIGH')
        user = os.getenv('SQL_USER', 'sa')
        password = os.getenv('SQL_PASSWORD', 'YourStrong!Passw0rd')

        try:
            conn = get_raw_connection(server, database, user, password)
            cursor = conn.cursor()
            
            # Querying dbo.Empleados. 
            # Note: We assume columns exists based on SQL file inspection.
            query = """
                SELECT 
                    Usuario, 
                    Nombres, 
                    ApellidoPaterno, 
                    ApellidoMaterno, 
                    DNI, 
                    esActivo
                FROM dbo.Empleados 
                WHERE Usuario IS NOT NULL AND Usuario <> ''
            """
            
            self.stdout.write("Fetching users from dbo.Empleados...")
            cursor.execute(query)
            rows = cursor.fetchall()
            
            self.stdout.write(f"Found {len(rows)} users. Syncing...")
            
            count_created = 0
            count_updated = 0
            
            for row in rows:
                # row is a tuple unless using Row factory, but pyodbc default is tuple/row object
                # Access by index or name if cursor configured? 
                # pyodbc Row supports name access
                
                username = row.Usuario.strip() if row.Usuario else None
                if not username:
                    continue
                
                nombres = row.Nombres.strip() if row.Nombres else ""
                paterno = row.ApellidoPaterno.strip() if row.ApellidoPaterno else ""
                materno = row.ApellidoMaterno.strip() if row.ApellidoMaterno else ""
                dni = row.DNI.strip() if row.DNI else ""
                # esActivo might be bit (True/False) or int
                is_active = bool(row.esActivo)
                
                last_name = f"{paterno} {materno}".strip()
                
                user_obj, created = User.objects.update_or_create(
                    username=username,
                    defaults={
                        'first_name': nombres[:30], 
                        'last_name': last_name[:150],
                        'is_active': is_active,
                    }
                )
                
                if created:
                    password_to_set = dni if dni else '123456'
                    user_obj.set_password(password_to_set)
                    user_obj.save()
                    count_created += 1
                else:
                    count_updated += 1
            
            self.stdout.write(self.style.SUCCESS(f"Sync complete. Created: {count_created}, Updated: {count_updated}"))
            
            conn.close()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during sync: {e}"))
