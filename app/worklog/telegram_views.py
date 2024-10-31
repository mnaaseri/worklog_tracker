from datetime import datetime, timedelta
import requests

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from persiantools.jdatetime import JalaliDate
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from userauths.models import User
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist

from .models import Leave, WorkLog
from .serializers import (
                          LeaveSerializer,
                          WorkLogSerializer, TelegramWorkLogSerializer,
                          TelegramJalaliLeaveSerializer)



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
        try:
            user = User.objects.get(telegram_id=telegram_id) 
            serializer.save(user=user)
        except ObjectDoesNotExist as exc:
            raise ValidationError({"error": f"User with telegram_id {telegram_id} does not exist."}) from exc
    
    def create(self, request, *args, **kwargs):
        telegram_id = self.kwargs['telegram_id']
        serializer = self.get_serializer(data=request.data, context={'telegram_id': telegram_id})
        try: 
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class TelegramLeaveView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = TelegramJalaliLeaveSerializer

    def get_queryset(self):
        telegram_id = self.kwargs['telegram_id']
        try:
            return Leave.objects.get(telegram_id=telegram_id)
        except ObjectDoesNotExist as exc:
            raise ValidationError({"error": f"No leaves found for telegram_id {telegram_id}."}) from exc


    def perform_create(self, serializer):
        telegram_id = self.kwargs['telegram_id']
        try:
            user = User.objects.get(telegram_id=telegram_id)
            serializer.save(user=user)
        except ObjectDoesNotExist as exc:
            raise ValidationError({"error": f"User with telegram_id {telegram_id} does not exist."}) from exc


    def create(self, request, *args, **kwargs):
        telegram_id = self.kwargs['telegram_id']
        serializer = self.get_serializer(data=request.data, context={'telegram_id': telegram_id})
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

@method_decorator(csrf_exempt, name='dispatch') 
class TelegramJalaliMonthlyWorkLogView(viewsets.ModelViewSet):
    serializer_class = WorkLogSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        telegram_id = self.kwargs['telegram_id']
        jalali_year = int(self.kwargs['jalali_year'])
        jalali_month = int(self.kwargs['jalali_month'])
        
        try:
            start_date = JalaliDate(jalali_year, jalali_month, 1).to_gregorian()
            end_date = JalaliDate(jalali_year, jalali_month + 1, 1).to_gregorian() - timedelta(seconds=1)
            
            user = User.objects.get(telegram_id=telegram_id)
            return WorkLog.objects.filter(
                user=user,
                recorded_time__range=(start_date, end_date)
                ).order_by('recorded_time')
        except ObjectDoesNotExist as exc:
            raise ValidationError({"error": f"User with telegram_id {telegram_id} does not exist."}) from exc
        except ValueError as exc:
            raise ValidationError({"error": "Invalid Jalali date."}) from exc


    def list(self, request, *args, **kwargs):
        try:
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
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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