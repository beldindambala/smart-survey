from django.urls import path

from .views import RegisterView, SmartLoginView, SmartLogoutView, dashboard, reports, survey, welcome


urlpatterns = [
    path("", welcome, name="welcome"),
    path("auth/", SmartLoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", SmartLogoutView.as_view(), name="logout"),
    path("dashboard/", dashboard, name="dashboard"),
    path("survey/", survey, name="survey"),
    path("reports/", reports, name="reports"),
]
