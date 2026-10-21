from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views
urlpatterns = [
    path('admin/', admin.site.urls), path('', views.home, name='home'),
    path('login/', views.login_view, name='login'), path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'), path('assets/', views.assets, name='assets'),
    path('assets/create/', views.create_asset, name='create_asset'), path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:pk>/review/<str:decision>/', views.review_asset, name='review_asset'),
    path('assets/<int:pk>/token/', views.configure_token, name='configure_token'),
    path('assets/<int:pk>/deploy/', views.deploy_contract, name='deploy_contract'),
    path('assets/<int:pk>/mint/', views.mint_tokens, name='mint_tokens'),
    path('marketplace/', views.marketplace, name='marketplace'), path('invest/<int:pk>/', views.invest, name='invest'),
    path('portfolio/', views.portfolio, name='portfolio'), path('audit/', views.audit, name='audit'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
