// Dark Mode Toggle
const toggleMode = document.getElementById('toggle-mode');
toggleMode.addEventListener('change', function() {
    document.body.classList.toggle('dark-mode', this.checked);
});
