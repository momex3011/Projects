// Function to set theme preference (targets <html> now)
function setTheme(theme) {
    const htmlElement = document.documentElement; // Target <html>
    if (htmlElement) {
        if (theme === 'dark') {
            htmlElement.classList.add('dark-mode');
        } else {
            htmlElement.classList.remove('dark-mode');
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // Theme toggle functionality
    const themeToggle = document.getElementById('theme-toggle');

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            // Check current theme based on <html> element
            const currentThemeIsDark = document.documentElement.classList.contains('dark-mode');
            const newTheme = currentThemeIsDark ? 'light' : 'dark';

            localStorage.setItem('theme', newTheme); // Save preference
            setTheme(newTheme); // Apply the theme immediately
        });
    }

    // NOTE: Initial theme setting on page load is now handled
    // by the inline script in layout.html's <head>, so we don't need it here.


    // --- Keep your other unrelated DOMContentLoaded code below ---

    // Function to animate the progress circles (Keep as is)
    function animateProgressCircle(elementId, value, total) {
        const circle = document.querySelector(`#${elementId} .progress`);
        const valueText = document.querySelector(`#${elementId} .value`);
        if (!circle || !valueText) return; // Add checks for element existence

        const radius = circle.getAttribute('r');
        const circumference = 2 * Math.PI * radius;
        // Ensure total is not zero to avoid division by zero
        const progress = total > 0 ? (value / total) * circumference : 0;

        // Clamp progress to circumference
        const offset = Math.max(0, Math.min(circumference, circumference - progress));

        circle.style.strokeDashoffset = offset;
        valueText.textContent = value;
    }

    // Get data from the HTML attributes (Keep as is, but add checks)
    const councilMembersElement = document.getElementById('council-members');
    const contactPersonsElement = document.getElementById('contact-persons');
    const projectsElement = document.getElementById('projects');

    if (councilMembersElement) {
        const councilMembersCount = parseInt(councilMembersElement.dataset.value) || 0;
        const totalCouncilMembers = parseInt(councilMembersElement.dataset.total) || 1; // Avoid division by zero
        animateProgressCircle('council-members', councilMembersCount, totalCouncilMembers);
    }
    if (contactPersonsElement) {
        const contactPersonsCount = parseInt(contactPersonsElement.dataset.value) || 0;
        const totalContactPersons = parseInt(contactPersonsElement.dataset.total) || 1;
        animateProgressCircle('contact-persons', contactPersonsCount, totalContactPersons);
    }
    if (projectsElement) {
        const projectsCount = parseInt(projectsElement.dataset.value) || 0;
        const totalProjects = parseInt(projectsElement.dataset.total) || 1;
        animateProgressCircle('projects', projectsCount, totalProjects);
    }

    // News card scroll buttons (Keep as is)
    const newsCardScroll = document.querySelector('.news-card-scroll');
    const prevButton = document.querySelector('.scroll-button.prev');
    const nextButton = document.querySelector('.scroll-button.next');

    if (prevButton && nextButton && newsCardScroll) {
        prevButton.addEventListener('click', function() {
            newsCardScroll.scrollBy({ left: -newsCardScroll.offsetWidth, behavior: 'smooth' });
        });

        nextButton.addEventListener('click', function() {
            newsCardScroll.scrollBy({ left: newsCardScroll.offsetWidth, behavior: 'smooth' });
        });
    }
});