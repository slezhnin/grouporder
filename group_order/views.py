# Create your views here.
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.views import generic
from django.contrib import admin, auth
from django.contrib.auth import views
from django.contrib.auth import REDIRECT_FIELD_NAME
from models import Purchase, Order, Item, Transfer
from django.utils.translation import ugettext_lazy as _


def index(request):
    if not request.user.is_authenticated():
        return views.login(request, template_name='group_order/login.html', extra_context={REDIRECT_FIELD_NAME: reverse('group_order:index')})
    return render(request, 'group_order/index.html',
                  {'purchase_list': Purchase.objects.all().order_by('-due')})


def logout(request):
    return views.logout(request, next_page=reverse('group_order:index'))


class DetailViewWithContext(generic.DetailView):
    def get_context_data(self, **kwargs):
        context = super(DetailViewWithContext, self).get_context_data(**kwargs)
        obj = context[self.model.__name__.lower()]
        context['title'] = unicode(obj)
        self.update_context(context, obj)
        return context

    def update_context(self, context, obj):
        pass


class PurchaseView(DetailViewWithContext):
    model = Purchase


class OrderView(DetailViewWithContext):
    model = Order


class ItemView(DetailViewWithContext):
    model = Item


class TransferView(DetailViewWithContext):
    model = Transfer
