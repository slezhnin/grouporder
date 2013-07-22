# Create your views here.
from django.forms import ModelForm
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib.auth import views
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from models import Purchase, Order, Item, Transfer


def index(request):
    if not request.user.is_authenticated():
        return views.login(request, template_name='group_order/login.html',
                           extra_context={REDIRECT_FIELD_NAME: reverse('group_order:index')})
    return render(request, 'group_order/index.html',
                  {'purchase_list': Purchase.objects.all().order_by('-due')})


def logout(request):
    return views.logout(request, next_page=reverse('group_order:index'))


class ModelContextMixin(SingleObjectMixin):
    def get_context_data(self, **kwargs):
        context = super(ModelContextMixin, self).get_context_data(**kwargs)
        obj = context[self.model.__name__.lower()]
        context['title'] = unicode(obj)
        self.update_context(context, obj)
        return context

    def update_context(self, context, obj):
        pass


class PurchaseCreateForm(ModelForm):
    class Meta:
        model = Purchase
        exclude = ('closed',)


class PurchaseUpdateForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PurchaseUpdateForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['closed'].widget.attrs['readonly'] = True
            if instance.closed:
                self.fields['due'].widget.attrs['readonly'] = True
                self.fields['supplier'].widget.attrs['disabled'] = True

    def clean_sku(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.closed
        else:
            return self.cleaned_data['closed']

    class Meta:
        model = Purchase
        exclude = ('manager',)


class PurchaseView(DetailView, ModelContextMixin):
    model = Purchase


class PurchaseCreate(CreateView):
    template_name_suffix = '_add'
    form_class = PurchaseCreateForm
    model = Purchase

    def form_valid(self, form):
        if not form.instance.manager:
            form.instance.manager = self.request.user.person
        return super(PurchaseCreate, self).form_valid(form)


class PurchaseUpdate(UpdateView, ModelContextMixin):
    template_name_suffix = ''
    form_class = PurchaseUpdateForm
    model = Purchase


class PurchaseDelete(DeleteView, ModelContextMixin):
    template_name_suffix = '_delete'
    form_class = PurchaseUpdateForm
    model = Purchase


class OrderView(DetailView, ModelContextMixin):
    model = Order


class ItemView(DetailView, ModelContextMixin):
    model = Item


class TransferView(DetailView, ModelContextMixin):
    model = Transfer
