from django.urls import path
from .views import *
from django.contrib.auth import views as v
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticSitemap
from django.views.generic.base import TemplateView

sitemaps={
    'static':StaticSitemap,
}

urlpatterns = [
    path('sitemap.xml',sitemap,{'sitemaps':sitemaps},name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt',TemplateView.as_view(template_name='robots.txt',content_type='text/plain')),

    path('',home,name='home'),

    path('about-us/',about,name='about'),
    path('How_it_works/',learn,name='how-it-works'),
    path('terms/',terms,name='terms'),
    path('Privacy/',privacy,name='privacy'),
    path('start-free-trial/',start_free_trial,name='start_free_trial'),

    path('cards/', card_list_view, name='card_list'),
    path('generate-cards/', generate_cards_view, name='generate_cards'),
    path('customers/', customer_list_view, name='customers_list'),
    path('saler-login/',sales_man,name='saler_login'),
    path('saler-man-info/<int:man_id>/',saler_man_info,name='saler-man-info'),
    
    path('menu/setup/', menu_setup, name='menu_setup'),

    path('register-customer/', register_customer, name='register-customer'),
    path('email-sent/', email_sent, name='email_sent'),

    path('activate/<uidb64>/<token>/',activate_user,name='activate'),
    path('plans/', plan_list, name='plan_list'),
    path('accounts/login/', user_login, name='user_login'),
    path('logout/', user_logout, name='user_logout'),
    path('reset-password/',v.PasswordResetView.as_view(template_name='reset_password.html' ,  email_template_name='password_reset_email.html',
    subject_template_name='password_reset_subject.txt'),name='reset_password'),
    path('reset-password-done/',v.PasswordResetDoneView.as_view(template_name='reset_password_done.html'),name='password_reset_done'),
    path('reset-password-confirm/<uidb64>/<token>',v.PasswordResetConfirmView.as_view(template_name='reset_password_confirm.html'),name='password_reset_confirm'),
    path('reset-password-complete/',v.PasswordResetCompleteView.as_view(template_name='reset_password_complete.html'),name='password_reset_complete'),


    path('wallet-charging/', wallet_charging, name='wallet_charging'),
    path('choose-template/<int:menu_id>', choose_template, name='choose_template'),
    path('menu/edit/<int:menu_id>/', edit_menu, name='edit_menu'),
    path('edit-customer-data/', edit_customer_data, name='update_customer'),
    path('apply-coupon/',apply_coupon,name='apply-coupon'),
    
    path('menu/<int:menu_id>/add_product/', add_product_view, name='add_product'),
    path('product/<int:product_id>/update/', update_product_view, name='update_product'),
    path('product/<int:product_id>/delete/', delete_product_view, name='delete_product'),

    path('menu/<int:menu_id>/add_city/', add_city_view, name='add_city'),
    path('city/<int:city_id>/update/', update_city_view, name='update_city'),
    path('city/<int:city_id>/delete/', delete_city_view, name='delete_city'),
    path('menu/<int:menu_id>/add_catogery/', add_catogery_view, name='add_catogery'),
    path('catogery/<int:catogery_id>/update/', update_catogery_view, name='update_catogery'),
    path('catogery/<int:catogery_id>/delete/', delete_catogery_view, name='delete_catogery'),
    path('menu/<int:menu_id>/add-customer-discount/', add_cpdiscount, name='add_cpdiscount'),
    path('customer-discount/edit/<int:cpdiscount_id>/', edit_cpdiscount, name='edit_cpcdiscount'),
    path('customer-discount/delete/<int:cpdiscount_id>/', delete_cpdiscount, name='delete_cpdiscount'),   


    path('submit-review/', submit_review, name='submit_review'),
    path('customer-dashboard/', customer_dashboard, name='customer_dashboard'),
    path('customer-dashboard/check-new-orders/',check_new_orders,name='check-new-orders'),
    path('preview-template/', preview_template, name='preview_template'),
    path('preview-invoice/', preview_invoice, name='preview_invoice'),
    path('choose-invoice/<int:menu_id>', choose_invoice, name='choose_invoice'),
    

    path('customer-dashboard/print-invoice/<int:order_id>', print_invoice, name='invoice'),
    path('orders/print-multiple/', print_multiple_invoices, name='invoice'),
    
    path('ship-order/<int:order_id>', ship_order, name='ship'),
    path('orders/ship-multiple/', ship_orders, name='ship_orders'),

    path('confirm-delivered/<int:order_id>', confirm_delivered, name='recive'),
    path('orders/confirm-delivered-multiple/', confirm_delivered_multiple, name='recive_orders'),


    path('customer-dashboard/cancel-order/<int:order_id>', delete_order, name='order_delete'),
    path('orders/cancel-order-multiple/', delete_order_multiple, name='order_delete_orders'),
    
    path('return-order/<int:order_id>', return_order, name='return'),
    path('orders/return-multiple/', return_order_multiple, name='return_orders'),
    
    path('add-quantity-to-product/<int:product_id>', add_quantity, name='add_quantity'),
    path('manage-storage/<int:menu_id>', manage_storage, name='storage'),

    path('orders/<int:menu_id>', manege_order, name='manege_order'),
    path('edite-order/<int:order_id>', edite_order, name='edite_order'),
    path('update-order/<int:order_id>/', update_order, name='update_order'),
    path('create_order/', create_order, name='create_order'),
    path('order/success/<int:order_id>/', order_success, name='order_success'),

    path('coupons/', coupon_list, name='coupon_list'),
    path('clients/', clint_list, name='clint_list'),

    path('discounts/', discount_list, name='discount_list'),

    path('<str:store_slug>/', menu_page_view, name='menu_page'),

    path('renew-subscription/<int:subscription_id>/', renew_subscription, name='renew_subscription'),
    path('buy_plan/<int:plan_id>/', buy_plan, name='buy_plan'),
    path('dashboard/control/', dashboard_view, name='control_dashboard'),

    path('dashboard/statistics/', statistics_dashboard, name='statistics_dashboard'),
    path('plans/', plan_list, name='plan_list'),
    path('plans/add/', add_plan, name='add_plan'),
    path('plans/update/<int:plan_id>/', update_plan, name='update_plan'),
    path('plans/delete/<int:plan_id>/', delete_plan, name='delete_plan'),  
    
    path('discount/add/', add_discount, name='add_discount'),
    path('discount/edit/<int:discount_id>/', edit_discount, name='edit_discount'),
    path('discount/delete/<int:discount_id>/', delete_discount, name='delete_discount'),   
    
    path('coupon/add/', add_coupon, name='add_coupon'),
    path('coupon/edit/<int:coupon_id>/', edit_coupon, name='edit_coupon'),
    path('coupon/delete/<int:coupon_id>/', delete_coupon, name='delete_coupon'),
    
    path('clint/add/', add_clint, name='add_clint'),
    path('clint/edit/<int:clint_id>/', edit_clint, name='edit_clint'),
    path('clint/delete/<int:clint_id>/', delete_clint, name='delete_clint'),

    

]