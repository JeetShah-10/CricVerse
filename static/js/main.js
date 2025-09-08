document.addEventListener('DOMContentLoaded', function() {

  // --- NEW: Pre-loader Logic ---
  const preloader = document.querySelector('.preloader');
  if (preloader) {
      window.addEventListener('load', () => {
          preloader.classList.add('fade-out');
          preloader.addEventListener('transitionend', () => {
              preloader.style.display = 'none';
          });
      });
  }

  // --- NEW: Navbar Scroll Effect ---
  const navbar = document.querySelector('.navbar');
  // Only apply this effect on the homepage
  if (document.querySelector('.hero')) {
      navbar.classList.add('bg-dark-transparent');

      window.addEventListener('scroll', () => {
          if (window.scrollY > 50) {
              navbar.classList.remove('bg-dark-transparent');
              navbar.classList.add('bg-dark-scrolled');
          } else {
              navbar.classList.remove('bg-dark-scrolled');
              navbar.classList.add('bg-dark-transparent');
          }
      });
  }

  // --- NEW: Theme Toggle ---
  const html = document.documentElement;
  const toggleBtn = document.getElementById('themeToggle');
  if (toggleBtn) {
    const saved = localStorage.getItem('theme');
    if (saved) html.dataset.bsTheme = saved;
    toggleBtn.addEventListener('click', () => {
      html.dataset.bsTheme = html.dataset.bsTheme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', html.dataset.bsTheme);
    });
  }
});


// --- ORIGINAL: AOS Refresh Logic (Kept as is) ---
document.addEventListener('visibilitychange', () => {
if (!document.hidden && window.AOS) { window.AOS.refreshHard(); }
});

