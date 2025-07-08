import logging
from flask import Flask, request, jsonify
from flasgger import Swagger
from marshmallow import ValidationError

from .models import AlertSchema, ExternalAlertsBatchSchema
from .services import (
    get_alerts, get_alert, create_alert, update_alert, delete_alert,
    acknowledge_alert, import_alerts, get_stats
)
from .utils import error_response

swagger_template = {
    'swagger': '2.0',
    'info': {
        'title': "API de Gestión de Alertas",
        'version': "1.0"
    },
    'definitions': {
        'Alert': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'description': {'type': 'string'},
                'severity': {'type': 'string', 'enum': ['low', 'medium', 'high', 'critical']},
                'source_system': {'type': 'string'},
                'assigned_to': {'type': 'string', 'nullable': True},
                'tags': {'type': 'array', 'items': {'type': 'string'}}
            },
            'required': ['title', 'description', 'severity', 'source_system', 'tags']
        },
        'AlertImport': {
            'type': 'object',
            'properties': {
                'external_id': {'type': 'string'},
                'title': {'type': 'string'},
                'description': {'type': 'string'},
                'severity': {'type': 'string', 'enum': ['low', 'medium', 'high', 'critical']}
            },
            'required': ['external_id', 'title', 'description', 'severity']
        }
    }
}

app = Flask(__name__)
swagger = Swagger(app, template=swagger_template)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

@app.before_request
def log_request_info():
    logging.info(f"Request: {request.method} {request.path} - Body: {request.get_data()} - Args: {request.args}")

@app.after_request
def log_response_info(response):
    try:
        if not response.direct_passthrough:
            logging.info(f"[Response] {response.status_code} - {response.get_data(as_text=True)}")
        else:
            logging.info(f"[Response] {response.status_code} - <passthrough response>")
    except Exception as e:
        logging.warning(f"[Response] {response.status_code} - <error logging response body: {e}>")
    return response

@app.route("/health", methods=["GET"])
def health():
    """
    Health check
    ---
    responses:
      200:
        description: OK
    """
    return jsonify({"status": "ok"}), 200

@app.route("/api/alerts", methods=["GET"])
def list_alerts():
    """
    Listar alertas con filtros y paginación
    ---
    parameters:
      - name: severity
        in: query
        type: string
      - name: status
        in: query
        type: string
      - name: source_system
        in: query
        type: string
      - name: page
        in: query
        type: integer
      - name: limit
        in: query
        type: integer
    responses:
      200:
        description: Lista de alertas
    """
    filters = {
        "severity": request.args.get("severity"),
        "status": request.args.get("status"),
        "source_system": request.args.get("source_system"),
    }
    filters = {k: v for k, v in filters.items() if v}
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    alerts, meta = get_alerts(filters, page, limit)
    return jsonify({"alerts": alerts, "meta": meta})

@app.route("/api/alerts/<alert_id>", methods=["GET"])
def retrieve_alert(alert_id):
    """
    Obtener una alerta específica
    ---
    parameters:
      - name: alert_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Alerta encontrada
      404:
        description: No encontrada
    """
    alert = get_alert(alert_id)
    if not alert:
        return error_response("Alerta no encontrada", 404)
    return jsonify(alert)

@app.route("/api/alerts", methods=["POST"])
def create_alert_route():
    """
    Crear alerta nueva
    ---
    parameters:
      - in: body
        name: alert
        required: true
        schema:
          $ref: '#/definitions/Alert'
        examples:
          application/json:
            value:
              title: "Nueva alerta"
              description: "Descripción de la alerta"
              severity: "high"
              source_system: "sistema-1"
              assigned_to: null
              tags: ["prueba", "api"]
    responses:
      201:
        description: Alerta creada
      400:
        description: Error de validación
    """
    schema = AlertSchema(exclude=["id", "created_at", "updated_at", "status"])
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return error_response(err.messages, 400)
    alert = create_alert(data)
    return jsonify(alert), 201

@app.route("/api/alerts/<alert_id>", methods=["PUT"])
def update_alert_route(alert_id):
    """
    Actualizar alerta
    ---
    parameters:
      - in: path
        name: alert_id
        type: string
        required: true
      - in: body
        name: alert
        schema:
          $ref: '#/definitions/Alert'
    responses:
      200:
        description: Alerta actualizada
      404:
        description: No encontrada
    """
    schema = AlertSchema(partial=True)
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return error_response(err.messages, 400)
    alert = update_alert(alert_id, data)
    if not alert:
        return error_response("Alerta no encontrada", 404)
    return jsonify(alert)

@app.route("/api/alerts/<alert_id>", methods=["DELETE"])
def delete_alert_route(alert_id):
    """
    Eliminar alerta
    ---
    parameters:
      - in: path
        name: alert_id
        type: string
        required: true
    responses:
      204:
        description: Eliminada
      404:
        description: No encontrada
    """
    ok = delete_alert(alert_id)
    if not ok:
        return error_response("Alerta no encontrada", 404)
    return "", 204

@app.route("/api/alerts/<alert_id>/acknowledge", methods=["POST"])
def acknowledge_alert_route(alert_id):
    """
    Acknowledge alerta y asignar usuario
    ---
    parameters:
      - in: path
        name: alert_id
        type: string
        required: true
      - in: body
        name: assigned_to
        schema:
          type: object
          properties:
            assigned_to:
              type: string
    responses:
      200:
        description: Alerta actualizada
      404:
        description: No encontrada
    """
    assigned_to = request.json.get("assigned_to") if request.json else None
    alert = acknowledge_alert(alert_id, assigned_to)
    if not alert:
        return error_response("Alerta no encontrada", 404)
    return jsonify(alert)

@app.route("/api/alerts/stats", methods=["GET"])
def alerts_stats():
    """
    Estadísticas de alertas
    ---
    responses:
      200:
        description: Estadísticas
    """
    stats = get_stats()
    return jsonify(stats)

@app.route("/api/alerts/import", methods=["POST"])
def import_alerts_route():
    """
    Importar alertas externas
    ---
    parameters:
      - in: body
        name: batch
        schema:
          type: object
          properties:
            source_system:
              type: string
            alerts:
              type: array
              items:
                $ref: '#/definitions/AlertImport'
    responses:
      200:
        description: Alertas importadas
      400:
        description: Error de validación
    """
    try:
        batch = ExternalAlertsBatchSchema().load(request.json)
    except ValidationError as err:
        return error_response(err.messages, 400)
    imported = import_alerts(batch)
    return jsonify({"imported": imported}), 200

from flasgger.utils import swag_from
from .models import SEVERITIES, STATUSES

def swagger_definitions():
    from flasgger import Schema, fields
    class Alert(Schema):
        id = fields.Str()
        title = fields.Str()
        description = fields.Str()
        severity = fields.Str()
        status = fields.Str()
        source_system = fields.Str()
        created_at = fields.Str()
        updated_at = fields.Str()
        assigned_to = fields.Str()
        tags = fields.List(fields.Str())
    class AlertImport(Schema):
        external_id = fields.Str()
        title = fields.Str()
        description = fields.Str()
        severity = fields.Str()
    return {"Alert": Alert, "AlertImport": AlertImport}

if __name__ == "__main__":
    app.run(port=8000, debug=True)