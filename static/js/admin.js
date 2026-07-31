document.addEventListener('DOMContentLoaded', () => {
    // ==========================================================================
    // 1. ЖИВОЙ ПОИСК ПО ТАБЛИЦЕ
    // ==========================================================================
    const searchInput = document.getElementById('userSearchInput');
    const userRows = document.querySelectorAll('.user-row');
    const emptyRow = document.getElementById('emptyRow');

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            let visibleCount = 0;

            userRows.forEach(row => {
                const username = row.getAttribute('data-username') || '';
                if (username.includes(query)) {
                    row.style.display = '';
                    row.classList.remove('hidden-row');
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                    row.classList.add('hidden-row');
                }
            });

            if (emptyRow) {
                emptyRow.style.display = (visibleCount === 0) ? '' : 'none';
            }
        });
    }

    // ==========================================================================
    // 2. УПРАВЛЕНИЕ МОДАЛЬНЫМИ ОКНАМИ И СБРОС ОШИБОК
    // ==========================================================================
    const createModal = document.getElementById('createModal');
    const editModal = document.getElementById('editModal');
    
    const openCreateBtn = document.getElementById('openCreateModalBtn');
    const closeCreateBtn = document.getElementById('closeCreateModal');
    const closeEditBtn = document.getElementById('closeEditModal');

    const createForm = document.getElementById('createForm');
    const editForm = document.getElementById('editForm');
    const deleteUserBtn = document.getElementById('deleteUserBtn');

    const createUsernameInput = document.getElementById('createUsername');
    const createPasswordInput = document.getElementById('createPassword');
    const editUsernameInput = document.getElementById('editUsername');
    
    const createErrorContainer = document.getElementById('createErrorContainer');
    const editErrorContainer = document.getElementById('editErrorContainer');

    function resetCreateErrors() {
        if (createUsernameInput) createUsernameInput.classList.remove('input-error');
        if (createPasswordInput) createPasswordInput.classList.remove('input-error');
        if (createErrorContainer) createErrorContainer.innerHTML = '';
    }

    function resetEditErrors() {
        if (editUsernameInput) editUsernameInput.classList.remove('input-error');
        if (editErrorContainer) editErrorContainer.innerHTML = '';
    }

    // Очистка при вводе
    [createUsernameInput, createPasswordInput].forEach(input => {
        if (input) {
            input.addEventListener('input', () => {
                input.classList.remove('input-error');
                if (createErrorContainer) createErrorContainer.innerHTML = '';
            });
        }
    });

    if (editUsernameInput) {
        editUsernameInput.addEventListener('input', () => {
            editUsernameInput.classList.remove('input-error');
            if (editErrorContainer) editErrorContainer.innerHTML = '';
        });
    }

    // Открытие / Закрытие модалок
    if (openCreateBtn && createModal) {
        openCreateBtn.addEventListener('click', () => {
            if (createForm) createForm.reset();
            resetCreateErrors();
            createModal.classList.add('active');
        });
    }

    if (closeCreateBtn && createModal) {
        closeCreateBtn.addEventListener('click', () => {
            createModal.classList.remove('active');
            resetCreateErrors();
        });
    }

    if (closeEditBtn && editModal) {
        closeEditBtn.addEventListener('click', () => {
            editModal.classList.remove('active');
            resetEditErrors();
        });
    }

    window.addEventListener('click', (e) => {
        if (e.target === createModal) {
            createModal.classList.remove('active');
            resetCreateErrors();
        }
        if (e.target === editModal) {
            editModal.classList.remove('active');
            resetEditErrors();
        }
    });

    // Открытие модалки редактирования (Клик на шестеренку)
    document.querySelectorAll('.btn-gear').forEach(btn => {
        btn.addEventListener('click', () => {
            resetEditErrors();

            const username = btn.getAttribute('data-username');
            const status = btn.getAttribute('data-status');
            const rolesAttr = btn.getAttribute('data-roles') || '';
            const roles = rolesAttr.split(',');

            const modalUsernameLabel = document.getElementById('editModalUsername');
            const targetUsernameInput = document.getElementById('editTargetUsername');
            const editStatusSelect = document.getElementById('editStatus');
            const editPasswordInput = document.getElementById('editPassword');

            if (modalUsernameLabel) modalUsernameLabel.textContent = username;
            if (targetUsernameInput) targetUsernameInput.value = username;
            if (editUsernameInput) editUsernameInput.value = username; // Заполняем поле смены логина
            if (editStatusSelect) editStatusSelect.value = status;
            if (editPasswordInput) editPasswordInput.value = '';

            document.querySelectorAll('input[name="editRoles"]').forEach(cb => {
                cb.checked = roles.includes(cb.value);
            });

            if (editModal) {
                editModal.classList.add('active');
            }
        });
    });

    // ==========================================================================
    // 3. ОТПРАВКА ФОРМ С КАСТОМНОЙ ВАЛИДАЦИЕЙ
    // ==========================================================================

    // Создание пользователя
    if (createForm) {
        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            resetCreateErrors();

            const username = createUsernameInput.value.trim();
            const password = createPasswordInput.value.trim();
            const status = document.getElementById('createStatus').value;
            
            if (!username || !password) {
                if (!username) createUsernameInput.classList.add('input-error');
                if (!password) createPasswordInput.classList.add('input-error');

                const errorMessage = createForm.dataset.errorEmpty || 'Заполните все поля!';
                
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-msg';
                errorDiv.textContent = errorMessage;
                createErrorContainer.appendChild(errorDiv);
                return;
            }

            const roles = [];
            document.querySelectorAll('input[name="createRoles"]:checked').forEach(cb => {
                roles.push(cb.value);
            });

            try {
                const res = await fetch('/admin/api/users/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password, roles, status })
                });

                const data = await res.json();

                if (data.success) {
                    window.location.reload();
                } else {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error-msg';
                    errorDiv.textContent = data.message || 'Ошибка';
                    createErrorContainer.appendChild(errorDiv);
                }
            } catch (err) {
                console.error('Error creating user:', err);
            }
        });
    }

    // Редактирование пользователя
    if (editForm) {
        editForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            resetEditErrors();

            const oldUsername = document.getElementById('editTargetUsername').value;
            const newUsername = editUsernameInput.value.trim();
            const password = document.getElementById('editPassword').value.trim();
            const status = document.getElementById('editStatus').value;

            if (!newUsername) {
                editUsernameInput.classList.add('input-error');
                const errorMessage = editForm.dataset.errorEmpty || 'Заполните все поля!';
                
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-msg';
                errorDiv.textContent = errorMessage;
                editErrorContainer.appendChild(errorDiv);
                return;
            }

            const roles = [];
            document.querySelectorAll('input[name="editRoles"]:checked').forEach(cb => {
                roles.push(cb.value);
            });

            try {
                const res = await fetch('/admin/api/users/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        old_username: oldUsername, 
                        new_username: newUsername, 
                        password, 
                        roles, 
                        status 
                    })
                });

                const data = await res.json();

                if (data.success) {
                    window.location.reload();
                } else {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error-msg';
                    errorDiv.textContent = data.message || 'Ошибка';
                    editErrorContainer.appendChild(errorDiv);
                }
            } catch (err) {
                console.error('Error updating user:', err);
            }
        });
    }

    // Удаление пользователя
    if (deleteUserBtn) {
        deleteUserBtn.addEventListener('click', async () => {
            resetEditErrors();
            const username = document.getElementById('editTargetUsername').value;
            const confirmMsg = editForm.dataset.confirmDelete || 'Удалить пользователя';
            
            if (!confirm(`${confirmMsg}: ${username}?`)) return;

            try {
                const res = await fetch('/admin/api/users/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username })
                });

                const data = await res.json();

                if (data.success) {
                    window.location.reload();
                } else {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error-msg';
                    errorDiv.textContent = data.message || 'Ошибка';
                    editErrorContainer.appendChild(errorDiv);
                }
            } catch (err) {
                console.error('Error deleting user:', err);
            }
        });
    }
});