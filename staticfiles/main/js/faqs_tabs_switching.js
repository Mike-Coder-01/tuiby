document.addEventListener('DOMContentLoaded', function () {
    // Tab switching logic
    const tabButtons = document.querySelectorAll('.tab-btn');
    const faqSections = document.querySelectorAll('.faq-accordion');

    tabButtons.forEach(button => {
        button.addEventListener('click', function () {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            const tab = this.getAttribute('data-tab');

            faqSections.forEach(section => {
                section.style.display = section.id === `${tab}-faq` ? 'block' : 'none';
            });
        });
    });

    // Accordion toggle logic
    const accordionButtons = document.querySelectorAll('.accordion-btn');

    accordionButtons.forEach(button => {
        button.addEventListener('click', function () {
            const content = this.nextElementSibling;
            const isActive = this.classList.contains('active');

            // Close all other accordions in the same section
            const parentAccordion = this.closest('.faq-accordion');
            const allButtons = parentAccordion.querySelectorAll('.accordion-btn');
            const allContents = parentAccordion.querySelectorAll('.accordion-content');

            allButtons.forEach(btn => btn.classList.remove('active'));
            allContents.forEach(cnt => {
                cnt.style.maxHeight = null;
            });

            if (!isActive) {
                this.classList.add('active');
                content.style.maxHeight = content.scrollHeight + "px";
            }
        });
    });
});
