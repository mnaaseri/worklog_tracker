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
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from userauths.models import User

from .forms import WorkLogForm
from .models import Leave, WorkLog
from .serializers import (HourlyLeaveSerializer, JalaliLeaveSerializer,
                          LeaveSerializer, WorkLogDaySerializer,
                          WorkLogSerializer, TelegramWorkLogSerializer,
                          TelegramLeaveSerializer, TelegramJalaliLeaveSerializer)




@method_decorator(csrf_exempt, name='dispatch')
class TelegramWorkLogView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = TelegramWorkLogSerializer

    def get_queryset(self):
        telegram_id = self.kwargs['telegram_id']
        recorded_time = self.kwargs['recorded_time']
        return WorkLog.objects.filter(user__telegram_id=telegram_id)

    def perform_create(self, serializer):
        telegram_id = self.kwargs['telegram_id']
        user = User.objects.get(telegram_id=telegram_id) 
        serializer.save(user=user)
    
    def create(self, request, *args, **kwargs):
        telegram_id = self.kwargs['telegram_id']
        # Pass telegram_id in the context
        serializer = self.get_serializer(data=request.data, context={'telegram_id': telegram_id})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@method_decorator(csrf_exempt, name='dispatch') 
class TelegramLeaveView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = TelegramJalaliLeaveSerializer
    
    def get_queryset(self):
        telegram_id = self.kwargs['telegram_id']
        return Leave.objects.get(telegram_id=telegram_id)
    
    def perform_create(self, serializer):
        telegram_id = self.kwargs['telegram_id']
        user = User.objects.get(telegram_id=telegram_id)
        serializer.save(user=user)
    
    def create(self, request, *args, **kwargs):
        telegram_id = self.kwargs['telegram_id']
        # Pass telegram_id in the context
        serializer = self.get_serializer(data=request.data, context={'telegram_id': telegram_id})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@method_decorator(csrf_exempt, name='dispatch') 
class TelegramJalaliMonthlyWorkLogView(viewsets.ModelViewSet):
    serializer_class = WorkLogSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        telegram_id = self.kwargs['telegram_id']
        jalali_year = int(self.kwargs['jalali_year'])
        jalali_month = int(self.kwargs['jalali_month'])
        start_date = JalaliDate(jalali_year, jalali_month, 1).to_gregorian()
        end_date = JalaliDate(jalali_year, jalali_month + 1, 1).to_gregorian() - timedelta(seconds=1)
        
        return WorkLog.objects.filter(
            user = User.objects.get(telegram_id=telegram_id),
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

@method_decorator(csrf_exempt, name='dispatch') 
class TelegramJalaliMonthlyLeaveView(viewsets.ModelViewSet):
    serializer_class = LeaveSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        telegram_id = self.kwargs['telegram_id']
        jalali_year = int(self.kwargs['jalali_year'])
        jalali_month = int(self.kwargs['jalali_month'])
        user = User.objects.get(telegram_id=telegram_id)
        queryset = Leave.objects.filter(user=user)

        filtered_queryset = []
        for leave in queryset:
            leave_jalali_date = JalaliDate.to_jalali(leave.leave_date)
            if leave_jalali_date.year == jalali_year and leave_jalali_date.month == jalali_month:
                filtered_queryset.append(leave)
        
        return filtered_queryset

    def list(self, request, *args, **kwargs):  
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        total_days = 0
        total_hours = timedelta()
        
        for leave in queryset:
            leave_jalali_date = JalaliDate.to_jalali(leave.leave_date)
            
            if leave_jalali_date.year == int(self.kwargs['jalali_year']) and leave_jalali_date.month == int(self.kwargs['jalali_month']):
                if leave.start_time and leave.end_time:
                    start_datetime = datetime.combine(leave.leave_date, leave.start_time)
                    end_datetime = datetime.combine(leave.leave_date, leave.end_time)
                    total_hours += (end_datetime - start_datetime)
                else:
                    total_days += 1

        total_hours_in_hours = total_hours.total_seconds() // 3600
        total_minutes_in_minutes = (total_hours.total_seconds() % 3600) // 60

        return Response({
            'leave_records': serializer.data,
            'total_days': total_days,
            'total_hours': int(total_hours_in_hours),
            'total_minutes': int(total_minutes_in_minutes),
            'jalali_year': self.kwargs['jalali_year'],
            'jalali_month': self.kwargs['jalali_month']
        })

    
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()



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


class LeaveCreateView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LeaveSerializer

    def get_queryset(self):
        user = self.request.user
        if self.action == 'list' and user.is_authenticated:
            return Leave.objects.filter(user=user)
        return Leave.objects.all()
    
    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()
    
class UserLeaveCountAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LeaveSerializer
    
    def get(self, request, user_id, month):
        user = get_object_or_404(User, pk=user_id)
        leave_count = Leave.objects.filter(user=user, leave_date__month=month).count()
        
        return Response({'user_id': user_id,
                         'month': month, 'total_leaves': leave_count},
                        status=status.HTTP_200_OK)
    
class HourlyLeaveViewSet(viewsets.ModelViewSet):
    queryset = Leave.objects.all()
    serializer_class = HourlyLeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MonthlyHourlyLeaveView(generics.ListAPIView):
    serializer_class = HourlyLeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        year = self.kwargs['year']
        month = self.kwargs['month']

        return Leave.objects.filter(
            user=user,
            leave_date__year=year,
            leave_date__month=month,
            start_time__isnull=False,
            end_time__isnull=False
        ).order_by('leave_date', 'start_time')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        total_leave_duration = queryset.aggregate(
            total_duration=Sum(
                ExpressionWrapper(
                    F('end_time') - F('start_time'),
                    output_field=DurationField()
                )
            )
        )['total_duration'] or timedelta()

        total_leave_hours = total_leave_duration.total_seconds() / 3600
        response_data = {
            'total_leave_hours': total_leave_hours,
            'leaves': serializer.data
        }
        
        return Response(response_data)
    
class YearlyJalaliLeaveView(APIView):
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request, jalali_year):
        leaves = Leave.objects.all()
        total_days = 0
        total_hours = timedelta()

        for leave in leaves:
            leave_jalali_date = JalaliDate.to_jalali(leave.leave_date)
            
            if leave_jalali_date.year == int(jalali_year):
                total_days += 1
                if leave.start_time and leave.end_time:
                    start_datetime = datetime.combine(leave.leave_date, leave.start_time)
                    end_datetime = datetime.combine(leave.leave_date, leave.end_time)
                    total_hours += (end_datetime - start_datetime)

        total_hours_in_hours = total_hours.total_seconds() / 3600

        return Response({
            'total_days': total_days,
            'total_hours': total_hours_in_hours,
            'jalali_year': jalali_year
        })

class MonthlyJalaliLeaveView(APIView):
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request, jalali_year, jalali_month):
        user = request.user
        leaves = Leave.objects.filter(user=user)
        total_days = 0
        total_hours = timedelta()
        
        for leave in leaves:
            leave_jalali_date = JalaliDate.to_jalali(leave.leave_date)
            
            if leave_jalali_date.year == int(jalali_year) and leave_jalali_date.month == int(jalali_month):
                if leave.start_time and leave.end_time:
                    start_datetime = datetime.combine(leave.leave_date, leave.start_time)
                    end_datetime = datetime.combine(leave.leave_date, leave.end_time)
                    total_hours += (end_datetime - start_datetime)
                else:
                    total_days += 1

        total_hours_in_hours = total_hours.total_seconds() // 3600
        total_minutes_in_minutes = (total_hours.total_seconds() % 3600) // 60

        return Response({
            'total_days': total_days,
            'total_hours': int(total_hours_in_hours),
            'total_minutes': int(total_minutes_in_minutes),
            'jalali_year': jalali_year,
            'jalali_month': jalali_month
        })

class JalaliLeaveCreateAPIView(viewsets.ModelViewSet):
    serializer_class = JalaliLeaveSerializer
    permission_class = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if self.action == 'list' and user.is_authenticated:
            return Leave.objects.filter(user=user)
        return Leave.objects.all()
    
    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    