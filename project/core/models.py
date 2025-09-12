from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
import secrets
from django.utils.text import slugify
from django.utils.encoding import force_str
import os
import uuid

def get_upload_path(instance, filename):
    name, ext = os.path.splitext(filename)
    safe_name = slugify(force_str(name))
    
    if not safe_name:
        safe_name = uuid.uuid4().hex
    
    return f'uploads/{safe_name}{ext}'


class Customer(models.Model):
    status = {
        ('inactive', 'inactive'),
        ('active', 'active'),
    }
    kind = {
        ('مطعم\مقهى','مطعم\مقهى'),
        ('متجر', 'متجر'),
        ('غير ذلك', 'غير ذلك'),
    }
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=13)
    store_ar_name = models.CharField(max_length=40)
    store_en_name = models.CharField(max_length=40,unique=True)
    customer_status = models.CharField(max_length=29, choices=status)
    store_kind = models.CharField(max_length=20, choices=kind)
    wallet=models.FloatField(default=0.0)
    has_used_free_trial = models.BooleanField(default=False)
    location_url = models.URLField(blank=True, null=True)
    created_at=models.DateField(auto_now_add=True)


    @property
    def active_subscription(self):
        """إرجاع الاشتراك النشط إن وجد"""
        return self.subscription_set.filter(is_active=True).first()
    
    @property
    def has_any_subscription(self):
        """التحقق من وجود أي اشتراكات سابقة"""
        return self.subscription_set.filter(is_active=False,is_free=False).first()
    
    @property
    def can_use_free_trial(self):
        """التحقق من إمكانية استخدام التجربة المجانية"""
        return not self.has_used_free_trial and not self.has_any_subscription
    def __str__(self):
        return f'{self.user.first_name}-{self.customer_status}'

class Paymentcard(models.Model):
    code=models.CharField(max_length=13, unique=True, db_index=True)
    value=models.IntegerField(default=0)
    is_used=models.BooleanField(default=False)
    def __str__(self):
        return f'{self.code}-{self.value}د.ل//{self.is_used}'
    @staticmethod
    def generate_card_number():
        while True:
            number = ''.join([str(secrets.randbelow(10)) for _ in range(13)])

            if len(set(number)) > 1:
                if not Paymentcard.objects.filter(code=number).exists():

                 return number

    @staticmethod
    def generate_cards(number_of_cards, value):
        created_cards = []
        for _ in range(number_of_cards):
            code = Paymentcard.generate_card_number()
            card = Paymentcard(code=code, value=value)
            card.save()
            created_cards.append(card)
        return created_cards



class Menu(models.Model):
    recivieing={
        ('التوصيل','التوصيل فقط'),
        ('الاستلام في المحل','التسليم فقط في المحل'),
        ('التوصيل او الاستلام في المحل',' التوصيل و التسليم في المحل'),
    }
    customer=models.ForeignKey(Customer,on_delete=models.CASCADE)
    logo=models.ImageField(upload_to=get_upload_path,null=True)    
    image=models.ImageField(upload_to=get_upload_path,null=True)    
    second_color=models.CharField(max_length=20,null=True)
    template=models.CharField(max_length=20,null=True)
    recivieing=models.CharField(max_length=50, choices=recivieing,default='التوصيل')
    desc=models.CharField(max_length=200)
    qr_image=models.ImageField(null=True,upload_to='Qr_images')
    def get_menu_url(self):
     return f'https://liysta.ly/{self.customer.store_en_name}'

    def generate_qr_code(self):
        url = self.get_menu_url()
        
        qr = qrcode.make(url)
        
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)
        
        self.qr_image.save(f'{self.customer.store_en_name}_qr.png', ContentFile(img_io.read()), save=False)
     

    
    def save(self, *args, **kwargs):
        if not self.qr_image:
            self.generate_qr_code()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.customer.user.first_name


class MenuStatistics(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    date = models.DateField()
    visits_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.menu.customer.user.first_name} - {self.date} - {self.visits_count} visits"

class Reviews(models.Model):
    menu=models.ForeignKey(Menu,on_delete=models.CASCADE)
    rating=models.IntegerField(default=1)
    created_at=models.DateTimeField(auto_now_add=True)

    def __st__(self):
        return f' {self.menu.customer.store_en_name} --{self.rating}'

class Catogery(models.Model):
    customer=models.ForeignKey(Customer,on_delete=models.CASCADE)
    name=models.CharField(max_length=25)
    def __str__(self):
        return self.name
    

    
class Products(models.Model):
    menu=models.ForeignKey(Menu,on_delete=models.CASCADE)
    catogery=models.ForeignKey(Catogery,on_delete=models.CASCADE)

    name=models.CharField(max_length=50)
    image=models.ImageField(upload_to=get_upload_path,null=False)
    bought_price=models.IntegerField(null=True,blank=True)
    price=models.IntegerField()
    quantity=models.IntegerField(null=True,blank=True)
    description=models.TextField()
    available_colors = models.CharField(max_length=255,null=True,blank=True, help_text="أدخل الألوان مفصولة بفاصلة مثل: أحمر, أخضر, أزرق")
    available_sizes = models.CharField(max_length=255,null=True ,blank=True, help_text="أدخل المقاسات مفصولة بفاصلة مثل: S, M, L, XL")
    def get_discounted_price(self):
        
         active_discount = CPDiscount.objects.filter(product=self, start_date__lte=timezone.now(), end_date__gte=timezone.now()).first()
         if active_discount:
            discount_amount = self.price * (active_discount.percentage / 100)
            return self.price - discount_amount
         else:
            

          return self.price          


    def save(self,*args,**kwargs):
     if not self.bought_price:
         self.bought_price=self.price
     super().save(*args,**kwargs)
    def __str__(self):
        return self.name
   

class CPDiscount(models.Model):
    menu=models.ForeignKey(Menu,on_delete=models.CASCADE)
    product = models.ForeignKey(Products,on_delete=models.CASCADE ,related_name='discounts')
    percentage = models.FloatField() 
    start_date = models.DateField()
    end_date = models.DateField()
    
    def is_active(self):
        return self.start_date <= timezone.now() <= self.end_date

    def __str__(self):
        return f"خصم {self.percentage} "


class City(models.Model):
    menu=models.ForeignKey(Menu,on_delete=models.CASCADE)
    name=models.CharField(max_length=25)
    price=models.IntegerField(default=0)
    def __str__(self):
        return f'{self.name}--{self.price}'
    def get_price_display(self):
        return f'{self.price} د.ل'



class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)  
    percentage = models.FloatField()  
    affiliate_percentage = models.FloatField(default=0) 
    affiliate_name = models.CharField(max_length=100, blank=True, null=True) 
    start_date = models.DateField()
    end_date = models.DateField()
    used_count = models.IntegerField(default=0) 
    total_earned = models.FloatField(default=0) 
    is_active = models.BooleanField(default=True)
    
    def is_valid(self):
        return self.start_date <= timezone.now() <= self.end_date

    def __str__(self):
        return f"كوبون: {self.code} - خصم {self.percentage}% - عمولة {self.affiliate_percentage}%"

    def record_usage(self, subscription_amount):
        """تسجيل استخدام الكوبون وحساب العمولة"""
        self.used_count += 1
        commission = (subscription_amount * self.affiliate_percentage) / 100
        self.total_earned += commission
        self.save()
        return commission    
    


class Plan(models.Model):
    DURATION_CHOICES = [
        ('free_trial', 'تجربة مجانية'), 
        ('monthly', 'شهر'),
        ('quarterly', 'ربع سنة(3 شهور)'),
        ('yearly', 'سنة'),
        ('halfy', 'نصف سنة (6 شهور)'),
        
        ('daily','يوم')
    ]

    name = models.CharField(max_length=100)
    price = models.IntegerField()
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES)
    ordering=models.BooleanField(default=False)
    whatsapp=models.BooleanField(default=False)
    product_count=models.IntegerField(default=5)
    review=models.BooleanField(default=False)
    
    
    
    def get_discounted_price(self):
   
        active_discount = Discount.objects.filter(plan=self, start_date__lte=timezone.now(), end_date__gte=timezone.now()).first()
        active = Discount.objects.filter(plan=self, start_date=timezone.now(), end_date__gte=timezone.now()).first()

        if active_discount:
            discount_amount = self.price * (active_discount.percentage )
            discounted_price=self.price - discount_amount
            return discounted_price
       
        elif active:
          discount_amount = self.price * (active.percentage )
          discounted_price=self.price - discount_amount
          return discounted_price
        else:
          return self.price  
    def get_discounted_price_with_coupon(self, coupon_code=None):
     
        discounted_price = self.get_discounted_price()

        if coupon_code:
            
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            if coupon:
             discount_amount = discounted_price * (coupon.percentage)
             discounted_price -= discount_amount
            else:
                pass    
        
        return discounted_price
    
    def __str__(self):
        return self.name


class Subscription(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)  
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)  
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)  
    is_active = models.BooleanField(default=True)
    is_free = models.BooleanField(default=False)

    sub_price = models.IntegerField(null=True, blank=True)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL) 
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  
    
    def save(self, *args, **kwargs):
        self.sub_price = self.plan.price
        
        self.final_price = self.plan.get_discounted_price_with_coupon(
            coupon_code=getattr(self.coupon, 'code', None)
        )
        
        if not self.start_date:
            self.start_date = timezone.now().date()
            
        if self.plan.duration == 'monthly':
            self.end_date = self.start_date + timedelta(days=30)  
        elif self.plan.duration == 'quarterly':
            self.end_date = self.start_date + timedelta(days=90)  
        elif self.plan.duration == 'yearly':
            self.end_date = self.start_date + timedelta(days=365)  
        elif self.plan.duration == 'daily':
            self.end_date = self.start_date + timedelta(days=1)  

        elif self.plan.duration == 'free_trial':
        
            self.end_date = self.start_date + timedelta(days=30)
            self.sub_price = 0
            self.final_price = 0
            self.customer.has_used_free_trial = True
            self.customer.save()
             
        if not self.end_date:
            self.end_date = self.start_date     


       
        if self.coupon and self.final_price:
            self.coupon.record_usage(self.final_price)
            
        super().save(*args, **kwargs)

    def remaining_days(self):
        if self.end_date:
            remaining = self.end_date - timezone.now().date()
            return remaining.days
        return 0
    def __str__(self):
        return f"Subscription for {self.customer.user.first_name} to {self.plan.name}"



class Discount(models.Model):
    plan = models.ForeignKey(Plan, related_name="discounts", on_delete=models.CASCADE)
    percentage = models.FloatField() 
    start_date = models.DateField()
    end_date = models.DateField()
    
    def is_active(self):
        return self.start_date <= timezone.now() <= self.end_date

    def __str__(self):
        return f"خصم {self.percentage}% على {self.plan.name}"




class OurCustomer(models.Model):
    name=models.CharField(max_length=40)
    logo=models.ImageField(upload_to='ourcustomer_logo',null=True)
    def __str__(self):
        return self.name
    






class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('indeliver', 'قيد التجهيز'),
        ('delivered', 'تم التسليم'),
    ]
    ordernumber=models.IntegerField(null=True,blank=True)
    order_type=models.CharField(max_length=25,null=True,blank=True)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    delivery_address = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateField(auto_now_add=True)
    sales_total=models.FloatField(null=True,blank=True)
    profit_total=models.FloatField(null=True,blank=True)
    
    def get_total(self):
        if self.delivery_address:
            total= self.sales_total + self.delivery_address.price
            return total
        else:
            total=self.sales_total
            return total




    def __str__(self):
        return f"طلب  - {self.menu.customer.store_en_name} - {self.customer_name}"


class OrderItem(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity=models.IntegerField(null=True,blank=True)
    color=models.CharField(max_length=30,null=True,blank=True)
    size=models.CharField(max_length=30,null=True,blank=True)
    def get_final_price(self):
       return self.quantity * self.product.price
    def __str__(self):
        return f"طلب  - {self.product} * {self.quantity}"
    

class AdminSales(models.Model):
    profit=models.FloatField(default=0)
    created_at=models.DateField(auto_now_add=True)
    def __str__(self):
        return self.profit

