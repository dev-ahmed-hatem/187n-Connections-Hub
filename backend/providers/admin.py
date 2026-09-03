from django.contrib import admin

from .models import Provider


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_mock', 'is_active')
    list_filter = ('is_mock', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
