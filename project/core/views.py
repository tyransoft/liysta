from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from .models import *
from .forms import *
from django.http import Http404, HttpResponse
from django.utils.timezone import localdate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Sum,F, ExpressionWrapper,DecimalField,Avg,IntegerField
from datetime import date
from django.db.models.functions import ExtractMonth
from django.core.mail import send_mail
from .utils import verification
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import transaction
from io import BytesIO
from openpyxl import Workbook
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify

#guest user and so on


def home(request):
    plans=Plan.objects.all()
    clints = OurCustomer.objects.all()
    if request.user.is_authenticated and not request.user.is_superuser :
     customer=Customer.objects.get(user=request.user)
     if customer.has_any_subscription:
      sub=Subscription.objects.get(customer=customer)
     else:
      sub=None
         
         
    
    else:
     sub=None
     
    return render(request,'home/index.html',{'plans':plans,'our_customers':clints,'sub':sub if sub else None})

def about(request):
    return render(request,'about.html')
def terms(request):
    return render(request,'terms.html')
def privacy(request):
    return render(request,'privacy.html')
def learn(request):
    return render(request,'learn.html')
def plan_list(request):
    plans = Plan.objects.all()
    return render(request, 'plan_list.html', {'plans': plans})


#admin views 

@staff_member_required
def generate_cards_view(request):
    if request.method == "POST":
        number_of_cards = int(request.POST.get('number_of_cards'))  
        value = int(request.POST.get('value'))  
        cards = Paymentcard.generate_cards(number_of_cards, value)
        wb=Workbook()
        ws=wb.active
        ws.title='بطاقات الدفع'
        ws.append(['الكود','القيمة'])
        for card in cards:
            ws.append([card.code,card.value])
        output=BytesIO()
        wb.save(output)
        output.seek(0)
        filename = "cards.xlsx"
        response = HttpResponse(
                    output,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
     
       
    
    return render(request, 'generate_cards.html')


@staff_member_required
def card_list_view(request):
    value_filter = None
    is_used_filter = None

    if request.method == "POST":
        value_filter = request.POST.get('value')
        is_used_filter = request.POST.get('is_used')
    

    if value_filter and not is_used_filter:
        cards = Paymentcard.objects.filter(value=value_filter)  
    
    elif is_used_filter and not value_filter:
        is_used_filter = is_used_filter.lower() == 'true'  
        cards = Paymentcard.objects.filter(is_used=is_used_filter)  
    elif value_filter and is_used_filter:
        is_used_filter = is_used_filter.lower() == 'true'  
        cards = Paymentcard.objects.filter(is_used=is_used_filter,value=value_filter) 
    else:
        cards=Paymentcard.objects.all()
    
    cards_pg=Paginator(cards,20)
    page_number=request.GET.get('page')
    cards_list=cards_pg.get_page(page_number)    
    return render(request, 'paymentcards.html', {'cards': cards_list})


@staff_member_required
def add_plan(request):
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('control_dashboard')  
    else:
        form = PlanForm()
    return render(request, 'add_plan.html', {'form': form})

@staff_member_required
def update_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if request.method == 'POST':
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            return redirect('control_dashboard')  
    else:
        form = PlanForm(instance=plan)
    return render(request, 'add_plan.html', {'form': form, 'plan': plan})

@staff_member_required
def delete_plan(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if request.method == 'POST':
        plan.delete()
        return redirect('control_dashboard')   
    return render(request, 'delete_plan.html', {'plan': plan})


@staff_member_required
def add_discount(request):
    if request.method == 'POST':
        form = DiscountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة التخفيض بنجاح.')
            return redirect('control_dashboard') 
        
    else:
        form = DiscountForm()
    return render(request, 'add_discount.html', {'form': form})

@staff_member_required
def edit_discount(request, discount_id):
    discount = get_object_or_404(Discount, id=discount_id)
    if request.method == 'POST':
        form = DiscountForm(request.POST, instance=discount)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل التخفيض بنجاح.')
            return redirect('control_dashboard')
    else:
        form = DiscountForm(instance=discount)
    return render(request, 'add_discount.html', {'form': form, 'discount': discount})

@staff_member_required
def delete_discount(request, discount_id):
    discount = get_object_or_404(Discount, id=discount_id)
    discount.delete()
    messages.success(request, 'تم حذف التخفيض بنجاح.')
    return redirect('control_dashboard')

@staff_member_required
def add_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة الكوبون بنجاح.')
            return redirect('coupon_list')  
        
    else:
        form = CouponForm()
    return render(request, 'add_coupon.html', {'form': form})

@staff_member_required
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل الكوبون بنجاح.')
            return redirect('coupon_list')
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'add_coupon.html', {'form': form, 'coupon': coupon})

@staff_member_required
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    messages.success(request, 'تم حذف الكوبون بنجاح.')
    return redirect('coupon_list')


@staff_member_required
def add_clint(request):
    if request.method == 'POST':
        form = OurCustomerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة العميل بنجاح.')
            return redirect('control_dashboard') 
        
    else:
        form = OurCustomerForm()
    return render(request, 'add_clint.html', {'form': form})

@staff_member_required
def edit_clint(request, clint_id):
    clint = get_object_or_404(OurCustomer, id=clint_id)
    if request.method == 'POST':
        form = OurCustomerForm(request.POST, request.FILES, instance=clint)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل العميل بنجاح.')
            return redirect('control_dashboard')
    else:
        form = OurCustomerForm(instance=clint)
    return render(request, 'add_clint.html', {'form': form, 'clint': clint})


@staff_member_required
def delete_clint(request, clint_id):
    clint = get_object_or_404(OurCustomer, id=clint_id)
    clint.delete()
    messages.success(request, 'تم حذف العميل بنجاح.')
    return redirect('/')


@staff_member_required
def clint_list(request):
    clints = OurCustomer.objects.all()
    return render(request, 'clint_list.html', {'clints': clints})

@staff_member_required
def discount_list(request):
    discount =Discount.objects.all()
    return render(request, 'discount_list.html', {'discounts': discount})

@staff_member_required
def coupon_list(request):
    coupons = Coupon.objects.all()
    return render(request, 'coupon_list.html', {'coupons': coupons})


@staff_member_required
def statistics_dashboard(request):
    today = timezone.now().date()
    
    active_users = Customer.objects.filter(customer_status='active').count()
    inactive_users = Customer.objects.filter(customer_status='inactive').count()
    subscriptions_count = Subscription.objects.count()
    active_subscriptions = Subscription.objects.filter(is_active=True).count()
    free_users = Customer.objects.filter(has_used_free_trial=True).count()
    currentfree_users = Customer.objects.filter(customer_status='inactive', has_used_free_trial=True).count()
    converted_users = Customer.objects.filter(customer_status='active', has_used_free_trial=True).count()
    converted_percentage = converted_users / free_users * 100 if free_users else 0
    
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    monthly_income = AdminSales.objects.filter(
        created_at__year=now.year,
        created_at__month=now.month
    ).aggregate(total=Sum('profit'))['total'] or 0
    
    yearly_income = AdminSales.objects.filter(
        created_at__year=now.year
    ).aggregate(total=Sum('profit'))['total'] or 0

    visit_exp = ExpressionWrapper(
        F('visits_count'),
        output_field=IntegerField()
    )

    visits = {
        'total': MenuStatistics.objects.all().aggregate(total=Sum(visit_exp))['total'] or 0,
        'month': MenuStatistics.objects.filter(date__gte=start_of_month).aggregate(total=Sum(visit_exp))['total'] or 0,
    }

    orders_stats = {
        'total': Order.objects.count(),
        'pending': Order.objects.filter(status='pending').count(),
        'delivered': Order.objects.filter(status='delivered').count(),
    }
    
    monthly_labels = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                      'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']

    monthly_sales = [0] * 12
    current_year = now.year

    sales_data = AdminSales.objects.filter(
        created_at__year=current_year,
    ).annotate(
        month=ExtractMonth('created_at')
    ).values('month').annotate(
        total_sales=Sum('profit'),
    ).order_by('month')

    for data in sales_data:
        month_index = data['month'] - 1
        monthly_sales[month_index] = float(data['total_sales'] or 0)

    context = {
        'active_users': active_users,
        'inactive_users': inactive_users,
        'subscriptions_count': subscriptions_count,
        'active_subscriptions': active_subscriptions,
        'monthly_income': monthly_income,
        'yearly_income': yearly_income,
        'orders_stats': orders_stats,
        'months': monthly_labels,
        'monthly_sales': monthly_sales,
        'free_users': free_users,
        'converted_users': converted_users,
        'converted_per': converted_percentage,
        'currentfree_users': currentfree_users,
        'visits': visits['total'],
        'month_visits': visits['month'],
        'current_year': current_year,
    }
    
    return render(request, 'statistics_dashboard.html', context)

@staff_member_required
def dashboard_view(request):
    context = {
        'cards_count': Paymentcard.objects.count(),
        'plans_count': Plan.objects.count(),
        'discounts_count': Discount.objects.count(),
        'coupons_count': Coupon.objects.count(),
        'clients_count': OurCustomer.objects.count(),
        'customers_count': Customer.objects.count(),

    }
    return render(request, 'control_dashboard.html', context)

def customer_list_view(request):
    today=timezone.now().date()
    today_joined=Customer.objects.filter(created_at=today)
    new_customer_pg=Paginator(today_joined,15)
    page_number=request.GET.get('page')
    new_customers=new_customer_pg.get_page(page_number)
    
    status_filter=None
    kind_filter=None
    freeplan_filter=None

    if request.method =='POST':
        status_filter=request.POST.get('status')
        kind_filter=request.POST.get('kind')
        freeplan_filter=request.POST.get('freeplan')

    if status_filter and kind_filter and freeplan_filter:
        all_customers=Customer.objects.filter(customer_status=status_filter,store_kind=kind_filter,has_used_free_trial=freeplan_filter)
    elif status_filter and not kind_filter and  freeplan_filter:
        all_customers=Customer.objects.filter(customer_status=status_filter)
    elif not status_filter and  kind_filter and  freeplan_filter:
        all_customers=Customer.objects.filter(customer_status=status_filter)
    elif status_filter and  kind_filter and not freeplan_filter:
        all_customers=Customer.objects.filter(customer_status=status_filter)
    elif status_filter and not kind_filter and not freeplan_filter:
        all_customers=Customer.objects.filter(customer_status=status_filter)                                
    
    elif status_filter and not kind_filter and not freeplan_filter:
        all_customers=Customer.objects.filter(customer_status=status_filter)
    elif  kind_filter and not status_filter and not freeplan_filter:
        all_customers=Customer.objects.filter(store_kind=kind_filter)
    elif  freeplan_filter and not status_filter and not kind_filter:
        all_customers=Customer.objects.filter(store_kind=kind_filter)    
    
    else:
        all_customers=Customer.objects.all()
    
    customer_pg=Paginator(all_customers,20)
    page_number=request.GET.get('page')
    customers=customer_pg.get_page(page_number)
    

    context = {
        'new_customers':new_customers,
        'customers':customers,

    }
    return render(request, 'customer_list.html', context)


#for user (subscription,authentication ......etc)



def register_customer(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        store_ar_name = request.POST.get('store_ar_name')
        store_en_name = request.POST.get('store_en_name')
        store_kind = request.POST.get('store_kind')
        location_url = request.POST.get('location_url')

        if not first_name or not email or not password or not phone or not store_ar_name or not store_en_name or not store_kind:
            messages.error(request, 'نرجوا منك تعبئة كامل البيانات')
            return redirect('register-customer')

        if User.objects.filter(username=email).exists():
            messages.error(request, 'عنوان البريد الالكتروني مستخدم حاول تسجيل الدخول')
            return redirect('register-customer')
        if  Customer.objects.filter(store_en_name=store_en_name).exists():
            messages.error(request, 'لسم المتجر باللغة الانجليزية مستخدم من قبل اجعله فريدا وحاول مجددا')
            return redirect('register-customer')       
        user = User.objects.create_user(
            username=email, email=email, password=password, 
            first_name=first_name,is_active=False)

        if user:
                customer = Customer.objects.create(
                    user=user,
                    phone=phone,
                    store_ar_name=store_ar_name,
                    store_en_name=store_en_name,
                    customer_status='inactive',
                    store_kind=store_kind,
                    location_url =location_url 

                             
                )
                customer.save()
           
                verification(request,user)

                return redirect('email_sent')
            
        messages.error(request, 'لم يتم تسجيلك حاول مرة اخرى')
        return redirect('register-customer')

    return render(request, 'register_customer.html')


def activate_user(request,uidb64,token):
    try:
      uid=urlsafe_base64_decode(uidb64).decode()
      user=User.objects.get(id=uid)
    except:     

      user=None
    if user and default_token_generator.check_token(user,token):
        user.is_active=True
        user.save()
      
        if user:
            login(request,user)
            messages.success(request, 'اهلا بك في عالمنا ,لبدأ رحلتك معنا يجب عليك شح محفظتك تواصل معنا للمزيد!')
            return redirect('/')
        else:
          messages.error(request, 'لم يتم تسجيلك حاول مرة اخرى')
          return redirect('register-customer')
    else:
        return HttpResponse('رابط التفعيل غير صالح')

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  
            return redirect('home')  
        else:
            messages.error(request, "بيانات الدخول غير صحيحة.")  
    return render(request, 'login.html') 

def email_sent(request):
    return render(request,'email_sent.html')


def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def wallet_charging(request):
 if request.method == 'POST':
    if request.user.is_authenticated:
 
      customer=Customer.objects.get(user=request.user)
      if customer:
        card_code = request.POST.get('code')
        card=Paymentcard.objects.get(code=card_code)
        if card:
            if card.is_used == False:
                customer.wallet= customer.wallet + card.value
                customer.save()
                card.is_used=True
                card.save()
                messages.success(request, f'تم  شحن محفظتك بقيمة {card.value}')
                return redirect('/')
            
            messages.error(request, 'رقم بطاقة التعبئة هذه مستعمل مسبقا  يرجى التاكد من صحته والمحاولة مجددا')
            return redirect('wallet_charging')
        messages.error(request, 'الرقم السري غير صحيح')
        return redirect('wallet_charging')
      messages.error(request, 'لم نتعرف عليك كعميل حاول مجددا')
      return redirect('/')
    messages.error(request, 'لم نتعرف عليك كعميل حاول مجددا')
    return redirect('login')

 return render(request, 'wallet_charging.html') 

@login_required
def apply_coupon(request):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            coupon_code = data.get('coupon_code')
            plan_id = data.get('plan_id')
            
            plan = Plan.objects.get(id=plan_id)
            customer = Customer.objects.get(user=request.user)
            
            try:
                coupon = Coupon.objects.get(
                    code=coupon_code,
                    is_active=True
                )
                final_price = plan.get_discounted_price_with_coupon(coupon_code)
                
                return JsonResponse({
                    'valid': True,
                    'final_price': final_price,
                    'message': 'تم تطبيق كود الخصم بنجاح!'
                })
            except Coupon.DoesNotExist:
                return JsonResponse({
                    'valid': False,
                    'message': 'كود الخصم غير صالح أو منتهي الصلاحية'
                })
                
        except Exception as e:
            return JsonResponse({
                'valid': False,
                'message': 'حدث خطأ أثناء معالجة الطلب'
            })
    
    return JsonResponse({
        'valid': False,
        'message': 'طلب غير صالح'
    })

@login_required
def buy_plan(request, plan_id):
    if request.method == 'POST':
        if request.user.is_authenticated:
            customer = Customer.objects.get(user=request.user)
            plan = Plan.objects.get(id=plan_id)
            now = timezone.now()
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            year=now.year
            if Subscription.objects.filter(customer=customer, is_active=True).exists():
                messages.error(request, 'لديك اشتراك فعال بالفعل')
                return redirect('/')
            coupon_code = request.POST.get('coupon_code')

            final_price = plan.get_discounted_price_with_coupon(coupon_code)

            if customer.wallet >= final_price:
                if Subscription.objects.filter(customer=customer, is_active=False).exists():
                    
                 subscription = Subscription.objects.get(customer=customer)
                 subscription.plan=plan
                 subscription.sub_price=plan.price
                 subscription.start_date=timezone.now()
                 subscription.final_price=final_price
                 subscription.is_active=True
                 subscription.save()
                else:
                 
                 subscription = Subscription.objects.create(
                     customer=customer,
                     plan=plan,
                     sub_price=plan.price,
                     final_price=final_price,              
                     
                     )
                 subscription.save()
                   
                
                if coupon_code:
                    try:
                        coupon = Coupon.objects.get(code=coupon_code)
                        subscription.coupon = coupon
                        subscription.save()
                        coupon.record_usage(final_price)
                    except Coupon.DoesNotExist:
                        pass
                try:
                 admin=AdminSales.objects.filter(created_at__month=start_of_month,created_at__year=year)
                
                 admin.profit += float(final_price)
                 admin.save() 
                except:
                 admin=AdminSales.objects.create(profit=final_price)
                 admin.save()
                customer.wallet -= final_price
                customer.customer_status = 'active'
                customer.save()
                subject="لقد اشتريت منجم ارباحك"
                
                message = f"""
تهانينا {customer.user.first_name}! 🎉

لقد أصبحت رسميًا قائدًا في جيش Liysta 💂‍♂️
- جميع الأسلحة (أدواتنا) أصبحت تحت تصرفك
- تقارير الاستخبارات (الأرباح) ستصلك يوميًا
- أنت الآن محمي بدرع التوصيل الذكي

"الدمار الإيجابي يبدأ من هنا..."
نحن سعداء بقرارك هذا ومتحمسون لنرى نجاحك معنا 
انطلق!

"الانتصارات تبدأ بقرار.. وأنت قد اتخذته"
فريق Liysta 🛡️
"""
                send_mail(
                  subject,
                  message,    
                  settings.DEFAULT_FROM_EMAIL,
                  [customer.user.email],
                  fail_silently=False,
                )
                messages.success(request, f'تم شراء الاشتراك بنجاح!')
                if Subscription.objects.filter(customer=customer, is_active=False).exists():

                 return redirect('home')
                else:
                 return redirect('menu_setup')

            else:
                messages.error(request, 'رصيدك غير كافٍ لإتمام عملية الشراء')
                return redirect('wallet_charging')
        else:
            return redirect('user_login')

    plan = Plan.objects.get(id=plan_id)
    customer = Customer.objects.get(user=request.user) if request.user.is_authenticated else None
    
    context = {
        'plan': plan,
        'customer': customer,
        'final_price': plan.get_discounted_price()    }
    return render(request, 'buy_plan.html', context)
    
     

@login_required
def start_free_trial(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'يجب تسجيل الدخول أولاً')
        return redirect('login')
    
    customer = Customer.objects.get(user=request.user)
    today=timezone.now().date()

    if Subscription.objects.filter(customer=customer, plan__duration='free_trial', end_date__lt=today).exists():
        messages.warning(request, 'لقد استخدمت التجربة المجانية مسبقاً')
        return redirect('/')  
    elif Subscription.objects.filter(customer=customer, plan__duration='free_trial', end_date__gt=today).exists():
        messages.warning(request, 'لقد استخدمت التجربة المجانية مسبقاً')
        return redirect('menu_setup')  
        
    try:
        free_plan = Plan.objects.get(duration='free_trial')
    except Plan.DoesNotExist:
        messages.error(request, 'خطأ في النظام، يرجى المحاولة لاحقاً')
        return redirect('/')
    
    subscription = Subscription(
        customer=customer,
        plan=free_plan,
        sub_price=0,
        final_price=0,
        is_free=True
    )
    subscription.save()
    subject=" لقد حصلت على بطاقة التجسس! "
    
    message = f"""
    
{subscription.customer.user.first_name}،  مرحبا بك🕵️‍♂️

تهانينا! هذه فرصتك ل:
- اختراق أسرار إدارة المتاجر الناجحة
- تجربة جميع الأسلحة السرية (مجانًا!)
-  كامل لمدة 30 يومًا

"الدمار الإيجابي يبدأ بالتدريب..."

استمتع باستخدام منصتنا  كما تحب نتمنى ان تساعدنا بمشاركة تجربتك معنا

"المجاني اليوم.. سيكون غدًا أغلى ما تملك"
فريق Liystا 🔐
"""
    send_mail(
    subject,
    message,    
    settings.DEFAULT_FROM_EMAIL,
    [customer.user.email],
    fail_silently=False,
    )    
    messages.success(request,'تم تفعيل التجربة المجانية بنجاح!')
    return redirect('menu_setup') 



@login_required
def add_product_view(request, menu_id):
    menu = get_object_or_404(Menu, id=menu_id)

    if request.user != menu.customer.user:
        messages.error(request, 'لا تملك صلاحية الوصول إلى هذه القائمة.')
        return redirect('customer_dashboard') 

    try:
        sub = Subscription.objects.get(customer=menu.customer)
    except Subscription.DoesNotExist:
        messages.error(request, 'لا يوجد اشتراك لهذا العميل. يرجى الاشتراك أولاً.')
        return redirect('customer_dashboard') 

    products_count = Products.objects.filter(menu=menu).count()
    form = ProductForm(request.POST or None, request.FILES or None, customer_instance=menu.customer)
    
    if sub.plan.product_count <= products_count:
        messages.error(request, 'لا يمكنك إضافة المزيد من المنتجات (وصلت إلى الحد الذي تسمح به الباقة الخاصة بك).')
        return redirect('customer_dashboard')

    if request.method == 'POST':
        if form.is_valid():
            product = form.save(commit=False)
            product.menu = menu 
            product.save()
            messages.success(request, 'تم إضافة المنتج بنجاح.')
            return redirect('customer_dashboard')
    return render(request, 'add_product.html', {
        'form': form,
        'menu': menu
    })

@login_required
def update_product_view(request, product_id):
    product = Products.objects.get(id=product_id)
    customer=Customer.objects.get(user=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product,customer_instance=customer)
        if form.is_valid():
       
            form.save()
            messages.success(request, 'تم تعديل المنتج بنجاح.')
            return redirect('customer_dashboard')
    else:
        form = ProductForm(instance=product,customer_instance=customer)
    
    return render(request, 'add_product.html', {'form': form, 'product': product})

@login_required
def delete_product_view(request, product_id):
    if request.method == 'POST':

      product = Products.objects.get(id=product_id)
      product.delete()
      return redirect('customer_dashboard')  
    return render(request, 'delete_product.html')
@login_required
def add_cpdiscount(request, menu_id):
    menu = Menu.objects.get(id=menu_id)

    if request.user != menu.customer.user:
        messages.error(request, 'لا تملك صلاحية إضافة تخفيضات لهذه القائمة.')
        return redirect('customer_dashboard')

    if request.method == 'POST':
        form = CPDiscountForm(request.POST, menu_instance=menu)
        if form.is_valid():
            products = form.cleaned_data['products']  
            percentage = form.cleaned_data['percentage']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            
            for product in products:
                discount, created = CPDiscount.objects.update_or_create(
                    product=product, 
                    menu=menu,
                    defaults={
                        'percentage': percentage,
                        'start_date': start_date,
                        'end_date': end_date,
                    }
                )
                print(f"تم {'إنشاء' if created else 'تحديث'} خصم للمنتج: {product.name}")
            
            messages.success(request, f'تم إضافة الخصم لـ {len(products)} منتج بنجاح')
            return redirect('customer_dashboard')
    else:
        form = CPDiscountForm(menu_instance=menu)

    return render(request, 'add_cpdiscount.html', {'form': form, 'menu': menu})
@login_required
def edit_cpdiscount(request, cpdiscount_id):
    discount = CPDiscount.objects.get(id=cpdiscount_id)
    if request.method == 'POST':
        form = CPDForm(request.POST, instance=discount)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل التخفيض بنجاح.')
            return redirect('customer_dashboard')
    else:
        form = CPDForm(instance=discount)
    return render(request, 'home/edit_cp.html', {'form': form, 'discount': discount})

@login_required
def delete_cpdiscount(request, cpdiscount_id):
    if request.method == 'POST':

     discount = get_object_or_404(CPDiscount, id=cpdiscount_id)
     discount.delete()
     messages.success(request, 'تم حذف التخفيض بنجاح.')
     return redirect('customer_dashboard')
    return render(request, 'delete_product.html')

@login_required
def add_city_view(request, menu_id):
    menu = get_object_or_404(Menu, id=menu_id)
    
    if request.method == 'POST':
        form = CityForm(request.POST)
        
        if form.is_valid():
            city = form.save(commit=False)  
            city.menu = menu  
            city.save() 
            messages.success(request, 'تم إضافة المدينة  بنجاح')
            return redirect('customer_dashboard')
    else:
        form = CityForm()
    
    return render(request, 'add_city.html', {
        'form': form,
        'menu': menu
    })
@login_required
def update_city_view(request, city_id):
    city = City.objects.get(id=city_id)
    
    if request.method == 'POST':
        form =CityForm(request.POST, instance=city)
        if form.is_valid():
       
            form.save()
            return redirect('customer_dashboard')
    else:
        form = CityForm(instance=city)
    
    return render(request, 'add_city.html', {'form': form, 'city': city})

@login_required
def delete_city_view(request, city_id):
    if request.method == 'POST':

      city = City.objects.get(id=city_id)
      city.delete()
      return redirect('customer_dashboard')  
    return render(request, 'delete_product.html')


@login_required
def add_catogery_view(request, menu_id):
    menu = get_object_or_404(Menu, id=menu_id)

    if request.user != menu.customer.user:
        messages.error(request, 'لا تملك صلاحية الوصول لإضافة فئات لهذه القائمة.')
        return redirect('customer_dashboard') 

    if request.method == 'POST':
        form = CatogeryForm(request.POST)

        if form.is_valid():
            catogery = form.save(commit=False)
            catogery.customer = menu.customer
            catogery.save()
            messages.success(request, 'تم إضافة الفئة بنجاح.')
            return redirect('customer_dashboard') 
    else:
        form = CatogeryForm()

    return render(request, 'add_catogery.html', {
        'form': form,
        'menu': menu,
    })


@login_required
def update_catogery_view(request, catogery_id):
    catogery = get_object_or_404(Catogery, id=catogery_id)

    if request.user != catogery.customer.user:
        messages.error(request, 'لا تملك صلاحية تعديل هذه الفئة.')
        return redirect('customer_dashboard') 

    if request.method == 'POST':
        form = CatogeryForm(request.POST, instance=catogery)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث الفئة بنجاح.')
            return redirect('customer_dashboard') 
    else:
        form = CatogeryForm(instance=catogery)

    return render(request, 'add_catogery.html', {
        'form': form,
        'catogery': catogery,
    })


@login_required
def delete_catogery_view(request, catogery_id):
    catogery = get_object_or_404(Catogery, id=catogery_id)

    if request.user != catogery.customer.user:
        messages.error(request, 'لا تملك صلاحية حذف هذه الفئة.')
        return redirect('customer_dashboard') 

    if request.method == 'POST':
        catogery.delete()
        messages.success(request, 'تم حذف الفئة بنجاح.')
        return redirect('customer_dashboard') 

    return render(request, 'delete_product.html')



@login_required
def menu_setup(request):
   if not request.user.is_authenticated:
        return redirect('user_login')   
   try:    
     customer = Customer.objects.get(user=request.user)
     menu=Menu.objects.get(customer=customer)
     messages.error(request, 'لديك صفحة بالفعل!')
     return redirect('customer_dashboard')
   except:
    if request.method == 'POST':
        logo = request.FILES.get('logo')
        second_color = request.POST.get('second_color')
        desc = request.POST.get('desc')
        image = request.FILES.get('image')

        recivieing = request.POST.get('recivieing')

        menu = Menu(
            customer=customer,
            logo=logo,
            image=image,
            desc=desc,
            second_color=second_color,
            recivieing=recivieing
        )
        menu.save()
        
        return redirect('choose_template', menu_id=menu.id)
    
    return render(request, 'menu_setup.html' )

@login_required
def preview_template(request):
    template_name = request.GET.get('template', 'template1')
    
    return render(request, f'p_{template_name}.html')

@login_required
def choose_template(request, menu_id):
    if request.method == 'POST':
        selected_template = request.POST.get('selected_template')  
        try:
            menu = Menu.objects.get(id=menu_id)
            
            if selected_template:
                menu.template = selected_template
                menu.save()
                
                messages.success(request, 'تم تحديث القالب بنجاح!')
                return redirect('customer_dashboard')
                
        except Menu.DoesNotExist:
            messages.error(request, 'لم يتم العثور على القائمة المطلوبة')
            return redirect('home')
    
    return render(request, 'choose_template.html', {
        'menu_id': menu_id
    })


@login_required
def edit_customer_data(request):
    try:
        clint = Customer.objects.get(user=request.user)

        if request.method == "POST":
            form = CustomerForm(request.POST, instance=clint)
            
            if form.is_valid():
                changed = form.changed_data
                form.save()

                if 'store_en_name' in changed:
                    clint.store_slug = slugify(clint.store_en_name)
                    clint.save()
                    menu = Menu.objects.get(customer=clint)
                    menu.generate_qr_code()
                    
                    menu.save()

                messages.success(request, 'تم تعديل بياناتك بنجاح!')
                return redirect('customer_dashboard')
            else:
                messages.error(request, 'يرجى تصحيح الأخطاء أدناه.')
        else:
            form = CustomerForm(instance=clint)
        
        return render(request, 'update_cust.html', {'form': form, 'customer': clint})
      
    except Customer.DoesNotExist:
        messages.error(request, 'لم يتم العثور على بيانات العميل.')
        return redirect('customer_dashboard')
    except Exception as e:
        messages.error(request, f'حدث خطأ: {str(e)}')
        return redirect('customer_dashboard')

@login_required
def edit_menu(request, menu_id):
    menu = get_object_or_404(Menu, id=menu_id)
    
    if menu.customer.user != request.user:
        raise Http404("ليس لديك صلاحية لتعديل هذه القائمة")

    if request.method == 'POST':
        form = MenuForm(request.POST, request.FILES, instance=menu)

        if form.is_valid():
            updated_menu = form.save(commit=False)
            template_choice = request.POST.get('template')
            if template_choice:
                updated_menu.template = template_choice
            updated_menu.save()
            messages.success(request, 'تم تحديث القائمة بنجاح')
            return redirect('customer_dashboard')
        else:
            messages.error(request, 'حدث خطأ في تحديث القائمة')
    else:
        form = MenuForm(instance=menu)

    context = {
        'form': form,
        'menu': menu
    }

    
    return render(request, 'edite_menu.html', context)






@login_required
def customer_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('user_login')

    try:
        customer = Customer.objects.get(user=request.user)
        menu = Menu.objects.get(customer=customer)
        subscription = Subscription.objects.get(customer=customer)
        catogerys=Catogery.objects.filter(customer=customer)
        if subscription.end_date <= timezone.now().date():
            subscription.is_active = False
            subscription.save()
            subscription.customer.status = "inactive"
            subscription.customer.save()

        today = date.today()
        total_days = (subscription.end_date - subscription.start_date).days
        remaining_days = max(0, (subscription.end_date - today).days)
        remaining_percentage = (remaining_days / total_days * 100) if total_days > 0 else 0

        total_circumference = 440
        stroke_dashoffset = total_circumference - (total_circumference * remaining_percentage / 100)

        statistics = MenuStatistics.objects.filter(menu=menu, date=today).first()

        visit_exp = ExpressionWrapper(
            F('visits_count'),
            output_field=IntegerField()
        )

        total_visits={
            'total':MenuStatistics.objects.filter(menu=menu).aggregate(total=Sum(visit_exp))['total'] or 0,
        }

        products = Products.objects.filter(menu=menu)
        cities = City.objects.filter(menu=menu)
        cpds = CPDiscount.objects.filter(menu=menu)

        menu.average_rating = Reviews.objects.filter(menu=menu).aggregate(
            Avg('rating'))['rating__avg'] or 0

        context = {
            'customer': customer,
            'menus': menu,
            'catogerys':catogerys,
            'statistics': statistics,
            'subscription': subscription,
            'remaining_days': remaining_days,
            'remaining_percentage': remaining_percentage,
            'stroke_dashoffset': stroke_dashoffset,
            'products': products,
            'citys': cities,
            'cpds':cpds,
            'total_visits':total_visits['total']
        }

        if subscription.plan.ordering:
            now = timezone.now()
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            current_year = now.year

            orders = {
                'new': Order.objects.filter(menu=menu, status='pending'),
                'indeliver': Order.objects.filter(menu=menu, status='indeliver'),
                'delivered': Order.objects.filter(menu=menu, status='delivered'),
            }

            sales_exp = ExpressionWrapper(
                F('sales_total'),
                output_field=DecimalField()
            )
            profit_exp = ExpressionWrapper(
                F('profit_total'),
                output_field=DecimalField()
            )

            sales_stats = {
                'total': Order.objects.filter(menu=menu,status='delivered').aggregate(total=Sum(sales_exp))['total'] or 0,
                'daily': Order.objects.filter(menu=menu,status='delivered' ,created_at__gte=start_of_day).aggregate(total=Sum(sales_exp))['total'] or 0,
                'monthly': Order.objects.filter(menu=menu,status='delivered' ,created_at__gte=start_of_month).aggregate(total=Sum(sales_exp))['total'] or 0,
            }

            profit_stats = {
                'total': Order.objects.filter(menu=menu,status='delivered').aggregate(profit=Sum(profit_exp))['profit'] or 0,
                'daily': Order.objects.filter(menu=menu,status='delivered' ,created_at__gte=start_of_day).aggregate(profit=Sum(profit_exp))['profit'] or 0,
                'monthly': Order.objects.filter(menu=menu,status='delivered' ,created_at__gte=start_of_month).aggregate(profit=Sum(profit_exp))['profit'] or 0,
            }

            months_labels = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                          'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']

            monthly_sales = [0] * 12
            monthly_profits = [0] * 12

            sales_data = Order.objects.filter(
                menu=menu,  
                created_at__year=current_year,
                status='delivered'
            ).annotate(
                month=ExtractMonth('created_at')
            ).values('month').annotate(
                total_sales=Sum(sales_exp),
                total_profit=Sum(profit_exp)
            ).order_by('month')

            for data in sales_data:
                month_index = data['month'] - 1
                monthly_sales[month_index] = float(data['total_sales'] or 0)
                monthly_profits[month_index] = float(data['total_profit'] or 0)

            context.update({
                'orders': orders,
                'total_sales': sales_stats['total'],
                'monthly_sales_value': sales_stats['monthly'],
                'total_profit': profit_stats['total'],
                'monthly_profit': profit_stats['monthly'],
                'monthly_sales': monthly_sales,
                'monthly_profits': monthly_profits,
                'months': json.dumps(months_labels),  
            })
        if subscription.plan.review:
            reviews = Reviews.objects.filter(menu=menu)
            context['reviews'] = reviews
            context['reviews_count'] = reviews.count()

        return render(request, 'customer_dashboard.html', context)

    except Customer.DoesNotExist:
        return redirect('user_login')
    except Menu.DoesNotExist:
        return redirect('/')
    except Subscription.DoesNotExist:
        return redirect('/')
    
def manege_order(request,menu_id):
   orders=Order.objects.filter(menu=menu_id)

   if request.method =='POST':
     date=request.POST.get('date')
     number=request.POST.get('number')
     if date and number:
       orders=Order.objects.filter(menu=menu_id,created_at=date,ordernumber=number)
     elif date and not number:     
       orders=Order.objects.filter(menu=menu_id,created_at=date)
     elif not date and  number:     
       orders=Order.objects.filter(menu=menu_id,ordernumber=number)
          
   context={
        'orders':orders,
        'menu_id':menu_id

    }
   return render(request, 'manege_orders.html', context)
def edite_order(request,order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    cities = City.objects.filter(menu=order.menu)
    
    context = {
        'order': order,
        'order_items': order_items,
        'cities': cities,
        'status_choices': Order.STATUS_CHOICES
    }
    return render(request, 'edite_order.html', context)

def update_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        order.customer_name = request.POST.get('customer_name')
        order.customer_phone = request.POST.get('customer_phone')
        
        delivery_address_id = request.POST.get('delivery_address')
        if delivery_address_id:
            order.delivery_address = get_object_or_404(City, id=delivery_address_id)
            
        order.notes = request.POST.get('notes')
        order.status = request.POST.get('status')
        
        order_items = OrderItem.objects.filter(order=order)
        total_sales = 0
        
        try:
            with transaction.atomic():
                for key in request.POST.keys():
                    if key.startswith('remove_'):
                        item_id = key.split('_')[1]
                        try:
                            item = OrderItem.objects.get(id=item_id, order=order)
                            product = item.product
                            product.quantity += item.quantity
                            product.save()
                            item.delete()
                            messages.success(request, f'تم إزالة {product.name} من الطلب وإرجاع الكمية إلى المخزون')
                        except OrderItem.DoesNotExist:
                            pass
                
                for item in order_items:
                    quantity_field = f"quantity_{item.id}"
                    
                    if OrderItem.objects.filter(id=item.id).exists():
                        if quantity_field in request.POST:
                            new_quantity = int(request.POST.get(quantity_field))
                            
                            if new_quantity != item.quantity:
                                quantity_diff = new_quantity - item.quantity
                                product = item.product
                                
                                if quantity_diff > 0:  
                                    if quantity_diff <= product.quantity:
                                        product.quantity -= quantity_diff
                                        product.save()
                                        item.quantity = new_quantity
                                        item.save()
                                        messages.success(request, f'تم تحديث كمية {product.name} وتقليل المخزون')
                                    else:
                                        messages.error(request, f'لا يوجد مخزون كافٍ من {product.name}. المتاح: {product.quantity}')
                                        return redirect('edite_order', order_id=order.id)
                                else: 
                                    product.quantity += abs(quantity_diff)
                                    product.save()
                                    item.quantity = new_quantity
                                    item.save()
                                    messages.success(request, f'تم تحديث كمية {product.name} وإضافة الفرق إلى المخزون')
                        
                        item.refresh_from_db() 
                        total_sales += item.get_final_price()
                
                order.sales_total = total_sales
                order.save()
                messages.success(request, 'تم تحديث الطلب بنجاح')
                return redirect('manege_order', menu_id=order.menu.id)
                
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء تحديث الطلب: {str(e)}')
        
        return redirect('edite_order', order_id=order.id)
    
    return redirect('manege_order', menu_id=order.menu.id)

def update_menu_statistics(menu):
    today = localdate()
    stat, created = MenuStatistics.objects.get_or_create(menu=menu, date=today)
    stat.visits_count += 1
    stat.save()

def menu_page_view(request, store_slug):

    menu =get_object_or_404(Menu,customer__store_slug=store_slug)
    subscription = Subscription.objects.get(customer=menu.customer)
    categories=Catogery.objects.filter(customer=menu.customer)
    menu.average_rating = Reviews.objects.filter(menu=menu).aggregate(
        Avg('rating')
    )['rating__avg'] or 0
    
    category=None
    if request.method =='GET':
        category=request.GET.get('category')
    if category:
     products = Products.objects.filter(menu=menu,catogery__id=category)
    else:
     products = Products.objects.filter(menu=menu)

    for product in products:
        if product.available_sizes:
         product.sizes_list = [s.strip() for s in product.available_sizes.split('،') if s.strip()]    
        if product.available_colors:
         product.colors_list = [s.strip() for s in product.available_colors.split('،') if s.strip()]    
        
 
    cities = City.objects.filter(menu=menu) 
    menu.review_count = Reviews.objects.filter(menu=menu).count()

    if menu:
        update_menu_statistics(menu)
    
    context = {
        'menu': menu,
        'products': products,
        'menu_id': menu.id,
        'cities': cities,  
        'categories':categories,
        'revewing': subscription.plan.review,
        'ordering': subscription.plan.ordering,
        'subscription':subscription,
    }
    return render(request, f'{menu.template}.html', context)
    
@login_required
def renew_subscription(request, subscription_id):
    sub=Subscription.objects.get(id=subscription_id)
    plan =sub.plan
    customer = Customer.objects.get(user=request.user)

    if request.method == 'POST':
        if request.user.is_authenticated:
            customer = Customer.objects.get(user=request.user)
            
            now = timezone.now()
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            year=now.year

            coupon_code = request.POST.get('coupon_code')

            final_price = plan.get_discounted_price_with_coupon(coupon_code)

            if customer.wallet >= final_price:
                if Subscription.objects.filter(customer=customer, is_active=False).exists():
                    
                 sub.final_price=final_price
                 sub.is_active=True
                 sub.start_date=timezone.now().date()
                 sub.save()

                   
                
                if coupon_code:
                    try:
                        coupon = Coupon.objects.get(code=coupon_code)
                        sub.coupon = coupon
                        sub.save()
                        coupon.record_usage(final_price)
                    except Coupon.DoesNotExist:
                        pass
                try:
                 admin=AdminSales.objects.filter(created_at__month=start_of_month,created_at__year=year)
                
                 admin.profit += float(final_price)
                 admin.save() 
                except:
                 admin=AdminSales.objects.create(profit=final_price)
                 admin.save()         
                customer.wallet -= final_price
                customer.customer_status = 'active'
                customer.save()
                subject="أنت معنا مجددا"
                
                message = f"""
تهانينا {customer.user.first_name}! 🎉

يسعدنا أنك جددت الثقة بنا وهذا يحملنا مسؤولية كبيرة  جدا

"الدمار  يبدأ من هنا..."
نحن سعداء بقرارك هذا ومتحمسون لنرى نجاحك معنا 
انطلق!

"الانتصارات تبدأ بقرار.. وأنت قد اتخذته"
فريق Liysta 🛡️
"""
                send_mail(
                  subject,
                  message,    
                  settings.DEFAULT_FROM_EMAIL,
                  [customer.user.email],
                  fail_silently=False,
                )
                messages.success(request, f'تم تجديد  الاشتراك بنجاح!')

                return redirect('customer_dashboard')

            else:
                messages.error(request, 'رصيدك غير كافٍ لإتمام عملية الشراء')
                return redirect('wallet_charging')
        else:
            return redirect('user_login')

    
    context = {
        'sub':sub,
        'plan': plan,
        'customer': customer,
        'final_price': plan.get_discounted_price()    }
    return render(request, 'buy_plan.html', context)
    
     

@csrf_exempt
def create_order(request):
    if request.method == 'POST':
        try:
            customer_name = request.POST.get('customer_name')
            customer_phone = request.POST.get('customer_phone')
            delivery_address = request.POST.get('delivery_address')
            type = request.POST.get('type')

            notes = request.POST.get('notes')
            menu = request.POST.get('menu_id')
            menu_id=Menu.objects.get(id=menu)
            if not all([customer_name, customer_phone, menu]):
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields'
                }, status=400)
            
            order_data_str = request.POST.get('order_data')
            if not order_data_str:
                return JsonResponse({
                    'success': False,
                    'error': 'Order data is missing'
                }, status=400)
                
            order_data = json.loads(order_data_str)
            items = order_data.get('items', [])
            
            if not items:
                return JsonResponse({
                    'success': False,
                    'error': 'No items in the order'
                }, status=400)
            
            today=timezone.now().date()
            number=Order.objects.filter(menu=menu_id,created_at=today).last()
            if number:
             num=number.ordernumber + 1
            else:
             num=1   
            order = Order.objects.create(
                customer_name=customer_name,
                customer_phone=customer_phone,
                delivery_address_id=delivery_address if delivery_address else None,
                notes=notes or '',
                menu=menu_id,
                sales_total=0,
                profit_total=0,
                ordernumber=num,
                order_type=type
            )
            order.save()
            total_sales = 0
            total_profit = 0
            
            for item in items:
                product_id = item.get('product_id')
                quantity = item.get('quantity', 1)
                color = item.get('color', '--')
                size = item.get('size', '--')
                
                try:
                    product = Products.objects.get(id=product_id)
                except Products.DoesNotExist:
                    continue  
                
                OrderItem.objects.create(
                    order=order,
                    menu=menu_id,
                    product=product,
                    quantity=quantity,
                    size=size,
                    color=color

                )
                
                item_total = product.price * quantity
                item_profit = (product.price - product.bought_price) * quantity
                total_sales += item_total
                total_profit += item_profit

            order.sales_total = total_sales
            order.profit_total = total_profit
            order.save()
            
            return JsonResponse({
                'success': True,
                'order_id': order.id
            })
            
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid order data format: {str(e)}'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'An error occurred: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
@csrf_exempt
def submit_review(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            menu_id = data.get('menu_id')
            rating = data.get('rating')
            menu=Menu.objects.get(id=menu_id)
            if not menu_id or not rating:
                return JsonResponse({'success': False, 'error': 'Missing required fields'})
            
            review = Reviews.objects.create(
                menu=menu,
                rating=int(rating)
            )
            review.save()
            menu.average_rating = Reviews.objects.filter(menu=menu).aggregate(Avg('rating'))['rating__avg']
            menu.save()
            
            return JsonResponse({
                'success': True,
                'new_rating': menu.average_rating,
                'total_reviews': Reviews.objects.filter(menu=menu).count()
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def order_success(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'order_success.html', {'order': order})
    



def print_invoice(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    items=OrderItem.objects.filter(order=order)
    if order.status =='pending':
        order.status = 'indeliver'
        order.save()
    context = {
        'items':items,
        'bill': order,
    }
    return render(request, 'invoice.html', context)

def confirm_delivered(request, order_id):
    order = get_object_or_404(Order,id=order_id ,status='indeliver')
    order.status = 'delivered'
    order.save()
    messages.success(request, 'تم تاكيد تسليم الطلب بنجاح.')

    return redirect('customer_dashboard')

def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items=OrderItem.objects.filter(order=order_id)
    for i in items:
        product=i.product
        product.quantity += i.quantity
        product.save()
    order.delete()
    messages.success(request, 'تم حذف الطلب بنجاح.')
    return redirect('customer_dashboard')


def check_new_orders(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'غير مصرح'}, status=401)
    
    try:
        customer = request.user.customer
        menu = customer.menu_set.first()
        
        if not menu:
            return JsonResponse({'error': 'لا يوجد متجر'}, status=404)
        
        last_check = request.GET.get('last_check')
        
        if last_check:
           last_check_time = parse_datetime(last_check) or timezone.now() - timedelta(minutes=5)
        else:
           last_check_time = timezone.now() - timedelta(minutes=5)

        new_orders = Order.objects.filter(
            menu=menu,
            last_check__gt=last_check_time,
            status='pending' 
        )
        
        new_orders_count = new_orders.count()
        
        orders_data = []
        for order in new_orders:
            orders_data.append({
                'id': order.id,
                'customer_name': order.customer_name,
                'customer_phone': order.customer_phone,
                'delivery_address': order.delivery_address or None,
                'total': str(order.sales_total),
                'created_at': order.created_at.isoformat()
            })
        
        return JsonResponse({
            'has_new_orders': new_orders_count > 0,
            'new_orders_count': new_orders_count,
            'orders': orders_data,
            'last_check': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def sales_man(request):
    if request.method == 'POST':
      try:   
        saler_id=request.POST.get('saler_id')
        man=Coupon.objects.get(saler_id=saler_id)    
        if man:
            messages.success(request,f'مرحبا بك{man.affiliate_name} لقد تم التعرف عليك شكرا لاستخدامك منصتنا')
            return redirect('saler-man-info',man.id)   
      except Exception as e:
          messages.error(request,f'{str(e)}هناك مشكلة ما توصل مع الدعم الفني')
          return redirect('/')
    return render(request,'saler_login.html')    
def saler_man_info(request, man_id):
    if request.method =='GET': 
     try:
        man=Coupon.objects.get(id=man_id)

     except Coupon.DoesNotExist:
         messages.error(request,'لم يتم التعرف عليك حاول مرة اخرى او تواصل معنا .') 
         return redirect('/')    
     return render(request, 'saler_info.html',{'coupon':man})     