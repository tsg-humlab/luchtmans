from django.db import models
from django.db.models.signals import post_save, post_delete
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


# # # END Helper classes and functions # # #


class Location(models.Model):
    wikidata_id = models.CharField(max_length=256)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        abstract = True


class Country(Location):
    name = models.CharField(max_length=256)

    class Meta:
        verbose_name_plural = 'countries'
        ordering = ['name']

    def __str__(self):
        return self.name


class Place(Location):
    name = models.CharField(max_length=256)
    country = models.ForeignKey(Country, models.PROTECT)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Street(models.Model):
    new_name = models.CharField(max_length=1024)
    old_name = models.TextField()
    place = models.ForeignKey(Place, models.PROTECT)

    def __str__(self):
        return f'{self.new_name} [old: {self.old_name}]'


class Address(Location):
    house_number = models.CharField(max_length=256)
    street = models.ForeignKey(Street, models.PROTECT)

    def __str__(self):
        return f'{self.street} {self.house_number}, {self.street.place}'


class Person(models.Model):
    """Represents a person."""

    class GenderChoices(models.TextChoices):
        FEMALE = "F", _("Female")
        MALE = "M", _("Male")
        OTHER = "O", _("Other")
        UNKNOWN = "U", _("Unknown")
        CORPORATE = "C", _("Corporate")

    short_name = models.CharField(max_length=256)
    surname = models.CharField(max_length=256, blank=True)
    first_names = models.CharField(max_length=256, blank=True)
    date_of_birth = models.CharField(max_length=50, blank=True)
    date_of_death = models.CharField(max_length=50, blank=True)
    sex = models.CharField(max_length=1, choices=GenderChoices.choices, blank=True)
    place_of_birth = models.ForeignKey(Place, models.PROTECT, blank=True, null=True, related_name="birthplace_of")
    place_of_death = models.ForeignKey(Place, models.PROTECT, blank=True, null=True, related_name="deathplace_of")
    related_to = models.ManyToManyField("self", blank=True, through="PersonPersonRelation",
                                        through_fields=('from_person', 'to_person'))
    notes = models.TextField(blank=True)
    bibliography_sources = models.TextField(blank=True)
    wikidata_id = models.CharField(max_length=256)

    def __str__(self):
        return self.short_name


class RelationType(models.Model):
    text = models.CharField(max_length=255, unique=True)
    reverse = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
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
        unique_together = ['from_person', 'to_person']

    def __str__(self):
        return f'{self.from_person} is related to {self.to_person}'


post_save_personpersonrelation = post_save_relation_creator(PersonPersonRelation, ('from_person', 'to_person'))
post_delete_personpersonrelation = post_delete_relation_creator(PersonPersonRelation, ('from_person', 'to_person'))