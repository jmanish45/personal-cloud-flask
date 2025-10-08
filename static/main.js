// Debug and prevent auto-redirects
console.log('Page loaded:', window.location.pathname);

// Prevent automatic redirects and handle errors gracefully
(function() {
    // Clear any existing timeouts that might cause redirects
    const highestTimeoutId = setTimeout(';');
    for (let i = 0; i < highestTimeoutId; i++) {
        clearTimeout(i);
    }
    
    // Clear any existing intervals
    const highestIntervalId = setInterval(';');
    for (let i = 0; i < highestIntervalId; i++) {
        clearInterval(i);
    }
})();

// Main initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('CloudDrive initialized on:', window.location.pathname);
    
    // Prevent any uncaught errors from causing redirects
    window.addEventListener('error', function(e) {
        console.error('JavaScript error caught:', e.error);
        e.preventDefault(); // Prevent default error handling
        return true; // Don't propagate the error
    });
    
    // Page-specific initialization
    const currentPath = window.location.pathname;
    
    if (currentPath === '/login' || currentPath === '/signup') {
        initAuthPages();
    } else if (currentPath === '/' || currentPath.includes('index')) {
        initDashboard();
    }
    
    // Check for page stability after 3 seconds
    setTimeout(() => {
        console.log('Page still active after 3 seconds');
    }, 3000);
});

// Initialize authentication pages (login/signup)
function initAuthPages() {
    console.log('Initializing auth page');
    
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        // Prevent double submission
        form.addEventListener('submit', function(e) {
            console.log('Form submitted:', form.action, form.method);
            
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = 'Please wait...';
                
                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    submitButton.disabled = false;
                    submitButton.textContent = submitButton.dataset.originalText || 'Submit';
                }, 5000);
            }
        });
        
        // Store original button text
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton && !submitButton.dataset.originalText) {
            submitButton.dataset.originalText = submitButton.textContent;
        }
    });
    
    // Prevent any automatic form submissions
    window.addEventListener('beforeunload', function(e) {
        console.log('Auth page is being unloaded');
    });
}

// Initialize dashboard/main app pages
function initDashboard() {
    console.log('Initializing dashboard');
    
    try {
        initFileUpload();
        initViewToggle();
        initSearchEnhancements();
        initShareHandling();
        initDragDrop();
        loadViewPreference();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
    }
}

// File Upload Enhancement
function initFileUpload() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput) return;
    
    try {
        fileInput.addEventListener('change', function(e) {
            updateFileName(this);
            validateFileSize(this);
        });
    } catch (error) {
        console.error('Error initializing file upload:', error);
    }
}

// Update file name display
function updateFileName(input) {
    const fileNameDisplay = document.getElementById('fileName');
    if (!fileNameDisplay) return;
    
    try {
        if (input.files && input.files[0]) {
            const file = input.files[0];
            const fileName = file.name;
            const fileSize = formatFileSize(file.size);
            fileNameDisplay.textContent = `${fileName} (${fileSize})`;
            fileNameDisplay.classList.remove('text-white');
            fileNameDisplay.classList.add('text-blue-100', 'font-medium');
        } else {
            fileNameDisplay.textContent = 'No file selected';
            fileNameDisplay.classList.remove('text-blue-100', 'font-medium');
            fileNameDisplay.classList.add('text-white');
        }
    } catch (error) {
        console.error('Error updating file name:', error);
    }
}

// Validate file size (max 50MB)
function validateFileSize(input) {
    const maxSize = 50 * 1024 * 1024; // 50MB in bytes
    
    try {
        if (input.files && input.files[0]) {
            if (input.files[0].size > maxSize) {
                alert('File size exceeds 50MB limit. Please choose a smaller file.');
                input.value = '';
                updateFileName(input);
                return false;
            }
        }
        return true;
    } catch (error) {
        console.error('Error validating file size:', error);
        return false;
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// View Toggle (Grid/List)
function initViewToggle() {
    const gridBtn = document.getElementById('gridViewBtn');
    const listBtn = document.getElementById('listViewBtn');
    
    if (!gridBtn || !listBtn) return;
    
    try {
        gridBtn.addEventListener('click', function() {
            toggleView('grid');
        });
        
        listBtn.addEventListener('click', function() {
            toggleView('list');
        });
        
        // Initialize with saved preference or grid view
        const savedView = localStorage.getItem('viewPreference') || 'grid';
        toggleView(savedView);
    } catch (error) {
        console.error('Error initializing view toggle:', error);
    }
}

// Toggle between grid and list view
function toggleView(view) {
    try {
        const gridViews = document.querySelectorAll('.grid-view');
        const listViews = document.querySelectorAll('.list-view');
        const gridBtn = document.getElementById('gridViewBtn');
        const listBtn = document.getElementById('listViewBtn');
        
        if (!gridBtn || !listBtn) return;
        
        if (view === 'grid') {
            gridViews.forEach(el => el.classList.remove('hidden'));
            listViews.forEach(el => el.classList.add('hidden'));
            
            gridBtn.classList.add('view-btn-active', 'bg-blue-600', 'text-white');
            gridBtn.classList.remove('text-gray-600');
            listBtn.classList.remove('view-btn-active', 'bg-blue-600', 'text-white');
            listBtn.classList.add('text-gray-600');
            
            localStorage.setItem('viewPreference', 'grid');
        } else {
            gridViews.forEach(el => el.classList.add('hidden'));
            listViews.forEach(el => el.classList.remove('hidden'));
            
            listBtn.classList.add('view-btn-active', 'bg-blue-600', 'text-white');
            listBtn.classList.remove('text-gray-600');
            gridBtn.classList.remove('view-btn-active', 'bg-blue-600', 'text-white');
            gridBtn.classList.add('text-gray-600');
            
            localStorage.setItem('viewPreference', 'list');
        }
    } catch (error) {
        console.error('Error toggling view:', error);
    }
}

// Load saved view preference
function loadViewPreference() {
    try {
        const savedView = localStorage.getItem('viewPreference') || 'grid';
        toggleView(savedView);
    } catch (error) {
        console.error('Error loading view preference:', error);
    }
}

// Search Enhancements
function initSearchEnhancements() {
    const searchInput = document.querySelector('input[name="query"]');
    
    if (!searchInput) return;
    
    try {
        searchInput.addEventListener('input', debounce(function(e) {
            console.log('Search query:', e.target.value);
        }, 300));
    } catch (error) {
        console.error('Error initializing search:', error);
    }
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Share Handling
function initShareHandling() {
    try {
        document.querySelectorAll('.share-form').forEach(form => {
            form.addEventListener('submit', function(e) {
                console.log('Share form submitted');
            });
        });
    } catch (error) {
        console.error('Error initializing share handling:', error);
    }
}

// Copy text to clipboard
function copyToClipboard(text) {
    try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function() {
                showNotification('Link copied to clipboard!', 'success');
            }).catch(function(err) {
                console.error('Could not copy text: ', err);
                showNotification('Failed to copy link', 'error');
            });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                showNotification('Link copied to clipboard!', 'success');
            } catch (err) {
                console.error('Could not copy text: ', err);
                showNotification('Failed to copy link', 'error');
            }
            document.body.removeChild(textArea);
        }
    } catch (error) {
        console.error('Error copying to clipboard:', error);
    }
}

// Show notification
function showNotification(message, type = 'info') {
    try {
        const notification = document.createElement('div');
        notification.className = `fixed top-20 right-4 z-50 max-w-md bg-white rounded-lg shadow-lg border-l-4 p-4 animate-slide-in ${
            type === 'success' ? 'border-green-500' : 
            type === 'error' ? 'border-red-500' : 
            'border-blue-500'
        }`;
        
        notification.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    ${type === 'success' ? 
                        '<svg class="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>' :
                    type === 'error' ?
                        '<svg class="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>' :
                        '<svg class="h-5 w-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>'
                    }
                </div>
                <div class="ml-3 flex-1">
                    <p class="text-sm font-medium text-gray-900">${message}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 flex-shrink-0">
                    <svg class="h-4 w-4 text-gray-400 hover:text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.transition = 'opacity 0.5s';
                notification.style.opacity = '0';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 500);
            }
        }, 5000);
    } catch (error) {
        console.error('Error showing notification:', error);
    }
}

// Delete confirmation
function confirmDelete(filename) {
    try {
        return confirm(`Are you sure you want to delete "${filename}"?\n\nThis action cannot be undone.`);
    } catch (error) {
        console.error('Error showing delete confirmation:', error);
        return false;
    }
}

// Initialize drag and drop for file upload
function initDragDrop() {
    const uploadSection = document.querySelector('.bg-gradient-to-br');
    
    if (!uploadSection) return;
    
    try {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadSection.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadSection.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadSection.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight(e) {
            uploadSection.classList.add('border-4', 'border-blue-400', 'border-dashed');
        }
        
        function unhighlight(e) {
            uploadSection.classList.remove('border-4', 'border-blue-400', 'border-dashed');
        }
        
        uploadSection.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            const fileInput = document.getElementById('fileInput');
            
            if (fileInput && files.length > 0) {
                fileInput.files = files;
                updateFileName(fileInput);
            }
        }
    } catch (error) {
        console.error('Error initializing drag and drop:', error);
    }
}