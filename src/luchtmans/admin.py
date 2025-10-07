from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from modeltranslation.admin import TranslationAdmin

from .models import (Country, Place, Street, Address, Person, PersonPersonRelation, RelationType, PeriodOfResidence,
                     Religion, PersonReligion)


@admin.register(Country)
class CountryAdmin(TranslationAdmin):
    search_fields = ["name"]


@admin.register(Place)
class PlaceAdmin(TranslationAdmin):
    search_fields = ["name", "country__name"]
    autocomplete_fields = ["country"]


@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    search_fields = ["name", "place__name"]
    autocomplete_fields = ["place"]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    search_fields = ["description", "streetname_old", "house_number"]
    autocomplete_fields = ["street"]


class RelatedPersonInline(admin.TabularInline):
    model = PersonPersonRelation
    fields = ["types", "to_person"]
    autocomplete_fields = ["types", "to_person"]
    extra = 0
    verbose_name = _("Related person")
    fk_name = "from_person"


class ReligionInline(admin.TabularInline):
    model = PersonReligion
    extra = 0
    verbose_name = _("Religious affiliation")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    search_fields = ["short_name", "surname", "first_names"]
    autocomplete_fields = ["place_of_birth", "place_of_death"]
    list_filter = ["sex", "place_of_birth", "place_of_death", "religious_affiliation"]
    inlines = [RelatedPersonInline, ReligionInline]


@admin.register(PersonPersonRelation)
class PersonPersonRelationAdmin(TranslationAdmin):
    search_fields = ["from_person__short_name", "to_person__short_name", "types__text"]
    autocomplete_fields = ["from_person", "to_person", "types"]


@admin.register(RelationType)
class RelationTypeAdmin(admin.ModelAdmin):
    search_fields = ["text", "reverse"]
    autocomplete_fields = ["reverse"]


@admin.register(PeriodOfResidence)
class PeriodOfResidenceAdmin(admin.ModelAdmin):
    search_fields = ["person__short_name", "address__street__name", "address__street__place__name"]
    autocomplete_fields = ["person", "address"]


@admin.register(Religion)
class ReligionAdmin(TranslationAdmin):
    search_fields = ["name"]