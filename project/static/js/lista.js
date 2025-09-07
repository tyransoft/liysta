// ----------- Toggle Menu -----------
const toggle = document.getElementById('menu-toggle');
const navbarLinks = document.querySelector('.navbar-links');

toggle.addEventListener('click', () => {
    navbarLinks.classList.toggle('open');
});

// ----------- Navbar Scroll Effect -----------
window.addEventListener('scroll', function () {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// ----------- Packages Animation Delay -----------
const packages = document.querySelectorAll('.package');
packages.forEach((pkg, index) => {
    pkg.style.transitionDelay = `${index * 0.1}s`;
});

// ----------- Swiper Slider -----------
var swiper = new Swiper(".mySwiper", {
    slidesPerView: 3,
    spaceBetween: 20,
    loop: true,
    autoplay: {
        delay: 2500,
        disableOnInteraction: false,
    },
    pagination: {
        el: ".swiper-pagination",
        clickable: true,
    },
    navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
    },
    breakpoints: {
        1024: { slidesPerView: 3 },
        768: { slidesPerView: 2 },
        480: { slidesPerView: 1, centeredSlides: true, slidesPerGroup: 1 },
    }
});

// ----------- AOS Animation Init -----------
AOS.init({
    duration: 1000,
    once: false
});
