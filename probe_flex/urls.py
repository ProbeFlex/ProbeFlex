from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

from probe_app.views import (
    CustomLoginView, SignUpView, home, send_request,
    ProjectListView, ProjectDetailView, ProjectCreateView, ProjectUpdateView, ProjectDeleteView,
    CollectionDetailView, CollectionCreateView,
    APIRequestDetailView, APIRequestCreateView,
    TeamListView, TeamDetailView, TeamCreateView, APIRequestUpdateView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    
    # Home and API testing
    path('', RedirectView.as_view(url='/home/'), name='index'),
    path('home/', home, name='home'),
    path('api/send/', send_request, name='send_request'),
    
    # Project URLs
    path('projects/', ProjectListView.as_view(), name='project_list'),
    path('projects/new/', ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<int:pk>/edit/', ProjectUpdateView.as_view(), name='project_update'),
    path('projects/<int:pk>/delete/', ProjectDeleteView.as_view(), name='project_delete'),
    
    # Collection URLs
    path('projects/<int:project_id>/collections/new/', CollectionCreateView.as_view(), name='collection_create'),
    path('collections/<int:pk>/', CollectionDetailView.as_view(), name='collection_detail'),
    
    # API Request URLs
    path('collections/<int:collection_id>/requests/new/', APIRequestCreateView.as_view(), name='request_create'),
    path('requests/<int:pk>/', APIRequestDetailView.as_view(), name='request_detail'),
    path('requests/<int:pk>/edit/', APIRequestUpdateView.as_view(), name='request_update'),

    # Team URLs
    path('teams/', TeamListView.as_view(), name='team_list'),
    path('teams/new/', TeamCreateView.as_view(), name='team_create'),
    path('teams/<int:pk>/', TeamDetailView.as_view(), name='team_detail'),
    
    # Include Django AllAuth URLs
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
