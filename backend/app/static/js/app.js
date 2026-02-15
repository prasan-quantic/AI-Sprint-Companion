/**
 * AI Sprint Companion - Frontend JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Sprint Companion loaded');

    // Add HTMX event listeners for better UX
    document.body.addEventListener('htmx:beforeRequest', function(event) {
        // Disable submit button during request
        const form = event.detail.elt.closest('form');
        if (form) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.dataset.originalText = submitBtn.textContent;
                submitBtn.textContent = '⏳ Processing...';
            }
        }
    });

    document.body.addEventListener('htmx:afterRequest', function(event) {
        // Re-enable submit button after request
        const form = event.detail.elt.closest('form');
        if (form) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                if (submitBtn.dataset.originalText) {
                    submitBtn.textContent = submitBtn.dataset.originalText;
                }
            }
        }

        // Scroll to result
        const target = document.querySelector(event.detail.target);
        if (target && target.innerHTML.trim()) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });

    document.body.addEventListener('htmx:responseError', function(event) {
        // Show error message on failed request
        const target = document.querySelector(event.detail.target);
        if (target) {
            target.innerHTML = `
                <div class="error-card">
                    <div class="error-icon">⚠️</div>
                    <p>An error occurred. Please try again.</p>
                </div>
            `;
        }

        // Re-enable submit button
        const form = event.detail.elt.closest('form');
        if (form) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                if (submitBtn.dataset.originalText) {
                    submitBtn.textContent = submitBtn.dataset.originalText;
                }
            }
        }
    });

    // Setup drag and drop for file upload areas
    setupDragAndDrop();
});

/**
 * Toggle mobile navigation menu
 */
function toggleMobileMenu() {
    const navLinks = document.getElementById('navLinks');
    if (navLinks) {
        navLinks.classList.toggle('active');
    }
}

/**
 * Switch between tabs on the home page
 */
function switchTab(tabId) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(function(tab) {
        tab.classList.remove('active');
    });

    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(function(btn) {
        btn.classList.remove('active');
    });

    // Show selected tab content
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Add active class to clicked button
    event.target.classList.add('active');

    // Clear previous results
    const quickResult = document.getElementById('quick-result');
    if (quickResult) {
        quickResult.innerHTML = '';
    }
}

/**
 * Update file name display when file is selected
 * When a file is selected, read its content and display in textarea
 */
function updateFileName(input, displayElementId) {
    const displayElement = document.getElementById(displayElementId);
    const form = input.closest('form');

    // Find the textarea in the same form
    const textarea = form ? form.querySelector('textarea') : null;

    // Find clear file button and action button
    const clearBtn = form ? form.querySelector('.clear-file-btn') : null;
    const actionBtn = form ? form.querySelector('.btn-file-action') : null;

    if (displayElement && input.files && input.files.length > 0) {
        const file = input.files[0];
        const fileName = file.name;
        const fileSize = (file.size / 1024).toFixed(1);
        displayElement.textContent = `✅ ${fileName} (${fileSize} KB)`;
        displayElement.style.color = '#10b981';

        // Also highlight the upload area
        const uploadArea = input.closest('.file-upload-area');
        if (uploadArea) {
            uploadArea.style.borderColor = '#10b981';
            uploadArea.style.backgroundColor = '#f0fdf4';
        }

        // Show clear file button and action button
        if (clearBtn) {
            clearBtn.style.display = 'inline-block';
        }
        if (actionBtn) {
            actionBtn.style.display = 'inline-block';
        }

        // Read file content and display in textarea
        if (textarea) {
            textarea.dataset.previousValue = textarea.value; // Store previous value

            // Check if it's a text file that we can read directly
            if (fileName.toLowerCase().endsWith('.txt')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    textarea.value = e.target.result;
                    textarea.style.backgroundColor = '#f0fdf4'; // Light green to indicate file content
                    textarea.style.borderColor = '#10b981';
                };
                reader.onerror = function() {
                    textarea.value = '';
                    textarea.placeholder = '📁 File uploaded - content will be extracted on submit.';
                };
                reader.readAsText(file);
            } else {
                // For PDF, DOC, DOCX - show message that content will be extracted on server
                textarea.value = '';
                textarea.placeholder = `📁 ${fileName} uploaded - content will be extracted when you submit. For preview, use .txt files.`;
                textarea.style.backgroundColor = '#fef3c7'; // Light yellow to indicate pending extraction
                textarea.style.borderColor = '#f59e0b';
            }
        }
    } else if (displayElement) {
        displayElement.textContent = '';

        // Hide clear file button and action button
        if (clearBtn) {
            clearBtn.style.display = 'none';
        }
        if (actionBtn) {
            actionBtn.style.display = 'none';
        }

        // Re-enable textarea when file is removed
        if (textarea) {
            textarea.style.backgroundColor = '';
            textarea.style.borderColor = '';
            textarea.style.cursor = '';
            textarea.style.opacity = '';
            // Restore previous placeholder based on textarea id
            restoreTextareaPlaceholder(textarea);
            // Restore previous value if available
            if (textarea.dataset.previousValue) {
                textarea.value = textarea.dataset.previousValue;
                delete textarea.dataset.previousValue;
            }
        }

        // Reset upload area style
        const uploadArea = input.closest('.file-upload-area');
        if (uploadArea) {
            uploadArea.style.borderColor = '';
            uploadArea.style.backgroundColor = '';
        }
    }
}

/**
 * Restore textarea placeholder based on its id
 */
function restoreTextareaPlaceholder(textarea) {
    const placeholders = {
        'entries_text': 'Enter standup entries in format:\nName: yesterday task | today task | blockers\n\nExample:\nAlice: Completed user auth API | Working on dashboard UI | Waiting for design specs',
        'notes': 'Paste your meeting notes here...',
        'user_stories': 'Enter user stories (one per line)...\n\nExample:\nAs a user, I want to reset my password so that I can regain access to my account'
    };

    if (textarea.id && placeholders[textarea.id]) {
        textarea.placeholder = placeholders[textarea.id];
    } else {
        textarea.placeholder = 'Enter text here...';
    }
}

/**
 * Setup drag and drop functionality for file upload areas
 */
function setupDragAndDrop() {
    document.querySelectorAll('.file-upload-area').forEach(function(area) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(function(eventName) {
            area.addEventListener(eventName, preventDefaults, false);
        });

        // Highlight drop area when dragging over
        ['dragenter', 'dragover'].forEach(function(eventName) {
            area.addEventListener(eventName, function() {
                area.style.borderColor = '#4f46e5';
                area.style.backgroundColor = '#e0e7ff';
            }, false);
        });

        // Remove highlight when leaving or dropping
        ['dragleave', 'drop'].forEach(function(eventName) {
            area.addEventListener(eventName, function() {
                area.style.borderColor = '';
                area.style.backgroundColor = '';
            }, false);
        });

        // Handle dropped files
        area.addEventListener('drop', function(e) {
            const files = e.dataTransfer.files;
            const fileInput = area.querySelector('input[type="file"]');

            if (files.length > 0 && fileInput) {
                // Create a new DataTransfer to set the files
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(files[0]);
                fileInput.files = dataTransfer.files;

                // Trigger change event to update file name display
                fileInput.dispatchEvent(new Event('change'));
            }
        }, false);
    });
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copied to clipboard!');
    }).catch(function(err) {
        console.error('Failed to copy: ', err);
    });
}

/**
 * Show toast notification
 */
function showToast(message, duration = 3000) {
    // Remove existing toast if any
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #333;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    `;

    document.body.appendChild(toast);

    setTimeout(function() {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(function() {
            if (toast.parentNode) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, duration);
}

// Add CSS animations for toast
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

/**
 * Clear file selection and re-enable textarea
 */
function clearFileSelection(inputId, displayElementId) {
    const fileInput = document.getElementById(inputId);
    const displayElement = document.getElementById(displayElementId);

    if (fileInput) {
        fileInput.value = '';
        // Trigger the updateFileName function to reset UI
        updateFileName(fileInput, displayElementId);
    }
}
