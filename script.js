const header = document.querySelector('.site-header');
const menuButton = document.querySelector('.menu-toggle');
const menu = document.querySelector('.main-nav');

function closeMenu() {
  menu.classList.remove('open');
  menuButton.setAttribute('aria-expanded', 'false');
  menuButton.setAttribute('aria-label', document.body.dataset.menuOpen);
  document.body.style.overflow = '';
}

menuButton.addEventListener('click', () => {
  const willOpen = !menu.classList.contains('open');
  menu.classList.toggle('open', willOpen);
  menuButton.setAttribute('aria-expanded', String(willOpen));
  menuButton.setAttribute('aria-label', willOpen ? document.body.dataset.menuClose : document.body.dataset.menuOpen);
  document.body.style.overflow = willOpen ? 'hidden' : '';
});

menu.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));

function updateHeader() {
  header.classList.toggle('scrolled', window.scrollY > 24);
}

updateHeader();
window.addEventListener('scroll', updateHeader, { passive: true });

if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -30px' });

  document.querySelectorAll('.reveal').forEach((element) => observer.observe(element));
} else {
  document.querySelectorAll('.reveal').forEach((element) => element.classList.add('visible'));
}

document.querySelectorAll('.faq-list details').forEach((item) => {
  item.addEventListener('toggle', () => {
    if (!item.open) return;
    document.querySelectorAll('.faq-list details').forEach((other) => {
      if (other !== item) other.open = false;
    });
  });
});
