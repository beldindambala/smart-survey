from django.contrib import admin

from .models import Project, Report, SurveyPoint


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
