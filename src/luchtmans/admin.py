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
    search_fields = ["short_name", "surname", "first_names"]
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
for model in [PersonWorkRelation, Format, STCNGenre,
              PersonEditionRelationRole, PersonEditionRelation, Collection, ItemType, Page, Binding, Item]:
    base_class = TranslationAdmin if model.__base__ == UniqueNameModel else admin.ModelAdmin
    admin_class = type(model.__name__+'Admin', (base_class,), {})
    admin.site.register(model, admin_class)


@admin.register(Language)
class LanguageAdmin(TranslationAdmin):
    search_fields = ['name']


@admin.register(GenreParisianCategory)
class GenreParisianCategoryAdmin(TranslationAdmin):
    search_fields = ['name']


@admin.register(PersonWorkRelationRole)
class PersonWorkRelationRoleAdmin(TranslationAdmin):
    search_fields = ['name']


class AuthorInline(admin.TabularInline):
    model = PersonWorkRelation
    fields = ["work", "person", "role"]
    autocomplete_fields = ["person", "role"]
    extra = 0
    verbose_name = _("author")
    verbose_name_plural = _("authors")


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ['title', 'authors_list', 'uncertain', 'language_list', 'viaf_id', 'genre_parisian_category', 'notes']
    search_fields = ['title']
    list_filter = ['uncertain', 'languages', 'genre_parisian_category']
    autocomplete_fields = ['languages', 'genre_parisian_category']
    inlines = [AuthorInline]

    @admin.display(description=_("authors"))
    def authors_list(self, obj):
        return ", ".join(obj.authors.values_list('short_name', flat=True))

    @admin.display(description=_("languages"))
    def language_list(self, obj):
        return ", ".join(obj.languages.values_list('name', flat=True))
