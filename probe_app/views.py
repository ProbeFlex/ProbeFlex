from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import Q

from .forms import (
    CustomAuthenticationForm, CustomUserCreationForm, 
    ProjectForm, CollectionForm, TeamForm, APIRequestForm
)
from .models import Project, Collection, Team, APIRequest, RequestHistory

import requests
import json
import time
from datetime import datetime


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

class CustomLoginView(LoginView):
    """
    Custom login view with enhanced functionality for API testing tool users.
    
    Extends Django's built-in LoginView to add 'remember me' functionality,
    which controls session expiry. When 'remember me' is unchecked, the session
    expires when the user closes their browser for enhanced security.
    """
    form_class = CustomAuthenticationForm
    template_name = 'registration/login.html'
    
    def form_valid(self, form):
        """
        Process successful login and handle 'remember me' functionality.
        
        If 'remember me' is not checked, the session will expire when the browser
        is closed. Otherwise, it uses Django's default session expiry settings.
        """
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            # Session expires when the user closes the browser
            self.request.session.set_expiry(0)
        return super().form_valid(form)


class SignUpView(CreateView):
    """
    User registration view for new API testing tool users.
    
    Allows new users to create accounts to access ProbeFlex's API testing features.
    Upon successful registration, users are redirected to the login page.
    """
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')


# ============================================================================
# MAIN APPLICATION VIEWS
# ============================================================================

@login_required
def home(request):
    """
    Main dashboard view for the API testing interface.
    
    Displays the primary workspace where users can test API endpoints.
    Shows projects that the user either owns or has access to through team membership.
    This serves as the main entry point for API testing activities.
    
    Returns:
        Rendered home.html template with accessible projects context
    """
    # Get projects that the user owns or has access to via team membership
    projects = (Project.objects.filter(owner=request.user) | 
                Project.objects.filter(teams__members=request.user)).distinct()
    
    context = {
        'projects': projects,
    }
    return render(request, 'home.html', context)


@login_required
@require_POST
@csrf_exempt  # For test purposes only, remove in production
def send_request(request):
    """
    Core API request execution endpoint.
    
    This is the heart of ProbeFlex - it handles the execution of API requests
    submitted from the frontend interface. It supports all major HTTP methods,
    various authentication types (Basic, Bearer, API Key), custom headers,
    query parameters, and request bodies.
    
    Features:
    - Supports GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS methods
    - Multiple authentication methods (Basic Auth, Bearer Token, API Key)
    - Custom headers and query parameters
    - JSON request bodies for POST/PUT/PATCH requests
    - SSL verification control and redirect following
    - Request timeout handling
    - Response time measurement
    - Automatic request history tracking
    
    Returns:
        JsonResponse containing:
        - status_code: HTTP status code from the API
        - headers: Response headers as dictionary
        - body: Response body (JSON or text)
        - time: Response time in milliseconds
    """
    try:
        # Debug logging for request analysis
        print(f"Request received: {request.body[:1000] if hasattr(request, 'body') else 'No body'}")
        
        # Handle both JSON and form data input formats
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            print(f"Parsed JSON data: {json.dumps(data)[:1000]}")
        else:
            # Handle form data from older interfaces
            data = {
                'url': request.POST.get('url', ''),
                'method': request.POST.get('method', 'GET').upper(),
                'headers': {},  # Form will handle this differently
                'params': {},
                'body': {},
                'auth': {},
            }
            
        # Extract request configuration from parsed data
        url = data.get('url', '')
        method = data.get('method', 'GET').upper()
        headers = data.get('headers', {})
        params = data.get('params', {})
        request_body = data.get('body', {})
        auth_data = data.get('auth', {})
        follow_redirects = data.get('follow_redirects', True)
        verify_ssl = data.get('verify_ssl', True)
        
        # Validate required fields
        if not url:
            return JsonResponse({'error': 'URL is required'}, status=400)
        
        # Debug logging for request processing
        print(f"Processing request: {method} {url}")
        print(f"Verify SSL: {verify_ssl}")
        print(f"Auth data structure: {type(auth_data)}")
        print(f"Auth data: {json.dumps(auth_data)}")
        print(f"Headers before auth: {json.dumps(headers)}")
        
        # Check if authentication is already applied to headers (by client-side JS)
        auth_already_applied = False
        if 'Authorization' in headers:
            print(f"Authorization header already exists: {headers['Authorization'][:15]}...")
            auth_already_applied = True
        
        # Handle different authentication methods
        auth = None
        
        # Basic Authentication: uses HTTP Basic Auth with username/password
        if auth_data and auth_data.get('type') == 'basic':
            username = auth_data.get('username', '')
            password = auth_data.get('password', '')
            if username:
                auth = (username, password)
                print(f"Using Basic Auth: username={username}, password={'*'*len(password) if password else 'None'}")
                
        # Bearer Token Authentication: adds Authorization header with Bearer token
        elif auth_data and auth_data.get('type') == 'bearer' and not auth_already_applied:
            token = auth_data.get('token', '')
            if token:
                headers['Authorization'] = f"Bearer {token}"
                print(f"Using Bearer Token Auth: {token[:5]}***")
                
        # API Key Authentication: can be in header or query parameter
        elif auth_data and auth_data.get('type') == 'apikey' and not auth_already_applied:
            key_name = auth_data.get('key', '')
            key_value = auth_data.get('value', '')
            location = auth_data.get('location', 'header')
            
            if key_name and key_value:
                if location == 'header':
                    headers[key_name] = key_value
                    print(f"Using API Key Auth in header: {key_name}={key_value[:5]}***")
                elif location == 'query':
                    params[key_name] = key_value
                    print(f"Using API Key Auth in query param: {key_name}={key_value[:5]}***")
        
        print(f"Headers after auth: {json.dumps(headers)}")
        print(f"Auth tuple: {auth}")
        
        # Set default headers if not already present
        if method in ['POST', 'PUT', 'PATCH'] and 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        
        # Add User-Agent for API identification
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'ProbeFlex/1.0 (API Testing Tool)'
        
        # Add Accept header for response format preference
        if 'Accept' not in headers:
            headers['Accept'] = 'application/json, text/plain, */*'
        
        print(f"Headers after defaults: {json.dumps(headers)}")
        
        # Record start time for response time measurement
        start_time = time.time()
        
        # Prepare request configuration
        request_kwargs = {
            'headers': headers,
            'params': params,
            'verify': verify_ssl,
            'allow_redirects': follow_redirects,
            'timeout': 30  # Add a reasonable timeout to prevent hanging
        }
        
        # Add Basic Auth if configured (for requests library)
        if auth:
            request_kwargs['auth'] = auth
            print(f"Added Basic Auth to request_kwargs")
        
        # Debug logging (hide sensitive auth information)
        debug_kwargs = request_kwargs.copy()
        if 'auth' in debug_kwargs:
            debug_kwargs['auth'] = '(AUTH CREDENTIALS HIDDEN)'
        if 'headers' in debug_kwargs and 'Authorization' in debug_kwargs['headers']:
            headers_copy = debug_kwargs['headers'].copy()
            headers_copy['Authorization'] = headers_copy['Authorization'][:10] + '...'
            debug_kwargs['headers'] = headers_copy
        
        print(f"Final request kwargs: {json.dumps(debug_kwargs)}")
        
        # Handle request body for methods that support it
        if method in ['POST', 'PUT', 'PATCH']:
            # Send empty JSON object if no body provided
            if not request_body or request_body == {}:
                request_kwargs['json'] = {}
            else:
                request_kwargs['json'] = request_body
            print(f"JSON body being sent: {request_kwargs.get('json', {})}")
            
        # Handle GET requests with body content (convert to query params)
        elif method == 'GET' and request_body:
            print(f"Warning: Body content sent with GET request: {request_body}")
            # Convert body content to query parameters for GET requests
            if isinstance(request_body, dict):
                for key, value in request_body.items():
                    request_kwargs['params'][key] = value
        
        # Execute the HTTP request based on method
        if method == 'GET':
            response = requests.get(url, **request_kwargs)
        elif method == 'POST':
            # Detailed logging for POST requests
            print(f"=== MAKING POST REQUEST ===")
            print(f"URL: {url}")
            print(f"Headers: {request_kwargs.get('headers', {})}")
            print(f"JSON Body: {request_kwargs.get('json', {})}")
            print(f"Auth: {request_kwargs.get('auth', 'None')}")
            print(f"Verify SSL: {request_kwargs.get('verify', True)}")
            print(f"========================")
            response = requests.post(url, **request_kwargs)
        elif method == 'PUT':
            response = requests.put(url, **request_kwargs)
        elif method == 'PATCH':
            response = requests.patch(url, **request_kwargs)
        elif method == 'DELETE':
            response = requests.delete(url, **request_kwargs)
        elif method == 'HEAD':
            response = requests.head(url, **request_kwargs)
        elif method == 'OPTIONS':
            response = requests.options(url, **request_kwargs)
        else:
            return JsonResponse({'error': 'Invalid HTTP method'}, status=400)
        
        # Log response details
        print(f"=== RESPONSE RECEIVED ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body (first 500 chars): {response.text[:500]}")
        print(f"========================")
        
        # Calculate response time
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Parse response body (attempt JSON first, fallback to text)
        try:
            response_body = response.json()
        except ValueError:
            response_body = response.text
        
        # Prepare response data for frontend
        response_data = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'body': response_body,
            'time': response_time
        }
        
        # Save request execution to history for tracking and debugging
        api_request_id = data.get('api_request_id')
        if api_request_id:
            try:
                api_request = get_object_or_404(APIRequest, id=api_request_id)
                
                # Create detailed history record
                history = RequestHistory.objects.create(
                    request=api_request,
                    url=url,
                    method=method,
                    headers=headers,
                    params=params,
                    body=request_body,
                    auth=auth_data,
                    response_status=response.status_code,
                    response_headers=dict(response.headers),
                    response_body=response_body,
                    response_time=response_time,
                    executed_by=request.user
                )
            except Exception as history_error:
                print(f"Error saving request history: {str(history_error)}")
                # Don't fail the main request if history saving fails
        
        print(f"Request completed: {method} {url} - {response.status_code}")
        return JsonResponse(response_data)
    
    except requests.RequestException as e:
        print(f"Request error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# PROJECT MANAGEMENT VIEWS
# ============================================================================

class ProjectListView(LoginRequiredMixin, ListView):
    """
    Display a list of API testing projects accessible to the current user.
    
    Shows projects that the user either owns directly or has access to through
    team membership. This provides an overview of all available API testing
    projects for the user.
    """
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        """
        Return projects accessible to the current user.
        
        Includes both owned projects and projects accessible via team membership,
        ensuring users see all projects they can work with.
        """
        return (Project.objects.filter(owner=self.request.user) | 
                Project.objects.filter(teams__members=self.request.user)).distinct()


class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Display detailed view of a specific API testing project.
    
    Shows project information and all collections within the project.
    Access is restricted to project owners and team members.
    """
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    
    def test_func(self):
        """
        Check if the current user has access to view this project.
        
        Returns True if user is the project owner or a member of any team
        that has access to the project.
        """
        project = self.get_object()
        return (project.owner == self.request.user or 
                project.teams.filter(members=self.request.user).exists())
    
    def get_context_data(self, **kwargs):
        """Add project's collections to the template context."""
        context = super().get_context_data(**kwargs)
        context['collections'] = self.object.collections.all()
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new API testing project.
    
    Allows authenticated users to create new projects for organizing their
    API testing workflows. The creating user automatically becomes the project owner.
    """
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('project_list')
    
    def form_valid(self, form):
        """Set the current user as the project owner."""
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update an existing API testing project.
    
    Only project owners can modify project details such as name, description,
    and team access permissions.
    """
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    
    def test_func(self):
        """Ensure only project owners can edit projects."""
        project = self.get_object()
        return project.owner == self.request.user
    
    def get_success_url(self):
        """Redirect to project detail page after successful update."""
        return reverse_lazy('project_detail', kwargs={'pk': self.object.pk})


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete an API testing project.
    
    Only project owners can delete projects. This will also delete all
    associated collections, API requests, and request history.
    """
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('project_list')
    
    def test_func(self):
        """Ensure only project owners can delete projects."""
        project = self.get_object()
        return project.owner == self.request.user


# ============================================================================
# COLLECTION MANAGEMENT VIEWS
# ============================================================================

class CollectionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create a new API request collection within a project.
    
    Collections help organize related API endpoints within a project.
    Access is restricted to project owners and team members.
    """
    model = Collection
    form_class = CollectionForm
    template_name = 'collections/collection_form.html'
    
    def test_func(self):
        """Check if user has access to create collections in this project."""
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        return (project.owner == self.request.user or 
                project.teams.filter(members=self.request.user).exists())
    
    def form_valid(self, form):
        """Associate the collection with the specified project."""
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        form.instance.project = project
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add project ID to template context for form processing."""
        context = super().get_context_data(**kwargs)
        context['project_id'] = self.kwargs.get('project_id')
        return context
    
    def get_success_url(self):
        """Redirect to project detail page after successful creation."""
        return reverse_lazy('project_detail', kwargs={'pk': self.kwargs.get('project_id')})


class CollectionDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Display detailed view of an API request collection.
    
    Shows collection information and all API requests within the collection.
    Access is restricted to project owners and team members.
    """
    model = Collection
    template_name = 'collections/collection_detail.html'
    context_object_name = 'collection'
    
    def test_func(self):
        """Check if user has access to view this collection."""
        collection = self.get_object()
        project = collection.project
        return (project.owner == self.request.user or 
                project.teams.filter(members=self.request.user).exists())
    
    def get_context_data(self, **kwargs):
        """Add collection's API requests to the template context."""
        context = super().get_context_data(**kwargs)
        context['requests'] = self.object.requests.all()
        return context


# ============================================================================
# API REQUEST MANAGEMENT VIEWS
# ============================================================================

class APIRequestCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create a new API request within a collection.
    
    Allows users to define new API endpoints for testing, including all
    request configuration such as URL, method, headers, parameters, body,
    and authentication settings.
    """
    model = APIRequest
    form_class = APIRequestForm
    template_name = 'requests/request_form.html'
    
    def test_func(self):
        """Check if user has access to create API requests in this collection."""
        collection_id = self.kwargs.get('collection_id')
        collection = get_object_or_404(Collection, id=collection_id)
        project = collection.project
        return (project.owner == self.request.user or 
                project.teams.filter(members=self.request.user).exists())
    
    def form_valid(self, form):
        """
        Process form data and create the API request with all configuration.
        
        Handles both basic form fields and complex JSON fields for headers,
        parameters, body, and authentication settings.
        """
        collection_id = self.kwargs.get('collection_id')
        collection = get_object_or_404(Collection, id=collection_id)
        form.instance.collection = collection
        
        # Set basic request configuration from form data
        form.instance.url = self.request.POST.get('url', '')
        form.instance.method = self.request.POST.get('method', 'GET')
        
        # Parse JSON fields for complex configuration
        form.instance.headers = json.loads(self.request.POST.get('headers', '{}'))
        form.instance.params = json.loads(self.request.POST.get('params', '{}'))
        form.instance.body = json.loads(self.request.POST.get('body', '{}'))
        form.instance.auth = json.loads(self.request.POST.get('auth', '{}'))
        
        # Set additional request options
        form.instance.timeout = int(self.request.POST.get('timeout', 30000))
        form.instance.follow_redirects = self.request.POST.get('follow_redirects', 'true').lower() == 'true'
        form.instance.verify_ssl = self.request.POST.get('verify_ssl', 'true').lower() == 'true'
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add collection ID to template context."""
        context = super().get_context_data(**kwargs)
        context['collection_id'] = self.kwargs.get('collection_id')
        return context
    
    def get_success_url(self):
        """Redirect to collection detail page after successful creation."""
        return reverse_lazy('collection_detail', kwargs={'pk': self.kwargs.get('collection_id')})


class APIRequestDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Display detailed view of an API request configuration.
    
    Shows the complete API request configuration and recent execution history.
    This allows users to review and analyze their API testing results.
    """
    model = APIRequest
    template_name = 'requests/request_detail.html'
    context_object_name = 'request'
    
    def test_func(self):
        """Check if user has access to view this API request."""
        api_request = self.get_object()
        project = api_request.collection.project
        return (project.owner == self.request.user or 
                project.teams.filter(members=self.request.user).exists())
    
    def get_context_data(self, **kwargs):
        """Add recent request execution history to template context."""
        context = super().get_context_data(**kwargs)
        # Show the 10 most recent executions for analysis
        context['history'] = self.object.history.all()[:10]
        return context


class APIRequestUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update an existing API request configuration.
    
    Allows users to modify all aspects of an API request including URL, method,
    headers, parameters, body, authentication, and request options.
    """
    model = APIRequest
    form_class = APIRequestForm
    template_name = 'requests/request_form.html'
    
    def test_func(self):
        """Check if user has access to edit this API request."""
        api_request = self.get_object()
        project = api_request.collection.project
        return (project.owner == self.request.user or 
                project.teams.filter(members=self.request.user).exists())
    
    def get_context_data(self, **kwargs):
        """Add collection ID to template context for form processing."""
        context = super().get_context_data(**kwargs)
        context['collection_id'] = self.object.collection.id
        return context
    
    def form_valid(self, form):
        """
        Process updated form data and save changes to the API request.
        
        Handles both basic form fields and complex JSON fields, similar
        to the create view but updating an existing record.
        """
        # Update basic request configuration
        form.instance.url = self.request.POST.get('url', '')
        form.instance.method = self.request.POST.get('method', 'GET')
        
        # Parse and update JSON fields
        form.instance.headers = json.loads(self.request.POST.get('headers', '{}'))
        form.instance.params = json.loads(self.request.POST.get('params', '{}'))
        form.instance.body = json.loads(self.request.POST.get('body', '{}'))
        form.instance.auth = json.loads(self.request.POST.get('auth', '{}'))
        
        # Update additional request options
        form.instance.timeout = int(self.request.POST.get('timeout', 30000))
        form.instance.follow_redirects = self.request.POST.get('follow_redirects', 'true').lower() == 'true'
        form.instance.verify_ssl = self.request.POST.get('verify_ssl', 'true').lower() == 'true'
        
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirect to API request detail page after successful update."""
        return reverse_lazy('request_detail', kwargs={'pk': self.object.pk})


# ============================================================================
# TEAM MANAGEMENT VIEWS
# ============================================================================

class TeamListView(LoginRequiredMixin, ListView):
    """
    Display a list of teams that the current user is a member of.
    
    Teams enable collaborative API testing by allowing multiple users
    to work together on projects and share API test collections.
    """
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'
    
    def get_queryset(self):
        """Return only teams where the current user is a member."""
        return Team.objects.filter(members=self.request.user)


class TeamCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new team for collaborative API testing.
    
    The user who creates the team automatically becomes a member and can
    then add other users to enable collaborative access to projects.
    """
    model = Team
    form_class = TeamForm
    template_name = 'teams/team_form.html'
    success_url = reverse_lazy('team_list')
    
    def form_valid(self, form):
        """
        Create the team and automatically add the creator as a member.
        
        This ensures that the person creating the team has immediate access
        to manage it and add other members.
        """
        response = super().form_valid(form)
        # Add the creator to the team members
        self.object.members.add(self.request.user)
        return response


class TeamDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Display detailed view of a team.
    
    Shows team information, all team members, and projects that the team
    has access to. Only team members can view team details.
    """
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'
    
    def test_func(self):
        """Ensure only team members can view team details."""
        team = self.get_object()
        return team.members.filter(id=self.request.user.id).exists()
    
    def get_context_data(self, **kwargs):
        """Add team's projects and members to template context."""
        context = super().get_context_data(**kwargs)
        context['projects'] = self.object.projects.all()
        context['members'] = self.object.members.all()
        return context


class TeamUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update an existing team.
    
    Allows team members to modify team details and manage team membership.
    Only team members can update team information.
    """
    model = Team
    form_class = TeamForm
    template_name = 'teams/team_form.html'
    
    def test_func(self):
        """Ensure only team members can update the team."""
        team = self.get_object()
        return team.members.filter(id=self.request.user.id).exists()
    
    def get_success_url(self):
        """Redirect to team detail page after successful update."""
        return reverse_lazy('team_detail', kwargs={'pk': self.object.pk})


class TeamDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete a team.
    
    Only team members can delete a team. This will remove the team
    but will not affect the projects it had access to.
    """
    model = Team
    template_name = 'teams/team_confirm_delete.html'
    success_url = reverse_lazy('team_list')
    
    def test_func(self):
        """Ensure only team members can delete the team."""
        team = self.get_object()
        return team.members.filter(id=self.request.user.id).exists()


# ============================================================================
# USER SEARCH VIEW
# ============================================================================

@login_required
def user_search(request):
    """
    AJAX endpoint for searching users to add to teams.
    
    Supports searching by username or email with pagination.
    Used by Select2 widget in team forms for user selection.
    
    Query Parameters:
        q: Search term for username or email
        page: Page number for pagination (optional)
    
    Returns:
        JsonResponse with Select2-compatible format:
        {
            "results": [{"id": user_id, "username": "...", "email": "..."}],
            "pagination": {"more": boolean}
        }
    """
    query = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1))
    page_size = 20
    
    if not query:
        return JsonResponse({
            'results': [],
            'pagination': {'more': False}
        })
    
    # Search users by username or email, excluding the current user
    users = User.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    ).exclude(id=request.user.id).order_by('username')
    
    # Implement pagination
    start_offset = (page - 1) * page_size
    end_offset = start_offset + page_size
    
    paginated_users = users[start_offset:end_offset]
    has_more = users.count() > end_offset
    
    # Format results for Select2
    results = []
    for user in paginated_users:
        results.append({
            'id': user.id,
            'username': user.username,
            'email': user.email or '',
        })
    
    return JsonResponse({
        'results': results,
        'pagination': {'more': has_more}
    })
