from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    # Add color for visual representation
    color = models.CharField(max_length=7, default='#2563eb', help_text='Hex color code')
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def task_count(self):
        """Return number of tasks in this category"""
        return self.task_set.count()
    
    def completed_task_count(self):
        """Return number of completed tasks in this category"""
        return self.task_set.filter(completed=True).count()

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('L', 'Low'),
        ('M', 'Medium'),
        ('H', 'High'),
    ]
    
    PRIORITY_COLORS = {
        'L': '#10b981',  # Green
        'M': '#f59e0b',  # Orange
        'H': '#ef4444',  # Red
    }
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    priority = models.CharField(
        max_length=1,
        choices=PRIORITY_CHOICES,
        default='M'
    )
    
    completed = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Add this
    completed_at = models.DateTimeField(null=True, blank=True)  # Add this
    
    class Meta:
        ordering = ['-priority', 'due_date', 'created_at']  # High priority first, then by due date
    
    def __str__(self):
        return self.title
    
    # Status methods
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and not self.completed:
            return self.due_date < date.today()
        return False
    
    def is_due_today(self):
        """Check if task is due today"""
        if self.due_date and not self.completed:
            return self.due_date == date.today()
        return False
    
    def is_due_tomorrow(self):
        """Check if task is due tomorrow"""
        if self.due_date and not self.completed:
            return self.due_date == date.today() + timedelta(days=1)
        return False
    
    def is_this_week(self):
        """Check if task is due this week"""
        if self.due_date and not self.completed:
            today = date.today()
            end_of_week = today + timedelta(days=(6 - today.weekday()))
            return today <= self.due_date <= end_of_week
        return False
    
    def get_status(self):
        """Get task status as string"""
        if self.completed:
            return 'completed'
        elif self.is_overdue():
            return 'overdue'
        else:
            return 'pending'
    
    def get_status_display(self):
        """Get human-readable status"""
        status_map = {
            'completed': '✅ Completed',
            'overdue': '⚠️ Overdue',
            'pending': '⏳ Pending',
        }
        return status_map.get(self.get_status(), '⏳ Pending')
    
    def get_status_color(self):
        """Get color for status badge"""
        color_map = {
            'completed': '#10b981',
            'overdue': '#ef4444',
            'pending': '#f59e0b',
        }
        return color_map.get(self.get_status(), '#64748b')
    
    # Priority methods
    def get_priority_color(self):
        """Get color for priority badge"""
        return self.PRIORITY_COLORS.get(self.priority, '#64748b')
    
    def get_priority_badge_class(self):
        """Get CSS class for priority badge"""
        return f"priority-{self.priority.lower()}"
    
    # Date formatting methods
    def formatted_due_date(self):
        """Return formatted due date with context"""
        if not self.due_date:
            return "No due date"
        
        if self.is_overdue():
            return f"Overdue! ({self.due_date.strftime('%b %d, %Y')})"
        elif self.is_due_today():
            return f"Today! ({self.due_date.strftime('%b %d, %Y')})"
        elif self.is_due_tomorrow():
            return f"Tomorrow ({self.due_date.strftime('%b %d, %Y')})"
        else:
            return self.due_date.strftime('%b %d, %Y')
    
    def days_until_due(self):
        """Return number of days until due"""
        if self.due_date and not self.completed:
            delta = self.due_date - date.today()
            return delta.days
        return None
    
    def time_remaining_display(self):
        """Human readable time remaining"""
        days = self.days_until_due()
        if days is None:
            return ""
        elif days < 0:
            return f"Overdue by {abs(days)} days"
        elif days == 0:
            return "Due today"
        elif days == 1:
            return "Due tomorrow"
        else:
            return f"{days} days left"
    
    # Completion methods
    def mark_completed(self):
        """Mark task as completed"""
        self.completed = True
        self.completed_at = timezone.now()
        self.save()
    
    def mark_pending(self):
        """Mark task as pending"""
        self.completed = False
        self.completed_at = None
        self.save()
    
    # Category methods
    def get_category_display(self):
        """Return category name or 'Uncategorized'"""
        return self.category.name if self.category else "Uncategorized"
    
    def get_category_color(self):
        """Return category color or default"""
        return self.category.color if self.category and hasattr(self.category, 'color') else '#64748b'

# Optional: Add a Profile model for user preferences
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    default_view = models.CharField(max_length=20, default='all')
    items_per_page = models.IntegerField(default=10)
    email_notifications = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"