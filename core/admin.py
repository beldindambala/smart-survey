from django.contrib import admin

from .models import ComputationRun, Project, Report, SurveyPoint, TelemetrySnapshot


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "project_code", "station_name", "is_connected", "updated_at")
    search_fields = ("name", "project_code", "station_name")


@admin.register(SurveyPoint)
class SurveyPointAdmin(admin.ModelAdmin):
    list_display = ("point_id", "project", "easting", "northing", "elevation", "captured_at")
    list_filter = ("project", "captured_at")
    search_fields = ("point_id", "description", "code")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "report_type", "is_ready", "created_at")
    list_filter = ("report_type", "is_ready")
    search_fields = ("title",)


@admin.register(TelemetrySnapshot)
class TelemetrySnapshotAdmin(admin.ModelAdmin):
    list_display = ("project", "latitude", "longitude", "elevation", "source", "captured_at")
    list_filter = ("source", "project")


@admin.register(ComputationRun)
class ComputationRunAdmin(admin.ModelAdmin):
    list_display = ("project", "computation_type", "result", "created_at")
    list_filter = ("computation_type", "project")
