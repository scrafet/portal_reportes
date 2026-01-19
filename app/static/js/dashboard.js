document.addEventListener('DOMContentLoaded', function () {
    // 1. Fetch and Build Filters
    fetchFilters();

    // 2. Initialize DataTables
    initDataTable();
});

function fetchFilters() {
    const container = document.getElementById('filters-container');
    const loading = document.getElementById('filters-loading');

    // Simulate getting metadata for parameters
    setTimeout(() => {
        // Parameters for 'sp_ListarAtenciones'
        const parameters = [
            { name: 'fecha_inicio', label: 'Fecha Inicio', type: 'date' },
            { name: 'fecha_fin', label: 'Fecha Fin', type: 'date' },
            { name: 'sucursal', label: 'Sucursal', type: 'select', options: ['Central', 'Norte', 'Sur', 'Emergencia'] },
            { name: 'producto', label: 'Filtrar por Paciente', type: 'text', placeholder: 'Nombre...' }
        ];

        loading.style.display = 'none';
        container.innerHTML = '';

        parameters.forEach(param => {
            const col = document.createElement('div');
            col.className = 'col-md-3 mb-3';

            let inputHtml = '';

            if (param.type === 'date') {
                inputHtml = `<input type="date" class="form-control bg-dark text-white" name="${param.name}" id="${param.name}">`;
            } else if (param.type === 'select') {
                const opts = param.options.map(o => `<option value="${o}">${o}</option>`).join('');
                inputHtml = `<select class="form-select bg-dark text-white" name="${param.name}" id="${param.name}">${opts}</select>`;
            } else {
                inputHtml = `<input type="text" class="form-control bg-dark text-white" name="${param.name}" id="${param.name}" placeholder="${param.placeholder || ''}">`;
            }

            col.innerHTML = `
                <label for="${param.name}" class="form-label text-light small text-uppercase fw-bold">${param.label}</label>
                ${inputHtml}
            `;
            container.appendChild(col);
        });

    }, 300);
}

var dataTableInstance;

function initDataTable() {
    if (!$.fn.DataTable) return;

    // Use standard form submit to reload table
    const form = document.getElementById('dynamic-filter-form');
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        dataTableInstance.ajax.reload();
    });

    dataTableInstance = $('#report-table').DataTable({
        "serverSide": true,
        "processing": true,
        "ajax": {
            "url": "/reporte/",
            "type": "POST",
            "data": function (d) {
                // Append custom form data to the DataTables request
                // We use standard jQuery serialization or manually add
                const formData = new FormData(document.getElementById('dynamic-filter-form'));
                for (var [key, value] of formData.entries()) {
                    d[key] = value;
                }
                // CSRF Token for Django
                const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
                if (csrfInput) {
                    d.csrfmiddlewaretoken = csrfInput.value;
                } else {
                    d.csrfmiddlewaretoken = getCookie('csrftoken');
                }
            }
        },
        "columns": [
            { title: "ID" },
            { title: "Paciente / Servicio" },
            { title: "Estado" },
            { title: "Fecha Ingreso" },
            { title: "Acciones", orderable: false }
        ],
        "paging": true,
        "lengthChange": true,
        "searching": true,
        "ordering": true,
        "info": true,
        "autoWidth": false,
        "responsive": true,
        "dom": "<'row mb-2'<'col-sm-6'B><'col-sm-6'f>>" +
            "<'row'<'col-sm-12'tr>>" +
            "<'row'<'col-sm-5'i><'col-sm-7'p>>",
        "buttons": [
            { extend: 'copy', className: 'btn btn-secondary btn-sm', text: '<i class="fas fa-copy"></i> Copiar' },
            { extend: 'csv', className: 'btn btn-secondary btn-sm', text: '<i class="fas fa-file-csv"></i> CSV' },
            { extend: 'excel', className: 'btn btn-secondary btn-sm', text: '<i class="fas fa-file-excel"></i> Excel' },
            { extend: 'pdf', className: 'btn btn-secondary btn-sm', text: '<i class="fas fa-file-pdf"></i> PDF' },
            { extend: 'print', className: 'btn btn-secondary btn-sm', text: '<i class="fas fa-print"></i> Imprimir' }
        ],
        "language": {
            "url": "//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json"
        }
    });

    // Refresh button logic
    document.getElementById('btn-reset').addEventListener('click', function () {
        form.reset();
        dataTableInstance.ajax.reload();
    });
}

// Utility to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
