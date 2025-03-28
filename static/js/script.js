document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const progressContainer = document.querySelector('.progress-container');
    const progressBar = document.getElementById('progress');
    const progressText = document.getElementById('progress-text');
    const resultContainer = document.getElementById('result-container');
    const originalImage = document.getElementById('original-image');
    const resultImage = document.getElementById('result-image');
    const downloadBtn = document.getElementById('download-btn');
    const processAnotherBtn = document.getElementById('process-another-btn');
    
    // Prevent default behavior for drag events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop area when dragging over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropArea.classList.add('active');
    }
    
    function unhighlight() {
        dropArea.classList.remove('active');
    }
    
    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length) {
            handleFiles(files);
        }
    }
    
    // Handle file input change
    fileInput.addEventListener('change', function() {
        if (this.files.length) {
            handleFiles(this.files);
        }
    });
    
    // Click on drop area to trigger file input
    dropArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    function handleFiles(files) {
        const file = files[0];
        
        if (!file.type.match('image.*')) {
            showError('Please select a valid image file (PNG, JPEG, or JPG)');
            return;
        }
        
        // Show progress bar
        progressContainer.style.display = 'block';
        
        // Prepare form data
        const formData = new FormData();
        formData.append('image', file);
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += 5;
            if (progress > 90) {
                clearInterval(interval);
            }
            progressBar.style.width = progress + '%';
            progressText.textContent = `Processing: ${progress}%`;
        }, 200);
        
        // Send to server
        fetch('/remove-background', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            clearInterval(interval);
            
            if (data.success) {
                // Complete the progress bar
                progressBar.style.width = '100%';
                progressText.textContent = 'Processing: 100%';
                
                // Display the result
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                    resultContainer.style.display = 'block';
                    
                    // Show both original and processed images
                    originalImage.src = data.input_url;
                    resultImage.src = data.output_url;
                    
                    // Set download link
                    downloadBtn.href = data.output_url;
                    
                    // Scroll to results
                    resultContainer.scrollIntoView({ behavior: 'smooth' });
                }, 500);
            } else {
                throw new Error(data.error || 'Failed to process image');
            }
        })
        .catch(error => {
            clearInterval(interval);
            progressContainer.style.display = 'none';
            showError(error.message);
            console.error('Error:', error);
        });
    }
    
    // Show error message
    function showError(message) {
        alert(message);
    }
    
    // Process another image button
    processAnotherBtn.addEventListener('click', function() {
        resultContainer.style.display = 'none';
        progressContainer.style.display = 'none';
        fileInput.value = '';
        originalImage.src = '';
        resultImage.src = '';
        progressBar.style.width = '0%';
        progressText.textContent = 'Processing: 0%';
    });
}); 