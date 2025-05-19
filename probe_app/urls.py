from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/send/', views.send_request, name='send_request'),
    
    # Project URLs
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/new/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    
    # Collection URLs
    path('projects/<int:project_id>/collections/new/', views.CollectionCreateView.as_view(), name='collection_create'),
    path('collections/<int:pk>/', views.CollectionDetailView.as_view(), name='collection_detail'),
    
    # API Request URLs
    path('collections/<int:collection_id>/requests/new/', views.APIRequestCreateView.as_view(), name='request_create'),
    path('requests/<int:pk>/', views.APIRequestDetailView.as_view(), name='request_detail'),
    
    # Team URLs
    path('teams/', views.TeamListView.as_view(), name='team_list'),
    path('teams/new/', views.TeamCreateView.as_view(), name='team_create'),
    path('teams/<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),
] 