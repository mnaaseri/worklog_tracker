# validators.py
from rest_framework import serializers
from .models import Leave, User, WorkLog
from django.utils.timezone import localtime, make_aware, is_naive


def validate_leave_overlap(telegram_id, leave_date, start_time, end_time):
    """
    Validator function to check for overlapping leave times based on telegram_id.
    This function handles full-day leaves, hourly leaves, and checks if a full-day leave exists.
    """
    # Fetch the user based on telegram_id
    try:
        user = User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        raise serializers.ValidationError("User with this telegram_id does not exist.")

    # Fetch existing leaves for the same user on the same date
    existing_leaves = Leave.objects.filter(user=user, leave_date=leave_date)

    # Case 1: Full-Day Leave (start_time and end_time are empty)
    if start_time is None and end_time is None:
        # Check if there are any existing hourly leaves on the same date
        if existing_leaves.exists():
            raise serializers.ValidationError(
                "Cannot add a full-day leave because there are existing leave hours on this day."
            )

    # Case 2: Hourly Leave (start_time and end_time are provided)
    else:
        for leave in existing_leaves:
            # Case 3: Full-Day Leave exists (check if existing leave has no start_time and end_time)
            if leave.start_time is None and leave.end_time is None:
                raise serializers.ValidationError(
                    "Cannot add hourly leaves because there is already a full-day leave on this day."
                )

            # Skip entries with missing start or end times for hourly leave comparison
            if leave.start_time is None or leave.end_time is None:
                continue

            # Compare times only if both are present
            if leave.start_time <= end_time and start_time <= leave.end_time:
                raise serializers.ValidationError(
                    f"Leave overlaps with an existing leave entry "
                    f"from {leave.start_time.strftime('%H:%M')} to {leave.end_time.strftime('%H:%M')}."
                )
                

def validate_worklog(telegram_id, status, recorded_time):
    
        # Fetch the user based on telegram_id
    try:
        user = User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        raise serializers.ValidationError("User with this telegram_id does not exist.")
        
    # Ensure the recorded_time is aware (convert naive datetime to aware if necessary)
    if is_naive(recorded_time):
        recorded_time = make_aware(recorded_time)
    
    # Convert the recorded time to the user's local timezone
    recorded_time = localtime(recorded_time)

    # Get the day start and end (for filtering work logs on the same day)
    day_start = recorded_time.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = recorded_time.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Check for overlapping work logs on the same day
    overlapping_logs = WorkLog.objects.filter(
        user=user,
        recorded_time__range=(day_start, day_end)
    ).exclude(status='ended')  # Ignore 'ended' logs as they are completed

    for log in overlapping_logs:
        log_start_time = log.recorded_time
        log_end_time = log_start_time  # If 'started', it's ongoing

        # If it's an 'ended' log, we consider the recorded time as the end of the work period
        if log.status == 'ended':
            log_end_time = log_start_time  # Adjust accordingly for ended logs

        # Check for overlap with existing logs
        if log_start_time <= recorded_time <= log_end_time:
            raise serializers.ValidationError(f"Work log overlaps with an existing log recorded at {log.recorded_time}.")

    # Get the last work log entry for this user (for sequence validation)
    last_log = WorkLog.objects.filter(user=user).last()

    # Validation: "started" must follow an "ended" session
    if last_log:
        if status == 'started' and last_log.status == 'started':
            raise serializers.ValidationError(f"You have a started work at {last_log.recorded_time} , You must end that first")
        if status == 'ended' and last_log.status == 'ended':
            raise serializers.ValidationError("You must start a work session before ending it.")

    # Validation: First entry of each day must be "started"
    first_log_today = WorkLog.objects.filter(
        user=user,
        recorded_time__range=(day_start, day_end)
    ).order_by('recorded_time').first()

    if not first_log_today and status != 'started':
        raise serializers.ValidationError("The first record of the day must be 'started'.")
    elif first_log_today and recorded_time == first_log_today.recorded_time and status != 'started':
        raise serializers.ValidationError("The first record of the day must be 'started'.")
