        const toggle = document.getElementById('menu-toggle');
        const navbarLinks = document.querySelector('.navbar-links');

        toggle.addEventListener('click', () => {
            navbarLinks.classList.toggle('open');
        });

        // إغلاق القائمة عند النقر على رابط
        document.querySelectorAll('.navbar-links a').forEach(link => {
            link.addEventListener('click', () => {
                navbarLinks.classList.remove('open');
            });
        });

        // تهيئة AOS
        AOS.init({
            duration: 800,
            once: true,
            offset: 100
        });