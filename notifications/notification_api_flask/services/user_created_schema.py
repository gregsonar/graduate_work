from marshmallow import Schema, fields, validate


class UserCreatedSchema(Schema):
    user_id = fields.UUID(required=True)
