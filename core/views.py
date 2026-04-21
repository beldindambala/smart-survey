from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.views.generic import FormView

from .forms import LoginForm, RegisterForm, SurveyPointForm
from .models import Project, Report, SurveyPoint


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
        Project.objects.get_or_create(
            user=user,
            project_code="WEST-RIDGE-001",
            defaults={
                "name": "West Ridge Site",
                "company": "SMART SITE SURVEYS",
                "station_name": "TS-08",
                "is_connected": True,
            },
        )
        _seed_reports(user)
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


@login_required
def dashboard(request):
    project = _get_or_create_default_project(request.user)
    points = project.survey_points.all()[:3]
    reports = project.reports.all()[:4]
    context = {
        "project": project,
        "point_count": project.survey_points.count(),
        "recent_points": points,
        "reports": reports,
    }
    return render(request, "core/dashboard.html", context)


@login_required
def survey(request):
    project = _get_or_create_default_project(request.user)

    if request.method == "POST":
        form = SurveyPointForm(request.POST)
        if form.is_valid():
            point = form.save(commit=False)
            point.project = project
            point.save()
            messages.success(request, f"Point {point.point_id} captured.")
            return redirect("survey")
    else:
        form = SurveyPointForm(
            initial={
                "point_id": "PT-1042",
                "description": "Boundary Peg",
                "code": "BND",
                "northing": Decimal("4582.221"),
                "easting": Decimal("1039.744"),
                "elevation": Decimal("224.671"),
            }
        )

    context = {
        "project": project,
        "form": form,
        "latest_points": project.survey_points.all()[:5],
    }
    return render(request, "core/survey.html", context)


@login_required
def reports(request):
    project = _get_or_create_default_project(request.user)
    return render(
        request,
        "core/reports.html",
        {"project": project, "reports": project.reports.all()},
    )


def _get_or_create_default_project(user):
    project, _ = Project.objects.get_or_create(
        user=user,
        project_code="WEST-RIDGE-001",
        defaults={
            "name": "West Ridge Site",
            "company": "SMART SITE SURVEYS",
            "station_name": "TS-08",
            "is_connected": True,
        },
    )
    _seed_reports(user)
    return project


def _seed_reports(user):
    project = Project.objects.filter(user=user).first()
    if not project:
        return

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
