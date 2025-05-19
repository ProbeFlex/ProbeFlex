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
            print(f"Request received: {request.POST or request.body}")
            
            # Try to handle both form data and JSON
            if request.content_type == 'application/json':
                data = json.loads(request.body)
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
            
            print(f"Processing request: {method} {url}")
            
            auth = None
            if auth_data.get('type') == 'basic':
                auth = (auth_data.get('username', ''), auth_data.get('password', ''))
            
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, auth=auth)
            elif method == 'POST':
                response = requests.post(url, headers=headers, params=params, json=request_body, auth=auth)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, params=params, json=request_body, auth=auth)
            elif method == 'PATCH':
                response = requests.patch(url, headers=headers, params=params, json=request_body, auth=auth)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, auth=auth)
            elif method == 'HEAD':
                response = requests.head(url, headers=headers, params=params, auth=auth)
            elif method == 'OPTIONS':
                response = requests.options(url, headers=headers, params=params, auth=auth)
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
        return Project.objects.filter(owner=self.request.user) | Project.objects.filter(teams__members=self.request.user).distinct()


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
        return super().form_valid(form)
    
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
