from django.urls import path

from g2b import views

app_name = 'g2b'

urlpatterns = [
    path('', views.index, name='index'),
    path('lookup/', views.lookup_bid, name='lookup_bid'),
    path('calculator/', views.calculator, name='calculator'),
    path('recommend/', views.recommend, name='recommend'),
    path('benchmark/', views.benchmark, name='benchmark'),
]
