import csv
import io
import math
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import FormView
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .forms import ComputationForm, ImportPointsForm, LoginForm, ProjectForm, RegisterForm, SurveyPointForm
from .models import ComputationRun, Project, Report, SurveyPoint, TelemetrySnapshot


class SmartLoginView(LoginView):
    template_name = "core/auth.html"
    authentication_form = LoginForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["register_form"] = RegisterForm()
        context["active_tab"] = "login"
        return context


class RegisterView(FormView):
    template_name = "core/auth.html"
    form_class = RegisterForm

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        project = Project.objects.get_or_create(
            user=user,
            project_code="WEST-RIDGE-001",
            defaults={
                "name": "West Ridge Site",
                "company": "SMART SITE SURVEYS",
                "location_name": "Dar es Salaam",
                "description": "Starter project for topographic capture and terrain modeling.",
                "station_name": "TS-08",
                "is_connected": True,
                "active": True,
            },
        )[0]
        _seed_project_data(project)
        messages.success(self.request, "Account created successfully.")
        return redirect("dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["login_form"] = LoginForm()
        context["active_tab"] = "register"
        return context


class SmartLogoutView(LogoutView):
    pass


def welcome(request):
    return render(request, "core/welcome.html")


def about(request):
    return render(request, "core/about.html")


@login_required
def dashboard(request):
    project = _get_active_project(request.user)
    context = {
        "project": project,
        "project_count": request.user.projects.count(),
        "point_count": project.survey_points.count(),
        "recent_points": project.survey_points.all()[:4],
        "reports": project.reports.all()[:3],
        "latest_telemetry": _latest_telemetry(project),
    }
    return render(request, "core/dashboard.html", context)


@login_required
def projects(request):
    user_projects = request.user.projects.all()
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            if not user_projects.exists():
                project.active = True
            project.save()
            _seed_project_data(project)
            messages.success(request, f"Project {project.name} created.")
            return redirect("projects")
    else:
        form = ProjectForm()

    return render(
        request,
        "core/projects.html",
        {"projects": user_projects, "form": form, "active_project": _get_active_project(request.user)},
    )


@login_required
def select_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, user=request.user)
    request.user.projects.update(active=False)
    project.active = True
    project.save(update_fields=["active", "updated_at"])
    messages.success(request, f"{project.name} is now active.")
    return redirect("dashboard")


@login_required
def survey(request):
    project = _get_active_project(request.user)

    if request.method == "POST" and request.POST.get("form_name") == "capture_point":
        form = SurveyPointForm(request.POST)
        if form.is_valid():
            point = form.save(commit=False)
            point.project = project
            point.save()
            _create_telemetry_from_point(project, point)
            messages.success(request, f"Point {point.point_id} captured.")
            return redirect("survey")
    else:
        latest = project.survey_points.first()
        form = SurveyPointForm(
            initial={
                "point_id": "PT-1042",
                "description": latest.description if latest else "Boundary Peg",
                "code": latest.code if latest else "BND",
                "northing": latest.northing if latest else Decimal("4582.221"),
                "easting": latest.easting if latest else Decimal("1039.744"),
                "elevation": latest.elevation if latest else Decimal("224.671"),
            }
        )

    return render(
        request,
        "core/survey.html",
        {
            "project": project,
            "form": form,
            "latest_points": project.survey_points.all()[:8],
            "latest_telemetry": _latest_telemetry(project),
        },
    )


@login_required
def computations(request):
    project = _get_active_project(request.user)
    result = None

    if request.method == "POST":
        form = ComputationForm(request.POST)
        if form.is_valid():
            computation_type = form.cleaned_data["computation_type"]
            a = form.cleaned_data["input_a"]
            b = form.cleaned_data["input_b"]
            c = form.cleaned_data["input_c"] or Decimal("0")
            result = _run_computation(computation_type, a, b, c)
            ComputationRun.objects.create(
                project=project,
                computation_type=computation_type,
                input_a=a,
                input_b=b,
                input_c=c,
                result=result,
            )
            messages.success(request, f"{computation_type.title()} computation completed.")
    else:
        form = ComputationForm(initial={"computation_type": "area", "input_a": 120.0, "input_b": 45.0})

    return render(
        request,
        "core/computations.html",
        {
            "project": project,
            "form": form,
            "result": result,
            "history": project.computations.all()[:6],
        },
    )


@login_required
def reports(request):
    project = _get_active_project(request.user)
    import_form = ImportPointsForm()
    return render(
        request,
        "core/reports.html",
        {
            "project": project,
            "reports": project.reports.all(),
            "import_form": import_form,
            "point_count": project.survey_points.count(),
            "dtm_summary": _build_dtm_context(project),
        },
    )


@login_required
def import_points(request):
    project = _get_active_project(request.user)
    if request.method != "POST":
        return redirect("reports")

    form = ImportPointsForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "Please choose a CSV file to import.")
        return redirect("reports")

    csv_file = form.cleaned_data["csv_file"]
    decoded = csv_file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    created_count = 0

    for row in reader:
        if not row.get("point_id"):
            continue
        point = SurveyPoint.objects.create(
            project=project,
            point_id=row["point_id"],
            description=row.get("description", ""),
            code=row.get("code", ""),
            notes=row.get("notes", ""),
            northing=Decimal(row.get("northing", "0")),
            easting=Decimal(row.get("easting", "0")),
            elevation=Decimal(row.get("elevation", "0")),
        )
        _create_telemetry_from_point(project, point)
        created_count += 1

    messages.success(request, f"Imported {created_count} survey points.")
    return redirect("reports")


@login_required
def export_points(request):
    project = _get_active_project(request.user)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{project.project_code.lower()}-survey-points.csv"'
    writer = csv.writer(response)
    writer.writerow(["point_id", "description", "code", "notes", "northing", "easting", "elevation", "captured_at"])
    for point in project.survey_points.all():
        writer.writerow(
            [
                point.point_id,
                point.description,
                point.code,
                point.notes,
                point.northing,
                point.easting,
                point.elevation,
                point.captured_at.isoformat(),
            ]
        )
    return response


@login_required
def live_map(request):
    project = _get_active_project(request.user)
    return render(request, "core/live_map.html", {"project": project, "latest_telemetry": _latest_telemetry(project)})


@login_required
def dtm_map(request):
    project = _get_active_project(request.user)
    return render(
        request,
        "core/dtm_map.html",
        {
            "project": project,
            "dtm": _build_dtm_context(project),
        },
    )


@login_required
def live_station_data(request):
    project = _get_active_project(request.user)
    latest = _simulate_live_telemetry(project)
    points = list(
        project.survey_points.values("point_id", "description", "northing", "easting", "elevation")[:20]
    )


@login_required
def report_pdf(request, report_type):
    project = _get_active_project(request.user)
    report = get_object_or_404(Report, project=project, report_type=report_type)
    latest_telemetry = _latest_telemetry(project)
    dtm = _build_dtm_context(project)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{project.project_code.lower()}-{report_type}.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    pdf.setFillColor(colors.HexColor("#083848"))
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#47d6c2"))
    pdf.circle(width - 40 * mm, height - 35 * mm, 18 * mm, fill=1, stroke=0)

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(20 * mm, height - 25 * mm, "SMART SITE APP")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(20 * mm, height - 38 * mm, report.title)

    pdf.setFont("Helvetica", 10)
    pdf.drawString(20 * mm, height - 48 * mm, f"Project: {project.name}")
    pdf.drawString(20 * mm, height - 54 * mm, f"Project Code: {project.project_code}")
    pdf.drawString(20 * mm, height - 60 * mm, f"Generated: {timezone.localtime().strftime('%Y-%m-%d %H:%M')}")

    y = height - 78 * mm
    pdf.setFillColor(colors.HexColor("#f4fbfa"))
    pdf.roundRect(16 * mm, y, width - 32 * mm, 48 * mm, 8 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#10232b"))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(22 * mm, y + 38 * mm, "Survey Summary")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(22 * mm, y + 30 * mm, f"Captured points: {project.survey_points.count()}")
    pdf.drawString(22 * mm, y + 23 * mm, f"Station: {project.station_name}")
    pdf.drawString(22 * mm, y + 16 * mm, f"Live position: {latest_telemetry.latitude}, {latest_telemetry.longitude}")
    pdf.drawString(22 * mm, y + 9 * mm, f"Elevation: {latest_telemetry.elevation} m")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(22 * mm, y - 10 * mm, "DTM Snapshot")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(22 * mm, y - 18 * mm, f"Min elevation: {dtm['min_elevation']} m")
    pdf.drawString(22 * mm, y - 25 * mm, f"Max elevation: {dtm['max_elevation']} m")
    pdf.drawString(22 * mm, y - 32 * mm, f"Relief: {dtm['relief']} m")

    pdf.setStrokeColor(colors.HexColor("#127c7e"))
    pdf.setLineWidth(1.5)
    mesh_origin_x = 22 * mm
    mesh_origin_y = y - 72 * mm
    mesh_width = 120 * mm
    mesh_height = 48 * mm
    pdf.roundRect(mesh_origin_x, mesh_origin_y, mesh_width, mesh_height, 4 * mm, stroke=1, fill=0)
    svg_points = dtm["svg_points"]
    if len(svg_points) >= 2:
        prev = None
        for point in svg_points:
            px = mesh_origin_x + (point["x"] / 100) * mesh_width
            py = mesh_origin_y + (point["y"] / 100) * mesh_height
            if prev:
                pdf.line(prev[0], prev[1], px, py)
            pdf.setFillColor(colors.HexColor("#47d6c2"))
            pdf.circle(px, py, 2.5, fill=1, stroke=0)
            prev = (px, py)

    sidebar_x = 150 * mm
    pdf.setFillColor(colors.white)
    pdf.roundRect(sidebar_x, y - 46 * mm, 38 * mm, 84 * mm, 6 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.HexColor("#10232b"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(sidebar_x + 4 * mm, y + 30 * mm, "Recommendations")
    pdf.setFont("Helvetica", 9)
    recommendations = [
        "Validate coordinate system before field export.",
        "Separate raw observations from derived results.",
        "Replace simulated telemetry with hardware adapter.",
    ]
    line_y = y + 22 * mm
    for line in recommendations:
        pdf.drawString(sidebar_x + 4 * mm, line_y, f"- {line}")
        line_y -= 8 * mm

    pdf.showPage()
    pdf.save()
    return response
    return JsonResponse(
        {
            "project": project.name,
            "station_name": project.station_name,
            "connected": project.is_connected,
            "telemetry": {
                "latitude": float(latest.latitude),
                "longitude": float(latest.longitude),
                "elevation": float(latest.elevation),
                "heading": float(latest.heading),
                "accuracy": float(latest.accuracy),
                "captured_at": latest.captured_at.isoformat(),
                "source": latest.source,
            },
            "points": [
                {
                    "point_id": point["point_id"],
                    "description": point["description"],
                    "northing": float(point["northing"]),
                    "easting": float(point["easting"]),
                    "elevation": float(point["elevation"]),
                }
                for point in points
            ],
        }
    )


def _run_computation(computation_type, a, b, c):
    if computation_type == "area":
        return a * b
    if computation_type == "volume":
        return a * b * c
    return Decimal(str(math.sqrt(float((a * a) + (b * b)))))


def _get_active_project(user):
    project = user.projects.filter(active=True).first()
    if project:
        _seed_project_data(project)
        return project

    project = user.projects.first()
    if project:
        project.active = True
        project.save(update_fields=["active", "updated_at"])
        _seed_project_data(project)
        return project

    project = Project.objects.create(
        user=user,
        name="West Ridge Site",
        project_code=f"WEST-RIDGE-{user.id:03d}",
        company="SMART SITE SURVEYS",
        location_name="Dar es Salaam",
        description="Starter project for topographic capture and terrain modeling.",
        station_name="TS-08",
        is_connected=True,
        active=True,
    )
    _seed_project_data(project)
    return project


def _seed_project_data(project):
    if not project.reports.exists():
        starter_reports = [
            ("Daily Survey Summary", "daily", "Project activity and captured points."),
            ("DTM Surface Report", "dtm", "Surface details and contour outputs."),
            ("Area & Volume Report", "volume", "Cut, fill, and net volume results."),
            ("Elevation Profile", "profile", "Graphical terrain profile."),
        ]
        for title, report_type, description in starter_reports:
            Report.objects.get_or_create(
                project=project,
                title=title,
                defaults={"report_type": report_type, "description": description, "is_ready": True},
            )

    if not project.survey_points.exists():
        seed_points = [
            ("PT-1001", "Benchmark", "BM", Decimal("4580.112"), Decimal("1031.220"), Decimal("223.140")),
            ("PT-1002", "Control Peg", "CTL", Decimal("4581.004"), Decimal("1035.882"), Decimal("223.891")),
            ("PT-1003", "Edge of Road", "RD", Decimal("4583.642"), Decimal("1040.044"), Decimal("224.335")),
        ]
        for point_id, description, code, northing, easting, elevation in seed_points:
            SurveyPoint.objects.create(
                project=project,
                point_id=point_id,
                description=description,
                code=code,
                northing=northing,
                easting=easting,
                elevation=elevation,
                notes="Seeded starter point",
            )

    if not project.telemetry.exists():
        _simulate_live_telemetry(project)


def _latest_telemetry(project):
    latest = project.telemetry.first()
    if latest:
        return latest
    return _simulate_live_telemetry(project)


def _create_telemetry_from_point(project, point):
    latitude = Decimal("-6.792354") + (Decimal(point.northing) - Decimal("4580")) / Decimal("100000")
    longitude = Decimal("39.208328") + (Decimal(point.easting) - Decimal("1030")) / Decimal("100000")
    return TelemetrySnapshot.objects.create(
        project=project,
        latitude=latitude,
        longitude=longitude,
        elevation=point.elevation,
        heading=Decimal("46.5"),
        accuracy=Decimal("0.003"),
        source="Survey Point Capture",
    )


def _simulate_live_telemetry(project):
    latest = project.telemetry.first()
    now = timezone.now()
    base_lat = Decimal("-6.792354")
    base_lng = Decimal("39.208328")

    if latest:
        seconds = Decimal(str((now - latest.captured_at).total_seconds() or 1))
        latitude = Decimal(str(float(latest.latitude) + 0.00001 * math.sin(float(seconds))))
        longitude = Decimal(str(float(latest.longitude) + 0.00001 * math.cos(float(seconds))))
        heading = Decimal(str((float(latest.heading) + 7.5) % 360))
        elevation = latest.elevation + Decimal("0.005")
    else:
        latitude = base_lat
        longitude = base_lng
        heading = Decimal("42.0")
        elevation = Decimal("224.671")

    return TelemetrySnapshot.objects.create(
        project=project,
        latitude=latitude,
        longitude=longitude,
        elevation=elevation,
        heading=heading,
        accuracy=Decimal("0.003"),
        source="Simulated Total Station Adapter",
    )


def _build_dtm_context(project):
    points = list(project.survey_points.order_by("point_id")[:40])
    if not points:
        return {
            "svg_points": [],
            "contours": [],
            "min_elevation": Decimal("0.000"),
            "max_elevation": Decimal("0.000"),
            "relief": Decimal("0.000"),
        }

    min_easting = min(point.easting for point in points)
    max_easting = max(point.easting for point in points)
    min_northing = min(point.northing for point in points)
    max_northing = max(point.northing for point in points)
    min_elevation = min(point.elevation for point in points)
    max_elevation = max(point.elevation for point in points)

    east_range = max(float(max_easting - min_easting), 1.0)
    north_range = max(float(max_northing - min_northing), 1.0)
    elev_range = max(float(max_elevation - min_elevation), 1.0)

    svg_points = []
    for point in points:
        x = ((float(point.easting - min_easting) / east_range) * 86) + 7
        y = 93 - ((float(point.northing - min_northing) / north_range) * 76)
        band = int(((float(point.elevation - min_elevation) / elev_range) * 4)) + 1
        svg_points.append(
            {
                "id": point.point_id,
                "label": point.description or point.point_id,
                "x": round(x, 2),
                "y": round(y, 2),
                "elevation": point.elevation,
                "band": min(band, 5),
            }
        )

    links = []
    for index in range(1, len(svg_points)):
        prev = svg_points[index - 1]
        curr = svg_points[index]
        links.append({"x1": prev["x"], "y1": prev["y"], "x2": curr["x"], "y2": curr["y"]})

    contours = []
    step = elev_range / 4
    for index in range(5):
        level = float(min_elevation) + (step * index)
        contours.append(
            {
                "name": f"Band {index + 1}",
                "elevation": round(level, 3),
                "offset": 18 + (index * 14),
                "opacity": round(0.14 + (index * 0.08), 2),
            }
        )

    return {
        "svg_points": svg_points,
        "links": links,
        "contours": contours,
        "min_elevation": min_elevation,
        "max_elevation": max_elevation,
        "relief": max_elevation - min_elevation,
    }
