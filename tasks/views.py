from django.shortcuts import render, redirect, get_object_or_404
from django.template.defaulttags import now
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db.models import Q
from datetime import timedelta


from .models import Task
from .forms import TaskForm
from django.utils import timezone

def task_list(request):
    tasks = Task.objects.all().order_by('due_date')
    return render(request, 'tasks/task_list.html', {'tasks': tasks})


def task_complete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.completed = True
    task.save()
    return redirect('task_list')

def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form, 'edit': True})

def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        task.delete()
        return redirect('task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})

def dashboard(request):
    tasks = Task.objects.all()
    context = {
        'total_tasks': tasks.count(),
        'completed': tasks.filter(completed=True).count(),
        'pending': tasks.filter(completed=False).count(),
        'overdue': tasks.filter(due_date__lt=now(), completed=False).count(),
    }
    return render(request, 'tasks/dashboard.html', context)

from django.contrib.auth.decorators import login_required

@login_required
def task_list(request):
    sort_by = request.GET.get('sort', 'due_date')
    search_query = request.GET.get('q', '')

    tasks = Task.objects.filter(user=request.user)

    if search_query:
        tasks = tasks.filter(Q(title__icontains=search_query))

    if sort_by == 'priority':
        tasks = tasks.order_by('priority', 'due_date')
    else:
        tasks = tasks.order_by('due_date')

    for task in tasks:
        task.is_overdue = not task.completed and task.due_date and task.due_date < timezone.now()

    return render(request, 'tasks/task_list.html', {
        'tasks': tasks,
        'sort_by': sort_by,
        'search_query': search_query,
    })



@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user  # Assign current user
            task.save()
            return redirect('task_list')
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form})

def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('task_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('task_list')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

def task_snooze(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    minutes = int(request.GET.get('minutes', 60))
    task.snoozed_until = timezone.now() + timedelta(minutes=minutes)
    task.reminder_time = task.snoozed_until  # optional: update reminder too
    task.save()
    return redirect('task_list')