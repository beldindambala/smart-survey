from django.contrib.auth.models import User
from django.db import models


class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=120)
    project_code = models.CharField(max_length=50, unique=True)
    company = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    location_name = models.CharField(max_length=120, blank=True)
    station_name = models.CharField(max_length=80, default="TS-08")
    is_connected = models.BooleanField(default=True)
    active = models.BooleanField(default=False)
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


class TelemetrySnapshot(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="telemetry")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    elevation = models.DecimalField(max_digits=10, decimal_places=3)
    heading = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    accuracy = models.DecimalField(max_digits=6, decimal_places=3, default=0.003)
    source = models.CharField(max_length=80, default="Simulated Total Station Adapter")
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-captured_at"]

    def __str__(self):
        return f"{self.project.project_code} @ {self.captured_at:%Y-%m-%d %H:%M:%S}"


class ComputationRun(models.Model):
    COMPUTATION_CHOICES = [
        ("area", "Area"),
        ("volume", "Volume"),
        ("distance", "Distance"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="computations")
    computation_type = models.CharField(max_length=20, choices=COMPUTATION_CHOICES)
    input_a = models.DecimalField(max_digits=12, decimal_places=3)
    input_b = models.DecimalField(max_digits=12, decimal_places=3)
    input_c = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    result = models.DecimalField(max_digits=14, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_computation_type_display()} = {self.result}"


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
