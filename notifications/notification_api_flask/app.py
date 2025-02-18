import json

from flask import Flask
from werkzeug.exceptions import HTTPException

from settings.config import configurations
from settings.extensions import db, logger
from views.message import MessageAPI
from views.new_user import UserCreatedAPI
from views.rule import RuleAPI
from views.to_all import SendGlobalMessageAPI

app = Flask(__name__)

app.config.from_object(configurations["dev"])
db.init_app(app)


@app.route("/")
def index() -> str:
    return "Hi there! from Notification API v.1.0"


app.add_url_rule("/new-user", view_func=UserCreatedAPI.as_view("new_user"))
app.add_url_rule("/to-all", view_func=SendGlobalMessageAPI.as_view("to_all"))
app.add_url_rule("/rule", view_func=RuleAPI.as_view("rule"))
app.add_url_rule("/instant_message", view_func=MessageAPI.as_view("instant_message"))


@app.errorhandler(HTTPException)
def exceptions(e: HTTPException):
    logger.error(e)
    response = e.get_response()
    response.data = json.dumps(
        {"code": e.code, "name": e.name, "description": e.description}
    )
    response.content_type = "application/json"
    return response
