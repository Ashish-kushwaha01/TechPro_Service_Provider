// Auth-specific JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Password strength indicator
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = calculatePasswordStrength(password);
            updatePasswordStrength(strength);
        });
    }
    
    // Confirm password validation
    const confirmPasswordInput = document.getElementById('confirm_password');
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            const password = document.getElementById('password').value;
            const confirmPassword = this.value;
            
            if (password && confirmPassword) {
                if (password === confirmPassword) {
                    this.style.borderColor = '#4CAF50';
                } else {
                    this.style.borderColor = '#f44336';
                }
            }
        });
    }
});

function calculatePasswordStrength(password) {
    let score = 0;
    
    // Length check
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    
    // Complexity checks
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    
    return Math.min(score, 5);
}

function updatePasswordStrength(strength) {
    const indicator = document.querySelector('.password-strength');
    if (!indicator) return;
    
    const colors = ['#f44336', '#ff5722', '#ff9800', '#ffc107', '#8bc34a', '#4CAF50'];
    indicator.style.background = colors[0];
    indicator.style.width = `${strength * 20}%`;
    indicator.style.background = colors[strength];
}

// Real-time form validation
function validateRegistrationForm(formData) {
    const errors = [];
    
    if (formData.username.length < 3) {
        errors.push('Username must be at least 3 characters');
    }
    
    if (!validateEmail(formData.email)) {
        errors.push('Please enter a valid email address');
    }
    
    if (formData.password.length < 8) {
        errors.push('Password must be at least 8 characters');
    }
    
    if (formData.password !== formData.confirm_password) {
        errors.push('Passwords do not match');
    }
    
    if (formData.role === 'technician') {
        if (!formData.service_type) {
            errors.push('Please select a service type');
        }
        
        if (!formData.hourly_rate || formData.hourly_rate < 15) {
            errors.push('Hourly rate must be at least $15');
        }
    }
    
    return errors;
}