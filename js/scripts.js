// Hamburger Menu Toggle
const hamburger = document.querySelector('.hamburger');
const navLinks = document.querySelector('.nav-links');

if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
        navLinks.classList.toggle('nav-active');
        hamburger.classList.toggle('toggle');
    });
}

// Modal Functionality (Only on Portfolio Page)
const modal = document.getElementById('modal');
const modalImage = document.getElementById('modal-image');
const modalDescription = document.getElementById('modal-description');
const modalLink = document.getElementById('modal-link');
const closeButton = document.querySelector('.close-button');

if (modal && modalImage && modalDescription && modalLink && closeButton) {
    // Sample project data
    const projects = {
        1: {
            title: 'Project Title 1',
            image: 'images/project1.jpg',
            description: 'Detailed description of Project 1.',
            link: 'https://liveproject1.com'
        },
        2: {
            title: 'Project Title 2',
            image: 'images/project2.jpg',
            description: 'Detailed description of Project 2.',
            link: 'https://liveproject2.com'
        },
        3: {
            title: 'Project Title 3',
            image: 'images/project3.jpg',
            description: 'Detailed description of Project 3.',
            link: 'https://liveproject3.com'
        }
        // Add more projects as needed
    };

    // Open Modal
    const portfolioItems = document.querySelectorAll('.portfolio-item');
    if (portfolioItems.length > 0) {
        portfolioItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const projectId = item.getAttribute('data-project');
                const project = projects[projectId];
                if (project) {
                    modalImage.src = project.image;
                    modalImage.alt = project.title;
                    modalDescription.textContent = project.description;
                    modalLink.href = project.link;
                    modal.querySelector('h2').textContent = project.title;
                    modal.style.display = 'block';
                }
            });
        });
    }

    // Close Modal
    closeButton.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Close Modal When Clicking Outside Content
    window.addEventListener('click', (e) => {
        if (e.target == modal) {
            modal.style.display = 'none';
        }
    });
}

// Smooth Scroll for Internal Links (Optional)
const internalLinks = document.querySelectorAll('a[href^="#"]');
if (internalLinks.length > 0) {
    internalLinks.forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Fade-in Elements on Scroll
const faders = document.querySelectorAll('.fade-in');

if (faders.length > 0) {
    const appearOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const appearOnScroll = new IntersectionObserver(function(
        entries,
        appearOnScroll
    ) {
        entries.forEach(entry => {
            if (!entry.isIntersecting) {
                return;
            } else {
                entry.target.classList.add('show');
                appearOnScroll.unobserve(entry.target);
            }
        });
    }, appearOptions);

    faders.forEach(fader => {
        appearOnScroll.observe(fader);
    });
}
