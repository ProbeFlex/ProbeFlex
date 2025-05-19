from django.contrib import admin
from .models import Team, Project, Collection, Environment, APIRequest, RequestHistory

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    filter_horizontal = ('members',)
    search_fields = ('name', 'description')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    list_filter = ('owner',)
    search_fields = ('name', 'description')
    filter_horizontal = ('teams',)

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'created_at')
    list_filter = ('project',)
    search_fields = ('name', 'description')

@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'created_at')
    list_filter = ('project',)
    search_fields = ('name', 'description')

@admin.register(APIRequest)
class APIRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'method', 'url', 'collection', 'created_at')
    list_filter = ('method', 'collection')
    search_fields = ('name', 'url', 'description')

@admin.register(RequestHistory)
class RequestHistoryAdmin(admin.ModelAdmin):
    list_display = ('request', 'method', 'url', 'response_status', 'executed_at', 'executed_by')
    list_filter = ('method', 'response_status', 'executed_by')
    search_fields = ('url',)
    date_hierarchy = 'executed_at'
    readonly_fields = ('executed_at',)
