from http.client import OK, BAD_REQUEST, CONFLICT, CREATED

from flask import request, jsonify, Response
from flask.views import MethodView
from werkzeug.exceptions import HTTPException

from services.rule import (
    get_all_rules,
    rule_data,
    RuleNotFound,
    add_message_rule,
    RuleExists,
    delete_message_rule,
    update_message_rule,
)
from services.serialization_schemas import DumpRuleSchema, LoadRuleSchema, Rule


class RuleAPI(MethodView):
    """Обработка вызовов по созданию и редактированию правил рассылки
    Правло включает в себя:
        1) Шаблон для рендера для jinja2 (template)
        2) Описание расписания запуска в формате crontab (timetable)
        3) Наименвоание правила (name)
        4) Заголовок для отпраки (subject)

    """

    def get(self):
        name = request.json.get("name")

        if name is None:
            form_schema = DumpRuleSchema(many=True)
            rules = form_schema.dump(get_all_rules())
            return jsonify(rules), OK
        try:
            form_schema = DumpRuleSchema()
            return form_schema.dump(rule_data(name)), OK
        except RuleNotFound:
            return f"No rule naming {name}", BAD_REQUEST

    def post(self):
        rule_data = self._get_rule_data()
        try:
            new_rule = add_message_rule(rule_data)
        except RuleExists:
            return "rule already exists", CONFLICT

        form_schema = DumpRuleSchema()
        return form_schema.dump(new_rule), CREATED

    def delete(self):
        name = request.json.get("name")
        if name is None:
            return "Filed name missing", BAD_REQUEST
        try:
            delete_message_rule(name)
        except RuleNotFound:
            return f"No rule naming {name}", BAD_REQUEST

        return "Success", OK

    def patch(self):
        rule_data = self._get_rule_data()
        try:
            new_rule = update_message_rule(rule_data)
        except RuleNotFound:
            return f"No rule naming {rule_data.name}", BAD_REQUEST

        form_schema = DumpRuleSchema()
        return form_schema.dump(new_rule), OK

    def _get_rule_data(self) -> Rule:
        form_schema = LoadRuleSchema()
        errors = form_schema.validate(request.json)
        if errors:
            raise HTTPException("Validation failed", Response(errors, BAD_REQUEST))
        return form_schema.load(request.json)
