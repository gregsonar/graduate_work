from http.client import BAD_REQUEST

from flask import request
from flask.views import MethodView

from services.rabbit_mq import send_user_created_event
from services.serialization_schemas import UserSchema
from services.user_created_schema import UserCreatedSchema
from services.users import find_user_by_id


class UserCreatedAPI(MethodView):
    def post(self):
        form_schema = UserCreatedSchema()
        errors = form_schema.validate(request.json)
        if errors:
            return errors, BAD_REQUEST
        user_id = request.json.get("user_id", None)
        user = find_user_by_id(user_id)
        if not user:
            return "User was not found", BAD_REQUEST
        user_schema = UserSchema()
        user_to_queue = user_schema.dump(user)

        send_user_created_event(user_to_queue)
        return user_to_queue
