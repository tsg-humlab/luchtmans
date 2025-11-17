from django.db import models
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver


# # # START Helper classes and functions # # #


def post_save_relation_creator(sender, relation_fields, other_fields=()):
    @receiver(post_save, sender=sender)
    def post_save_relation(sender, instance, created, **kwargs):
        """Create/update a/the symmetrical relation"""
        relation_fields_swapped = {
            relation_fields[0]: getattr(instance, relation_fields[1]),
            relation_fields[1]: getattr(instance, relation_fields[0]),
        }

        other_field_values = {field: getattr(instance, field) for field in other_fields}

        opposite_objects = sender.objects.filter(**relation_fields_swapped)
        if not opposite_objects.exists():
            sender.objects.create(**{**relation_fields_swapped, **other_field_values})
            return

        sender.objects.filter(id=opposite_objects[0].id).update(**other_field_values)

        # Delete superfluous objects
        sender.objects.filter(id__in=opposite_objects[1:].values_list('id', flat=True)).delete()

    return post_save_relation


def post_delete_relation_creator(sender, relation_fields):
    @receiver(post_delete, sender=sender)
    def post_delete_relation(sender, instance, **kwargs):
        """Delete the symmetrical relation"""
        relation_fields_swapped = {
            relation_fields[0]: getattr(instance, relation_fields[1]),
            relation_fields[1]: getattr(instance, relation_fields[0]),
        }
        sender.objects.filter(**relation_fields_swapped).delete()

    return post_delete_relation


def copy_reverse_many_to_many_objects(base_obj, other_obj, many_to_many_fields, reverse_field_name, calling_function):
    """
    Takes the many-to-many objects from base_obj en adds the reverse of those objects to the other_obj.
    """
    # Prevent recursively calling m2m_changed signal
    calling_function = globals()[calling_function]
    m2m_changed.disconnect(calling_function, sender=PersonPersonRelation.types.through)

    for field in many_to_many_fields:
        base_m2m_objects = getattr(base_obj, field).all()
        other_m2m_relation = getattr(other_obj, field)
        other_m2m_relation.clear()
        for base_m2m_object in base_m2m_objects:
            reverse_obj = getattr(base_m2m_object, reverse_field_name)
            other_m2m_relation.add(reverse_obj)

    m2m_changed.connect(calling_function, sender=PersonPersonRelation.types.through)


def m2m_changed_relation_creator(sender, relation_fields, relation_type_fields, m2m_relation_name, reverse_field_name='reverse'):
    @receiver(m2m_changed, sender=sender)
    def m2m_changed_relation(sender, instance, **kwargs):
        relation_fields_swapped = {
            relation_fields[0]: getattr(instance, relation_fields[1]),
            relation_fields[1]: getattr(instance, relation_fields[0]),
        }
        reverse = instance._meta.model.objects.get(**relation_fields_swapped)
        sender.objects.filter(**{relation_type_fields[0]: reverse}).delete()
        types_for_reverse = []
        for type in getattr(instance, m2m_relation_name).all():
            reverse_type = getattr(type, reverse_field_name)
            relation_type = reverse_type if reverse_type else type
            types_for_reverse.append(sender(**{relation_type_fields[0]: reverse,
                                               relation_type_fields[1]: relation_type}))
        sender.objects.bulk_create(types_for_reverse)

    return m2m_changed_relation


class Wikidata(models.Model):
    wikidata_id = models.CharField(max_length=256, blank=True)

    class Meta:
        abstract = True


class GeoLocation(models.Model):
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, editable=False)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, editable=False)

    class Meta:
        abstract = True


class UniqueNameModel(models.Model):
    name = models.CharField(_("name"), max_length=256, unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


# # # END Helper classes and functions # # #


class Country(Wikidata, GeoLocation):
    name = models.CharField(_("name"), max_length=256)

    class Meta:
        verbose_name = _("country")
        verbose_name_plural = _("countries")
        ordering = ['name']

    def __str__(self):
        return self.name


class Place(Wikidata, GeoLocation):
    name = models.CharField(_("name"), max_length=256)
    country = models.ForeignKey(Country, models.PROTECT)

    class Meta:
        verbose_name = _("place")
        verbose_name_plural = _("places")
        ordering = ['name']

    def __str__(self):
        return self.name


class Street(Wikidata, GeoLocation):
    name = models.CharField(_("name"), max_length=1024)
    place = models.ForeignKey(Place, models.PROTECT)

    class Meta:
        verbose_name = _("street")
        verbose_name_plural = _("streets")

    def __str__(self):
        return f'{self.name}'


class Address(Wikidata, GeoLocation):
    description = models.CharField(_("description"), max_length=256, default='')
    streetname_old = models.CharField(_("old street name"), max_length=256, blank=True)
    house_number = models.CharField(_("house number"), max_length=256)
    street = models.ForeignKey(Street, models.PROTECT)

    class Meta:
        verbose_name = _("address")
        verbose_name_plural = _("addresses")

    def __str__(self):
        return f'{self.street} {self.house_number}, {self.street.place}'


class Religion(models.Model):
    name = models.CharField(_("name"), max_length=255, unique=True)

    class Meta:
        verbose_name = _("religion")
        verbose_name_plural = _("religions")
        ordering = ['name']

    def __str__(self):
        return self.name


class Person(Wikidata):
    """Represents a person."""

    class GenderChoices(models.TextChoices):
        FEMALE = "F", _("Female")
        MALE = "M", _("Male")
        OTHER = "O", _("Other")
        UNKNOWN = "U", _("Unknown")
        CORPORATE = "C", _("Corporate")

    short_name = models.CharField(_("short name"), max_length=256)
    surname = models.CharField(_("surname"), max_length=256, blank=True)
    first_names = models.CharField(_("first names"), max_length=256, blank=True)
    date_of_birth = models.CharField(_("date of birth"), max_length=50, blank=True)
    date_of_death = models.CharField(_("date of death"), max_length=50, blank=True)
    sex = models.CharField(_("sex"), max_length=1, choices=GenderChoices.choices, blank=True)
    place_of_birth = models.ForeignKey(Place, models.PROTECT, blank=True, null=True, related_name="birthplace_of")
    place_of_death = models.ForeignKey(Place, models.PROTECT, blank=True, null=True, related_name="deathplace_of")
    related_to = models.ManyToManyField("self", blank=True, through="PersonPersonRelation",
                                        through_fields=('from_person', 'to_person'),
                                        verbose_name=_("related to"))
    notes = models.TextField(_("notes"), blank=True)
    bibliography_sources = models.TextField(_("bibliography sources"), blank=True)
    religious_affiliation = models.ManyToManyField(
        Religion,
        blank=True,
        through="PersonReligion",
        through_fields=('person', 'religion'),
        verbose_name=_("religious affiliation")
    )

    class Meta:
        verbose_name = _("person")
        verbose_name_plural = _("persons")

    def __str__(self):
        return self.short_name


class RelationType(models.Model):
    text = models.CharField(_("text"), max_length=255, unique=True)
    reverse = models.ForeignKey("self", blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = _("relation type")
        verbose_name_plural = _("relation types")
        ordering = ['text']

    def __str__(self):
        return self.text


@receiver(post_save, sender=RelationType)
def post_save_relation(sender, instance, created, **kwargs):
    reverse = instance.reverse
    if reverse and reverse.reverse != instance:
        reverse.reverse = instance
        reverse.save()


class PersonPersonRelation(models.Model):
    from_person = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="from_relations")
    to_person = models.ForeignKey(Person, on_delete=models.DO_NOTHING, related_name="to_relations")
    types = models.ManyToManyField(RelationType, blank=True)

    class Meta:
        verbose_name = _('person person relation')
        verbose_name_plural = _('person person relations')
        unique_together = ['from_person', 'to_person']

    def __str__(self):
        return f'{self.from_person} is related to {self.to_person}'


# Signal receivers for handling reverse PersonPersonRelations
post_save_personpersonrelation = post_save_relation_creator(PersonPersonRelation, ('from_person', 'to_person'))
post_delete_personpersonrelation = post_delete_relation_creator(PersonPersonRelation, ('from_person', 'to_person'))
m2m_changed_personpersonrelation = m2m_changed_relation_creator(PersonPersonRelation.types.through,
                                                                ('from_person', 'to_person'),
                                                                ('personpersonrelation', 'relationtype'),
                                                                'types')


class PeriodOfResidence(models.Model):
    """Model linking Person to Address over a period of time."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    start_year = models.IntegerField(_("start year"), blank=True, null=True)
    end_year = models.IntegerField(_("end year"), blank=True, null=True)

    class Meta:
        verbose_name = _("period of residence")
        verbose_name_plural = _("periods of residence")

    def __str__(self):
        from_string = f" from {self.start_year}" if self.start_year else ""
        until_string = f" until {self.end_year}" if self.end_year else ""
        return f"{self.person} lived at {self.address}{from_string}{until_string}"


class PersonReligion(models.Model):
    """Model linking a Person to a Religion during a period of time."""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    religion = models.ForeignKey(Religion, models.PROTECT)
    start_year = models.IntegerField(_("start year"), blank=True, null=True)
    end_year = models.IntegerField(_("end year"), blank=True, null=True)

    def __str__(self):
        return f'{self.person.short_name} was {self.religion.name.lower()}'


class Language(UniqueNameModel):

    class Meta:
        verbose_name = _("language")
        verbose_name_plural = _("languages")


class GenreParisianCategory(UniqueNameModel):

    class Meta:
        verbose_name = _("genre Parisian category")
        verbose_name_plural = _("genre Parisian categories")


class Work(Wikidata, models.Model):
    authors = models.ManyToManyField(
        Person,
        through="PersonWorkRelation",
        through_fields=('work', 'person'),
        verbose_name=_("authors")
    )
    title = models.CharField(_("title"), max_length=256)
    uncertain = models.BooleanField(_("uncertain"))
    languages = models.ManyToManyField(
        Language,
        blank=True,
        verbose_name=_("languages"),
    )
    viaf_id = models.CharField(_("VIAF identifier"), max_length=256, blank=True)
    genre_parisian_category = models.ForeignKey(GenreParisianCategory, null=True, blank=True, on_delete=models.PROTECT,
                                                verbose_name=_("genre Parisian category"))
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("work")
        verbose_name_plural = _("works")

    def __str__(self):
        return self.title


class PersonWorkRelationRole(UniqueNameModel):

    class Meta:
        verbose_name = _("person work relation role")
        verbose_name_plural = _("person work relation roles")


class PersonWorkRelation(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name=_("person"))
    work = models.ForeignKey(Work, on_delete=models.CASCADE, verbose_name=_("work"))
    role = models.ForeignKey(PersonWorkRelationRole, on_delete=models.PROTECT, verbose_name=_("role"))

    class Meta:
        verbose_name = _("person work relation")
        verbose_name_plural = _("person work relations")


class Format(UniqueNameModel):

    class Meta:
        verbose_name = _("format")
        verbose_name_plural = _("formats")


class STCNGenre(UniqueNameModel):

    class Meta:
        verbose_name = _("STCN genre")
        verbose_name_plural = _("STCN genres")


class Edition(models.Model):
    stcn_id = models.CharField(_("STCN identifier"), max_length=256, blank=True)
    persons = models.ManyToManyField(
        Person,
        blank=True,
        through="PersonEditionRelation",
        through_fields=('edition', 'person'),
        verbose_name=_("authors")
    )
    title = models.CharField(_("title"), max_length=256)
    edition_uncertain = models.BooleanField(_("edition is uncertain"))
    year_of_publication_start = models.IntegerField(_("year of publication start"), null=True, blank=True)
    year_of_publication_end = models.IntegerField(_("year of publication end"), null=True, blank=True)
    places_of_publication = models.ManyToManyField(
        Place,
        blank=True,
        verbose_name=_("places of publication")
    )
    volumes = models.CharField(_("volumes"), blank=True)
    languages = models.ManyToManyField(
        Language,
        blank=True,
        verbose_name=_("languages")
    )
    stcn_genres = models.ManyToManyField(
        STCNGenre,
        blank=True,
        verbose_name=_("STCN genres")
    )
    notes = models.TextField(_("notes"), blank=True)
    short_title = models.CharField(_("short title"), max_length=256)
    work = models.ForeignKey(Work, on_delete=models.PROTECT, verbose_name=_("work"))

    class Meta:
        verbose_name = _("edition")
        verbose_name_plural = _("editions")

    def __str__(self):
        return self.short_title


class PersonEditionRelationRole(UniqueNameModel):

    class Meta:
        verbose_name = _("person edition relation role")
        verbose_name_plural = _("person edition relation roles")


class PersonEditionRelation(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name=_("person"))
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE, verbose_name=_("edition"))
    role = models.ForeignKey(PersonEditionRelationRole, on_delete=models.PROTECT, verbose_name=_("role"))

    class Meta:
        verbose_name = _("person edition relation")
        verbose_name_plural = _("person edition relations")

    def __str__(self):
        return _('{person} is {role} of {edition}').format(person=self.person, role=self.role, edition=self.edition)


class Collection(models.Model):
    short_title = models.CharField(_("short title"), max_length=256)
    all_headers = models.TextField(_("all headers"), blank=True)
    client = models.OneToOneField(Person, related_name="collection", on_delete=models.PROTECT, verbose_name=_("client"))
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("collection")
        verbose_name_plural = _("collections")


class ItemType(UniqueNameModel):

    class Meta:
        verbose_name = _("item type")
        verbose_name_plural = _("item type")


class Page(models.Model):
    RECTO = 'R'
    VERSO = 'V'
    RECTO_VERSO_CHOICES = {
        RECTO: 'Recto',
        VERSO: 'Verso'
    }
    volume = models.IntegerField(_("volume"))
    folio = models.CharField(_("folio"), max_length=256)
    recto_verso = models.CharField(_("recto or verso"), max_length=1, choices=RECTO_VERSO_CHOICES)

    class Meta:
        verbose_name = _("page")
        verbose_name_plural = _("pages")


class Binding(UniqueNameModel):

    class Meta:
        verbose_name = _("binding")
        verbose_name_plural = _("bindings")


class Item(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.PROTECT, verbose_name=_("collection"))
    transcription_full = models.CharField(_("full transcription"), max_length=256)
    type = models.ForeignKey(ItemType, on_delete=models.PROTECT, verbose_name=_("type"))
    non_book = models.BooleanField(_("non book"))
    transcription_incomplete = models.BooleanField(_("transcription is incomplete"))
    page = models.ForeignKey(Page, on_delete=models.PROTECT, verbose_name=_("page"))
    date = models.DateField(_("date"), null=True, blank=True)
    date_paid = models.DateField(_("date_paid"), null=True, blank=True)
    editions = models.ManyToManyField(Edition, verbose_name=_("editions"))
    edition_uncertain = models.BooleanField(_("edition is uncertain"))
    volumes = models.CharField(_("volumes"), max_length=10, default='1')
    number_of_copies = models.CharField(_("number of copies"), max_length=10, default='1')
    binding = models.ManyToManyField(Binding, blank=True, verbose_name=_("bindings"))
    languages = models.ManyToManyField(Language, blank=True, verbose_name=_("languages"))
    price = models.CharField(_("price"), max_length=20, blank=True)
    price_decimal = models.DecimalField(_("decimal price"), max_digits=20, decimal_places=2, blank=True)
    notes = models.TextField(_("notes"), blank=True)
    work_in_progress = models.BooleanField(_("work in progress"))

    class Meta:
        verbose_name = _("item")
        verbose_name_plural = _("items")
