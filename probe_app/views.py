from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .forms import (
    CustomAuthenticationForm, CustomUserCreationForm, 
    ProjectForm, CollectionForm, TeamForm, APIRequestForm
)
from .models import Project, Collection, Team, APIRequest, RequestHistory

import requests
import json
import time
from datetime import datetime


class CustomLoginView(LoginView):
    """Custom login view with remember me functionality"""
    form_class = CustomAuthenticationForm
    template_name = 'registration/login.html'
    
    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            # Session expires when the user closes the browser
            self.request.session.set_expiry(0)
        return super().form_valid(form)


class SignUpView(CreateView):
    """Sign up view for new users"""
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')


@login_required
def home(request):
    """Home view for API testing interface"""
    projects = (Project.objects.filter(owner=request.user) | 
                Project.objects.filter(teams__members=request.user)).distinct()
    
    context = {
        'projects': projects,
    }
    return render(request, 'home.html', context)


@login_required
@csrf_exempt  # For test purposes only, remove in production
def send_request(request):
    """View for sending API requests and storing results"""
    if request.method == 'POST':
        try:
            # Print debug info to console
            print(f"Request received: {request.body[:1000] if hasattr(request, 'body') else 'No body'}")
            
            # Try to handle both form data and JSON
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                print(f"Parsed JSON data: {json.dumps(data)[:1000]}")
            else:
                # Handle form data
                data = {
                    'url': request.POST.get('url', ''),
                    'method': request.POST.get('method', 'GET').upper(),
                    'headers': {},  # Form will handle this differently
                    'params': {},
                    'body': {},
                    'auth': {},
                }
                
            url = data.get('url', '')
            method = data.get('method', 'GET').upper()
            headers = data.get('headers', {})
            params = data.get('params', {})
            request_body = data.get('body', {})
            auth_data = data.get('auth', {})
            follow_redirects = data.get('follow_redirects', True)
            verify_ssl = data.get('verify_ssl', True)
            
            print(f"Processing request: {method} {url}")
            print(f"Verify SSL: {verify_ssl}")
            print(f"Auth data structure: {type(auth_data)}")
            print(f"Auth data: {json.dumps(auth_data)}")
            print(f"Headers before auth: {json.dumps(headers)}")
            
            # Check if auth is already applied to headers (by client-side JS)
            auth_already_applied = False
            if 'Authorization' in headers:
                print(f"Authorization header already exists: {headers['Authorization'][:15]}...")
                auth_already_applied = True
            
            auth = None
            # Handle Basic auth
            if auth_data and auth_data.get('type') == 'basic':
                username = auth_data.get('username', '')
                password = auth_data.get('password', '')
                if username:
                    auth = (username, password)
                    print(f"Using Basic Auth: username={username}, password={'*'*len(password) if password else 'None'}")
            # Handle Bearer token
            elif auth_data and auth_data.get('type') == 'bearer' and not auth_already_applied:
                token = auth_data.get('token', '')
                if token:
                    headers['Authorization'] = f"Bearer {token}"
                    print(f"Using Bearer Token Auth: {token[:5]}***")
            # Handle API Key
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
            
            start_time = time.time()
            
            request_kwargs = {
                'headers': headers,
                'params': params,
                'verify': verify_ssl,
                'allow_redirects': follow_redirects,
                'timeout': 30  # Add a reasonable timeout
            }
            
            # Only add auth if it's present (for basic auth)
            if auth:
                request_kwargs['auth'] = auth
                print(f"Added Basic Auth to request_kwargs")
            
            # For debugging - show actual request parameters
            debug_kwargs = request_kwargs.copy()
            if 'auth' in debug_kwargs:
                debug_kwargs['auth'] = '(AUTH CREDENTIALS HIDDEN)'
            if 'headers' in debug_kwargs and 'Authorization' in debug_kwargs['headers']:
                headers_copy = debug_kwargs['headers'].copy()
                headers_copy['Authorization'] = headers_copy['Authorization'][:10] + '...'
                debug_kwargs['headers'] = headers_copy
            
            print(f"Final request kwargs: {json.dumps(debug_kwargs)}")
            
            # Add json body for methods that support it
            if method in ['POST', 'PUT', 'PATCH']:
                request_kwargs['json'] = request_body
            # For GET requests, we handle the body separately by adding to query params if needed
            elif method == 'GET' and request_body:
                # If there's body content in a GET request, log a warning
                print(f"Warning: Body content sent with GET request: {request_body}")
                # Use params instead of body for GET requests
                if isinstance(request_body, dict):
                    for key, value in request_body.items():
                        request_kwargs['params'][key] = value
            
            if method == 'GET':
                response = requests.get(url, **request_kwargs)
            elif method == 'POST':
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
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Try to parse response as JSON, if not return text
            try:
                response_body = response.json()
            except ValueError:
                response_body = response.text
            
            response_data = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response_body,
                'time': response_time
            }
            
            # Save request history if there's an associated API request
            api_request_id = data.get('api_request_id')
            if api_request_id:
                api_request = get_object_or_404(APIRequest, id=api_request_id)
                
                # Create request history
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
            
            print(f"Request completed: {method} {url} - {response.status_code}")
            return JsonResponse(response_data)
        
        except requests.RequestException as e:
            print(f"Request error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    # For debugging - allow GET requests temporarily
    if request.method == 'GET':
        test_url = request.GET.get('url')
        if test_url:
            try:
                response = requests.get(test_url)
                return JsonResponse({
                    'status_code': response.status_code,
                    'body': response.text[:1000],  # Truncate long responses
                    'headers': dict(response.headers),
                    'time': 0
                })
            except Exception as e:
                return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


# Project Views
class ProjectListView(LoginRequiredMixin, ListView):
    """View for listing projects accessible to the user"""
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        # Show projects owned by the user or accessible via teams
        return (Project.objects.filter(owner=self.request.user) | 
                Project.objects.filter(teams__members=self.request.user)).distinct()


class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View for project details"""
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    
    def test_func(self):
        project = self.get_object()
        return (project.owner == self.request.user or 
                project.teams.filter(members=self.request.user).exists())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['collections'] = self.object.collections.all()
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    """View for creating new projects"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('project_list')
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for updating existing projects"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    
    def test_func(self):
        project = self.get_object()
        return project.owner == self.request.user
    
    def get_success_url(self):
        return reverse_lazy('project_detail', kwargs={'pk': self.object.pk})


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View for deleting projects"""
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('project_list')
    
    def test_func(self):
        project = self.get_object()
        return project.owner == self.request.user


# Collection Views
class CollectionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for creating new collections within a project"""
    model = Collection
    form_class = CollectionForm
    template_name = 'collections/collection_form.html'
    
    def test_func(self):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        return (project.owner == self.request.user or 
                project.teams.filter(members=self.request.user).exists())
    
    def form_valid(self, form):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        form.instance.project = project
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project_id'] = self.kwargs.get('project_id')
        return context
    
    def get_success_url(self):
        return reverse_lazy('project_detail', kwargs={'pk': self.kwargs.get('project_id')})


class CollectionDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View for collection details"""
    model = Collection
    template_name = 'collections/collection_detail.html'
    context_object_name = 'collection'
    
    def test_func(self):
        collection = self.get_object()
        project = collection.project
        return (project.owner == self.request.user or 
                project.teams.filter(members=self.request.user).exists())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['requests'] = self.object.requests.all()
        return context


# API Request Views
class APIRequestCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for creating new API requests within a collection"""
    model = APIRequest
    form_class = APIRequestForm
    template_name = 'requests/request_form.html'
    
    def test_func(self):
        collection_id = self.kwargs.get('collection_id')
        collection = get_object_or_404(Collection, id=collection_id)
        project = collection.project
        return (project.owner == self.request.user or 
                project.teams.filter(members=self.request.user).exists())
    
    def form_valid(self, form):
        collection_id = self.kwargs.get('collection_id')
        collection = get_object_or_404(Collection, id=collection_id)
        form.instance.collection = collection
        
        # Set additional fields from hidden form inputs
        form.instance.url = self.request.POST.get('url', '')
        form.instance.method = self.request.POST.get('method', 'GET')
        
        # Handle JSON fields
        form.instance.headers = json.loads(self.request.POST.get('headers', '{}'))
        form.instance.params = json.loads(self.request.POST.get('params', '{}'))
        form.instance.body = json.loads(self.request.POST.get('body', '{}'))
        form.instance.auth = json.loads(self.request.POST.get('auth', '{}'))
        
        # Handle additional request settings
        form.instance.timeout = int(self.request.POST.get('timeout', 30000))
        form.instance.follow_redirects = self.request.POST.get('follow_redirects', 'true').lower() == 'true'
        form.instance.verify_ssl = self.request.POST.get('verify_ssl', 'true').lower() == 'true'
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['collection_id'] = self.kwargs.get('collection_id')
        return context
    
    def get_success_url(self):
        return reverse_lazy('collection_detail', kwargs={'pk': self.kwargs.get('collection_id')})


class APIRequestDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View for API request details"""
    model = APIRequest
    template_name = 'requests/request_detail.html'
    context_object_name = 'request'
    
    def test_func(self):
        api_request = self.get_object()
        project = api_request.collection.project
        return (project.owner == self.request.user or 
                project.teams.filter(members=self.request.user).exists())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['history'] = self.object.history.all()[:10]  # Get the last 10 request executions
        return context


class APIRequestUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for updating API requests"""
    model = APIRequest
    form_class = APIRequestForm
    template_name = 'requests/request_form.html'
    
    def test_func(self):
        api_request = self.get_object()
        project = api_request.collection.project
        return (project.owner == self.request.user or 
                project.teams.filter(members=self.request.user).exists())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['collection_id'] = self.object.collection.id
        return context
    
    def form_valid(self, form):
        # Set additional fields from hidden form inputs
        form.instance.url = self.request.POST.get('url', '')
        form.instance.method = self.request.POST.get('method', 'GET')
        
        # Handle JSON fields
        form.instance.headers = json.loads(self.request.POST.get('headers', '{}'))
        form.instance.params = json.loads(self.request.POST.get('params', '{}'))
        form.instance.body = json.loads(self.request.POST.get('body', '{}'))
        form.instance.auth = json.loads(self.request.POST.get('auth', '{}'))
        
        # Handle additional request settings
        form.instance.timeout = int(self.request.POST.get('timeout', 30000))
        form.instance.follow_redirects = self.request.POST.get('follow_redirects', 'true').lower() == 'true'
        form.instance.verify_ssl = self.request.POST.get('verify_ssl', 'true').lower() == 'true'
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('request_detail', kwargs={'pk': self.object.pk})


# Team Views
class TeamListView(LoginRequiredMixin, ListView):
    """View for listing teams the user is a member of"""
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'
    
    def get_queryset(self):
        return Team.objects.filter(members=self.request.user)


class TeamCreateView(LoginRequiredMixin, CreateView):
    """View for creating new teams"""
    model = Team
    form_class = TeamForm
    template_name = 'teams/team_form.html'
    success_url = reverse_lazy('team_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Add the creator to the team members
        self.object.members.add(self.request.user)
        return response


class TeamDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View for team details"""
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'
    
    def test_func(self):
        team = self.get_object()
        return team.members.filter(id=self.request.user.id).exists()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = self.object.projects.all()
        context['members'] = self.object.members.all()
        return context
