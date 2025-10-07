from modeltranslation.translator import register, TranslationOptions
from luchtmans.models import Country, Place, Religion, RelationType, PersonPersonRelation


@register(Country)
class CountryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Place)
class PlaceTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Religion)
class ReligionTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(RelationType)
class RelationTypeTranslationOptions(TranslationOptions):
    fields = ('text',)


@register(PersonPersonRelation)
class PersonPersonRelationTranslationsOptions(TranslationOptions):
    fields = tuple()