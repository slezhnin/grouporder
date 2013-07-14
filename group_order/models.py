from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_init
from django.dispatch import receiver
from django.utils import timezone


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name


class Manufacturer(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name


class Category(models.Model):
    upper = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, blank=True, null=True, on_delete=models.SET_NULL)
    manufacturer = models.ForeignKey(Manufacturer, blank=True, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return ' '.join((
            unicode(self.category) if self.category else '', unicode(self.manufacturer) if self.manufacturer else '',
            self.name))


class Price(models.Model):
    supplier = models.ForeignKey(Supplier)
    product = models.ForeignKey(Product)
    price = models.FloatField()

    def __unicode__(self):
        return ' '.join((unicode(self.supplier), unicode(self.product), unicode(self.price)))


class Purchase(models.Model):
    manager = models.ForeignKey(User)
    supplier = models.ForeignKey(Supplier)
    due = models.DateField()
    closed = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField(editable=False)
    updated = models.DateTimeField(editable=False)

    def __unicode__(self):
        return ' '.join((unicode(self.supplier), unicode(self.manager), unicode(self.due)))

    class Meta:
        ordering = ["created"]


class Order(models.Model):
    purchase = models.ForeignKey(Purchase)
    customer = models.ForeignKey(User)
    created = models.DateTimeField(editable=False)
    updated = models.DateTimeField(editable=False)

    def __unicode__(self):
        return ' '.join((unicode(self.purchase), unicode(self.customer), unicode(self.created)))

    class Meta:
        ordering = ["created"]


class Transfer(models.Model):
    customer = models.ForeignKey(User)
    order = models.ForeignKey(Order)
    amount = models.FloatField()
    created = models.DateTimeField(editable=False)

    def __unicode__(self):
        return ' '.join((unicode(self.order), unicode(self.customer), unicode(self.amount)))

    class Meta:
        ordering = ["created"]


class Item(models.Model):
    order = models.ForeignKey(Order)
    price = models.ForeignKey(Price)
    amount = models.IntegerField()
    created = models.DateTimeField(editable=False)
    updated = models.DateTimeField(editable=False)

    def __unicode__(self):
        return ' '.join((unicode(self.order), unicode(self.price), unicode(self.amount)))

    class Meta:
        ordering = ["created"]


@receiver(pre_save, weak=False)
def date_pre_save(sender, **kwargs):
    if sender in (Purchase, Order, Item):
        instance = kwargs["instance"]
        instance.updated = timezone.now()


@receiver(post_init, weak=False)
def date_post_init(sender, **kwargs):
    instance = kwargs["instance"]
    if sender in (Purchase, Order, Item, Transfer) and not instance.created:
        instance.created = timezone.now()
