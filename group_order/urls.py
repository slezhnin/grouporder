__author__ = 'sirius'

from django.conf.urls import patterns, url
from group_order import views

urlpatterns = patterns('', url(r'^$', views.index, name='index'),
                       url(r'^logout/$', views.logout, name='logout'),
                       url(r'^add/$', views.PurchaseCreate.as_view(), name='purchase_add'),
                       url(r'^(?P<pk>\d+)/$', views.PurchaseUpdate.as_view(), name='purchase'),
                       url(r'^(?P<pk>\d+)/delete/$', views.PurchaseDelete.as_view(), name='purchase_delete'),
                       url(r'^order/(?P<pk>\d+)/$', views.OrderView.as_view(), name='order'),
                       url(r'^item/(?P<pk>\d+)/$', views.ItemView.as_view(), name='item'),
                       url(r'^transfer/(?P<pk>\d+)/$', views.TransferView.as_view(),
                           name='transfer'), )
