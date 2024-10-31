from datetime import datetime, timedelta

import requests
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import DurationField, ExpressionWrapper, F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.timezone import localtime
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import CreateView
from persiantools.jdatetime import JalaliDate
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from userauths.models import User
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied


from .forms import WorkLogForm
from .models import Leave, WorkLog
from .serializers import (HourlyLeaveSerializer, JalaliLeaveSerializer,
                          LeaveSerializer, WorkLogDaySerializer,
                          WorkLogSerializer, TelegramWorkLogSerializer,
                          TelegramLeaveSerializer, TelegramJalaliLeaveSerializer)




    
class WorkLogCreateView(LoginRequiredMixin, CreateView):
    model = WorkLog
    form_class = WorkLogForm
    template_name = 'worklog/add_work_log.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to add a work log.")
            return redirect(reverse('login'))
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'POST':
            kwargs['instance'] = WorkLog(user=self.request.user)
        return kwargs
    
    def form_valid(self, form):
        try:
            form.instance.user = self.request.user
            self.object = form.save()
            current_month = datetime.now().strftime('%B')
            current_year = datetime.now().year
            current_month_logs = WorkLog.objects.filter(
                user=self.request.user,
                recorded_time__year=current_year,
                recorded_time__month=datetime.now().month
                ).order_by('recorded_time')
            context = self.get_context_data(form=form)
            context['current_month_logs'] = current_month_logs
            context['current_month'] = current_month
            context['current_year'] = current_year
            return self.render_to_response(context)
        except Exception as e:
            messages.error(self.request, f"Error creating work log: {str(e)}")
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('user-worklogs', kwargs={'user_pk': self.request.user.pk})

class WorkLogViewSet(viewsets.ModelViewSet):
    serializer_class = WorkLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if self.action == 'list' and user.is_authenticated:
            return WorkLog.objects.filter(user=user)
        return WorkLog.objects.all()

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except Http404:
            return Response({"error": "Work log not found"}, status=status.HTTP_404_NOT_FOUND)



class WorkLogJalaliMonthlyView(generics.ListAPIView):
    serializer_class = WorkLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        jalali_year = self.kwargs['jalali_year']
        jalali_month = self.kwargs['jalali_month']
        start_date = JalaliDate(jalali_year, jalali_month, 1).to_gregorian()
        end_date = JalaliDate(jalali_year, jalali_month + 1, 1).to_gregorian() - timedelta(seconds=1)
        
        return WorkLog.objects.filter(
            user=user,
            recorded_time__range=(start_date, end_date)
            ).order_by('recorded_time')


    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        total_seconds = 0
        current_start_time = None

        for log in queryset:
            if log.status == 'started':
                current_start_time = log.recorded_time
            elif log.status == 'ended' and current_start_time:
                duration = log.recorded_time - current_start_time
                total_seconds += duration.total_seconds()
                current_start_time = None

        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

        response_data = {
            'work_logs': serializer.data,
            'total_hours': {
                'days': int(days),
                'hours': int(hours),
                'minutes': int(minutes)
            }
        }

        return Response(response_data)


class UserWorkLogListView(viewsets.ModelViewSet):
    serializer_class = WorkLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_pk = self.kwargs['user_pk']
        user = get_object_or_404(User, pk=user_pk)
        return WorkLog.objects.filter(user=user)


class WorkLogDayView(APIView):
    serializer_class = WorkLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id, month, day):
        user = get_object_or_404(User, id=user_id)
        day_start = datetime.strptime(f'{day} {month}', '%d %B').replace(year=datetime.now().year)
        work_logs = WorkLog.objects.filter(
            user=user,
            recorded_time__date=day_start.date()
        ).order_by('recorded_time')

        total_time = timedelta(0)
        start_time = None

        for log in work_logs:
            if log.status == 'started':
                start_time = localtime(log.recorded_time)
            elif log.status == 'ended' and start_time:
                end_time = localtime(log.recorded_time)
                total_time += end_time - start_time
                start_time = None

        total_seconds = int(total_time.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        total_time_str = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"

        serializer = WorkLogDaySerializer({'total_time': total_time_str})
        return Response(serializer.data)


class MonthlyWorkLogView(generics.ListAPIView):
    serializer_class = WorkLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        year = self.kwargs['year']
        month = self.kwargs['month']

        return WorkLog.objects.filter(
            user=user,
            recorded_time__year=year,
            recorded_time__month=month
        ).order_by('recorded_time')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        total_work_duration = timedelta()
        current_start_time = None
        
        for log in queryset:
            if log.status == 'started':
                current_start_time = log.recorded_time
            elif log.status == 'ended' and current_start_time:
                total_work_duration += log.recorded_time - current_start_time
                current_start_time = None

        total_seconds = int(total_work_duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        response_data = {
            'total_work_time': {
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds,
            },
            'work_logs': serializer.data
        }
        return Response(response_data)
