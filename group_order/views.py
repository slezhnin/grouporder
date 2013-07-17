# Create your views here.
from django.views import generic
from models import Purchase, Order, Item, Transfer


class PurchaseListView(generic.ListView):
    def get_queryset(self):
        return Purchase.objects.all().order_by('-due')


class PurchaseView(generic.DetailView):
    model = Purchase


class OrderView(generic.DetailView):
    model = Order


class ItemView(generic.DetailView):
    model = Item


class TransferView(generic.DetailView):
    model = Transfer
