from marshmallow import Schema, fields, validate, ValidationError

SEVERITIES = ["low", "medium", "high", "critical"]
STATUSES = ["active", "acknowledged", "resolved"]

class AlertSchema(Schema):
    id = fields.Str(required=True)
    title = fields.Str(required=True)
    description = fields.Str(required=True)
    severity = fields.Str(required=True, validate=validate.OneOf(SEVERITIES))
    status = fields.Str(required=True, validate=validate.OneOf(STATUSES))
    source_system = fields.Str(required=True)
    created_at = fields.Str(required=True)
    updated_at = fields.Str(required=True)
    assigned_to = fields.Str(allow_none=True)
    tags = fields.List(fields.Str(), required=True)

class AlertImportSchema(Schema):
    external_id = fields.Str(required=True)
    title = fields.Str(required=True)
    description = fields.Str(required=True)
    severity = fields.Str(required=True, validate=validate.OneOf(SEVERITIES))

class ExternalAlertsBatchSchema(Schema):
    source_system = fields.Str(required=True)
    alerts = fields.List(fields.Nested(AlertImportSchema), required=True)