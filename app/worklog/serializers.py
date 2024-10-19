from datetime import datetime

from persiantools.jdatetime import JalaliDate
from rest_framework import serializers
from userauths.models import User

from worklog.models import Leave, WorkLog

from worklog.validators import validate_leave_overlap, validate_worklog

class WorkLogSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = WorkLog
        fields = '__all__' 
        

class TelegramWorkLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkLog
        fields = ['status', 'comment', 'recorded_time']

    def validate(self, data):
        # Get the telegram_id from the context
        telegram_id = self.context.get('telegram_id')
        # Extract status and recorded_time from the data
        status = data.get('status')
        recorded_time = data.get('recorded_time', datetime.now())  # Default to now if not provided

        # Ensure telegram_id is present
        if not telegram_id:
            raise serializers.ValidationError("Telegram ID is required.")

        # Call the validate_worklog function to perform all necessary validation checks
        validate_worklog(telegram_id, status, recorded_time)

        # Return the validated data
        return data

    def create(self, validated_data):
        # Create the WorkLog instance. The model's save method will handle Jalali date fields.
        work_log = WorkLog.objects.create(**validated_data)
        return work_log

            
class TelegramLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields = ['leave_date', 'start_time', 'end_time', 'reason']
        


class TelegramJalaliLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields = ['leave_date', 'start_time', 'end_time', 'reason']

    def validate(self, data):
        telegram_id = self.context.get('telegram_id')

        if not telegram_id:
            raise serializers.ValidationError("Telegram ID is required.")

        leave_date = data['leave_date']
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        validate_leave_overlap(telegram_id, leave_date, start_time, end_time)

        return data

# class TelegramJalaliLeaveSerializer(serializers.ModelSerializer):
        
#     jalali_leave_date = serializers.CharField(max_length=20, required=True)

#     class Meta:
#         model = Leave
#         fields = ['jalali_leave_date', 'start_time', 'end_time', 'reason']

#     def validate(self, data):
#         # Validate and convert Jalali date to Gregorian
#         try:
#             # Manually parse the Jalali date string
#             jalali_year, jalali_month, jalali_day = map(int, data['jalali_leave_date'].split('-'))
#             jalali_date = JalaliDate(jalali_year, jalali_month, jalali_day)
#             gregorian_date = jalali_date.to_gregorian()
#             data['leave_date'] = gregorian_date
#         except ValueError:
#             raise serializers.ValidationError("Invalid Jalali date format. Use 'YYYY-MM-DD'.")
#         return data

class WorkLogDaySerializer(serializers.Serializer):
    total_time = serializers.CharField()

class LeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields =  '__all__' 


class HourlyLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields = ['user', 'leave_date', 'start_time', 'end_time', 'reason']



class JalaliLeaveSerializer(serializers.ModelSerializer):
        
    jalali_leave_date = serializers.CharField(max_length=20, required=True)

    class Meta:
        model = Leave
        fields = ['user', 'jalali_leave_date', 'start_time', 'end_time', 'reason']

    def validate(self, data):
        # Validate and convert Jalali date to Gregorian
        try:
            # Manually parse the Jalali date string
            jalali_year, jalali_month, jalali_day = map(int, data['jalali_leave_date'].split('-'))
            jalali_date = JalaliDate(jalali_year, jalali_month, jalali_day)
            gregorian_date = jalali_date.to_gregorian()
            data['leave_date'] = gregorian_date
        except ValueError:
            raise serializers.ValidationError("Invalid Jalali date format. Use 'YYYY-MM-DD'.")
        
        return data

    def create(self, validated_data):
        # Remove the jalali_leave_date as it won't be saved directly
        validated_data.pop('jalali_leave_date')
        return super().create(validated_data)

