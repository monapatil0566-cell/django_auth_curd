from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import UserProfile


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username or not email or not password:
            messages.error(request, "Required fields are missing.")

        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")

        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")

        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")

        elif len(password) < 8:
            messages.error(
                request,
                "Password must contain at least 8 characters."
            )

        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            profile, created = UserProfile.objects.get_or_create(
                user=user
            )
            profile.full_name = full_name
            profile.phone = phone
            profile.address = address
            profile.save()

            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect("dashboard")

    return render(request, "register.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request, username=username, password=password
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Invalid username or password.")

    return render(request, "login.html")


@login_required
def dashboard(request):
    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )
    return render(request,"dashboard.html",
        {"profile": profile}
    )


@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have logged out.")
    return redirect("login")



@login_required
def profile_page(request):
    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    return render(request, "profile.html", {
        "profile": profile,
    })


@login_required
@require_POST
def profile_update(request):
    user = request.user

    profile, created = UserProfile.objects.get_or_create(
        user=user
    )

    email = request.POST.get("email", "").strip()
    full_name = request.POST.get("full_name", "").strip()
    phone = request.POST.get("phone", "").strip()
    address = request.POST.get("address", "").strip()

    if not email:
        messages.error(request, "Email is required.")

    elif User.objects.filter(email=email).exclude(
        pk=user.pk
    ).exists():
        messages.error(
            request, "Email already belongs to another user."
        )

    else:
        user.email = email
        user.save(update_fields=["email"])

        profile.full_name = full_name
        profile.phone = phone
        profile.address = address

        if request.FILES.get("profile_image"):
            profile.profile_image = request.FILES["profile_image"]

        profile.save()

        messages.success(
            request, "Profile updated successfully!"
        )
        return redirect("profile")

    return redirect("profile")


def staff_required(view):
    return login_required(user_passes_test(
        lambda user: user.is_staff
    )(view))


@staff_required
def user_list(request):
    users = User.objects.order_by("-date_joined")
    return render(request, "users.html", {"users": users})


@staff_required
def user_create(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        password = request.POST.get("password", "")

        if not username or not email or not password:
            messages.error(request, "Required fields are missing.")

        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")

        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")

        elif len(password) < 8:
            messages.error(request, "Password must have 8 characters.")

        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            profile, created = UserProfile.objects.get_or_create(
                user=user
            )
            profile.full_name = full_name
            profile.phone = phone
            profile.address = address
            profile.save()

            messages.success(request, "User created successfully!")
            return redirect("user_list")

    return render(
        request,
        "user_form.html",
        {"user_obj": None}
    )


@staff_required
def user_update(request, pk):
    user_obj = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()

        if not username or not email:
            messages.error(request, "All fields are required.")

        elif User.objects.filter(username=username).exclude(
            pk=pk
        ).exists():
            messages.error(request, "Username already exists.")

        elif User.objects.filter(email=email).exclude(
            pk=pk
        ).exists():
            messages.error(request, "Email already exists.")

        else:
            user_obj.username = username
            user_obj.email = email
            user_obj.save()
            messages.success(request, "User updated successfully!")
            return redirect("user_list")

    return render(
        request,
        "user_form.html",
        {"user_obj": user_obj}
    )


@staff_required
@require_POST
def user_delete(request, pk):
    user_obj = get_object_or_404(User, pk=pk)

    if user_obj.pk == request.user.pk:
        messages.error(
            request,
            "You cannot delete your own account here."
        )
    elif user_obj.is_superuser:
        messages.error(
            request,
            "Superuser accounts cannot be deleted here."
        )
    else:
        user_obj.delete()
        messages.success(request, "User deleted successfully!")

    return redirect("user_list")