from django.urls import path
from . import views


urlpatterns = [
    path("api/check-student/", views.check_student,name="check_student"),
    path('', views.login_user, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboardView, name='dashboard'),
    path("teacher/students/add/", views.add_student, name="add_student"),
    path("check-student/", views.check_student, name="check_student"),
    path("game-status/", views.game_status, name="game_status"),
    path(
    "students/delete/<int:student_id>/",
    views.delete_student,
    name="delete_student"
),
    path(
        "dashboard/live-data/",
        views.dashboard_live_data,
        name="dashboard_live_data"
    ),
]