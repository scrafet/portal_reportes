import os
import pyodbc
from cryptography.fernet import Fernet
from django.conf import settings

def get_fernet():
    key = os.getenv('FERNET_KEY')
    if not key:
        raise ValueError("FERNET_KEY not set in environment")
    return Fernet(key.encode())

def encrypt_password(password):
    """Encrypts a plaintext password."""
    if not password:
        return ""
    f = get_fernet()
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    """Decrypts an encrypted password."""
    if not encrypted_password:
        return ""
    f = get_fernet()
    try:
        return f.decrypt(encrypted_password.encode()).decode()
    except Exception as e:
        print(f"Error decrypting password: {e}")
        return None

def get_raw_connection(server_host, database, user, password, timeout=30):
    """
    Establishes a raw pyodbc connection to MSSQL.
    Tries to find a suitable driver.
    """
    drivers = pyodbc.drivers()
    # Prefer ODBC Driver 18, then 17, then whatever is available
    preferred_drivers = [
        'ODBC Driver 18 for SQL Server',
        'ODBC Driver 17 for SQL Server',
        'SQL Server'
    ]
    
    driver_name = None
    for d in preferred_drivers:
        if d in drivers:
            driver_name = d
            break
    
    if not driver_name and drivers:
        driver_name = drivers[0]
        
    if not driver_name:
        raise Exception("No ODBC driver found for SQL Server.")

    # Construct connection string
    # TrustServerCertificate=yes is usually required for Docker/Self-signed environments
    # Encrypt=no allows unencrypted connections if server permits (or encrypted if server requires), avoiding strict client-side enforcement
    conn_str = (
        f"DRIVER={{{driver_name}}};"
        f"SERVER={server_host};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"  
    )
    
    try:
        conn = pyodbc.connect(conn_str, timeout=timeout)
        return conn
    except pyodbc.Error as e:
        # Fallback or clean error
        raise Exception(f"Error connecting to MSSQL ({server_host}): {e}")
