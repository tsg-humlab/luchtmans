from modeltranslation.translator import register, TranslationOptions, translator
from luchtmans.models import (Country, Place, Religion, PersonPersonRelation, RelationType, Language, GenreParisianCategory,
                              PersonWorkRelationRole, Format, STCNGenre, PersonEditionRelationRole, ItemType,
                              Binding)


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


class NameModelTranslationOptions(TranslationOptions):
    fields = ('name',)

translator.register(Language, NameModelTranslationOptions)
translator.register(GenreParisianCategory, NameModelTranslationOptions)
translator.register(PersonWorkRelationRole, NameModelTranslationOptions)
translator.register(Format, NameModelTranslationOptions)
translator.register(STCNGenre, NameModelTranslationOptions)
translator.register(PersonEditionRelationRole, NameModelTranslationOptions)
translator.register(ItemType, NameModelTranslationOptions)
translator.register(Binding, NameModelTranslationOptions)

