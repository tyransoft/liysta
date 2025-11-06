from django import forms
from .models import *

class ProductForm(forms.ModelForm):
    class Meta:
        model = Products
        fields = ['name', 'image','quantity','catogery' ,'bought_price','price', 'description','available_colors','available_sizes']
        labels = {
            'name': 'الاسم',
            'image': 'الصورة',
            'price': 'السعر',
            'catogery':'فئة المنتج',
            'description': 'الوصف',
            'bought_price':'سعر التكلفة(يفضل ادخاله للحصول على احصاءات دقيقة)',
            'quantity':'الكمية(يجب اضافته للتحكم في الطلبات)'
        }
        widgets={
            'catogery': forms.Select(attrs={'class': 'form-input'}), 
        }
    def __init__(self, *args, **kwargs):
        customer_instance = kwargs.pop('customer_instance', None)
        
        super().__init__(*args, **kwargs)

        if customer_instance:
            self.fields['catogery'].queryset = Catogery.objects.filter(customer=customer_instance)
        else:
            self.fields['catogery'].queryset = Catogery.objects.none()

class CPDiscountForm(forms.ModelForm):
    products = forms.ModelMultipleChoiceField(
        queryset=Products.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    percentage = forms.FloatField(
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '1'}),
        label="نسبة الخصم (مثلاً: 0.25 = 25%)"
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
        exclude = ['user', 'has_used_free_trial', 'wallet', 'customer_status']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and self.instance:
            self.fields['first_name'].initial = user.first_name
            self._user = user
    
    def save(self, commit=True):
        customer = super().save(commit=False)
        
        if hasattr(self, '_user'):
            self._user.first_name = self.cleaned_data['first_name']
            if commit:
                self._user.save()
        
        if commit:
            customer.save()
            self.save_m2m() 
        
        return customer
    
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
        fields = ['code', 'percentage','affiliate_percentage','affiliate_name', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
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