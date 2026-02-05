/**
 * AWSIS Theme JavaScript
 * Initializes animations, carousels, and interactive components
 */

document.addEventListener('DOMContentLoaded', function() {
  'use strict';

  // Initialize AOS (Animate on Scroll)
  if (typeof AOS !== 'undefined') {
    AOS.init({
      duration: 600,
      easing: 'ease-out-cubic',
      once: true,
      offset: 50,
      disable: 'mobile'
    });
  }

  // Initialize CountUp animations for statistics
  initCountUp();

  // Initialize Swiper carousel for featured datasets
  initSwiper();
});

/**
 * Initialize CountUp animations for statistic numbers
 */
function initCountUp() {
  if (typeof countUp === 'undefined' && typeof CountUp === 'undefined') {
    return;
  }

  const CountUpClass = typeof CountUp !== 'undefined' ? CountUp : countUp.CountUp;
  const statNumbers = document.querySelectorAll('[data-countup]');

  if (!statNumbers.length) return;

  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.5
  };

  const observer = new IntersectionObserver(function(entries, observer) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        const element = entry.target;
        const endValue = parseInt(element.getAttribute('data-countup'), 10);

        if (endValue > 0) {
          const counter = new CountUpClass(element, endValue, {
            duration: 2.5,
            useEasing: true,
            useGrouping: true,
            separator: ',',
          });

          if (!counter.error) {
            counter.start();
          }
        } else {
          element.textContent = '0';
        }

        observer.unobserve(element);
      }
    });
  }, observerOptions);

  statNumbers.forEach(function(stat) {
    observer.observe(stat);
  });
}

/**
 * Initialize Swiper carousel for featured datasets
 */
function initSwiper() {
  if (typeof Swiper === 'undefined') {
    return;
  }

  const swiperContainer = document.querySelector('.awsis-swiper');
  if (!swiperContainer) return;

  new Swiper('.awsis-swiper', {
    slidesPerView: 1,
    spaceBetween: 24,
    loop: true,
    autoplay: {
      delay: 5000,
      disableOnInteraction: false,
      pauseOnMouseEnter: true
    },
    pagination: {
      el: '.swiper-pagination',
      clickable: true,
    },
    navigation: {
      nextEl: '.swiper-button-next',
      prevEl: '.swiper-button-prev',
    },
    breakpoints: {
      640: {
        slidesPerView: 2,
        spaceBetween: 24,
      },
      1024: {
        slidesPerView: 3,
        spaceBetween: 32,
      },
    },
    a11y: {
      prevSlideMessage: 'Previous slide',
      nextSlideMessage: 'Next slide',
    },
  });
}

/**
 * Smooth scroll to element
 * @param {string} targetId - The ID of the target element
 */
function smoothScrollTo(targetId) {
  const target = document.getElementById(targetId);
  if (target) {
    target.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  }
}

/**
 * Debounce function for performance optimization
 * @param {Function} func - The function to debounce
 * @param {number} wait - The wait time in milliseconds
 * @returns {Function} - The debounced function
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction() {
    const context = this;
    const args = arguments;
    const later = function() {
      timeout = null;
      func.apply(context, args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
