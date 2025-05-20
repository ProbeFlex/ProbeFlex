from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
import uuid

class Team(models.Model):
    """Team model for grouping users with access to projects"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    members = models.ManyToManyField(User, related_name='teams')

    def __str__(self):
        return self.name

class Project(models.Model):
    """Project model for organizing collections of API endpoints"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    teams = models.ManyToManyField(Team, related_name='projects', blank=True)
    
    def __str__(self):
        return self.name

class Collection(models.Model):
    """Collection model for grouping related API endpoints within a project"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='collections')
    
    def __str__(self):
        return self.name

class Environment(models.Model):
    """Environment model for storing variables for API requests"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='environments')
    variables = models.JSONField(default=dict)
    
    def __str__(self):
        return self.name

class APIRequest(models.Model):
    """API Request model for storing API endpoints and request data"""
    HTTP_METHODS = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
        ('HEAD', 'HEAD'),
        ('OPTIONS', 'OPTIONS'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    url = models.TextField()
    method = models.CharField(max_length=10, choices=HTTP_METHODS, default='GET')
    headers = models.JSONField(default=dict)
    params = models.JSONField(default=dict)
    body = models.JSONField(default=dict, blank=True, null=True)
    auth = models.JSONField(default=dict, blank=True, null=True)
    timeout = models.IntegerField(default=30000)  # Timeout in milliseconds
    follow_redirects = models.BooleanField(default=True)
    verify_ssl = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='requests')
    
    def __str__(self):
        return f"{self.method} {self.name}"

class RequestHistory(models.Model):
    """Request History model for storing request and response data"""
    request = models.ForeignKey(APIRequest, on_delete=models.CASCADE, related_name='history')
    url = models.TextField()
    method = models.CharField(max_length=10)
    headers = models.JSONField(default=dict)
    params = models.JSONField(default=dict)
    body = models.JSONField(default=dict, blank=True, null=True)
    auth = models.JSONField(default=dict, blank=True, null=True)
    response_status = models.IntegerField(null=True, blank=True)
    response_headers = models.JSONField(default=dict, blank=True, null=True)
    response_body = models.JSONField(default=dict, blank=True, null=True)
    response_time = models.FloatField(default=0)  # Response time in milliseconds
    executed_at = models.DateTimeField(default=timezone.now)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='request_history')
    
    class Meta:
        ordering = ['-executed_at']
        verbose_name_plural = "Request histories"
    
    def __str__(self):
        return f"{self.method} {self.url} - {self.response_status}"
