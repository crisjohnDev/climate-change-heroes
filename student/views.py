import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, GameStatus
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.models import User

def login_user(request):

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        # =================================================
        # VALIDATION
        # =================================================

        if not username:

            return render(
                request,
                "login.html",
                {
                    "error": "Please enter your username."
                }
            )

        if not password:

            return render(
                request,
                "login.html",
                {
                    "error": "Please enter your password.",
                    "username": username
                }
            )

        # =================================================
        # AUTHENTICATE
        # =================================================

        user = authenticate(
            request,
            username=username,
            password=password
        )

        # =================================================
        # LOGIN SUCCESS
        # =================================================

        if user is not None:

            login(request, user)

            return redirect("dashboard")

        # =================================================
        # LOGIN FAILED
        # =================================================

        return render(
            request,
            "login.html",
            {
                "error": "Invalid username or password.",
                "username": username
            }
        )

    # =====================================================
    # GET REQUEST
    # =====================================================

    return render(
        request,
        "login.html"
    )

def teacher_register(request):

    # =====================================================
    # ALREADY LOGGED IN
    # =====================================================

    if request.user.is_authenticated:

        return redirect("dashboard")


    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )


        # =================================================
        # USERNAME REQUIRED
        # =================================================

        if not username:

            return render(
                request,
                "teacher_register.html",
                {
                    "error": "Teacher username is required.",
                    "username": username,
                }
            )


        # =================================================
        # PASSWORD REQUIRED
        # =================================================

        if not password:

            return render(
                request,
                "teacher_register.html",
                {
                    "error": "Password is required.",
                    "username": username,
                }
            )


        # =================================================
        # CONFIRM PASSWORD REQUIRED
        # =================================================

        if not confirm_password:

            return render(
                request,
                "teacher_register.html",
                {
                    "error": "Please re-enter your password.",
                    "username": username,
                }
            )


        # =================================================
        # PASSWORD MATCH
        # =================================================

        if password != confirm_password:

            return render(
                request,
                "teacher_register.html",
                {
                    "error": "Passwords do not match.",
                    "username": username,
                }
            )


        # =================================================
        # CHECK USERNAME
        # =================================================

        if User.objects.filter(
            username__iexact=username
        ).exists():

            return render(
                request,
                "teacher_register.html",
                {
                    "error": "That teacher username is already taken.",
                    "username": username,
                }
            )


        # =================================================
        # CREATE TEACHER ACCOUNT
        # =================================================

        teacher = User.objects.create_user(
            username=username,
            password=password
        )


        # =================================================
        # TEACHER PERMISSIONS
        # =================================================

        teacher.is_staff = False

        teacher.is_superuser = False

        teacher.save()


        # =================================================
        # LOGIN AUTOMATICALLY
        # =================================================

        login(
            request,
            teacher
        )


        # =================================================
        # DASHBOARD
        # =================================================

        return redirect("dashboard")


    # =====================================================
    # GET
    # =====================================================

    return render(
        request,
        "teacher_register.html"
    )


def logout_user(request):
    logout(request)
    return redirect("login")

# =========================================================
# TEACHER DASHBOARD
# =========================================================

@login_required(login_url="teacher_login")
def dashboardView(request):

    from .models import Student, GameStatus

    teacher = request.user

    students = (
        Student.objects
        .filter(teacher=teacher)
        .select_related("game_status")
        .order_by("-id")
    )

    total_students = students.count()

    games_completed = GameStatus.objects.filter(
        student__teacher=teacher,
        status="completed"
    ).count()

    active_students = GameStatus.objects.filter(
        student__teacher=teacher,
        status="playing"
    ).count()

    context = {
        "students": students,
        "total_students": total_students,
        "games_completed": games_completed,
        "active_students": active_students,
    }

    return render(
        request,
        "pages/dashboard.html",
        context
    )


# =========================================================
# REAL-TIME DASHBOARD DATA
# =========================================================

@login_required(login_url="teacher_login")
@require_GET
def dashboard_live_data(request):

    from .models import Student, GameStatus

    teacher = request.user

    students = (
        Student.objects
        .filter(teacher=teacher)
        .select_related("game_status")
        .order_by("-id")
    )

    total_students = students.count()

    games_completed = GameStatus.objects.filter(
        student__teacher=teacher,
        status="completed"
    ).count()

    active_students = GameStatus.objects.filter(
        student__teacher=teacher,
        status="playing"
    ).count()

    # =====================================================
    # STUDENT DATA
    # =====================================================

    student_data = []

    for student in students:

        game_status = getattr(
            student,
            "game_status",
            None
        )

        game = None

        if game_status:

            game = {
                "status": game_status.status,
                "stage": game_status.stage,
                "monster": game_status.monster,
                "enemy_number": game_status.enemy_number,
                "difficulty": game_status.difficulty or "",
                "hp": game_status.hp,
                "max_hp": game_status.max_hp,
                "score": game_status.score or 0,
                "updated_at": (
                    game_status.updated_at.strftime(
                        "%b %d, %Y %I:%M %p"
                    )
                    if game_status.updated_at
                    else ""
                ),
            }

        student_data.append({
            "id": student.id,
            "name": student.name,
            "grade": student.grade,
            "score": (
                game_status.score
                if game_status
                else 0
            ),
            "game": game,
        })

    # =====================================================
    # LEADERBOARD
    # =====================================================

    leaderboard_queryset = (
        GameStatus.objects
        .filter(
            student__teacher=teacher
        )
        .select_related("student")
        .order_by(
            "-score",
            "student__name"
        )[:10]
    )

    leaderboard_data = []

    for index, game_status in enumerate(
        leaderboard_queryset,
        start=1
    ):

        student = game_status.student

        leaderboard_data.append({
            "rank": index,
            "name": student.name,
            "score": game_status.score or 0,
            "grade": student.grade,
        })

    # =====================================================
    # RESPONSE
    # =====================================================

    return JsonResponse({
        "total_students": total_students,
        "games_completed": games_completed,
        "active_students": active_students,
        "students": student_data,
        "leaderboard": leaderboard_data,
    })

# =========================================================
# DELETE STUDENT
# =========================================================

@login_required
@require_POST
def delete_student(request, student_id):

    student = get_object_or_404(
        Student,
        id=student_id
    )

    student_name = student.name

    student.delete()

    return redirect("dashboard")

@login_required(login_url="teacher_login")
def add_student(request):

    if request.method == "POST":

        name = request.POST.get(
            "name",
            ""
        ).strip()

        grade = request.POST.get(
            "grade",
            ""
        ).strip()


        # =====================================================
        # VALIDATION
        # =====================================================

        if not name:

            return render(
                request,
                "pages/add_student.html",
                {
                    "error": "Student name is required.",
                    "name": name,
                    "grade": grade,
                }
            )


        if not grade:

            return render(
                request,
                "pages/add_student.html",
                {
                    "error": "Grade level is required.",
                    "name": name,
                    "grade": grade,
                }
            )


        # =====================================================
        # CREATE STUDENT
        # =====================================================

        Student.objects.create(
            teacher=request.user,
            name=name,
            grade=grade
        )


        # =====================================================
        # RETURN TO DASHBOARD
        # =====================================================

        return redirect("dashboard")


    return render(
        request,
        "pages/add_student.html"
    )

@csrf_exempt
def check_student(request):

    # =====================================================
    # ONLY POST IS ALLOWED
    # =====================================================

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "message": "POST method required."
        }, status=405)


    try:

        # =================================================
        # READ JSON
        # =================================================

        data = json.loads(
            request.body
        )


        # =================================================
        # GET NAME ONLY
        # =================================================

        student_name = data.get(
            "name",
            ""
        ).strip()


        # =================================================
        # EMPTY NAME
        # =================================================

        if student_name == "":

            return JsonResponse({
                "success": False,
                "message": "Student name is required."
            }, status=400)


        # =================================================
        # CHECK DATABASE
        # =================================================

        student_exists = Student.objects.filter(
            name__iexact=student_name
        ).exists()


        # =================================================
        # REGISTERED
        # =================================================

        if student_exists:

            return JsonResponse({
                "success": True,
                "registered": True,
                "message": "Student registered."
            })


        # =================================================
        # NOT REGISTERED
        # =================================================

        return JsonResponse({
            "success": True,
            "registered": False,
            "message": "Student Not Registered."
        })


    except json.JSONDecodeError:

        return JsonResponse({
            "success": False,
            "message": "Invalid JSON."
        }, status=400)


    except Exception as e:

        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)


# =========================================================
# GAME STATUS API
# =========================================================

@csrf_exempt
def game_status(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "POST method required."
        }, status=405)

    try:

        data = json.loads(request.body)

        student_name = data.get(
            "name",
            ""
        ).strip()

        status_value = data.get(
            "status",
            "playing"
        )

        stage = data.get(
            "stage",
            1
        )

        monster = data.get(
            "monster",
            1
        )

        enemy_number = data.get(
            "enemy_number",
            1
        )

        difficulty = data.get(
            "difficulty",
            ""
        )

        hp = data.get(
            "hp",
            0
        )

        max_hp = data.get(
            "max_hp",
            100
        )

        if student_name == "":
            return JsonResponse({
                "success": False,
                "message": "Student name is required."
            }, status=400)

        valid_statuses = [
            "not_started",
            "playing",
            "paused",
            "game_over",
            "completed"
        ]

        if status_value not in valid_statuses:
            return JsonResponse({
                "success": False,
                "message": "Invalid game status."
            }, status=400)

        try:

            student = Student.objects.get(
                name__iexact=student_name
            )

        except Student.DoesNotExist:

            return JsonResponse({
                "success": False,
                "message": "Student not registered."
            }, status=404)

        game_status_object, created = (
            GameStatus.objects.get_or_create(
                student=student
            )
        )

        game_status_object.status = status_value
        game_status_object.stage = int(stage)
        game_status_object.monster = int(monster)
        game_status_object.enemy_number = int(enemy_number)
        game_status_object.difficulty = str(difficulty)
        game_status_object.hp = int(hp)
        game_status_object.max_hp = int(max_hp)

        game_status_object.save()

        print("================================")
        print("GAME STATUS RECEIVED")
        print("Student:", student.name)
        print("Status:", status_value)
        print("Stage:", stage)
        print("Monster:", monster)
        print("Enemy:", enemy_number)
        print("Difficulty:", difficulty)
        print("HP:", hp, "/", max_hp)
        print("================================")

        return JsonResponse({

            "success": True,

            "message":
                "Game status updated.",

            "student":
                student.name,

            "grade":
                student.grade,

            "status":
                game_status_object.status,

            "stage":
                game_status_object.stage,

            "monster":
                game_status_object.monster,

            "enemy_number":
                game_status_object.enemy_number,

            "difficulty":
                game_status_object.difficulty,

            "hp":
                game_status_object.hp,

            "max_hp":
                game_status_object.max_hp,

            "updated_at":
                game_status_object.updated_at.isoformat()

        })

    except json.JSONDecodeError:

        return JsonResponse({
            "success": False,
            "message": "Invalid JSON."
        }, status=400)

    except ValueError:

        return JsonResponse({
            "success": False,
            "message": "Invalid numeric value."
        }, status=400)

    except Exception as e:

        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)