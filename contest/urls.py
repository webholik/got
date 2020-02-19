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
    path('verify/', views.verifyview, name='verify'),
    path('resend_email/', views.resend_email, name='resend_email'),
    path('rules/', views.rules, name='rules'),
    # path('api/<int:id>', views.api, name='api'),
]
