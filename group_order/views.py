# Create your views here.
from bootstrap_toolkit.widgets import BootstrapDateInput
from django.forms import ModelForm, ChoiceField
from django.forms.models import inlineformset_factory
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth import views
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from models import Purchase, Order, Item, Transfer, Person


def index(request):
    return index_filter(request, 'all')


def index_filter(request, filter):
    if not request.user.is_authenticated():
        return views.login(request, template_name='group_order/login.html',
                           extra_context={'title': _('Group Order'),
                                          REDIRECT_FIELD_NAME: reverse('group_order:index')})
    try:
        person = Person.objects.get(user=request.user)
    except Person.DoesNotExist:
        person = None
    my_order_list = Order.objects.all().filter(customer=person).order_by(
        '-created') if person else ()
    purchase_list = Purchase.objects.all()
    if filter == 'my' and person:
        purchase_list = purchase_list.filter(manager=person)
    purchase_list = purchase_list.order_by('-due')
    return render(request, 'group_order/index.html',
                  {'purchase_list': purchase_list, 'my_order_list': my_order_list,
                   'filter': filter})


def password_change(request):
    return views.password_change(request, template_name='group_order/password_change_form.html',
                                 post_change_redirect=reverse('group_order:password_change_done'))


def password_change_done(request):
    return views.password_change_done(request,
                                      template_name='group_order/password_change_done.html')


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
        exclude = ('closed', 'transferred',)


class PurchaseUpdateForm(ModelForm):
    class Meta:
        model = Purchase
        exclude = ('transferred',)

    transfer = ChoiceField(required=False, label=_('Transfer remainder to') + ':')


class PurchaseCreate(CreateView):
    template_name_suffix = '_add'
    form_class = PurchaseCreateForm
    model = Purchase

    @method_decorator(login_required(login_url=reverse_lazy('group_order:index')))
    def dispatch(self, request, *args, **kwargs):
        return super(PurchaseCreate, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class):
        form = super(PurchaseCreate, self).get_form(form_class)
        user = self.request.user
        form.fields['manager'].initial = user.person
        if not user.is_staff:
            form.fields['manager'].widget.attrs['disabled'] = True
        return form

    def form_valid(self, form):
        if not form.instance.manager:
            form.instance.manager = self.request.user.person
        return super(PurchaseCreate, self).form_valid(form)


class PurchaseUpdate(UpdateView, ModelContextMixin):
    template_name_suffix = ''
    form_class = PurchaseUpdateForm
    model = Purchase
    additional_action = ('close_purchase', 'open_purchase', 'add_order', 'transfer_remainder')

    @method_decorator(login_required(login_url=reverse_lazy('group_order:index')))
    def dispatch(self, request, *args, **kwargs):
        return super(PurchaseUpdate, self).dispatch(request, *args, **kwargs)

    def update_context(self, context, obj):
        context['is_manager'] = obj.is_manager(self.request.user.person)
        context['has_order'] = obj.has_order(self.request.user.person)
        context['can_transfer'] = self.can_transfer(obj)

    def can_transfer(self, obj):
        c_and_t = obj.closed and not obj.transferred
        return c_and_t and obj.transfer_count() and obj.valid_to_transfer().count()

    def get_form(self, form_class):
        form = super(PurchaseUpdate, self).get_form(form_class)
        user = self.request.user
        if not user.is_staff or self.object.closed:
            form.fields['manager'].widget.attrs['disabled'] = True
        form.fields['supplier'].widget.attrs['disabled'] = True
        form.fields['closed'].widget.attrs['readonly'] = True
        form.fields['due'].widget = BootstrapDateInput()
        if (not self.object.is_manager(user.person) and not user.is_staff) or self.object.closed:
            form.fields['due'].widget.attrs['readonly'] = True
        if self.can_transfer(self.object):
            choices = []
            for p in self.object.valid_to_transfer().order_by('-due'):
                choices.append((p.id, unicode(p)))
            form.fields['transfer'].choices = choices
        else:
            del form.fields['transfer']
        return form

    def post(self, request, *args, **kwargs):
        for action in self.additional_action:
            if action in request.POST:
                object = self.get_object()
                handler = getattr(self, action)
                if handler:
                    return redirect(handler(object, request))
        return super(PurchaseUpdate, self).post(request, *args, **kwargs)

    def close_purchase(self, object, request):
        object.closed = timezone.now()
        object.save()
        return reverse('group_order:purchase', kwargs={'pk': object.id})

    def open_purchase(self, object, request):
        object.closed = None
        object.save()
        return reverse('group_order:purchase', kwargs={'pk': object.id})

    def add_order(self, object, request):
        order = Order(purchase=object, customer=request.user.person)
        order.save()
        return reverse('group_order:order', kwargs={'pk': order.id})

    def transfer_remainder(self, object, request):
        object.transfer_remainder(request.POST['transfer'])
        messages.add_message(request, messages.SUCCESS,
                             _('Purchase remainder was transferred successfully.'))
        return reverse('group_order:purchase', kwargs={'pk': object.id})


class ItemForm(ModelForm):
    class Meta:
        model = Item
        fields = ('product', 'quantity', 'price')

    def __init__(self, *args, **kwargs):
        super(ItemForm, self).__init__(*args, **kwargs)
        self.fields['price'].widget.attrs['readonly'] = True


class OrderForm(ModelForm):
    class Meta:
        model = Order


class TransferForm(ModelForm):
    class Meta:
        model = Transfer
        fields = ('customer', 'amount')


class OrderView(UpdateView, ModelContextMixin):
    template_name_suffix = ''
    form_class = OrderForm
    model = Order
    ItemFormSet = inlineformset_factory(Order, Item, form=ItemForm, extra=1)
    TransferFormSet = inlineformset_factory(Order, Transfer, form=TransferForm, extra=1)
    form_action = {'item_set': 'item_action', 'transfer_set': 'transfer_action'}

    def update_context(self, context, obj):
        context['item_formset'] = self.ItemFormSet(instance=obj)
        context['can_save_item'] = not obj.purchase.closed and not obj.purchase.past_due and (
            obj.customer == self.request.user.person or self.request.user.is_staff)
        context['transfer_formset'] = self.TransferFormSet(instance=obj)
        context[
            'can_save_transfer'] = obj.purchase.manager == self.request.user.person or self.request.user.is_staff

    def post(self, request, *args, **kwargs):
        for token in self.form_action:
            if any(map(lambda f: token in f, self.request.POST)):
                handler = getattr(self, self.form_action[token])
                if handler:
                    return redirect(handler(self.get_object(), request))
        return super(OrderView, self).post(request, *args, **kwargs)

    def item_action(self, object, request):
        item_formset = self.ItemFormSet(request.POST, instance=self.get_object())
        if item_formset.is_valid():
            item_formset.save()
        return reverse('group_order:order', kwargs={'pk': object.id})

    def transfer_action(self, object, request):
        transfer_formset = self.TransferFormSet(request.POST, instance=self.get_object())
        if transfer_formset.is_valid():
            transfer_formset.save()
        return reverse('group_order:order', kwargs={'pk': object.id})
