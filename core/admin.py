from django.contrib import admin
from .models import Profile, Asset, TokenConfiguration, Investment, AuditLog
admin.site.register(Profile)
@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin): list_display = ('name','symbol','issuer','status','total_value','created_at'); list_filter = ('status','asset_type')
admin.site.register(TokenConfiguration)
@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin): list_display = ('reference','investor','asset','amount','tokens','status','created_at')
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin): list_display = ('created_at','user','action','entity'); list_filter = ('action',)
