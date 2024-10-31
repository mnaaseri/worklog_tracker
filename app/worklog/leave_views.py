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