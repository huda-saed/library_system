from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('libraries/', views.library_list, name='library_list'),
    path('libraries/add/', views.library_create, name='library_create'),
    path('libraries/<int:pk>/edit/', views.library_update, name='library_update'),
    path('libraries/<int:pk>/delete/', views.library_delete, name='library_delete'),
]
