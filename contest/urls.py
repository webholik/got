from django.urls import path

from . import views

app_name = 'contest'
urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.loginview, name='login'),
    path('signup/', views.signup, name='signup'),
    path('questions/', views.ques, name='question'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('logout/', views.logoutview, name='logout'),
    path('verify/', views.verify_view, name='verify'),
    # path('resend_email/', views.resend_email, name='resend_email'),
    path('rules/', views.rules, name='rules'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('reset/', views.reset, name='reset'),
    # path('api/<int:id>', views.api, name='api'),
]
