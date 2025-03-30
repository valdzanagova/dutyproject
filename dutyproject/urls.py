from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from dutyapp.views import (DutyAssignmentViewSet, DutyConfigViewSet, create_duty_config, delete_duty_config,
                           duty_config_detail, duty_config_list, duty_config_schedule, edit_duty_config,
                           root_redirect_view, send_code_view, verify_code_view)


router = routers.DefaultRouter()
router.register(r'configs', DutyConfigViewSet)
router.register(r'assignments', DutyAssignmentViewSet)

urlpatterns = [
    # API endpoints from DRF
    path('api/', include(router.urls)),

    # Root URL
    path('', root_redirect_view, name='root_redirect'),

    path('admin/', admin.site.urls),

    # Authorization pages
    path('send_code/', send_code_view, name='send_code'),
    path('verify_code/', verify_code_view, name='verify_code'),

    # Web interface (protected pages)
    path('create/', create_duty_config, name='create_duty_config'),
    path('config/<int:pk>/', duty_config_detail, name='duty_config_detail'),
    path('configs/', duty_config_list, name='duty_config_list'),
    path('config/<int:pk>/schedule/', duty_config_schedule, name='duty_config_schedule'),
    path('config/<int:pk>/edit/', edit_duty_config, name='edit_duty_config'),
    path('config/<int:pk>/delete/', delete_duty_config, name='delete_duty_config'),
]
