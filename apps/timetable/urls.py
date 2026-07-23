from django.urls import path
from . import views

app_name = 'timetable'

urlpatterns = [
    # Main hub
    path('', views.index, name='index'),

    # Schedule configuration (Secretary only)
    path('config/', views.schedule_config, name='schedule_config'),
    path('config/<int:pk>/edit/', views.timeslot_edit, name='timeslot_edit'),
    path('config/<int:pk>/delete/', views.timeslot_delete, name='timeslot_delete'),

    # Classroom timetable grid
    path('classe/<int:classroom_id>/', views.classroom_timetable, name='classroom_timetable'),
    path('classe/<int:classroom_id>/entry/add/', views.entry_add, name='entry_add'),
    path('entry/<int:pk>/edit/', views.entry_edit, name='entry_edit'),
    path('entry/<int:pk>/delete/', views.entry_delete, name='entry_delete'),
    path('classe/<int:classroom_id>/publish/', views.schedule_publish, name='schedule_publish'),
    path('classe/<int:classroom_id>/print/', views.print_classroom_timetable, name='print_classroom'),

    # Teacher timetable
    path('enseignant/', views.teacher_timetable, name='teacher_timetable'),
    path('enseignant/<int:teacher_id>/', views.teacher_timetable, name='teacher_timetable_by_id'),
    path('enseignant/<int:teacher_id>/print/', views.teacher_timetable, name='print_teacher'),
]
