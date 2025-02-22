from flask.views import MethodView
from flask import request, Response, jsonify
from werkzeug.exceptions import HTTPException
from http.client import OK, BAD_REQUEST

from services.serialization_schemas import MessageSchema
from services.rabbit_mq import send_instant_message
from services.users import find_user_by_id
from settings.extensions import logger


class MessageAPI(MethodView):
    def post(self):
        try:
            form_schema = MessageSchema()
            errors = form_schema.validate(request.json)
            if errors:
                logger.error(f"Validation errors: {errors}")
                return (
                    jsonify({"message": "Validation failed", "errors": errors}),
                    BAD_REQUEST,
                )

            message = form_schema.load(request.json)
            user = find_user_by_id(message.user_id)

            if not user:
                return jsonify({"message": "User was not found"}), BAD_REQUEST

            send_instant_message(message)
            return jsonify({"message": "Message sent successfully"}), OK

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return jsonify({"message": str(e)}), BAD_REQUEST
