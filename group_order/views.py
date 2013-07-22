# Create your views here.
from django.forms import ModelForm
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth import views
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from models import Purchase, Order, Item, Transfer


def index(request):
    if not request.user.is_authenticated():
        return views.login(request, template_name='group_order/login.html',
                           extra_context={REDIRECT_FIELD_NAME: reverse('group_order:index')})
    return render(request, 'group_order/index.html', {'purchase_list': Purchase.objects.all().order_by('-due')})


def logout(request):
    return views.logout(request, next_page=reverse('group_order:index'))


class ModelContextMixin(SingleObjectMixin):
    def get_context_data(self, **kwargs):
        context = super(ModelContextMixin, self).get_context_data(**kwargs)
        context['title'] = unicode(self.object)
        self.update_context(context, self.object)
        return context

    def update_context(self, context, obj):
        pass


class PurchaseCreateForm(ModelForm):
    class Meta:
        model = Purchase
        exclude = ('closed',)


class PurchaseUpdateForm(ModelForm):
    class Meta:
        model = Purchase


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
    additional_action = ('close_purchase', 'open_purchase')

    def get_form(self, form_class):
        form = super(PurchaseUpdate, self).get_form(form_class)
        if not self.request.user.is_staff or self.object.closed:
            form.fields['manager'].widget.attrs['disabled'] = True
        form.fields['closed'].widget.attrs['readonly'] = True
        if (self.request.user.person != self.object.manager and not self.request.user.is_staff) or self.object.closed:
            form.fields['due'].widget.attrs['readonly'] = True
            form.fields['supplier'].widget.attrs['disabled'] = True
        return form

    def post(self, request, *args, **kwargs):
        for action in self.additional_action:
            if action in request.POST:
                object = self.get_object()
                handler = getattr(self, action)
                if handler and handler(object):
                    object.save()
                    return redirect(reverse('group_order:purchase', kwargs={'pk': object.id}))
        return super(PurchaseUpdate, self).post(request, *args, **kwargs)

    def close_purchase(self, object):
        object.closed = timezone.now()
        return True

    def open_purchase(self, object):
        object.closed = None
        return True


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
