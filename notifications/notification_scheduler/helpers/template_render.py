from typing import Callable

from jinja2 import BaseLoader, Environment
from notification_scheduler.helpers.data_getter import TemplateDataGetter, User


def render_template(template: str, data: dict) -> str:
    render = Environment(loader=BaseLoader()).from_string(template)
    return render.render(**data)


class UsersTemplateRender:
    def __init__(
        self,
        template: str,
        data_getter: "TemplateDataGetter",
        render: Callable[[str, dict], str],
    ):
        self._template = template
        self._data_getter = data_getter
        self.render = render

    def gen_templates(self) -> (str, "User"):
        for template_data in self._data_getter.template_data():
            yield self.render(
                self._template, template_data.render_data()
            ), template_data.user
