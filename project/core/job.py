from django.utils.timezone import now
from .models import Subscription
from django.core.mail import send_mail
from django.conf import settings
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events,DjangoJobStore


def deactivate_users_subs():
    today=now().date()
    subs=Subscription.objects.filter(end_date__lt=today,is_active=True)
    for sub in subs:
        sub.is_active=False
        sub.save()
        if sub.plan.duration =='تجربة مجانية':
         subject="انتهى تدريبنا المجاني"
         message = f"""
انتبه {sub.customer.store_ar_name}! ⏳

بطاقة التجسس الخاصة بك على وشك الانتهاء:
- سيتم تعطيل الوصول للأسلحة المتقدمة
- تقارير الاستخبارات ستتوقف
- لكن.. كل بياناتك ستظل آمنة

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

def start():
    scheduler=BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(),"default")
    scheduler.add_job(
        deactivate_users_subs, trigger='cron',
        hour=4,
        minute=0,
        id='deactive_subs',
        replace_existing=True
    )
    register_events(scheduler)
    scheduler.start()

