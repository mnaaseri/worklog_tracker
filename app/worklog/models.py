from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import localtime
from persiantools.jdatetime import JalaliDate
from userauths.models import User


class WorkLog(models.Model): 
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('ended', 'Ended'),
    ]

    recorded_time = models.DateTimeField(null=True, blank=True)
    jalali_date = models.CharField(max_length=20, editable=False) 
    jalali_day_of_week = models.CharField(max_length=9, editable=False)  
    jalali_month = models.CharField(max_length=9, editable=False) 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    day_of_week = models.CharField(max_length=9, editable=False)  
    month = models.CharField(max_length=9, editable=False) 
    comment = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='work_logs')


    def save(self, *args, **kwargs):
        if not self.recorded_time:
            self.recorded_time = datetime.now()
        
        jalali_date = JalaliDate(self.recorded_time)
        self.jalali_date = jalali_date.strftime('%Y-%m-%d')
        self.jalali_day_of_week = jalali_date.strftime('%A')  
        self.jalali_month = jalali_date.strftime('%B') 
        self.day_of_week = self.recorded_time.strftime('%A')
        self.month = self.recorded_time.strftime('%B')
        
        super(WorkLog, self).save(*args, **kwargs)

    def __str__(self):
        return f"Work {self.status} on {self.recorded_time} ({self.day_of_week}, {self.month})"


class Leave(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaves')
    leave_date = models.DateField()
    jalali_leave_date = models.CharField(max_length=20, editable=False)
    jalali_day_of_week = models.CharField(max_length=9, editable=False)  
    jalali_month = models.CharField(max_length=9, editable=False) 
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'leave_date', 'start_time', 'end_time')
    
    
    def save(self, *args, **kwargs):
        # Convert leave_date to Solar Hijri date
        jalali_date = JalaliDate(self.leave_date)
        self.jalali_leave_date = jalali_date.strftime('%Y-%m-%d')
        self.jalali_day_of_week = jalali_date.strftime('%A')
        self.jalali_month = jalali_date.strftime('%B')
        
        super(Leave, self).save(*args, **kwargs)         
    def __str__(self):
        return f"{self.user.username} - {self.leave_date} ({self.start_time} to {self.end_time})"
