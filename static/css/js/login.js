document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('loginForm');
    const usernameInput = document.getElementById('usernameInput');
    const passwordInput = document.getElementById('passwordInput');
    const errorContainer = document.getElementById('errorContainer');

    if (!form) return;

    form.addEventListener('submit', (e) => {
        // Сбрасываем старую ошибку и подсветку полей
        usernameInput.classList.remove('input-error');
        passwordInput.classList.remove('input-error');
        errorContainer.innerHTML = '';

        let hasError = false;

        if (!usernameInput.value.trim()) {
            usernameInput.classList.add('input-error');
            hasError = true;
        }

        if (!passwordInput.value.trim()) {
            passwordInput.classList.add('input-error');
            hasError = true;
        }

        if (hasError) {
            e.preventDefault(); // Запрещаем отправку формы
            
            // Берем переведенную строчку из data-error-empty формы
            const errorMessage = form.dataset.errorEmpty || 'Заполните все поля!';
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-msg';
            errorDiv.textContent = errorMessage;
            errorContainer.appendChild(errorDiv);
        }
    });

    // Снимаем подсветку ошибки при вводе символов
    [usernameInput, passwordInput].forEach(input => {
        input.addEventListener('input', () => {
            if (input.value.trim()) {
                input.classList.remove('input-error');
            }
        });
    });
});
