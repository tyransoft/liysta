const toggle = document.getElementById('menu-toggle');
const navbarLinks = document.querySelector('.navbar-links');

toggle.addEventListener('click', () => {
    navbarLinks.classList.toggle('open');
});


window.addEventListener('scroll', function () {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.boxShadow = '0 2px 20px rgba(0,0,0,0.1)';
        navbar.style.padding = '0.5rem 5%';
    } else {
        navbar.style.boxShadow = '0 2px 20px rgba(0,0,0,0.1)';
        navbar.style.padding = '1rem 5%';
    }
});

const packages = document.querySelectorAll('.package');
packages.forEach((pkg, index) => {
    pkg.style.transitionDelay = `${index * 0.1}s`;
});




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
        1024: {slidesPerView: 3 },
    768: {slidesPerView: 2 },
    480: {slidesPerView: 1 },
    }
});
