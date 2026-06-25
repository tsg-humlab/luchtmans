import re
import datetime
import logging

import requests
from django.conf import settings
from django.db.models import Subquery, FloatField


logger = logging.getLogger(__name__)


def get_nested_object(data, path, *args):
    """Give a path, return the value"""
    try:
        for key in path:
            data = data[key]
        return data
    except (KeyError, IndexError) as error:
        if args:
            return args[0]
        raise error


def str_to_date(value):
    """Convert a string to a datetime object if possible. Otherwise return the original value."""
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    return value


class SubqueryMedian(Subquery):
    template = '(SELECT PERCENTILE_CONT(.50) WITHIN GROUP (ORDER BY %(field_name)s) FROM (%(subquery)s) _median)'
    output_field = FloatField()

    def __init__(self, queryset, output_field=None, **extra):
        extra['field_name'] = queryset._fields[0]
        super().__init__(queryset, output_field, **extra)


def get_STCN_resource(api_id: str) -> tuple[requests.Response, bool]:
    """Get the STCN resource"""
    try:
        response = requests.get(settings.STCN_URL.format(api_id), headers={'accept': 'application/json'},
                                timeout=5)
        logger.debug(f'{response.request.url}: {response.status_code}')
        return response, False
    except requests.exceptions.RequestException as e:
        logger.error(f'{e.__class__.__name__}: {e}')
        return response, True
