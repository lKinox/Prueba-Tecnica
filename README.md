# Prueba Técnica - API de Gestión de Alertas

## Descripción

API RESTful desarrollada en Flask para gestionar alertas de aplicaciones. Permite crear, consultar, actualizar, eliminar, filtrar y obtener estadísticas de alertas, usando un archivo JSON como almacenamiento.

## Instalación

```bash
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install -r requirements.txt
```

## Ejecución

```bash
python -m app.main
```

La API estará disponible en [http://localhost:8000](http://localhost:8000)

## Documentación automática

Swagger UI: [http://localhost:8000/apidocs](http://localhost:8000/apidocs)

## Endpoints principales

- `GET /api/alerts`  
  Lista alertas. Filtros: severity, status, source_system. Paginación: page, limit.
- `GET /api/alerts/{alert_id}`  
  Devuelve una alerta por ID.
- `POST /api/alerts`  
  Crea una alerta nueva.
- `PUT /api/alerts/{alert_id}`  
  Actualiza una alerta.
- `DELETE /api/alerts/{alert_id}`  
  Elimina una alerta.
- `POST /api/alerts/{alert_id}/acknowledge`  
  Cambia status a "acknowledged" y permite asignar usuario.
- `GET /api/alerts/stats`  
  Estadísticas de alertas.
- `POST /api/alerts/import`  
  Importa alertas desde sistema externo.
- `GET /health`  
  Health check.

```

## Ejecutar tests

```bash
python -m pytest tests/ -v
```

---

## Preguntas Conceptuales

**¿Cómo manejarías la concurrencia si múltiples procesos escriben al archivo JSON simultáneamente?**  
Usaría un mecanismo de bloqueo (como threading.Lock) para asegurar que solo un proceso/escritura accede al archivo a la vez y evitar corrupción de datos.

**¿Qué estrategia usarías para migrar este sistema a una base de datos real manteniendo la API compatible?**  
Reemplazaría la lógica de almacenamiento en `storage.py` para leer/escribir desde base de datos (ej: SQLite, PostgreSQL) usando un ORM, pero manteniendo los mismos modelos y lógica de negocio para que la API y endpoints sigan funcionando igual.

**¿Cómo implementarías rate limiting en esta API?**  
Utilizaría una extensión como Flask-Limiter para establecer límites de peticiones por IP o usuario, configurando reglas por endpoint según necesidad.
