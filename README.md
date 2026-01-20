# Portal de Reportes - Django AdminLTE Dashboard

Este proyecto implementa un portal de reportes moderno utilizando **Django 5**, **PostgreSQL** y **SQL Server**. El frontend ha sido diseñado para replicar la experiencia de **AdminLTE 3** en modo oscuro, utilizando **Bootstrap 5** y **DataTables.net** con procesamiento del lado del servidor.

## � Características Principales

*   **Stack Tecnológico**: Django 5, Python 3.11+, PostgreSQL 15, SQL Server 2019.
*   **Frontend**: Bootstrap 5 (Dark Mode), DataTables.net (Server-side, Export Buttons), jQuery.
*   **Estilo Visual**: Replicación fiel de AdminLTE 3 Dark Mode con CSS personalizado.
*   **Funcionalidades**:
    *   **Dashboard Interactivo**: Visualización de datos con filtros dinámicos.
    *   **Asistente de Creación de Reportes (Wizard)**:
        *   Conexión a bases de datos SQL Server externas.
        *   Descubrimiento automático de Stored Procedures.
        *   Configuración guiada paso a paso.
    *   **Gestión Integral (CRUD)**:
        *   Categorías: Organización dinámica del menú lateral.
        *   Reportes: Administración de metadatos de reportes.
        *   Usuarios: Gestión de acceso y perfiles.
    *   **Ejecución y Auditoría**:
        *   Ejecución de SPs con parámetros dinámicos.
        *   Registro de auditoría de todas las consultas realizadas (`ConsultaAuditoria`).

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

*   [Docker Desktop](https://www.docker.com/products/docker-desktop)
*   [Git](https://git-scm.com/)

## �️ Instalación y Despliegue (Docker Compose)

Sigue estos pasos para levantar el entorno completo de desarrollo:

1.  **Clonar el repositorio:**

    ```bash
    git clone <url-del-repositorio>
    cd portal_reportes
    ```

2.  **Configurar Variables de Entorno:**
    Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido (ajusta las contraseñas según tu preferencia):

    ```ini
    # Django
    SECRET_KEY=tu_clave_secreta_django
    DEBUG=True
    ALLOWED_HOSTS=*

    # PostgreSQL (Base de datos principal)
    DB_NAME=portal_db
    DB_USER=postgres
    DB_PASSWORD=postgres
    DB_HOST=db
    DB_PORT=5432

    # SQL Server (Fuente externa)
    MSSQL_SA_PASSWORD=TuPasswordFuerte123!
    MSSQL_PID=Developer
    ```

3.  **Construir y Levantar Contenedores:**

    Ejecuta el siguiente comando para compilar la imagen de Django y descargar las imágenes de base de datos:

    ```bash
    docker-compose up --build
    ```

    *   El proceso puede tardar unos minutos la primera vez, especialmente mientras SQL Server se inicializa y ejecuta los scripts de `DB/SIGH.sql`.

4.  **Acceder a la Aplicación:**
    Una vez que los contenedores estén corriendo, abre tu navegador en:
    *   [http://localhost:8000](http://localhost:8000)

## 🧪 Ejecución de Tests

Para ejecutar las pruebas unitarias y de integración dentro del entorno Docker, utiliza el siguiente comando:

```bash
docker-compose run --rm web python manage.py test
```

Esto ejecutará el runner de pruebas de Django (`manage.py test`) dentro del contenedor `web` y mostrará los resultados en tu terminal.

## 📂 Estructura del Proyecto

*   **app/**: Código fuente de la aplicación Django.
    *   `core/`: App principal con vistas, modelos y templates.
    *   `static/`: Archivos CSS y JS (incluyendo `adminlte_custom.css` y `dashboard.js`).
    *   `templates/`: Plantillas HTML (Base, Dashboard, Parciales).
*   **DB/**: Scripts SQL de inicialización para SQL Server.
*   **docker-compose.yml**: Definición de servicios (Web, DB, SQLServer, DB-Init).
*   **Dockerfile**: Configuración de la imagen de Python/Django.