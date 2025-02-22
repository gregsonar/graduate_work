from http.client import BAD_REQUEST, CREATED

from flask import request
from flask.views import MethodView

from services.rabbit_mq import send_instant_message_from_moderator


class SendGlobalMessageAPI(MethodView):
    def post(self):
        message = request.json.get("body") if request.json else None
        if not message:
            return "Message body is empty", BAD_REQUEST
        send_instant_message_from_moderator(message)
        return message, CREATED
