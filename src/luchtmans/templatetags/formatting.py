import re
import datetime

from django import template
from django.template.defaultfilters import stringfilter

from luchtmans.utils import str_to_date


register = template.Library()


register.filter("str_to_date", stringfilter(str_to_date))