/**
 * UI.js - General UI utilities and interactions
 */

// Toast notification system
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed top-20 right-4 z-50 px-6 py-4 rounded-lg shadow-lg max-w-md text-white ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        type === 'warning' ? 'bg-yellow-500' :
        'bg-blue-500'
    }`;
    
    toast.innerHTML = `
        <div class="flex items-center justify-between">
            <p>${message}</p>
            <button onclick="this.parentElement.parentElement.remove()" 
                    class="ml-4 text-white hover:text-gray-200">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Confirm dialog
function confirmAction(message, onConfirm) {
    if (confirm(message)) {
        onConfirm();
    }
}

// Loading spinner
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="flex items-center justify-center py-12">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        `;
    }
}

// HTMX event listeners
document.addEventListener('htmx:beforeRequest', function(event) {
    // Show loading indicator
    const target = event.detail.target;
    if (target) {
        target.classList.add('htmx-loading');
    }
});

document.addEventListener('htmx:afterRequest', function(event) {
    // Remove loading indicator
    const target = event.detail.target;
    if (target) {
        target.classList.remove('htmx-loading');
    }
    
    // Handle errors
    if (!event.detail.successful) {
        showToast('An error occurred. Please try again.', 'error');
    }
});

document.addEventListener('htmx:responseError', function(event) {
    showToast('Server error. Please try again later.', 'error');
});

// Form validation helpers
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('border-red-500');
            isValid = false;
        } else {
            field.classList.remove('border-red-500');
        }
    });
    
    return isValid;
}

// File upload preview
function previewImage(input, previewId) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const preview = document.getElementById(previewId);
            if (preview) {
                preview.src = e.target.result;
                preview.classList.remove('hidden');
            }
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Smooth scroll to element
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copied to clipboard!', 'success');
    }, function(err) {
        showToast('Failed to copy', 'error');
    });
}

// Format numbers
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Debounce function for search inputs
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

// Initialize tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'absolute z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg';
            tooltip.textContent = this.getAttribute('data-tooltip');
            tooltip.style.top = (this.offsetTop - 40) + 'px';
            tooltip.style.left = this.offsetLeft + 'px';
            tooltip.id = 'active-tooltip';
            document.body.appendChild(tooltip);
        });
        
        element.addEventListener('mouseleave', function() {
            const tooltip = document.getElementById('active-tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        });
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initTooltips();
});

// Export for use in other modules
window.showToast = showToast;
window.confirmAction = confirmAction;
window.showLoading = showLoading;
window.validateForm = validateForm;
window.previewImage = previewImage;
window.scrollToElement = scrollToElement;
window.copyToClipboard = copyToClipboard;
window.formatNumber = formatNumber;
window.debounce = debounce;
