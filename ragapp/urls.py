"""
URL configuration for RAG app
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_document, name='upload_document'),
    path('query/', views.query, name='query'),
    path('status/', views.status, name='status'),
    path('clear/', views.clear_database, name='clear_database'),
]
