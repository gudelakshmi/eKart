from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='eshop_home'),
    path('about/', views.about, name='about_us'),
    path('contact/', views.contact, name='contact_us'),
    path('tracker/', views.tracker, name='tracking_status'),
    path('search/', views.search, name='search'),
    path('products/<int:myid>', views.productView, name='product_view'),
    path('checkout/', views.checkout, name='checkout'),
    path('handlerequest/', views.handlerequest, name='HandleRequest '),
]