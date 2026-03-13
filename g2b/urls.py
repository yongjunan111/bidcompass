from django.urls import path

from g2b import ui_api, views

app_name = 'g2b'

urlpatterns = [
    path('', ui_api.frontend_app, name='index'),
    path('dashboard/', ui_api.frontend_app, name='dashboard'),
    path('notices/search/', ui_api.frontend_app, name='notice_search'),
    path('notices/recommendation/', ui_api.frontend_app, name='recommendation_result'),
    path('calculator/', ui_api.frontend_app, name='calculator'),
    path('report/latest/', ui_api.frontend_app, name='report_latest'),
    path('history/', ui_api.frontend_app, name='history'),
    path('settings/', ui_api.frontend_app, name='settings'),
    path('workspace/', ui_api.frontend_app, name='workspace'),
    path('api/ui/dashboard/', ui_api.api_dashboard, name='api_dashboard'),
    path('api/ui/notices/search/', ui_api.api_notice_search, name='api_notice_search'),
    path('api/ui/notices/recommendation/', ui_api.api_recommendation_result, name='api_recommendation_result'),
    path('api/ui/calculator/', ui_api.api_price_calculator, name='api_price_calculator'),
    path('api/ui/report/latest/', ui_api.api_ai_report, name='api_ai_report'),
    path('api/ui/history/', ui_api.api_history, name='api_history'),
    path('api/ui/settings/', ui_api.api_settings, name='api_settings'),
    path('lookup/', views.lookup_bid, name='lookup_bid'),
    path('legacy/calculator/', views.calculator, name='legacy_calculator'),
    path('legacy/recommend/', views.recommend, name='legacy_recommend'),
    path('legacy/ai-report/', views.ai_report, name='legacy_ai_report'),
    path('legacy/benchmark/', views.benchmark, name='legacy_benchmark'),
]
