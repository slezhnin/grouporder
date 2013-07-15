__author__ = 'sirius'

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, User
from group_order.models import Person, Supplier, Purchase, Product, Price, Order, Item, Transfer, Category, Manufacturer

admin.site.register(Person)
admin.site.register(Supplier)
admin.site.register(Purchase)
admin.site.register(Category)
admin.site.register(Manufacturer)
admin.site.register(Product)
admin.site.register(Price)
admin.site.register(Order)
admin.site.register(Transfer)
admin.site.register(Item)


class PersonInline(admin.StackedInline):
    model = Person
    can_delete = False


# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (PersonInline, )


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
