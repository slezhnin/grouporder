from django.core.urlresolvers import reverse_lazy
from django.db import models
from django.db.models.signals import pre_save, post_init
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class Person(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_('user'))
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    middle_name = models.CharField(_('middle name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)

    def get_full_name(self):
        return ' '.join(filter(lambda x: len(x), map(lambda x: x.strip().capitalize(), (
            self.first_name.strip() or self.user.first_name, self.middle_name,
            self.last_name.strip() or self.user.last_name)))) or self.user.name

    def __unicode__(self):
        return self.get_full_name()


class Supplier(models.Model):
    name = models.CharField(_('name'), max_length=100)
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    address = models.TextField(_('address'), blank=True)
    description = models.TextField(_('description'), blank=True)

    def __unicode__(self):
        return self.name


class Manufacturer(models.Model):
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)

    def __unicode__(self):
        return self.name


class Category(models.Model):
    upper = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = _('categories')


class Product(models.Model):
    category = models.ForeignKey(Category, verbose_name=_('category'), blank=True, null=True,
                                 on_delete=models.SET_NULL)
    manufacturer = models.ForeignKey(Manufacturer, verbose_name=_('manufacturer'), blank=True,
                                     null=True, on_delete=models.SET_NULL)
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)

    def __unicode__(self):
        return ' '.join(map(lambda x: unicode(x),
                            filter(None, (self.category, self.manufacturer, self.name))))


class Price(models.Model):
    supplier = models.ForeignKey(Supplier, verbose_name=_('supplier'))
    product = models.ForeignKey(Product, verbose_name=_('product'))
    price = models.FloatField(_('price'))
    created = models.DateTimeField(editable=False)
    updated = models.DateTimeField(editable=False)

    def __unicode__(self):
        return ' '.join((unicode(self.product), '|', unicode(self.price)))

    class Meta:
        ordering = ["created"]


class Purchase(models.Model):
    manager = models.ForeignKey(Person, verbose_name=_('manager'))
    supplier = models.ForeignKey(Supplier, verbose_name=_('supplier'))
    due = models.DateField(_('due'))
    closed = models.DateTimeField(_('close date'), blank=True, null=True)
    transferred = models.BooleanField(_('transferred'), default=False)
    created = models.DateTimeField(editable=False)
    updated = models.DateTimeField(editable=False)

    def get_absolute_url(self):
        return reverse_lazy('group_order:purchase', kwargs={'pk': self.id})

    def is_manager(self, person):
        return self.manager == person

    def has_order(self, person):
        return self.order_set.filter(customer=person).aggregate(models.Count('id'))['id__count']

    def past_due(self):
        return self.due < timezone.now().date()

    def quantity(self):
        return self.order_set.aggregate(models.Sum('item__quantity'))['item__quantity__sum'] or 0

    def total(self):
        return self.order_set.aggregate(models.Sum('item__price'))['item__price__sum'] or 0

    def paid(self):
        amount = models.Sum('transfer__amount')
        return self.order_set.aggregate(amount)['transfer__amount__sum'] or 0

    def transfer_count(self):
        aggr_trans_cnt = models.Count('transfer__amount')
        return self.order_set.aggregate(aggr_trans_cnt)['transfer__amount__count'] or 0

    def remainder(self):
        return self.paid() - self.total()

    def valid_to_transfer(self):
        return Purchase.objects.exclude(id=self.id).filter(closed=None)

    def product_quantity_report(self):
        report = {}
        for order in self.order_set.all():
            for item in order.item_set.all():
                product = report.get(unicode(item.product.product),
                                     {"product": unicode(item.product.product), "quantity": 0,
                                      "sum": 0.0})
                product["quantity"] += item.quantity
                product["sum"] += item.price
                report[product["product"]] = product
        report = report.values()
        report.sort(lambda a, b: cmp(a["product"].lower(), b["product"].lower()))
        return report

    def transfer_remainder(self, purchase_id):
        # Check if id is valid
        transfer_to_purchase = Purchase.objects.get(id=purchase_id)
        # Make transfer for each order
        for order in self.order_set.all():
            remainder = order.remainder()
            if remainder != 0:
                new_transfer = Transfer(
                    order=self._find_or_create_order(transfer_to_purchase, order),
                    customer=order.customer, amount=remainder)
                new_transfer.save()
        self.transferred = True
        self.save()

    def _find_or_create_order(self, transfer_to_purchase, order):
        if transfer_to_purchase.order_set.filter(customer=order.customer).count():
            return transfer_to_purchase.order_set.get(customer=order.customer)
        new_order = Order(purchase=transfer_to_purchase, customer=order.customer)
        new_order.save()
        return new_order

    def __unicode__(self):
        return ' '.join((
            _('Purchase from supplier') + ':', unicode(self.supplier) + ',', _('manager') + ':',
            unicode(self.manager) + ',', _('due') + ':', unicode(self.due)))

    class Meta:
        ordering = ["created"]


class Order(models.Model):
    purchase = models.ForeignKey(Purchase, verbose_name=_('purchase'))
    customer = models.ForeignKey(Person, verbose_name=_('customer'))
    created = models.DateTimeField(editable=False)
    updated = models.DateTimeField(editable=False)

    def get_absolute_url(self):
        return reverse_lazy('group_order:order', kwargs={'pk': self.id})

    def quantity(self):
        return self.item_set.aggregate(models.Sum('quantity'))['quantity__sum'] or 0

    def total(self):
        return self.item_set.aggregate(models.Sum('price'))['price__sum'] or 0

    def paid(self):
        return self.transfer_set.aggregate(models.Sum('amount'))['amount__sum'] or 0

    def remainder(self):
        return self.paid() - self.total()

    def __unicode__(self):
        return ' '.join((_('order').capitalize(), unicode(self.customer) + ',', _('date') + ':',
                         timezone.localtime(self.created).strftime("%y-%m-%d")))

    class Meta:
        ordering = ["created"]


class Transfer(models.Model):
    customer = models.ForeignKey(Person, verbose_name=_('customer'))
    order = models.ForeignKey(Order, verbose_name=_('order'))
    amount = models.FloatField(_('sum'))
    created = models.DateTimeField(editable=False)

    def __unicode__(self):
        return ' '.join((unicode(self.order), unicode(self.customer), unicode(self.amount)))

    class Meta:
        ordering = ["created"]


class Item(models.Model):
    order = models.ForeignKey(Order, verbose_name=_('order'))
    product = models.ForeignKey(Price, verbose_name=_('product'))
    quantity = models.IntegerField(_('quantity'))
    price = models.FloatField(_('sum'), blank=True, default=0.0)
    created = models.DateTimeField(editable=False)
    updated = models.DateTimeField(editable=False)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.price = self.quantity * self.product.price
        super(Item, self).save(force_insert, force_update, using, update_fields)

    def __unicode__(self):
        return ' '.join((
            unicode(self.order), unicode(self.product), unicode(self.quantity),
            unicode(self.price), timezone.localtime(self.created).strftime("%H:%M:%S")))

    class Meta:
        ordering = ["created"]


@receiver(pre_save, weak=False)
def date_pre_save(sender, **kwargs):
    if sender in (Price, Purchase, Order, Item):
        instance = kwargs["instance"]
        instance.updated = timezone.now()


@receiver(post_init, weak=False)
def date_post_init(sender, **kwargs):
    instance = kwargs["instance"]
    if sender in (Price, Purchase, Order, Item, Transfer) and not instance.created:
        instance.created = timezone.now()
