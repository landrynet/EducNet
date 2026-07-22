"""URL Configuration for School Management System."""

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('apps.dashboard.urls', namespace='dashboard')),
    path('auth/', include('apps.authentication.urls')),
    path('schools/', include('apps.schools.urls', namespace='schools')),
    path('users/', include('apps.users.urls', namespace='users')),
    path('academic/', include('apps.academic.urls', namespace='academic')),
    path('students/', include('apps.students.urls', namespace='students')),
    path('parents/', include('apps.parents.urls', namespace='parents')),
    path('staff/', include('apps.staff.urls', namespace='staff')),
    path('enrollment/', include('apps.enrollment.urls', namespace='enrollment')),
    path('timetable/', include('apps.timetable.urls', namespace='timetable')),
    path('assessments/', include('apps.assessments.urls', namespace='assessments')),
    path('reports/', include('apps.reports.urls', namespace='reports')),
    path('finance/', include('apps.finance.urls', namespace='finance')),
    path('transport/', include('apps.transport.urls', namespace='transport')),
    path('communication/', include('apps.communication.urls', namespace='communication')),
    path('documents/', include('apps.documents.urls', namespace='documents')),
    path('analytics/', include('apps.analytics.urls', namespace='analytics')),
    path('audit/', include('apps.audit.urls', namespace='audit')),
    path('backup/', include('apps.backup.urls', namespace='backup')),
    # REST API
    path('api/v1/', include('apps.users.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
