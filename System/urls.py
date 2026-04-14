from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Courses
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/enroll/', views.enroll, name='enroll'),

    # Materials
    path('courses/<int:course_pk>/materials/add/', views.material_add, name='material_add'),
    path('materials/<int:pk>/delete/', views.material_delete, name='material_delete'),
    path('materials/<int:pk>/view/', views.track_material_view, name='track_material_view'),

    # Meetings
    path('courses/<int:course_pk>/meetings/create/', views.meeting_create, name='meeting_create'),
    path('meetings/<uuid:pk>/', views.meeting_room, name='meeting_room'),
    path('meetings/<uuid:pk>/end/', views.meeting_end, name='meeting_end'),

    # Exams
    path('courses/<int:course_pk>/exams/create/', views.exam_create, name='exam_create'),
    path('exams/<int:pk>/edit/', views.exam_edit, name='exam_edit'),
    path('exams/<int:exam_pk>/questions/add/', views.question_add, name='question_add'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
    path('exams/<int:pk>/take/', views.exam_take, name='exam_take'),
    path('exams/result/<int:pk>/', views.exam_result, name='exam_result'),

    # Grades & Students
    path('grades/', views.student_grades, name='student_grades'),
    path('my-students/', views.teacher_students, name='teacher_students'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path('teacher/<int:pk>/', views.teacher_profile, name='teacher_profile'),

    # Notifications
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('enrollment/<int:enrollment_id>/approve/', views.approve_enrollment, name='approve_enrollment'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Support
    path('support/', views.support_list, name='support_list'),
    path('support/new/', views.support_create, name='support_create'),
    path('support/<int:pk>/', views.support_detail, name='support_detail'),
    path('support/<int:pk>/close/', views.support_close, name='support_close'),
]
