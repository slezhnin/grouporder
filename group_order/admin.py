__author__ = 'sirius'

from django.contrib import admin
from group_order.models import Supplier, Purchase, Product, Price, Order, Item, Transfer, Category, Manufacturer

admin.site.register(Supplier)
admin.site.register(Purchase)
admin.site.register(Category)
admin.site.register(Manufacturer)
admin.site.register(Product)
admin.site.register(Price)
admin.site.register(Order)
admin.site.register(Transfer)
admin.site.register(Item)
