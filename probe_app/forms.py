from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Team, Project, Collection, APIRequest


# ============================================================================
# AUTHENTICATION FORMS
# ============================================================================

class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form for ProbeFlex user login.
    
    Extends Django's built-in AuthenticationForm to add Bootstrap styling
    and a 'remember me' checkbox functionality. The remember me feature
    allows users to stay logged in across browser sessions, which is
    convenient for API testing workflows where users may need extended
    access to their test configurations.
    """
    # Username field with Bootstrap styling and placeholder
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',  # Bootstrap form control styling
        'placeholder': 'Username'  # User-friendly placeholder text
    }))
    
    # Password field with Bootstrap styling and placeholder
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',  # Bootstrap form control styling
        'placeholder': 'Password'  # User-friendly placeholder text
    }))
    
    # Remember me checkbox for extended session duration
    remember_me = forms.BooleanField(
        required=False,  # Optional field - users can choose
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'  # Bootstrap checkbox styling
        })
    )


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user registration form for new ProbeFlex users.
    
    Extends Django's UserCreationForm to include email field and apply
    Bootstrap styling. New users need to provide username, email, and
    password to create an account for accessing API testing features.
    The email field is required for potential future features like
    password recovery and team invitations.
    """
    # Username field with Bootstrap styling
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    
    # Email field (required) - useful for account recovery and team features
    email = forms.EmailField(
        required=True,  # Email is mandatory for account creation
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    
    # Password field with Bootstrap styling
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))
    
    # Password confirmation field with Bootstrap styling
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm Password'
    }))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        """
        Save the new user with email address.
        
        Overrides the parent save method to ensure the email field
        is properly saved to the User model, as it's not included
        in the default UserCreationForm.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


# ============================================================================
# PROJECT ORGANIZATION FORMS
# ============================================================================

class ProjectForm(forms.ModelForm):
    """
    Form for creating and editing API testing projects.
    
    Projects are the top-level organizational unit in ProbeFlex, containing
    collections of related API endpoints. This form allows users to define
    the project name and description. Additional project settings like team
    access are handled separately in the views.
    """
    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            # Project name input with Bootstrap styling
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            # Project description textarea with Bootstrap styling and limited rows
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3  # Keep description concise but allow multiple lines
            }),
        }


class CollectionForm(forms.ModelForm):
    """
    Form for creating and editing API request collections within projects.
    
    Collections help organize related API endpoints within a project.
    For example, a project might have separate collections for "Authentication APIs",
    "User Management APIs", and "Data APIs". This organizational structure
    makes it easier to manage and navigate large sets of API tests.
    """
    class Meta:
        model = Collection
        fields = ['name', 'description']
        widgets = {
            # Collection name input with Bootstrap styling
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            # Collection description textarea with Bootstrap styling
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3  # Adequate space for describing the collection's purpose
            }),
        }


# ============================================================================
# TEAM COLLABORATION FORMS
# ============================================================================

class TeamForm(forms.ModelForm):
    """
    Form for creating and editing teams for collaborative API testing.
    
    Teams enable multiple users to work together on API testing projects.
    Team creators can add other users as members, and teams can be granted
    access to specific projects. This form handles team metadata and
    member selection with a multi-select widget for easy user management.
    """
    class Meta:
        model = Team
        fields = ['name', 'description', 'members']
        widgets = {
            # Team name input with Bootstrap styling
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            # Team description textarea for explaining the team's purpose
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3
            }),
            # Multi-select widget for choosing team members
            # Uses select2 class for enhanced UI (if Select2 is implemented)
            'members': forms.SelectMultiple(attrs={
                'class': 'form-control select2'
            }),
        }


# ============================================================================
# API REQUEST CONFIGURATION FORMS
# ============================================================================

class APIRequestForm(forms.ModelForm):
    """
    Form for creating and editing API request configurations.
    
    This form handles the basic metadata for API requests (name and description).
    The actual API request configuration (URL, method, headers, parameters,
    body, authentication) is handled through JavaScript in the frontend
    interface and passed as hidden form fields or AJAX data to the views.
    
    This separation allows for a more interactive API testing interface
    while still maintaining proper form validation for the core fields.
    """
    class Meta:
        model = APIRequest
        fields = ['name', 'description']
        widgets = {
            # API request name input with Bootstrap styling
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            # API request description textarea with limited rows
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2  # Keep concise - main details are in the API config
            }),
        } 