import re
import datetime
import logging

import requests
from django.conf import settings
from django.db.models import Subquery, FloatField
import shlex

from django.db.models import Subquery, FloatField, Q


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
        return None, True


def and_or_to_q(search_string: str, field_name:str, AND: str= 'AND', OR: str= 'OR') -> Q:
    """Convert a search string to an AND and OR queryset"""
    search_list = and_or_to_list(search_string, AND, OR)

    q = make_q(search_list.pop(0), field_name)
    while search_list:
        operator = search_list.pop(0)
        new_q = make_q(search_list.pop(0), field_name)
        if operator == AND:
            q &= new_q
        elif operator == OR:
            q |= new_q
    return q


def make_q(term: str, field_name: str) -> Q:
    """Make a Q() object while taking a trailing '-' into account for negation"""
    if term.startswith('-'):
        return ~Q(**{f'{field_name}__icontains': term[1:]})
    return Q(**{f'{field_name}__icontains': term})


def and_or_to_list(search_string: str, AND: str, OR: str) -> list[str]:
    """Convert a search string to an AND and OR list"""
    search_list = shlex.split(search_string)
    while search_list and search_list[0] in [AND, OR]: search_list.pop(0)
    while search_list and search_list[-1] in [AND, OR]: search_list.pop()

    search_list_clean = search_list[:1]
    for word in search_list[1:]:
        if search_list_clean[-1] not in [AND, OR] and word not in [AND, OR]:
            search_list_clean.append(AND)
        elif search_list_clean[-1] in [AND, OR] and word in [AND, OR]:
            search_list_clean.append('')
        search_list_clean.append(word)
    return search_list_clean
