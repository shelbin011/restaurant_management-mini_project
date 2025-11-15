from django.contrib import admin
from waiter_app.models import Waiter

# Register your models here.

@admin.register(Waiter)
class WaiterAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'user', 'id')
    list_filter = ('display_name',)
    search_fields = ('display_name', 'user__username', 'user__email')
    ordering = ('display_name',)
