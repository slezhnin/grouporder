__author__ = 'sirius'

from django.conf.urls import patterns, url
from group_order import views

urlpatterns = patterns('', url(r'^$', views.index, name='index'),
                       url(r'^logout/$', views.logout, name='logout'),
                       url(r'^password_change/$', views.password_change, name='password_change'),
                       url(r'^password_change/done/$', views.password_change_done,
                           name='password_change_done'),
                       url(r'^add/$', views.PurchaseCreate.as_view(), name='purchase_add'),
                       url(r'^(?P<pk>\d+)/$', views.PurchaseUpdate.as_view(), name='purchase'),
                       url(r'^order/(?P<pk>\d+)/$', views.OrderView.as_view(), name='order'), )
