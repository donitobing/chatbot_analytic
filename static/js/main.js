document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadBox = document.querySelector('.upload-box');
    const uploadedFiles = document.getElementById('uploaded-files');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    
    // Handle drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadBox.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadBox.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadBox.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        uploadBox.classList.add('bg-light');
    }
    
    function unhighlight() {
        uploadBox.classList.remove('bg-light');
    }
    
    // Handle file drop
    uploadBox.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        
        if (file) {
            fileInput.files = dt.files;
            handleFileUpload(file);
        }
    }
    
    // Handle file selection via input
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFileUpload(this.files[0]);
        }
    });
    
    // Handle file upload
    function handleFileUpload(file) {
        // Create file item in UI
        const fileId = 'file-' + Date.now();
        const fileItem = document.createElement('div');
        fileItem.className = 'uploaded-file';
        fileItem.id = fileId;
        
        // Determine icon based on file type
        let fileIcon;
        const fileType = file.name.split('.').pop().toLowerCase();
        
        if (['docx', 'doc'].includes(fileType)) {
            fileIcon = 'bi-file-earmark-word';
        } else if (['xlsx', 'xls'].includes(fileType)) {
            fileIcon = 'bi-file-earmark-excel';
        } else if (fileType === 'pdf') {
            fileIcon = 'bi-file-earmark-pdf';
        } else {
            fileIcon = 'bi-file-earmark-text';
        }
        
        fileItem.innerHTML = `
            <div class="file-icon"><i class="bi ${fileIcon}"></i></div>
            <div class="file-name">${file.name}</div>
            <div class="file-status">
                <div class="loading-dots">
                    <span></span><span></span><span></span>
                </div>
                <span class="ms-1">Processing...</span>
            </div>
        `;
        
        uploadedFiles.appendChild(fileItem);
        
        // Show notification to indicate file is being uploaded
        console.log(`Uploading file: ${file.name}`);
        addMessage(`Uploading file: ${file.name}...`, 'system');
        
        // Send file to server
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log('Response status:', response.status);
            return response.json().catch(err => {
                console.error('Error parsing JSON:', err);
                throw new Error('Invalid server response');
            });
        })
        .then(data => {
            console.log('Response data:', data);
            const fileStatus = document.querySelector(`#${fileId} .file-status`);
            
            if (data && data.success) {
                // Update UI to show success
                fileStatus.innerHTML = '<i class="bi bi-check-circle me-1"></i> Processed';
                fileStatus.classList.add('success');
                
                // Add system message about successful upload
                addMessage('Great! I\'ve processed your document. You can now ask questions about it.', 'system');
            } else {
                // Update UI to show error
                const errorMsg = data && data.error ? data.error : 'Unknown error';
                fileStatus.innerHTML = `<i class="bi bi-x-circle me-1"></i> ${errorMsg}`;
                fileStatus.classList.add('error');
                
                // Add system message about failed upload
                addMessage(`Sorry, there was an issue processing your document: ${errorMsg}`, 'system');
            }
        })
        .catch(error => {
            const fileStatus = document.querySelector(`#${fileId} .file-status`);
            fileStatus.innerHTML = '<i class="bi bi-x-circle me-1"></i> Error';
            fileStatus.classList.add('error');
            
            // Add system message about error
            addMessage('Sorry, there was an error uploading your document. Please try again.', 'system');
            console.error('Error:', error);
        });
    }
    
    // Handle chat submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, 'user');
        
        // Clear input
        chatInput.value = '';
        
        // Add temporary bot response (loading)
        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot-message';
        loadingDiv.id = loadingId;
        loadingDiv.innerHTML = `
            <div class="message-content">
                <div class="loading-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(loadingDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Send message to server
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading message
            document.getElementById(loadingId).remove();
            
            // Add bot response
            if (data.response) {
                addMessage(data.response, 'bot');
            } else {
                addMessage('Sorry, I couldn\'t process your request.', 'bot');
            }
        })
        .catch(error => {
            // Remove loading message
            document.getElementById(loadingId).remove();
            
            // Add error message
            addMessage('Sorry, there was an error processing your request.', 'bot');
            console.error('Error:', error);
        });
    });
    
    // Function to add message to chat
    function addMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${type === 'user' ? message : formatBotMessage(message)}</p>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Format bot message with markdown-like syntax
    function formatBotMessage(message) {
        // Convert line breaks to <br>
        let formattedMessage = message.replace(/\n/g, '<br>');
        
        // Bold text between ** **
        formattedMessage = formattedMessage.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic text between * *
        formattedMessage = formattedMessage.replace(/\*([^\*]+)\*/g, '<em>$1</em>');
        
        // Code blocks
        formattedMessage = formattedMessage.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Inline code
        formattedMessage = formattedMessage.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        return formattedMessage;
    }
});
