// Sidebar toggle for mobile/tablet viewports
document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.querySelector('.app-sidebar');
  const backdrop = document.querySelector('.sidebar-backdrop');
  const toggleBtns = document.querySelectorAll('[data-sidebar-toggle]');

  function openSidebar() {
    sidebar && sidebar.classList.add('show');
    backdrop && backdrop.classList.add('show');
  }
  function closeSidebar() {
    sidebar && sidebar.classList.remove('show');
    backdrop && backdrop.classList.remove('show');
  }

  toggleBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (sidebar && sidebar.classList.contains('show')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  });

  backdrop && backdrop.addEventListener('click', closeSidebar);

  // Auto-dismiss toasts/alerts after 5s
  document.querySelectorAll('.alert').forEach(function (el) {
    setTimeout(function () {
      if (window.bootstrap) {
        const alert = window.bootstrap.Alert.getOrCreateInstance(el);
        alert.close();
      }
    }, 5000);
  });
});
