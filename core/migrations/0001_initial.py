from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("project_code", models.CharField(max_length=50, unique=True)),
                ("company", models.CharField(blank=True, max_length=120)),
                ("description", models.TextField(blank=True)),
                ("location_name", models.CharField(blank=True, max_length=120)),
                ("station_name", models.CharField(default="TS-08", max_length=80)),
                ("is_connected", models.BooleanField(default=True)),
                ("active", models.BooleanField(default=False)),
                ("last_sync", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="projects", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="ComputationRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("computation_type", models.CharField(choices=[("area", "Area"), ("volume", "Volume"), ("distance", "Distance")], max_length=20)),
                ("input_a", models.DecimalField(decimal_places=3, max_digits=12)),
                ("input_b", models.DecimalField(decimal_places=3, max_digits=12)),
                ("input_c", models.DecimalField(decimal_places=3, default=0, max_digits=12)),
                ("result", models.DecimalField(decimal_places=3, max_digits=14)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="computations", to="core.project")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Report",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("report_type", models.CharField(choices=[("daily", "Daily Survey Summary"), ("dtm", "DTM Surface Report"), ("volume", "Area & Volume Report"), ("profile", "Elevation Profile")], max_length=20)),
                ("description", models.TextField(blank=True)),
                ("is_ready", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reports", to="core.project")),
            ],
            options={"ordering": ["title"]},
        ),
        migrations.CreateModel(
            name="SurveyPoint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("point_id", models.CharField(max_length=50)),
                ("description", models.CharField(blank=True, max_length=120)),
                ("code", models.CharField(blank=True, max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("northing", models.DecimalField(decimal_places=3, max_digits=12)),
                ("easting", models.DecimalField(decimal_places=3, max_digits=12)),
                ("elevation", models.DecimalField(decimal_places=3, max_digits=10)),
                ("captured_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="survey_points", to="core.project")),
            ],
            options={"ordering": ["-captured_at"]},
        ),
        migrations.CreateModel(
            name="TelemetrySnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("latitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("longitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("elevation", models.DecimalField(decimal_places=3, max_digits=10)),
                ("heading", models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ("accuracy", models.DecimalField(decimal_places=3, default=0.003, max_digits=6)),
                ("source", models.CharField(default="Simulated Total Station Adapter", max_length=80)),
                ("captured_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="telemetry", to="core.project")),
            ],
            options={"ordering": ["-captured_at"]},
        ),
    ]
