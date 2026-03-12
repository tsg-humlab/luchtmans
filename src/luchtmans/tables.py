from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html, format_html_join

import django_tables2 as tables

from .models import Person


class PersonTable(tables.Table):
    collections = tables.Column(empty_values=(None))
    roles = tables.Column(empty_values=(None))
    relations = tables.Column(
        verbose_name=_("Relations"),
        orderable=False,
        empty_values=()
    )

    class Meta:
        model = Person
        template_name = "django_tables2/bootstrap5.html"
        attrs = {'class': 'table table-sortable'}
        fields = [
            'short_name',
            'sex',
            'roles',
            'place_of_birth',
            'date_of_birth',
            'place_of_death',
            'date_of_death',
            'collections',
            'relations',
        ]

    def render_relations(self, record):
        person = record
        of_str = ' of'
        relations = []
        for relation in person.to_relations.all():
            relation_of_str = '' if relation.type.name.endswith(of_str) else of_str
            relation_str = format_html(_('{}{} <a href="{}">{}</a>'), str(relation.type).capitalize(), relation_of_str,
                                     relation.second_person.get_absolute_url(), relation.second_person)
            relations.append(relation_str)
        for relation in person.from_relations.all():
            type = str(relation.type)
            type_without_of = type[:-len(of_str)] if type.endswith(of_str) else type
            relation_str = format_html(_('{}: <a href="{}">{}</a>'), type_without_of.capitalize(),
                                     relation.first_person.get_absolute_url(), relation.first_person)
            relations.append(relation_str)
        return format_html_join('\n', '{}<br/>', ((rel,) for rel in relations))