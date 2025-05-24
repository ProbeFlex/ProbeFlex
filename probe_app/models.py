from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
import uuid

class Team(models.Model):
    """
    Team model for collaborative API testing.
    
    Teams allow multiple users to work together on API testing projects.
    Users can be members of multiple teams, and teams can have access to multiple projects.
    This enables organizations to control who can access and modify specific API test collections.
    """
    name = models.CharField(max_length=100, help_text="The display name of the team")
    description = models.TextField(blank=True, null=True, help_text="Optional description explaining the team's purpose")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the team was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the team was last modified")
    # Many-to-many relationship: users can belong to multiple teams
    members = models.ManyToManyField(User, related_name='teams', help_text="Users who are members of this team")

    def __str__(self):
        return self.name

class Project(models.Model):
    """
    Project model for organizing API testing workflows.
    
    Projects are the top-level organizational unit in ProbeFlex. They contain collections
    of related API endpoints and can be shared with teams for collaborative testing.
    Each project has an owner who controls access and can assign teams to the project.
    """
    name = models.CharField(max_length=100, help_text="The display name of the project")
    description = models.TextField(blank=True, null=True, help_text="Optional description of the project's purpose")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the project was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the project was last modified")
    # Foreign key: each project has exactly one owner
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects', 
                             help_text="The user who owns and controls this project")
    # Many-to-many relationship: projects can be shared with multiple teams
    teams = models.ManyToManyField(Team, related_name='projects', blank=True,
                                  help_text="Teams that have access to this project")
    
    def __str__(self):
        return self.name

class Collection(models.Model):
    """
    Collection model for grouping related API endpoints within a project.
    
    Collections help organize API requests logically within a project. For example,
    you might have separate collections for "User Management APIs", "Payment APIs",
    and "Authentication APIs" within an e-commerce project. This organizational
    structure makes it easier to find and manage related API tests.
    """
    name = models.CharField(max_length=100, help_text="The display name of the collection")
    description = models.TextField(blank=True, null=True, help_text="Optional description of what APIs this collection contains")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the collection was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the collection was last modified")
    # Foreign key: each collection belongs to exactly one project
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='collections',
                               help_text="The project that contains this collection")
    
    def __str__(self):
        return self.name

class Environment(models.Model):
    """
    Environment model for storing configuration variables for API requests.
    
    Environments allow users to define different sets of variables for different
    deployment stages (development, staging, production). Variables can include
    base URLs, API keys, authentication tokens, and other configuration values
    that change between environments. This enables easy switching between
    different API environments without manually updating each request.
    """
    name = models.CharField(max_length=100, help_text="The display name of the environment (e.g., 'Development', 'Production')")
    description = models.TextField(blank=True, null=True, help_text="Optional description of this environment")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the environment was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the environment was last modified")
    # Foreign key: each environment belongs to exactly one project
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='environments',
                               help_text="The project that contains this environment")
    # JSON field to store key-value pairs of environment variables
    variables = models.JSONField(default=dict, help_text="Key-value pairs of environment variables (e.g., {'base_url': 'https://api.example.com', 'api_key': 'xyz123'})")
    
    def __str__(self):
        return self.name

class APIRequest(models.Model):
    """
    APIRequest model for storing complete API endpoint configurations.
    
    This is the core model that represents an API test case. It stores all the
    information needed to make an HTTP request including URL, method, headers,
    parameters, request body, authentication details, and various request options.
    Each API request can be executed multiple times, with each execution creating
    a RequestHistory record for tracking and debugging purposes.
    """
    # Choices for HTTP methods supported by the API testing tool
    HTTP_METHODS = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
        ('HEAD', 'HEAD'),
        ('OPTIONS', 'OPTIONS'),
    )
    
    name = models.CharField(max_length=100, help_text="A descriptive name for this API request")
    description = models.TextField(blank=True, null=True, help_text="Optional description explaining what this API does")
    url = models.TextField(help_text="The complete URL or URL template for the API endpoint")
    method = models.CharField(max_length=10, choices=HTTP_METHODS, default='GET',
                             help_text="The HTTP method to use for this request")
    # JSON fields to store structured data for the request configuration
    headers = models.JSONField(default=dict, help_text="HTTP headers to send with the request (e.g., {'Content-Type': 'application/json'})")
    params = models.JSONField(default=dict, help_text="Query parameters to append to the URL (e.g., {'page': 1, 'limit': 10})")
    body = models.JSONField(default=dict, blank=True, null=True, 
                           help_text="Request body data for POST/PUT/PATCH requests (JSON format)")
    auth = models.JSONField(default=dict, blank=True, null=True,
                           help_text="Authentication configuration (e.g., {'type': 'bearer', 'token': 'xyz123'})")
    # Request configuration options
    timeout = models.IntegerField(default=30000, help_text="Request timeout in milliseconds")
    follow_redirects = models.BooleanField(default=True, help_text="Whether to automatically follow HTTP redirects")
    verify_ssl = models.BooleanField(default=True, help_text="Whether to verify SSL certificates for HTTPS requests")
    # Timestamp fields for tracking when the request was created and modified
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when this API request was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when this API request was last modified")
    # Foreign key: each API request belongs to exactly one collection
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='requests',
                                  help_text="The collection that contains this API request")
    
    def __str__(self):
        return f"{self.method} {self.name}"

class RequestHistory(models.Model):
    """
    RequestHistory model for tracking API request executions and their results.
    
    Every time an API request is executed through ProbeFlex, a RequestHistory record
    is created to store both the request details and the response received. This
    provides a complete audit trail of API testing activities and allows users to
    track how API responses change over time, debug issues, and monitor API performance.
    """
    # Foreign key: each history record is associated with exactly one API request
    request = models.ForeignKey(APIRequest, on_delete=models.CASCADE, related_name='history',
                               help_text="The API request configuration that was executed")
    
    # Request details (captured at execution time, may differ from the current API request config)
    url = models.TextField(help_text="The actual URL that was called (after variable substitution)")
    method = models.CharField(max_length=10, help_text="The HTTP method that was used")
    headers = models.JSONField(default=dict, help_text="The actual headers that were sent")
    params = models.JSONField(default=dict, help_text="The actual query parameters that were sent")
    body = models.JSONField(default=dict, blank=True, null=True, help_text="The actual request body that was sent")
    auth = models.JSONField(default=dict, blank=True, null=True, help_text="The authentication configuration that was used")
    
    # Response details (what we received back from the API)
    response_status = models.IntegerField(null=True, blank=True, help_text="HTTP status code received (e.g., 200, 404, 500)")
    response_headers = models.JSONField(default=dict, blank=True, null=True, help_text="HTTP headers received in the response")
    response_body = models.JSONField(default=dict, blank=True, null=True, help_text="Response body content (JSON or text)")
    response_time = models.FloatField(default=0, help_text="Time taken for the request to complete (in milliseconds)")
    
    # Execution metadata
    executed_at = models.DateTimeField(default=timezone.now, help_text="Timestamp when this request was executed")
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='request_history',
                                   help_text="The user who executed this request")
    
    class Meta:
        ordering = ['-executed_at']  # Show most recent executions first
        verbose_name_plural = "Request histories"
    
    def __str__(self):
        return f"{self.method} {self.url} - {self.response_status}"
