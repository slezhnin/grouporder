__author__ = 'sirius'

from django.conf.urls import patterns, url
from group_order import views

urlpatterns = patterns('', url(r'^$', views.index, name='index'),
                       url(r'^logout/$', views.logout, name='logout'),
                       url(r'^(?P<pk>\d+)/$', views.PurchaseView.as_view(), name='purchase'),
                       url(r'^order/(?P<pk>\d+)/$', views.OrderView.as_view(), name='order'),
                       url(r'^item/(?P<pk>\d+)/$', views.ItemView.as_view(), name='item'),
                       url(r'^transfer/(?P<pk>\d+)/$', views.TransferView.as_view(),
                           name='transfer'), )
