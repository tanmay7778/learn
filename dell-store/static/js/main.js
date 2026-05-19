// ====== MAIN.JS - Dell Store Frontend Logic ======

document.addEventListener('DOMContentLoaded', function() {

    // Auto-dismiss flash alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    });

    // Confirm before triggering scrape
    const scrapeForm = document.querySelector('form[action*="scrape"]');
    if (scrapeForm) {
        scrapeForm.addEventListener('submit', function(e) {
            if (!confirm('This will scrape Dell website for new products. Continue?')) {
                e.preventDefault();
            }
        });
    }

    // Confirm before removing cart item
    const removeForms = document.querySelectorAll('form[action*="cart/remove"]');
    removeForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm('Remove this item from cart?')) {
                e.preventDefault();
            }
        });
    });

    // Password confirmation validation on register page
    const registerForm = document.querySelector('form[action*="register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password');
            if (confirmPassword && password !== confirmPassword.value) {
                e.preventDefault();
                alert('Passwords do not match!');
            }
        });
    }

    // Add active state to current nav link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(function(link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    console.log('Dell Store loaded successfully.');
});
