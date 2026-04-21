from django.contrib.auth.models import User
from django.db import models


class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=120)
    project_code = models.CharField(max_length=50, unique=True)
    company = models.CharField(max_length=120, blank=True)
    station_name = models.CharField(max_length=80, default="TS-08")
    is_connected = models.BooleanField(default=True)
    last_sync = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.project_code})"


class SurveyPoint(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="survey_points")
    point_id = models.CharField(max_length=50)
    description = models.CharField(max_length=120, blank=True)
    code = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    northing = models.DecimalField(max_digits=12, decimal_places=3)
    easting = models.DecimalField(max_digits=12, decimal_places=3)
    elevation = models.DecimalField(max_digits=10, decimal_places=3)
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-captured_at"]

    def __str__(self):
        return self.point_id


class Report(models.Model):
    REPORT_CHOICES = [
        ("daily", "Daily Survey Summary"),
        ("dtm", "DTM Surface Report"),
        ("volume", "Area & Volume Report"),
        ("profile", "Elevation Profile"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="reports")
    title = models.CharField(max_length=120)
    report_type = models.CharField(max_length=20, choices=REPORT_CHOICES)
    description = models.TextField(blank=True)
    is_ready = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
