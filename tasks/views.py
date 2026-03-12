from django.shortcuts import render, redirect, get_object_or_404
from .models import Task, Category
from .forms import TaskForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse

@login_required
def task_list(request):
    """View all tasks with filtering, search, and pagination"""
    
    # Get filter parameters
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    category_id = request.GET.get('category', '')
    sort_by = request.GET.get('sort', 'due_date')
    
    # Base queryset
    tasks = Task.objects.filter(user=request.user)
    
    # Apply search
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Apply status filter
    if status == 'completed':
        tasks = tasks.filter(completed=True)
    elif status == 'pending':
        tasks = tasks.filter(completed=False)
    elif status == 'overdue':
        tasks = tasks.filter(completed=False, due_date__lt=date.today())
    elif status == 'due_today':
        tasks = tasks.filter(completed=False, due_date=date.today())
    elif status == 'due_this_week':
        end_of_week = date.today() + timedelta(days=7)
        tasks = tasks.filter(
            completed=False, 
            due_date__gte=date.today(),
            due_date__lte=end_of_week
        )
    
    # Apply priority filter
    if priority in ['H', 'M', 'L']:
        tasks = tasks.filter(priority=priority)
    
    # Apply category filter
    if category_id:
        tasks = tasks.filter(category_id=category_id)
    
    # Apply sorting
    if sort_by == 'due_date':
        tasks = tasks.order_by('due_date', '-priority')
    elif sort_by == 'priority':
        tasks = tasks.order_by('-priority', 'due_date')
    elif sort_by == 'created':
        tasks = tasks.order_by('-created_at')
    elif sort_by == 'title':
        tasks = tasks.order_by('title')
    
    # Get categories for filter
    categories = Category.objects.all()
    
    # Calculate statistics
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(completed=True).count()
    pending_tasks = tasks.filter(completed=False).count()
    overdue_tasks = tasks.filter(completed=False, due_date__lt=date.today()).count()
    
    # Pagination
    paginator = Paginator(tasks, 10)  # Show 10 tasks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'tasks': page_obj,  # Keep for compatibility
        'categories': categories,
        'query': query,
        'current_status': status,
        'current_priority': priority,
        'current_category': category_id,
        'current_sort': sort_by,
        'stats': {
            'total': total_tasks,
            'completed': completed_tasks,
            'pending': pending_tasks,
            'overdue': overdue_tasks,
        },
        'today': date.today(),
    }
    
    return render(request, 'tasks/task_list.html', context)


@login_required
def add_task(request):
    """Add a new task"""
    
    if request.method == "POST":
        form = TaskForm(request.POST)
        
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            
            messages.success(request, '✅ Task created successfully!')
            
            # Check if this was an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Task created successfully',
                    'task_id': task.id
                })
            
            return redirect('task_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    
    else:
        form = TaskForm()
    
    # Pre-fill category from query param if provided
    category_id = request.GET.get('category')
    if category_id:
        try:
            category = Category.objects.get(id=category_id)
            form.fields['category'].initial = category
        except Category.DoesNotExist:
            pass
    
    context = {
        'form': form,
        'action': 'Add',
        'today': date.today(),
    }
    
    return render(request, 'tasks/add_task.html', context)


@login_required
def edit_task(request, task_id):
    """Edit an existing task"""
    
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Task updated successfully!')
            
            # Check if this was an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Task updated successfully',
                    'task_id': task.id
                })
            
            return redirect('task_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    
    else:
        form = TaskForm(instance=task)
    
    context = {
        'form': form,
        'task': task,
        'action': 'Edit',
        'today': date.today(),
    }
    
    return render(request, 'tasks/edit_task.html', context)


@login_required
def delete_task(request, task_id):
    """Delete a task"""
    
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == "POST":
        task_title = task.title
        task.delete()
        
        messages.success(request, f'🗑 Task "{task_title}" deleted successfully!')
        
        # Check if this was an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Task deleted successfully'
            })
        
        return redirect('task_list')
    
    # GET request - show confirmation page
    context = {
        'task': task
    }
    
    return render(request, 'tasks/delete_task.html', context)


@login_required
def toggle_task_status(request, task_id):
    """Toggle task completion status"""
    
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == "POST":
        task.completed = not task.completed
        task.save()
        
        status = "completed" if task.completed else "pending"
        messages.success(request, f'✅ Task marked as {status}!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'completed': task.completed,
                'message': f'Task marked as {status}'
            })
        
    return redirect('task_list')


@login_required
def bulk_task_action(request):
    """Handle bulk actions on tasks"""
    
    if request.method == "POST":
        action = request.POST.get('action')
        task_ids = request.POST.getlist('task_ids')
        
        if not task_ids:
            messages.warning(request, 'No tasks selected!')
            return redirect('task_list')
        
        tasks = Task.objects.filter(id__in=task_ids, user=request.user)
        
        if action == 'complete':
            count = tasks.update(completed=True)
            messages.success(request, f'✅ {count} task(s) marked as completed!')
        
        elif action == 'pending':
            count = tasks.update(completed=False)
            messages.success(request, f'⏳ {count} task(s) marked as pending!')
        
        elif action == 'delete':
            count = tasks.count()
            tasks.delete()
            messages.success(request, f'🗑 {count} task(s) deleted successfully!')
        
        elif action == 'high_priority':
            count = tasks.update(priority='H')
            messages.success(request, f'⚠️ {count} task(s) updated to High priority!')
        
        elif action == 'medium_priority':
            count = tasks.update(priority='M')
            messages.success(request, f'📊 {count} task(s) updated to Medium priority!')
        
        elif action == 'low_priority':
            count = tasks.update(priority='L')
            messages.success(request, f'📉 {count} task(s) updated to Low priority!')
        
    return redirect('task_list')


@login_required
def task_detail(request, task_id):
    """View task details"""
    
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    context = {
        'task': task,
        'now': timezone.now(),
    }
    
    return render(request, 'tasks/task_detail.html', context)


@login_required
def duplicate_task(request, task_id):
    """Duplicate an existing task"""
    
    original_task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == "POST":
        # Create a copy
        new_task = Task.objects.get(pk=original_task.pk)
        new_task.pk = None  # This creates a new record
        new_task.title = f"{original_task.title} (Copy)"
        new_task.completed = False
        new_task.save()
        
        messages.success(request, f'📋 Task duplicated successfully!')
        
    return redirect('task_list')


@login_required
def category_tasks(request, category_id):
    """View tasks by category"""
    
    category = get_object_or_404(Category, id=category_id)
    tasks = Task.objects.filter(user=request.user, category=category)
    
    context = {
        'tasks': tasks,
        'category': category,
    }
    
    return render(request, 'tasks/category_tasks.html', context)


@login_required
def export_tasks(request):
    """Export tasks to CSV"""
    
    import csv
    from django.http import HttpResponse
    
    tasks = Task.objects.filter(user=request.user)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="my_tasks.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Title', 'Description', 'Priority', 'Category', 'Due Date', 'Status', 'Created At'])
    
    for task in tasks:
        writer.writerow([
            task.title,
            task.description,
            task.get_priority_display(),
            task.category.name if task.category else 'Uncategorized',
            task.due_date,
            'Completed' if task.completed else 'Pending',
            task.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    
    return response