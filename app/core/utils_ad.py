from ldap3 import Server, Connection, ALL, NTLM
from django.conf import settings

def get_ad_users():
    """
    Connects to Active Directory using settings from .env (via settings.py)
    Returns a list of dicts: {username, fullname, email}
    """
    # Use environment settings mapped in settings.py preferably
    # For now, we look for them in settings or defaults
    AD_SERVER = getattr(settings, 'AD_SERVER', None) 
    AD_USER = getattr(settings, 'AD_USER', None)
    AD_PASSWORD = getattr(settings, 'AD_PASSWORD', None)
    AD_SEARCH_BASE = getattr(settings, 'AD_SEARCH_BASE', None)
    
    if not AD_SERVER:
        # Return mock data if no config
        return [
            {'username': 'u1', 'fullname': 'Usuario AD 1', 'email': 'u1@domain.com'},
            {'username': 'u2', 'fullname': 'Usuario AD 2', 'email': 'u2@domain.com'},
        ]

    users = []
    
    try:
        server = Server(AD_SERVER, get_info=ALL)
        conn = Connection(server, user=AD_USER, password=AD_PASSWORD, authentication=NTLM, auto_bind=True)
        
        # Search for Person objects
        conn.search(AD_SEARCH_BASE, '(&(objectClass=person)(sAMAccountName=*))', attributes=['sAMAccountName', 'displayName', 'mail'])
        
        for entry in conn.entries:
            users.append({
                'username': str(entry.sAMAccountName),
                'fullname': str(entry.displayName) if entry.displayName else str(entry.sAMAccountName),
                'email': str(entry.mail) if entry.mail else ''
            })
    except Exception as e:
        print(f"LDAP Error: {e}")
        # Retain empty users or re-raise?
        # For UI safety, return empty and let caller handle
        pass
        
    return users
