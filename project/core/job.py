from .models import *
from django.core.mail import send_mail,EmailMessage
from django.conf import settings
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events,DjangoJobStore
from datetime import timedelta , date
import calendar
from openpyxl import  Workbook
from io import BytesIO
from django.db.models import Sum
from django.core.files import File



def send_monthly_report():
    today=date.today()

    previous_month = today.month - 1
    previous_year = today.year
    
    if previous_month == 0:
      previous_month = 12
      previous_year -= 1

    if  not  Liystanumbers.objects.filter(created_at__year=previous_year, created_at__month=previous_month).exists():
     
     # عدد الاشتراكات
     subs_count=Subscription.objects.count()
     #عدد النشطين في الشهر الجدد
     new_active_users = Customer.objects.filter(customer_status='active',created_at__year=previous_year, created_at__month=previous_month).count()
     #عدد غير النشطاء في هذا الشهر
     new_inactive_users = Customer.objects.filter(customer_status='inactive',created_at__year=previous_year,created_at__month=previous_month).count()
     #النشطين القدامى
     old_active_users= Customer.objects.filter(customer_status='active').count() -  new_active_users
     
     #غير النشطين القدامى
     
     old_inactive_users = Customer.objects.filter(customer_status='inactive').count() - new_inactive_users
     #نسبة النشطين في هذا الشهر
     month_actives_percentage = new_active_users / old_active_users * 100 if old_active_users else 0
     #نسبة النشطين من غيرهم
     actives_percentage = ((old_active_users + new_active_users) / (old_inactive_users + new_inactive_users)) * 100 if old_inactive_users or new_inactive_users   else 0
     #نسبة التحول من غير نشط الى نشط
     activetion_converted_percentage = ( new_active_users / (old_inactive_users + new_inactive_users)) * 100 if old_inactive_users or new_inactive_users   else 0
     #عدد الاشتركات النشطة
     active_subscriptions = Subscription.objects.filter(is_active=True).count()
     #نسبة الاشتركات الفعالة من الكل 
     active_subs=active_subscriptions / subs_count * 100 if subs_count else 0  

     #من استخدم الخطة المجانية
     free_users = Customer.objects.filter(has_used_free_trial=True).count()
     #من استخدم المجانية واشترك
     converted_users = Customer.objects.filter(customer_status='active', has_used_free_trial=True).count()
     #النسبة بينهم
     converted_percentage = converted_users / free_users * 100 if free_users else 0
    
     
     #الايرادات الشهرية
     monthly_income = AdminSales.objects.filter(
        created_at__year=previous_year,
        created_at__month=previous_month,
     ).aggregate(total=Sum('profit'))['total'] or 0

     #تكاليف تشغيلية شهرية 
     operations=Coasts.objects.filter(coast_kind='Operations',  created_at__year=previous_year,created_at__month=previous_month)
     operations_amount=0
     if operations: 
      for i in operations:
       if i.created_at.month==previous_month or i.recurring:
          operations_amount += i.amount 
     operations_amount += monthly_income * 0.1

     #نسبة مندوبي المبيعات
     sellers=Coasts.objects.filter(coast_kind='sellermen',  created_at__year=previous_year,created_at__month=previous_month).first()
     seller_amount=sellers.amount if sellers else 0
      

     #تكاليف تسويقية شهرية
     marketing=Coasts.objects.filter(coast_kind='Marketing&sells',  created_at__year=previous_year,created_at__month=previous_month)
     marketing_amount=seller_amount
     if marketing:
      for i in marketing:
       if i.created_at.month==previous_month or i.recurring:
         marketing_amount += i.amount
     
     #هامش الربح
     gross_profit=monthly_income - operations_amount
     #نسبة هامش الربح
     gross_percentage=gross_profit / monthly_income * 100 if monthly_income else 0
     #الربح الصافي 
     net_profit=gross_profit - marketing_amount
     #نسبة الربح الصافي
     net_percentage=net_profit / monthly_income * 100 if monthly_income else 0
     #تكلفة العميل الجديد
     news_coast=marketing_amount / new_active_users if new_active_users else 0 
     
     wb=Workbook()
     ws=wb.active
     ws.title=f"{previous_year}لسنة-{previous_month}-بيانات شهر"
     ws.append(['seller $','news coast $','NP %','NP $','GP %','GP $','sells $','M&S $','operations $','converted  %','free subs','activate %','all actives %','month actives %','olds inactive','olds active','news inactive','news active','active subs %','active subs','all subs'])
     ws.append([seller_amount,news_coast,net_percentage,net_profit,gross_percentage,gross_profit,monthly_income,marketing_amount,operations_amount,converted_percentage,free_users,activetion_converted_percentage,actives_percentage,month_actives_percentage,old_inactive_users,old_active_users,new_inactive_users,new_active_users,active_subs,active_subscriptions,subs_count])
     output=BytesIO()
     wb.save(output)
     output.seek(0)
     filename=f'report_{previous_year}_{previous_month}.xlsx'
     report_date=date(previous_year,previous_month,28)
     report=Liystanumbers.objects.create(
        month_data=File(output,name=filename),
        created_at=report_date
     )
     report.save()

     email=EmailMessage(
       
        subject=f"Liysta report for {previous_month}/{previous_year}",
        body="Hi Mr.Moad this is a report about our results in the last month thank you for your effort.",
        from_email="liystacompany@gmail.com",
        to=["hamodamourad72@gmail.com"],

     )
    
     email.attach(filename, output.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
     email.send()
    else:
       pass    





def clean_cards():
    cards=Paymentcard.objects.filter(is_used=True).delete()

    






def deactivate_users_subs():
    today=date.today()
    subs=Subscription.objects.filter(end_date__lt=today,is_active=True)
    for sub in subs:
        if sub.plan.duration != 'forever':
          customer = sub.customer 
          customer.customer_status = 'inactive'
          customer.save()
        
          sub.is_active=False
          sub.save()
        else:
          sub.end_date = sub.end_date + timedelta(days=10000) 
          sub.save()  
        if  sub.plan.duration == 'free_trial':
         subject="انتهت تجربتك المجانية"
         message = f"""
انتبه {sub.customer.store_ar_name}! ⏳

بطاقة التجسس الخاصة بك على وشك الانتهاء:
- سيتم تعطيل الوصول للأسلحة المتقدمة
- تقارير الاستخبارات ستتوقف
- لكن.. كل بياناتك ستظل آمنة
احصل على خصم عشرين في المئة باستخدام هذا الكوبون:liyfree20
"الآن تعرف الأسرار.. حان وقت التطبيق"
احتفظ بأسلحتك: https://liysta.ly/plans

"التجارب تنتهي.. والخبراء يبقون"
فريق Liystا 🎯
""" 
         send_mail(
          subject,
          message,    
          settings.DEFAULT_FROM_EMAIL,
          [sub.customer.user.email],
          fail_silently=False,
         )
        else:
         subject=" انتهاء الاشتراك"
         message = f"""
{sub.customer.store_ar_name}، القائد العزيز.. ⚠️

درع الحماية الخاص بك على وشك الانتهاء!
- سيتم تعطيل أسلحتك (الميزات) خلال 48 ساعة
- التقارير الاستخباراتية ستتوقف
- المنافسون قد يلاحظون ضعفك!

"لا تدع مملكتك تتعرض للهجوم"
جدد ترسانتك الآن: https://liysta.ly/renew-subscription/{sub.id}

"الأبطال لا يتراجعون.. يجددون عهدهم"
فريق Liystا 🚨
"""
         send_mail(
          subject,
          message,    
          settings.DEFAULT_FROM_EMAIL,
          [sub.customer.user.email],
          fail_silently=False,
         )           


def refresh_tokens():
   darbs=DarbAsabilConnection.objects.all()
   for darb in darbs:
     if darb.should_refresh():
       darb.refreshtoken()
     else:
       pass
   
   

def start():
    scheduler=BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(),"default")
    scheduler.add_job(
        deactivate_users_subs, 
        trigger='cron',
        hour=7,
        minute=0,
        id='deactive_subs',
        replace_existing=True,
    )
    
    scheduler.add_job(
     send_monthly_report,
      trigger='cron',
      hour=3,
      minute=0, 
      id='send_monthly',
      replace_existing=True,
    )
    scheduler.add_job(
      clean_cards,
      trigger='cron',
      hour=2,
      minute=0, 
      id='clean_cards',
      replace_existing=True,
    )

 
