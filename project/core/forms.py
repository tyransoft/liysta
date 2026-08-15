from django import forms
from .models import *
from django.core.exceptions import ValidationError

class ProductForm(forms.ModelForm):
    class Meta:
        model = Products
        fields = ['name', 'image','quantity','catogery' ,'bought_price'
        ,'price', 'description','available_colors','available_sizes','priority','high'
        ,'length','latitude','openable','breakable','measurable']
        
        labels = {
            'name': 'الاسم',
            'image': 'الصورة',
            'price': 'السعر',
            'catogery':'فئة المنتج',
            'description': 'الوصف',
            'bought_price':'سعر التكلفة(يفضل ادخاله للحصول على احصاءات دقيقة)',
            'quantity':'الكمية(يجب اضافته للتحكم في الطلبات)',
            'priority':'أولوية العرض ',
            'length':'الطول',
            'high':'الارتفاع',
            'latitude':'العرض',
            
        }
        widgets={
            'catogery': forms.Select(attrs={'class': 'form-input'}), 
        }
    def __init__(self, *args, **kwargs):
        customer_instance = kwargs.pop('customer_instance', None)
        
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk: 
            fields_to_make_optional = ['price', 'quantity', 'bought_price']
            for field in fields_to_make_optional:
                if field in self.fields:
                    self.fields[field].required = False
        
        if customer_instance:
            self.fields['catogery'].queryset = Catogery.objects.filter(customer=customer_instance)
        else:
            self.fields['catogery'].queryset = Catogery.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.instance.pk:
            if not cleaned_data.get('price'):
                self.add_error('price', 'سعر البيع مطلوب للمنتج الجديد')
            if not cleaned_data.get('quantity'):
                self.add_error('quantity', 'الكمية مطلوبة للمنتج الجديد')
        
        else:
            if not cleaned_data.get('price'):
                cleaned_data['price'] = self.instance.price
            if not cleaned_data.get('quantity'):
                cleaned_data['quantity'] = self.instance.quantity
            if not cleaned_data.get('bought_price'):
                cleaned_data['bought_price'] = self.instance.bought_price
        dimension_fields = ['length', 'high', 'latitude']

        for field in dimension_fields:
          value = cleaned_data.get(field)

          if value in [None, '']:
            if self.instance and self.instance.pk:
                old_value = getattr(self.instance, field, None)

                if old_value not in [None, '']:
                    cleaned_data[field] = old_value
                else:
                    cleaned_data[field] = None
            else:
                 cleaned_data[field] = None

        return cleaned_data
       
class CPDiscountForm(forms.ModelForm):
    products = forms.ModelMultipleChoiceField(
        queryset=Products.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    percentage = forms.FloatField(
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '1'}),
        label="نسبة الخصم (مثال: %25 اكتبها 0.25  )"
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="تاريخ البداية"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="تاريخ الانتهاء"
    )
    
    class Meta:
        model = CPDiscount
        fields = ['products', 'percentage', 'start_date', 'end_date']
    
    def __init__(self, *args, **kwargs):
        menu_instance = kwargs.pop('menu_instance', None)
        super().__init__(*args, **kwargs)
        
        if menu_instance:
            self.fields['products'].queryset = Products.objects.filter(menu=menu_instance)

class CPDForm(forms.ModelForm):
    class Meta:
        model=CPDiscount
        exclude=['menu','product']

class CustomerForm(forms.ModelForm):
    first_name = forms.CharField(label='الاسم', max_length=200)
    
    class Meta:
        model = Customer
        exclude = ['user', 'has_used_free_trial', 'wallet', 'customer_status','store_slug','connected_del_method']
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
    
    def save(self, commit=True):
        customer = super().save(commit=commit)
        if self.user and commit:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.save()
        return customer
    def clean_store_en_name(self):
      store_en_name = self.cleaned_data['store_en_name']

      qs = Customer.objects.filter(store_en_name=store_en_name)

      if self.instance.pk:
        qs = qs.exclude(pk=self.instance.pk)

      if qs.exists():
        raise forms.ValidationError(
            "اسم المتجر الإنجليزي مستخدم بالفعل، يرجى اختيار اسم آخر."
        )

      return store_en_name
class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ['name','price']
        labels = {
            'name': 'الاسم',
            'price': 'السعر',
        }

        widgits={
            'name':forms.TextInput(attrs={'class': 'form-input'}),
            'price':forms.NumberInput(attrs={'class': 'form-input'}),
        }

class CatogeryForm(forms.ModelForm):
    class Meta:
        model = Catogery
        fields = ['name']
        labels = {
            'name': 'اسم الفئة',
        }
        widgets = {
           'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'أدخل اسم الفئة'}),
         }


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['name', 'price', 'duration','review', 'ordering','product_count']        
        widgets = {
            'review': forms.CheckboxInput(),
            'ordering': forms.CheckboxInput(),

        }
        labels = {
            'name': 'اسم الباقة',
            'price': 'السعر',
            'duration': 'المدة الزمنية',
            'ordering': 'ميزة الطلب',
            'review': 'ميزة التقييم',
            'product_count': 'عدد المنتجات المتاح',

        }



class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['logo', 'image',  'second_color', 'recivieing','template','desc']
        widgets = {
            'second_color': forms.TextInput(attrs={'type': 'color'}),
            'recivieing': forms.RadioSelect,
            'desc': forms.Textarea(attrs={
                'placeholder': 'أدخل وصف القائمة هنا...',
                'rows': 5,
            }),
        }
        labels = {
            'logo': 'شعار المتجر',
            'image': 'الصورة الرئيسية',
            'second_color': 'لون التصميم',
            'recivieing': 'التسليم:',
            'desc':'وصف للمتجر'
        }



        
class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ['plan', 'percentage', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'plan': ' الباقة',
            'percentage': 'نسبة الخصم',
           
            'start_date':'تاريخ البداية',
            'end_date':'تاريخ نهاية صلاحية الخضم',

        }
class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['saler_id','code', 'percentage','affiliate_percentage','affiliate_name', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'saler_id':'الرقم التعريفي',
            'code': 'كود الخصم',
            'percentage': 'نسبة الخصم',
            'affiliate_name':'اسم المسوق',
            'affiliate_percentage':'نسبة المسوق',
            'start_date':'تاريخ البداية',
            'end_date':'تاريخ نهاية صلاحية الكوبون',

        }

class OurCustomerForm(forms.ModelForm):
    class Meta:
        model = OurCustomer
        fields =['name','logo']
        labels = {
            'name': 'الاسم',
            'logo': 'الشعار',
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_phone', 'delivery_address', 'notes']
        widgets = {
            'delivery_address': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        menu = kwargs.pop('menu', None)
        super().__init__(*args, **kwargs)
        if menu:
            self.fields['delivery_address'].queryset = City.objects.filter(menu=menu)



class CustomerCoastForm(forms.ModelForm):
    
    class Meta:
        model = CustomerCoasts
        fields = ['coast_kind', 'amount', 'recurring']
        widgets = {
            'coast_kind': forms.RadioSelect(choices=CustomerCoasts.KIND, attrs={
                'class': 'radio-input'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل المبلغ',
                'step': '0.01',
                'min': '0'
            }),
            'recurring': forms.CheckboxInput(attrs={
                'class': 'toggle-input',
                'id': 'recurring'
            })
        }
        labels = {
            'coast_kind': 'نوع التكلفة',
            'amount': 'المبلغ',
            'recurring': 'تكلفة متكررة'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['coast_kind'].choices = [
            ('Operations', 'عمليات'),
            ('Marketing&sells', 'تسويق ومبيعات'),
        ]
        
        self.fields['coast_kind'].widget.attrs.update({
            'data-icon-operations': 'fa-cogs',
            'data-icon-marketing': 'fa-chart-line'
        })
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError('يجب أن يكون المبلغ أكبر من صفر')
        return amount

class DarbasabilForm(forms.ModelForm):
    class Meta:
        model = DarbAsabilConnection
        exclude = ['customer', 'state', 'access_token', 'refresh_token', 
                   'token_expire_at', 'refresh_expire_at', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['collecting'].widget.attrs.update({'class': 'custom-checkbox'})
        self.fields['epay'].widget.attrs.update({'class': 'custom-checkbox'})
        self.fields['paymentby'].widget.attrs.update({'class': 'radio-group'})
        self.fields['epay_coast'].widget.attrs.update({'class': 'radio-group'})
        self.fields['storeing'].widget.attrs.update({'class': 'real-checkbox-input'})
        self.fields['epay_coast'].required = False

class NawrisForm(forms.ModelForm):
    class Meta:
        model = NawrisConnection
        exclude = ['customer', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['storeing'].widget.attrs.update({'class': 'custom-checkbox'})
        self.fields['epay'].widget.attrs.update({'class': 'custom-checkbox'})
        self.fields['paymentby'].widget.attrs.update({'class': 'radio-group'})

class CoastsForm(forms.ModelForm):
    class Meta:
        model = Coasts
        fields = ['coast_kind', 'amount', 'recurring']
        widgets = {
            'coast_kind': forms.Select(attrs={
                'class': 'form-input',
                'placeholder': 'اختر نوع التكلفة'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'أدخل المبلغ',
                'step': '1',
                'min': '0'
            }),
            'recurring': forms.CheckboxInput(attrs={
                'class': 'checkbox-input'
            })
        }
        labels = {
            'coast_kind': 'نوع التكلفة',
            'amount': 'المبلغ',
            'recurring': 'تكلفة متكررة '
        }



class PaymentGatewaySettingForm(forms.ModelForm):
    class Meta:
        model = PaymentGatewaySetting
        fields = ['provider', 'api_key', 'webhook_secret', 'payment_methods', 'is_active']
        widgets = {
            'api_key': forms.PasswordInput(attrs={'class': 'form-control'}),
            'webhook_secret': forms.PasswordInput(attrs={'class': 'form-control'}),
            'payment_methods': forms.Select(attrs={'class': 'form-control'}),
            'provider': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['api_key'].required = True
        self.fields['webhook_secret'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        merchant = cleaned_data.get('merchant')
        provider = cleaned_data.get('provider')
        payment_methods = cleaned_data.get('payment_methods')
        
        if merchant and provider:
            existing = PaymentGatewaySetting.objects.filter(
                merchant=merchant,
                provider=provider
            )
            
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f'يوجد إعدادات مكررة للمتجر {merchant.user.first_name}'
                )
        
        if payment_methods == PaymentGatewaySetting.PaymentMethods.ONLINE:
            if not cleaned_data.get('api_key'):
                raise ValidationError({
                    'api_key': 'مفتاح API مطلوب عند تفعيل الدفع الإلكتروني'
                })
            if not cleaned_data.get('webhook_secret'):
                raise ValidationError({
                    'webhook_secret': 'مفتاح Webhook مطلوب عند تفعيل الدفع الإلكتروني'
                })
        
        return cleaned_data