document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('loginForm');
    const usernameInput = document.getElementById('usernameInput');
    const passwordInput = document.getElementById('passwordInput');
    const errorContainer = document.getElementById('errorContainer');

    if (!form) return;

    form.addEventListener('submit', (e) => {
        usernameInput.classList.remove('input-error');
        passwordInput.classList.remove('input-error');
        errorContainer.innerHTML = '';

        const usernameVal = usernameInput.value.trim();
        const passwordVal = passwordInput.value.trim();

        if (!usernameVal || !passwordVal) {
            e.preventDefault();
            
            if (!usernameVal) usernameInput.classList.add('input-error');
            if (!passwordVal) passwordInput.classList.add('input-error');

            const errorMessage = form.dataset.errorEmpty || 'Заполните все поля!';
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-msg';
            errorDiv.textContent = errorMessage;
            errorContainer.appendChild(errorDiv);
        }
    });

    [usernameInput, passwordInput].forEach(input => {
        input.addEventListener('input', () => {
            if (input.value.trim()) {
                input.classList.remove('input-error');
            }
        });
    });
});