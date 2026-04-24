from django.urls import path

from .views import (
    RegisterView,
    SmartLoginView,
    SmartLogoutView,
    about,
    computations,
    dashboard,
    dtm_map,
    export_points,
    import_points,
    live_map,
    live_station_data,
    projects,
    reports,
    report_pdf,
    select_project,
    survey,
    welcome,
)


urlpatterns = [
    path("", welcome, name="welcome"),
    path("about/", about, name="about"),
    path("auth/", SmartLoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", SmartLogoutView.as_view(), name="logout"),
    path("dashboard/", dashboard, name="dashboard"),
    path("projects/", projects, name="projects"),
    path("projects/<int:project_id>/select/", select_project, name="select_project"),
    path("survey/", survey, name="survey"),
    path("computations/", computations, name="computations"),
    path("dtm-map/", dtm_map, name="dtm_map"),
    path("live-map/", live_map, name="live_map"),
    path("reports/", reports, name="reports"),
    path("reports/<str:report_type>/pdf/", report_pdf, name="report_pdf"),
    path("reports/import/", import_points, name="import_points"),
    path("reports/export/", export_points, name="export_points"),
    path("api/live-station-data/", live_station_data, name="live_station_data"),
]
