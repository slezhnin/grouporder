__author__ = 'sirius'

from django.contrib import admin
from django.db.models import Sum, Avg
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.admin import UserAdmin, User
from django.utils.translation import ugettext_lazy as _
from group_order.models import Person, Supplier, Purchase, Product, Price, Order, Item, Transfer, Category, Manufacturer

admin.site.register(Person)


# Price Admin UI
class PriceInline(admin.TabularInline):
    model = Price
    extra = 1

admin.site.register(Price)


# Supplier Admin UI
class SupplierAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name',)}),
        (_('Extra'), {'fields': ('phone', 'address', 'description'), 'classes': ('collapse',)})
    )
    inlines = (PriceInline,)

admin.site.register(Supplier, SupplierAdmin)


# Transfer Admin UI
class TransferInline(admin.TabularInline):
    model = Transfer
    extra = 1
admin.site.register(Transfer)


# Item sum
class ItemSumChangeList(ChangeList):
    #provide the list of fields that we need to calculate averages and totals
    fields_to_total = ('amount', 'price')

    def get_total_values(self, queryset):
        """
        Get the totals
        """
        #basically the total parameter is an empty instance of the given model
        total = Item()
        total.custom_alias_name = "Totals"  # the label for the totals row
        for field in self.fields_to_total:
            setattr(total, field, queryset.aggregate(Sum(field)).items()[0][1])
        return total

    def get_average_values(self, queryset):
        """
        Get the averages
        """
        average = Item()
        average.custom_alias_name = "Averages"  # the label for the averages row

        for field in self.fields_to_total:
            setattr(average, field, queryset.aggregate(Avg(field)).items()[0][1])
        return average

    def get_results(self, request):
        """
        The model admin gets queryset results from this method
        and then displays it in the template
        """
        super(ItemSumChangeList, self).get_results(request)
        #first get the totals from the current changelist
        total = self.get_total_values(self.query_set)
        #then get the averages
        #average = self.get_average_values(self.query_set)
        #small hack. in order to get the objects loaded we need to call for
        #queryset results once so simple len function does it
        len(self.result_list)
        #and finally we add our custom rows to the resulting changelist
        self.result_list._result_cache.append(total)
        #self.result_list._result_cache.append(average)


# Item Admin UI
class ItemInline(admin.TabularInline):
    readonly_fields = ('price',)
    fields = ('product', 'amount', 'price')
    model = Item
    extra = 1

    # def get_changelist(self, request, **kwargs):
    #     return ItemSumChangeList


class ItemAdmin(admin.ModelAdmin):
    list_filter = ('order',)
    list_display = ('order', 'product', 'amount', 'price')
    readonly_fields = ('price',)
    model = Item
    # extra = 1

    def get_changelist(self, request, **kwargs):
        return ItemSumChangeList

admin.site.register(Item, ItemAdmin)


# Order Admin UI
class OrderMixin:
    def order_sum(self, obj):
        return obj.order_sum
    order_sum.short_description = _('sum')
    order_sum.admin_order_field = 'order_sum'

    def transfer_sum(self, obj):
        return obj.transfer_sum
    transfer_sum.short_description = _('paid')
    transfer_sum.admin_order_field = 'transfer_sum'


class OrderInline(admin.TabularInline, OrderMixin):
    model = Order
    extra = 1

    def admin_link(self, instance):
        url = reverse('admin:%s_%s_change' % (
            instance._meta.app_label,  instance._meta.module_name),  args=[instance.pk])
        if instance.pk:
            return mark_safe(u'<a href="{u}">{e}</a>'.format(u=url, e=_('edit')))
        return ''
    admin_link.short_description = _('link')

    readonly_fields = ('admin_link', 'order_sum', 'transfer_sum')

    def queryset(self, request):
        qs = super(OrderInline, self).queryset(request)
        return qs.annotate(order_sum=Sum('item__price'), transfer_sum=Sum('transfer__amount'))


class OrderAdmin(admin.ModelAdmin, OrderMixin):
    list_display = ('purchase', 'customer', 'order_sum', 'transfer_sum')
    readonly_fields = ('order_sum', 'transfer_sum')
    list_filter = ('purchase',)
    inlines = (ItemInline, TransferInline)

    def queryset(self, request):
        qs = super(OrderAdmin, self).queryset(request)
        return qs.annotate(order_sum=Sum('item__price'), transfer_sum=Sum('transfer__amount'))

admin.site.register(Order, OrderAdmin)


# Purchase Admin UI
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'manager', 'closed', 'due', 'purchase_sum')
    readonly_fields = ('purchase_sum',)
    inlines = (OrderInline,)

    def queryset(self, request):
        qs = super(PurchaseAdmin, self).queryset(request)
        return qs.annotate(purchase_sum=Sum('order__item__price'))

    def purchase_sum(self, obj):
        return obj.purchase_sum
    purchase_sum.short_description = _('sum')
    purchase_sum.admin_order_field = 'purchase_sum'

admin.site.register(Purchase, PurchaseAdmin)


# Product Admin UI
class ProductAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('category', 'manufacturer', 'name')}),
        (_('Extra'), {'fields': ('description',), 'classes': ('collapse',)})
    )


class ProductInline(admin.StackedInline):
    fieldsets = (
        (None, {'fields': ('category', 'manufacturer', 'name')}),
        (_('Extra'), {'fields': ('description',), 'classes': ('collapse',)})
    )
    model = Product
    extra = 1

admin.site.register(Product, ProductAdmin)


# Category Admin UI
class CategoryAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('upper', 'name')}),
        (_('Extra'), {'fields': ('description',), 'classes': ('collapse',)})
    )
    inlines = (ProductInline,)

admin.site.register(Category, CategoryAdmin)


# Manufacturer Admin UI
class ManufacturerAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name',)}),
        (_('Extra'), {'fields': ('description',), 'classes': ('collapse',)})
    )
    inlines = (ProductInline,)

admin.site.register(Manufacturer, ManufacturerAdmin)


class PersonInline(admin.StackedInline):
    model = Person
    can_delete = False


# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (PersonInline, )


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
