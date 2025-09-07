        AOS.init({
            duration: 1000,
            once: true,
            offset: 100
        });
        
        // تبديل القائمة في الشاشات الصغيرة
        const toggle = document.getElementById('menu-toggle');
        const navbarLinks = document.querySelector('.navbar-links');
        
        toggle.addEventListener('click', () => {
            navbarLinks.classList.toggle('open');
            toggle.classList.toggle('fa-times');
        });
        
        // إضافة تأثير التمرير للشريط العلوي
        window.addEventListener('scroll', function () {
            const navbar = document.querySelector('.navbar');
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
        
        // إغلاق الرسائل عند النقر على زر الإغلاق
        document.querySelectorAll('.btn-close').forEach(button => {
            button.addEventListener('click', function() {
                this.parentElement.style.display = 'none';
            });
        });