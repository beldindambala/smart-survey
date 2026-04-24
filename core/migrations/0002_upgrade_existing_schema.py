import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="description",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="project",
            name="location_name",
            field=models.CharField(blank=True, default="", max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="project",
            name="active",
            field=models.BooleanField(default=False),
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
                (
                    "project",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="telemetry", to="core.project"),
                ),
            ],
            options={"ordering": ["-captured_at"]},
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
                (
                    "project",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="computations", to="core.project"),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
