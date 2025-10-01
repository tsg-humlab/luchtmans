from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from modeltranslation.admin import TranslationAdmin

from .models import (Country, Place, Street, Address, Person, PersonPersonRelation, RelationType, PeriodOfResidence,
                     Religion, PersonReligion, UniqueNameModel, Language, GenreParisianCategory, Work,
                     PersonWorkRelationRole, PersonWorkRelation, Format, STCNGenre, Edition, PersonEditionRelationRole,
                     PersonEditionRelation, Collection, ItemType, Page, Binding, Item)


@admin.register(Country)
class CountryAdmin(TranslationAdmin):
    pass


@admin.register(Place)
class PlaceAdmin(TranslationAdmin):
    pass


@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    pass


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    pass


class ReligionInline(admin.TabularInline):
    model = PersonReligion
    extra = 0
    verbose_name = _("Religious affiliation")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    inlines = [ReligionInline]


@admin.register(PersonPersonRelation)
class PersonPersonRelationAdmin(admin.ModelAdmin):
    pass


@admin.register(RelationType)
class RelationTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(PeriodOfResidence)
class PeriodOfResidenceAdmin(admin.ModelAdmin):
    pass


@admin.register(Religion)
class ReligionAdmin(TranslationAdmin):
    pass

# Register empty admin classes in one go
for model in [Language, GenreParisianCategory, Work, PersonWorkRelationRole, PersonWorkRelation, Format, STCNGenre,
              Edition, PersonEditionRelationRole, PersonEditionRelation, Collection, ItemType, Page, Binding, Item]:
    base_class = TranslationAdmin if model.__base__ == UniqueNameModel else admin.ModelAdmin
    admin_class = type(model.__name__+'Admin', (base_class,), {})
    admin.site.register(model, admin_class)