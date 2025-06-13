// File upload handling
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('upload-form');
    const fileInput = form.querySelector('input[type="file"]');
    const dropZone = document.getElementById('resume-drop-zone');
    const resultsSection = document.getElementById('results');
    const loadingOverlay = document.getElementById('loading-overlay');
    const analyzeButton = form.querySelector('button[type="submit"]');
    const nav = document.querySelector('nav'); // Get the navigation bar

    // Log to check if elements are found on DOMContentLoaded
    console.log('DOMContentLoaded - Form:', form);
    console.log('DOMContentLoaded - FileInput:', fileInput);
    console.log('DOMContentLoaded - DropZone:', dropZone);
    console.log('DOMContentLoaded - ResultsSection:', resultsSection);
    console.log('DOMContentLoaded - LoadingOverlay:', loadingOverlay);
    console.log('DOMContentLoaded - AnalyzeButton:', analyzeButton);
    console.log('DOMContentLoaded - Nav:', nav);

    // Drag and drop handling
    if (!dropZone) {
        console.error('Drop zone element not found');
        return;
    }

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    // Highlight drop zone when item is dragged over it
    dropZone.addEventListener('dragenter', () => {
        console.log('dragenter - dropZone:', dropZone);
        dropZone.classList.add('drag-over');
    });
    dropZone.addEventListener('dragover', () => {
        console.log('dragover - dropZone:', dropZone);
        dropZone.classList.add('drag-over');
    });

    // Remove highlight when item is dragged away or dropped
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            console.log(`${eventName} - dropZone:`, dropZone);
            dropZone.classList.remove('drag-over');
        });
    });

    // Handle dropped files
    dropZone.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            updateFileName(files[0]);
        }
    }, false);

    // Handle file input change
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                updateFileName(this.files[0]);
            }
        });
    }

    function updateFileName(file) {
        if (!file || !dropZone) return;

        const fileName = file.name;
        const fileSize = (file.size / (1024 * 1024)).toFixed(2);
        
        // Remove previous file info if exists
        let fileInfoDiv = dropZone.querySelector('.file-info');
        if (!fileInfoDiv) {
            fileInfoDiv = document.createElement('div');
            fileInfoDiv.className = 'file-info';
            dropZone.appendChild(fileInfoDiv);
        }

        fileInfoDiv.innerHTML = `
            <i class="fas fa-file-pdf file-icon"></i>
            <p class="file-name">${fileName}</p>
            <p class="file-size">${fileSize} MB</p>
        `;
        
        // Hide default text
        const defaultText = dropZone.querySelector('.default-drop-text');
        if (defaultText) defaultText.style.display = 'none';

        const uploadBtn = dropZone.querySelector('.file-label');
        if (uploadBtn) uploadBtn.style.display = 'none';
    }

    // Form submission
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select a file to upload');
                return;
            }

            // Log file details for debugging
            console.log('File details:', {
                name: file.name,
                type: file.type,
                size: file.size
            });

            // Ensure the file is sent with the correct field name
            formData.set('file', file);

            // Log FormData contents for debugging
            for (let pair of formData.entries()) {
                console.log('FormData entry:', pair[0], pair[1]);
            }

            try {
                // Ensure loadingOverlay is not null before accessing classList
                if (loadingOverlay) {
                    console.log('submit - loadingOverlay before remove hidden:', loadingOverlay);
                    loadingOverlay.classList.remove('hidden');
                    console.log('submit - loadingOverlay before add show:', loadingOverlay);
                    loadingOverlay.classList.add('show'); // Trigger fade-in
                }
                analyzeButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
                analyzeButton.disabled = true;
                
                console.log('Sending request to /analyze');
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });

                console.log('Response status:', response.status);
                const responseText = await response.text();
                console.log('Response text:', responseText);

                if (!response.ok) {
                    let errorMessage;
                    try {
                        const errorData = JSON.parse(responseText);
                        errorMessage = errorData.error || 'Analysis failed';
                    } catch (e) {
                        errorMessage = responseText || 'Analysis failed';
                    }
                    throw new Error(errorMessage);
                }

                const data = JSON.parse(responseText);
                
                // Store the analysis data for the report download
                window.analysisData = data;
                
                // Update ATS score
                updateATSScore(data.ats_score);
                
                // Update score breakdown
                if (data.score_breakdown) {
                    updateScoreBreakdown(data.score_breakdown);
                }

                // Update resume analysis
                updateResumeAnalysis(data.analysis);

                // Update job recommendations
                updateJobRecommendations(data.job_recommendations);

                // Update skills analysis
                updateSkillsAnalysis(data.skills_analysis);

                // Show results section with animation
                if (resultsSection) {
                    console.log('submit - resultsSection before remove hidden:', resultsSection);
                    resultsSection.classList.remove('hidden');
                    console.log('submit - resultsSection before add show:', resultsSection);
                    setTimeout(() => resultsSection.classList.add('show'), 10); // Trigger transition
                }
                
                // Scroll to results
                if (resultsSection) {
                    resultsSection.scrollIntoView({ behavior: 'smooth' });
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred during analysis: ' + error.message);
            } finally {
                // Ensure loadingOverlay is not null before accessing classList
                if (loadingOverlay) {
                    console.log('finally - loadingOverlay before remove show:', loadingOverlay);
                    loadingOverlay.classList.remove('show'); // Trigger fade-out
                    console.log('finally - loadingOverlay before add hidden:', loadingOverlay);
                    loadingOverlay.classList.add('hidden');
                }
                analyzeButton.innerHTML = 'Analyze Resume';
                analyzeButton.disabled = false;
            }
        });
    }

    // Download report handler
    const downloadReportButton = document.getElementById('download-report');
    if (downloadReportButton) {
        downloadReportButton.addEventListener('click', async function() {
            try {
                const analysisData = window.analysisData;
                if (!analysisData) {
                    throw new Error('No analysis data available. Please analyze a resume first.');
                }

                // Add a temporary loading state for download
                downloadReportButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
                downloadReportButton.disabled = true;

                const encodedData = encodeURIComponent(JSON.stringify(analysisData));
                const response = await fetch(`/download-report?data=${encodedData}`);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Failed to download report: ${errorText}`);
                }
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'resume-analysis-report.pdf';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();

                alert('Report downloaded successfully!');

            } catch (error) {
                console.error('Error downloading report:', error);
                alert('Error downloading report: ' + error.message);
            } finally {
                downloadReportButton.innerHTML = '<i class="fas fa-download"></i> Download Full Report';
                downloadReportButton.disabled = false;
            }
        });
    }

    // Navigation active state
    const navLinks = document.querySelectorAll('.nav-links a');
    const sections = document.querySelectorAll('section[id]');

    function updateActiveNavLink() {
        let currentActive = '';
        sections.forEach(section => {
            // Add a check for nav before accessing offsetHeight
            const sectionTop = section.offsetTop - (nav ? nav.offsetHeight : 0); 
            const sectionHeight = section.clientHeight;
            if (pageYOffset >= sectionTop && pageYOffset < sectionTop + sectionHeight) {
                currentActive = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').includes(currentActive)) {
                link.classList.add('active');
            }
        });
    }

    window.addEventListener('scroll', updateActiveNavLink);
    updateActiveNavLink(); // Set active link on load

    // Skills Analysis Collapsible behavior
    document.querySelectorAll('.skills-category-header').forEach(header => {
        header.addEventListener('click', () => {
            const content = header.nextElementSibling; // This is the skills-category-content div
            
            if (content) {
                header.classList.toggle('collapsed');
                content.classList.toggle('collapsed');

                // Adjust max-height for smooth transition
                if (content.classList.contains('collapsed')) {
                    content.style.maxHeight = '0';
                } else {
                    content.style.maxHeight = content.scrollHeight + 'px';
                }
            }
        });
    });

    // Initial state: ensure content is visible and max-height is set correctly on load
    document.querySelectorAll('.skills-category-content').forEach(content => {
        if (!content.classList.contains('collapsed')) {
            content.style.maxHeight = content.scrollHeight + 'px';
        }
    });
});

// ATS Score Gauge
function updateATSScore(score) {
    const gaugeContainer = document.getElementById('ats-gauge');
    if (!gaugeContainer) return;

    // Clear previous elements within gauge container to prevent duplicates
    gaugeContainer.innerHTML = '<canvas></canvas>';

    const ctx = gaugeContainer.querySelector('canvas').getContext('2d');
    
    // Clear previous chart if it exists
    if (window.atsGauge) {
        window.atsGauge.destroy();
    }

    // Create new gauge chart
    window.atsGauge = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [score, 100 - score],
                backgroundColor: [
                    getScoreColor(score),
                    '#E5E5EA' // Using border-color from CSS vars for consistency
                ],
                borderWidth: 0,
                borderRadius: 5 // Rounded ends
            }]
        },
        options: {
            cutout: '80%',
            rotation: -90,
            circumference: 180,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1000 // Smooth animation duration
            }
        }
    });

    // Add score text
    const scoreTextDiv = document.createElement('div');
    scoreTextDiv.className = 'ats-score-text';
    scoreTextDiv.innerHTML = `
        <div class="score-value" style="color: ${getScoreColor(score)};">${score}</div>
        <div class="score-label">ATS Score</div>
    `;
    gaugeContainer.appendChild(scoreTextDiv);
}

function updateScoreBreakdown(breakdown) {
    const scoreBreakdownContainer = document.querySelector('.score-breakdown');
    if (!scoreBreakdownContainer) return;

    const scoreItems = {
        'keyword_match': { label: 'Keyword Match', max: 25 },
        'section_presence': { label: 'Section Presence', max: 10 },
        'experience_relevance': { label: 'Experience Relevance', max: 15 },
        'formatting': { label: 'Formatting', max: 10 },
        'grammar': { label: 'Grammar', max: 10 },
        'contact_info': { label: 'Contact Info', max: 5 },
        'filename': { label: 'File Naming', max: 5 },
        'customization': { label: 'Customization', max: 10 }
    };

    for (const key in scoreItems) {
        if (scoreItems.hasOwnProperty(key)) {
            const item = scoreItems[key];
            const score = breakdown[key] !== undefined ? breakdown[key] : 0;
            const percentage = (score / item.max) * 100;

            const barFill = document.getElementById(`${key}-bar`);
            if (barFill) {
                console.log(`updateScoreBreakdown - barFill ${key}:`, barFill);
                barFill.style.width = `${percentage}%`;
                // Update score text within the item if present
                const scoreText = barFill.closest('.score-item').querySelector('p');
                if (scoreText) scoreText.textContent = `${score} points`;
            }
        }
    }
}

function updateResumeAnalysis(analysis) {
    const analysisDiv = document.getElementById('resume-analysis');
    if (!analysisDiv) return;

    analysisDiv.innerHTML = ''; // Clear previous content

    let contentHtml = '';

    if (analysis.overall_assessment) {
        contentHtml += `
            <h3>Overall Assessment</h3>
            <p>${analysis.overall_assessment}</p>
        `;
    }

    if (analysis.strengths && analysis.strengths.length > 0) {
        contentHtml += '<h3>Strengths</h3><ul>' +
            analysis.strengths.map(s => `<li><i class="fas fa-check-circle success-icon"></i> ${s}</li>`).join('') +
            '</ul>';
    }

    if (analysis.improvements && analysis.improvements.length > 0) {
        contentHtml += '<h3>Areas for Improvement</h3><ul>' +
            analysis.improvements.map(i => `<li><i class="fas fa-exclamation-circle danger-icon"></i> ${i}</li>`).join('') +
            '</ul>';
    }

    analysisDiv.innerHTML = contentHtml;

    // Add fade-in effect to newly rendered content
    const newContentElements = analysisDiv.querySelectorAll('h3, p, ul');
    newContentElements.forEach((el, index) => {
        console.log(`updateResumeAnalysis - newContentElement ${index}:`, el);
        el.classList.add('content-fade-in');
        setTimeout(() => el.classList.add('show'), 100 * index); // Staggered animation
    });
}

function updateJobRecommendations(recommendations) {
    const recommendationsDiv = document.getElementById('job-recommendations');
    if (!recommendationsDiv) return;

    recommendationsDiv.innerHTML = ''; // Clear previous content

    if (recommendations && recommendations.length > 0) {
        const ul = document.createElement('ul');
        recommendations.forEach(job => {
            const li = document.createElement('li');
            li.innerHTML = `
                <h4>${job.title}</h4>
                <p>${job.company} - ${job.location}</p>
                <p>${job.match_score}% Match</p>
            `;
            ul.appendChild(li);
        });
        recommendationsDiv.appendChild(ul);

        // Add fade-in effect to newly rendered content
        const newContentElements = recommendationsDiv.querySelectorAll('li');
        newContentElements.forEach((el, index) => {
            console.log(`updateJobRecommendations - newContentElement ${index}:`, el);
            el.classList.add('content-fade-in');
            setTimeout(() => el.classList.add('show'), 100 * index); // Staggered animation
        });

    } else {
        console.log('updateJobRecommendations - fallback p:', recommendationsDiv.querySelector('p'));
        recommendationsDiv.innerHTML = '<p class="content-fade-in">No job recommendations available at this time. Please provide a job description for better matches.</p>';
        setTimeout(() => recommendationsDiv.querySelector('p').classList.add('show'), 10);
    }
}

function updateSkillsAnalysis(skills) {
    console.log('Updating skills analysis:', skills);

    const technicalSkillsDiv = document.getElementById('technical-skills-list');
    const softSkillsDiv = document.getElementById('soft-skills-list');
    const missingSkillsDiv = document.getElementById('missing-skills-list');

    const noTechnicalSkillsMsg = document.getElementById('no-technical-skills');
    const noSoftSkillsMsg = document.getElementById('no-soft-skills');
    const noMissingSkillsMsg = document.getElementById('no-missing-skills');

    // Ensure elements exist before proceeding
    if (!technicalSkillsDiv || !softSkillsDiv || !missingSkillsDiv || !noTechnicalSkillsMsg || !noSoftSkillsMsg || !noMissingSkillsMsg) {
        console.error('One or more skills analysis elements not found.');
        return;
    }

    // Clear previous content
    technicalSkillsDiv.innerHTML = '';
    softSkillsDiv.innerHTML = '';
    missingSkillsDiv.innerHTML = '';

    noTechnicalSkillsMsg.style.display = 'none';
    noSoftSkillsMsg.style.display = 'none';
    noMissingSkillsMsg.style.display = 'none';

    const createSkillTag = (skill, type) => {
        const span = document.createElement('span');
        span.className = `skill-tag ${type}`;
        span.textContent = skill;
        span.style.opacity = '0'; // For fade-in animation
        span.style.transform = 'translateY(20px)'; // For slide-up animation
        return span;
    };

    let allSkillTags = [];

    // Populate Technical Skills
    if (skills.technical && skills.technical.length > 0) {
        skills.technical.forEach(skill => {
            const tag = createSkillTag(skill, 'technical');
            technicalSkillsDiv.appendChild(tag);
            allSkillTags.push(tag);
        });
    } else {
        noTechnicalSkillsMsg.style.display = 'block';
        noTechnicalSkillsMsg.textContent = 'No technical skills found.';
    }

    // Populate Soft Skills
    if (skills.soft_skills && skills.soft_skills.length > 0) {
        skills.soft_skills.forEach(skill => {
            const tag = createSkillTag(skill, 'soft');
            softSkillsDiv.appendChild(tag);
            allSkillTags.push(tag);
        });
    } else {
        noSoftSkillsMsg.style.display = 'block';
        noSoftSkillsMsg.textContent = 'No soft skills found.';
    }

    // Populate Missing Skills
    if (skills.missing_skills && skills.missing_skills.length > 0) {
        skills.missing_skills.forEach(skill => {
            const tag = createSkillTag(skill, 'missing');
            missingSkillsDiv.appendChild(tag);
            allSkillTags.push(tag);
        });
    } else {
        noMissingSkillsMsg.style.display = 'block';
        noMissingSkillsMsg.textContent = 'No suggested skills at the moment.';
    }

    // Staggered fade-in animation for skill tags
    allSkillTags.forEach((tag, index) => {
        setTimeout(() => {
            tag.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
            tag.style.opacity = '1';
            tag.style.transform = 'translateY(0)';
        }, index * 50); // Stagger by 50ms
    });
}

function getScoreColor(score) {
    if (score >= 80) return '#34C759'; // Green
    if (score >= 60) return '#FFD60A'; // Yellow
    if (score >= 40) return '#FF9500'; // Orange
    return '#FF3B30'; // Red
}

// Smooth scrolling for navigation links
document.querySelectorAll('nav a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();

        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// New: Intersection Observer for scroll-triggered animations
const faders = document.querySelectorAll('.feature-card, .result-card');

const appearOptions = {
    threshold: 0.2, // When 20% of the item is visible
    rootMargin: "0px 0px -50px 0px" // Adjust this to load slightly earlier or later
};

const appearOnScroll = new IntersectionObserver(function(entries, appearOnScroll) {
    entries.forEach(entry => {
        if (!entry.isIntersecting) {
            return;
        }
        console.log('IntersectionObserver - entry.target:', entry.target);
        entry.target.classList.add('is-visible');
        appearOnScroll.unobserve(entry.target);
    });
}, appearOptions);

faders.forEach(fader => {
    console.log('Fader init:', fader);
    fader.classList.add('fade-in-on-scroll'); // Add the base class
    appearOnScroll.observe(fader);
});

// Theme handling
function initTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Check for saved theme preference or use system preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    } else if (prefersDarkScheme.matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }

    // Theme toggle click handler
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });

    // Listen for system theme changes
    prefersDarkScheme.addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
        }
    });
}

// Initialize theme when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    // ... rest of your existing DOMContentLoaded code ...
}); 