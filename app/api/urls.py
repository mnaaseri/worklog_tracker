from django.urls import include, path, re_path
from rest_framework_simplejwt.views import TokenRefreshView

from userauths import views as userauth_views
from worklog import views as worklog_views


urlpatterns = [
    # User Authentication
    path('user/', include('rest_framework.urls')),
    path('user/token/', userauth_views.MyTokenObtainPairView.as_view()),
    path('user/token/refresh/', TokenRefreshView.as_view()),
    path('user-signup/', userauth_views.UserSignUpView.as_view({'post': 'create'}), name='user-signup'),
    path('telegram/user-signup/', userauth_views.UserSignUpView.as_view({'post': 'create'}), name='telegram-user-signup'),

    # Worklog
    path(
         'worklog/add/<int:user_pk>/',
         worklog_views.WorkLogViewSet.as_view({'post': 'create'}),
         name='worklog-list-create'
         ),
    path(
         'worklog/<int:user_pk>/',
         worklog_views.UserWorkLogListView.as_view({'get': 'list'}),
         name='user-worklogs'
         ),  
    path(
         'worklog/record/<int:pk>/',
         worklog_views.WorkLogViewSet.as_view({
              'get': 'retrieve', 'put': 'update',
              'patch': 'partial_update', 'delete': 'destroy'
              })
         , name='worklog-detail'
         ),
    path(
         'worklog/day/<int:user_id>/<str:month>/<int:day>/',
         worklog_views.WorkLogDayView.as_view(),
         name='worklog-time'
         ),
    path(
         'worklog/monthly/<int:year>/<int:month>/',
         worklog_views.MonthlyWorkLogView.as_view(),
         name='monthly-worklog'
         ),
    path(
         'worklog/jalali/monthly/<int:jalali_year>/<int:jalali_month>/',
         worklog_views.WorkLogJalaliMonthlyView.as_view(),
         name='monthly-worklog'
         ),

    # Leave
    path(
         'leave/add-daily/<int:user_pk>/',
         worklog_views.LeaveCreateView.as_view({'get': 'list', 'post': 'create'}),
         name='add-leave'
         ),
    path('leave/record/<int:pk>/',
         worklog_views.LeaveCreateView.as_view({
              'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
              }), name='leave-detail'
         ),
    path(
         'leave/add-hourly/<int:user_pk>/',
         worklog_views.HourlyLeaveViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='add-leave'),
    path(
         'leave/total/<int:user_id>/<int:month>/',
         worklog_views.UserLeaveCountAPIView.as_view(),
         name='user-leave-count'
         ),
    path(
         'leave/total-hourly/<int:year>/<int:month>/',
         worklog_views.MonthlyHourlyLeaveView.as_view(),
         name='total-monthly-hourly-leave'
         ),
    path(
         'leave/jalali/total-year/<int:jalali_year>/',
         worklog_views.YearlyJalaliLeaveView.as_view(),
         name='total_leave_jalali_year'
         ),
    path(
         'leave/jalali/total-month/<int:jalali_year>/<int:jalali_month>/',
         worklog_views.MonthlyJalaliLeaveView.as_view(),
         name='total_leave_jalali_month'),
    path(
         'leave/jalali/add-daily/<int:user_pk>',
         worklog_views.JalaliLeaveCreateAPIView.as_view({'post': 'create'}),
         name='add_jalali_leave_day'),

   # Telegram
   re_path(
        r'^telegram/worklog/add/(?P<telegram_id>\d+)/$',
        worklog_views.TelegramWorkLogView.as_view({'post': 'create'}),
        name='worklog-telegram-create'
        ),
   re_path(
        r'^telegram/leave/add/(?P<telegram_id>\d+)/$',
        worklog_views.TelegramLeaveView.as_view({'post': 'create'}),
        name='leave-telegram-create'
        ),
     re_path(
     r'^telegram/worklog/jalali/monthly/(?P<telegram_id>\d+)/(?P<jalali_year>\d{4})/(?P<jalali_month>\d{1,2})/$',
     worklog_views.TelegramJalaliMonthlyWorkLogView.as_view({'get': 'list'}),
     name='jalali-monthly-worklog'
     ),
     re_path(
     r'^telegram/leave/jalali/monthly/(?P<telegram_id>\d+)/(?P<jalali_year>\d{4})/(?P<jalali_month>\d{1,2})/$',
     worklog_views.TelegramJalaliMonthlyLeaveView.as_view({'get': 'list'}),
     name='jalali-monthly-leave'
     ),
   
   ]