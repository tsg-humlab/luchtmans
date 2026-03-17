from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html, format_html_join

import django_tables2 as tables
from django_tables2.utils import A

from .models import Person


class PersonTable(tables.Table):
    short_name = tables.LinkColumn('person_detail', args=[A("pk")])
    uuid = tables.Column(empty_values=(), verbose_name="", orderable=False)
    collections = tables.Column(empty_values=(None))
    roles = tables.Column(empty_values=(None))
    relations = tables.Column(
        verbose_name=_("Relations"),
        orderable=False,
        empty_values=(None)
    )

    class Meta:
        model = Person
        template_name = "django_tables2/bootstrap5.html"
        attrs = {'class': 'table table-sortable'}
        fields = [
            'short_name',
            'uuid',
            'sex',
            'roles',
            'place_of_birth',
            'date_of_birth',
            'place_of_death',
            'date_of_death',
            'collections',
            'relations',
        ]


    def render_uuid(self, record, value):
        context = {
            'object': record,
            'url_name_change': 'admin:luchtmans_person_change' if self.request.user.has_perm('luchtmans.change_person') else '',
            'url_name_delete': 'admin:luchtmans_person_delete' if self.request.user.has_perm('luchtmans.delete_person') else '',
        }
        return render_to_string('uuid_column.html', context)

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