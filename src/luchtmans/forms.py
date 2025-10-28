from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe

from django_select2.forms import HeavySelect2Widget


class ApiSelectWidget(HeavySelect2Widget):
    def __init__(self, *args, **kwargs):
        self.obj = kwargs.pop('obj', None)
        super().__init__(*args, **kwargs)

    def render(self, *args, **kwargs):
        output =  super().render(*args, **kwargs)

        if not self.obj or not self.obj.wikidata_id:
            return output

        wikidata_id = escape(self.obj.wikidata_id)
        wikidata_link = mark_safe(
            f'<div style="margin: 4px 0 0 10px">'
            f'<a href="{settings.WIKIDATA_URL.format(wikidata_id)}" target="_blank">Show on Wikidata</a>'
            f'</div>'
        )
        return output + wikidata_link