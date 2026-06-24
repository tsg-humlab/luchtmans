from dataclasses import dataclass, astuple

from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.db import models

from django_select2.forms import HeavySelect2Widget


@dataclass
class ApiInfo:
    obj: object
    model: models.Model
    model_field_name: str
    url_template: str
    api_name: str
    fill_field_name: str


class ApiSelectWidget(HeavySelect2Widget):
    css_class_name = 'django-select2 django-select2-apilink'
    js = 'apilink.js'

    def __init__(self, *args, **kwargs):
        self.api_info = kwargs.pop('api_info', None)
        super().__init__(*args, **kwargs)

    def render(self, *args, **kwargs):
        output =  super().render(*args, **kwargs)
        obj, model, model_field_name, url_template, api_name, fill_field_name = astuple(self.api_info)
        field = model._meta.get_field(model_field_name)
        api_id, display_style = ("", "display: none") if not obj or not getattr(obj, model_field_name, None) \
                                else (escape(getattr(obj, model_field_name)), "")

        return output + mark_safe(f"""
            <div id='api_block_{model_field_name}' style="margin: 4px 0 0 10px;{display_style}">
                <a id="apilink_{model_field_name}" href="{url_template.format(api_id)}" target="_blank"
                 href_base="{url_template[:-2]}">
                    Show on {api_name}
                </a>
                <button class="button fill-button" id="fillbutton_{model_field_name}" data-fill-field-name="{fill_field_name}" 
                type="button">Fill in</button>
            </div>
            <div id='api_object_exists_{model_field_name}' style="display: none;" data-django-model="{model.__name__}">
                <p style="color: red; margin: .4em 1em 0em 1em">A {model.__name__.lower()} with this {field.verbose_name} already exists.</p>
                <a href="" target="_blank" style="margin-left:1em">
                    <img src="/static/admin/img/icon-viewlink.svg" alt="View"> View that {model.__name__.lower()}
                </a>
            </div>
            <script src="{settings.STATIC_URL}{self.js}"></script>
        """)