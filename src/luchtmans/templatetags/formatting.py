import re
import datetime

from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()


@register.filter
@stringfilter
def str_to_date(value):
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    return value
