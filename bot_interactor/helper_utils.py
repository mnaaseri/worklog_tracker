
def format_leave_response(leave_data):
    leave_records = leave_data['leave_records']
    total_days = leave_data['total_days']
    total_hours = leave_data['total_hours']
    total_minutes = leave_data['total_minutes']
    
    message = "Your Leave Days for the Month:\n"
    for leave in leave_records:
        message += f"- {leave['leave_date']} (Reason: {leave['reason']})\n"
    
    message += f"\nTotal Days of Leave: {total_days} days\nTotal Hours of Leave: {total_hours} hours and {total_minutes} minutes"
    return message

def format_worklog_response(worklog_data):
    total_hours = worklog_data['total_hours']
    work_logs = worklog_data['work_logs']
    
    message = "Your Work Logs for the Month:\n"
    for log in work_logs:
        message += f"- {log['status']} at {log['recorded_time']}\n"
    
    message += f"\nTotal Hours Worked: {total_hours['days']} days, {total_hours['hours']} hours, {total_hours['minutes']} minutes"
    return message