from django.db import models


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
    country = models.ForeignKey(Country)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Street(models.Model):
    new_name = models.CharField(max_length=1024)
    old_name = models.TextField()
    place = models.ForeignKey(Place)

    def __str__(self):
        return f'{self.new_name} [old: {self.old_name}]'


class Address(Location):
    house_number = models.CharField(max_length=256)
    street = models.ForeignKey(Street)

    def __str__(self):
        return f'{self.street} {self.house_number}, {self.street.place}'
