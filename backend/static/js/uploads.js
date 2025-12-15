/**
 * Uploads.js - File upload handling with preview
 */

// Handle image upload with preview
class ImageUploader {
    constructor(inputId, previewId, options = {}) {
        this.input = document.getElementById(inputId);
        this.preview = document.getElementById(previewId);
        this.options = {
            maxSize: options.maxSize || 5 * 1024 * 1024, // 5MB default
            allowedTypes: options.allowedTypes || ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'],
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.input) return;
        
        this.input.addEventListener('change', (e) => this.handleFileSelect(e));
    }
    
    handleFileSelect(event) {
        const file = event.target.files[0];
        
        if (!file) return;
        
        // Validate file type
        if (!this.options.allowedTypes.includes(file.type)) {
            showToast('Invalid file type. Please upload an image.', 'error');
            this.input.value = '';
            return;
        }
        
        // Validate file size
        if (file.size > this.options.maxSize) {
            const maxSizeMB = (this.options.maxSize / (1024 * 1024)).toFixed(1);
            showToast(`File too large. Maximum size is ${maxSizeMB}MB.`, 'error');
            this.input.value = '';
            return;
        }
        
        // Show preview
        this.showPreview(file);
    }
    
    showPreview(file) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            if (this.preview) {
                if (this.preview.tagName === 'IMG') {
                    this.preview.src = e.target.result;
                    this.preview.classList.remove('hidden');
                } else {
                    this.preview.innerHTML = `
                        <img src="${e.target.result}" 
                             alt="Preview" 
                             class="max-w-full h-auto rounded-lg">
                    `;
                }
            }
        };
        
        reader.readAsDataURL(file);
    }
}

// Handle multiple file uploads (for portfolios)
class MultipleImageUploader {
    constructor(inputId, previewContainerId, options = {}) {
        this.input = document.getElementById(inputId);
        this.previewContainer = document.getElementById(previewContainerId);
        this.files = [];
        this.options = {
            maxFiles: options.maxFiles || 10,
            maxSize: options.maxSize || 5 * 1024 * 1024,
            allowedTypes: options.allowedTypes || ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'],
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.input) return;
        
        this.input.addEventListener('change', (e) => this.handleFilesSelect(e));
    }
    
    handleFilesSelect(event) {
        const newFiles = Array.from(event.target.files);
        
        // Check max files limit
        if (this.files.length + newFiles.length > this.options.maxFiles) {
            showToast(`Maximum ${this.options.maxFiles} files allowed.`, 'error');
            return;
        }
        
        // Validate each file
        newFiles.forEach(file => {
            if (!this.options.allowedTypes.includes(file.type)) {
                showToast(`Skipped ${file.name}: Invalid file type.`, 'warning');
                return;
            }
            
            if (file.size > this.options.maxSize) {
                showToast(`Skipped ${file.name}: File too large.`, 'warning');
                return;
            }
            
            this.files.push(file);
            this.addPreview(file, this.files.length - 1);
        });
        
        // Clear input
        this.input.value = '';
    }
    
    addPreview(file, index) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            const previewDiv = document.createElement('div');
            previewDiv.className = 'relative group';
            previewDiv.innerHTML = `
                <img src="${e.target.result}" 
                     alt="${file.name}" 
                     class="w-full h-32 object-cover rounded-lg">
                <button type="button" 
                        onclick="removeFile(${index})"
                        class="absolute top-2 right-2 bg-red-600 text-white w-8 h-8 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                    <i class="fas fa-times"></i>
                </button>
                <div class="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded">
                    ${(file.size / 1024).toFixed(1)} KB
                </div>
            `;
            
            this.previewContainer.appendChild(previewDiv);
        };
        
        reader.readAsDataURL(file);
    }
    
    removeFile(index) {
        this.files.splice(index, 1);
        this.refreshPreviews();
    }
    
    refreshPreviews() {
        this.previewContainer.innerHTML = '';
        this.files.forEach((file, index) => {
            this.addPreview(file, index);
        });
    }
    
    getFiles() {
        return this.files;
    }
}

// Document upload handler
class DocumentUploader {
    constructor(inputId, options = {}) {
        this.input = document.getElementById(inputId);
        this.options = {
            maxSize: options.maxSize || 10 * 1024 * 1024, // 10MB default
            allowedTypes: options.allowedTypes || [
                'application/pdf',
                'image/jpeg',
                'image/png',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ],
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.input) return;
        
        this.input.addEventListener('change', (e) => this.handleFileSelect(e));
    }
    
    handleFileSelect(event) {
        const file = event.target.files[0];
        
        if (!file) return;
        
        // Validate file type
        if (!this.options.allowedTypes.includes(file.type)) {
            showToast('Invalid file type. Please upload a valid document.', 'error');
            this.input.value = '';
            return;
        }
        
        // Validate file size
        if (file.size > this.options.maxSize) {
            const maxSizeMB = (this.options.maxSize / (1024 * 1024)).toFixed(1);
            showToast(`File too large. Maximum size is ${maxSizeMB}MB.`, 'error');
            this.input.value = '';
            return;
        }
        
        // Show file info
        this.showFileInfo(file);
    }
    
    showFileInfo(file) {
        const fileInfo = document.getElementById('file-info');
        if (fileInfo) {
            fileInfo.innerHTML = `
                <div class="flex items-center p-3 bg-green-50 border border-green-200 rounded-lg">
                    <i class="fas fa-file-alt text-green-600 mr-3"></i>
                    <div class="flex-1">
                        <p class="font-semibold text-green-900">${file.name}</p>
                        <p class="text-sm text-green-700">${(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                    <i class="fas fa-check-circle text-green-600"></i>
                </div>
            `;
        }
    }
}

// Export for global use
window.ImageUploader = ImageUploader;
window.MultipleImageUploader = MultipleImageUploader;
window.DocumentUploader = DocumentUploader;
