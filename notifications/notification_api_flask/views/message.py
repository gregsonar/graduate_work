from flask.views import MethodView
from flask import request, Response
from werkzeug.exceptions import HTTPException
from http.client import OK, BAD_REQUEST

from services.serialization_schemas import MessageSchema
from services.rabbit_mq import send_instant_message
from services.users import find_user_by_id


class MessageAPI(MethodView):
    def post(self):
        form_schema = MessageSchema()
        errors = form_schema.validate(request.json)
        if errors:
            raise HTTPException(
                'Validation faild', Response(errors, BAD_REQUEST)
            )

        message = form_schema.load(request.json)

        user_id = request.json.get('user_id', None)
        user = find_user_by_id(user_id)
        if not user:
            return 'User was not found', BAD_REQUEST

        send_instant_message(message)
        return 'Message send', OK
