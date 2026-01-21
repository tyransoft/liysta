from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings


def verification(request, user):
    uid=urlsafe_base64_encode(force_bytes(user.id))
    token=default_token_generator.make_token(user)
    domain=get_current_site(request).domain
    link=f"http://{domain}/activate/{uid}/{token}"
    subject="أحدٌ ما يسعى نحو هدفه"
   
    message = f"""
مرحبًا {user.first_name}،

لقد تركت بصمتك الرقمية على منصتنا...
تهانينا! أنت الآن عضو في عالم Liysta السحري 🎩✨

🎯انت لست مجرد رقم بل انت قائد هذه المرحلة سنسادك لتحقق اهدافك عن طريق خدماتنا 
التي ستكون متاحة عندك بجرد الاشتراك او الحصول على تجربة مجانية فريدة
لاتفرط بها فهذ هي الادوات التي ستساعدك لتفوز بالحرب.....فقط تحتاج لبعض الجرئة

"تمنى لك الدمار الايجابي في مشروعك"
ابدأ مغامرتك الآن:
{link}
 
"لقد عثرت على منجم ارباحك"
مع تحيات فريق Liysta 🚀
"""
    send_mail(
    subject,
    message,    
    settings.EMAIL_HOST_USER,
    [user.email],
    fail_silently=False,
    )

    