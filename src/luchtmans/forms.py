from dataclasses import dataclass, astuple

from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe

from django_select2.forms import HeavySelect2Widget


@dataclass
class ApiInfo:
    obj: object
    model_field_name: str
    url_template: str
    api_name: str


class ApiSelectWidget(HeavySelect2Widget):
    def __init__(self, *args, **kwargs):
        self.api_info = kwargs.pop('api_info', None)
        super().__init__(*args, **kwargs)

    def render(self, *args, **kwargs):
        output =  super().render(*args, **kwargs)

        if not self.api_info:
            return output

        obj, model_field_name, url_template, api_name = astuple(self.api_info)

        if not obj or not getattr(obj, model_field_name, None):
            return output

        id = escape(getattr(obj, model_field_name))
        link = mark_safe(
            f'<div style="margin: 4px 0 0 10px">'
            f'<a href="{url_template.format(id)}" target="_blank">Show on {api_name}</a>'
            f'</div>'
        )
        return output + link