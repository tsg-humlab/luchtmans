from django.contrib import admin

from .models import Country, Place, Street, Address, Person, PersonPersonRelation, RelationType


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    pass


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    pass


@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    pass


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    pass


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    pass


@admin.register(PersonPersonRelation)
class PersonPersonRelationAdmin(admin.ModelAdmin):
    pass


@admin.register(RelationType)
class RelationTypeAdmin(admin.ModelAdmin):
    pass