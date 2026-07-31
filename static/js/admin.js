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
                const fullContent = row.textContent.toLowerCase();

                if (username.includes(query) || fullContent.includes(query)) {
                    row.classList.remove('hidden-row');
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.classList.add('hidden-row');
                    row.style.display = 'none';
                }
            });

            if (emptyRow) {
                emptyRow.style.display = (visibleCount === 0) ? '' : 'none';
            }
        });
    }

    // ==========================================================================
    // 2. УПРАВЛЕНИЕ МОДАЛЬНЫМИ ОКНАМИ
    // ==========================================================================
    const createModal = document.getElementById('createModal');
    const editModal = document.getElementById('editModal');
    
    const openCreateBtn = document.getElementById('openCreateModalBtn');
    const closeCreateBtn = document.getElementById('closeCreateModal');
    const closeEditBtn = document.getElementById('closeEditModal');

    const createForm = document.getElementById('createForm');
    const editForm = document.getElementById('editForm');
    const deleteUserBtn = document.getElementById('deleteUserBtn');

    // --- Открытие / Закрытие модалки создания ---
    if (openCreateBtn && createModal) {
        openCreateBtn.addEventListener('click', () => {
            if (createForm) createForm.reset();
            createModal.classList.add('active');
        });
    }

    if (closeCreateBtn && createModal) {
        closeCreateBtn.addEventListener('click', () => {
            createModal.classList.remove('active');
        });
    }

    // --- Закрытие модалки редактирования ---
    if (closeEditBtn && editModal) {
        closeEditBtn.addEventListener('click', () => {
            editModal.classList.remove('active');
        });
    }

    // --- Закрытие по клику на затемненный фон (Backdrop) ---
    window.addEventListener('click', (e) => {
        if (e.target === createModal) createModal.classList.remove('active');
        if (e.target === editModal) editModal.classList.remove('active');
    });

    // --- Открытие модалки редактирования (Клик на шестеренку) ---
    document.querySelectorAll('.btn-gear').forEach(btn => {
        btn.addEventListener('click', () => {
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
            if (editStatusSelect) editStatusSelect.value = status;
            if (editPasswordInput) editPasswordInput.value = '';

            // Выставление чекбоксов ролей
            document.querySelectorAll('input[name="editRoles"]').forEach(cb => {
                cb.checked = roles.includes(cb.value);
            });

            if (editModal) {
                editModal.classList.add('active');
            }
        });
    });

    // ==========================================================================
    // 3. ОТПРАВКА ФОРМ (API)
    // ==========================================================================

    // --- Создание пользователя ---
    if (createForm) {
        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('createUsername').value.trim();
            const password = document.getElementById('createPassword').value.trim();
            const status = document.getElementById('createStatus').value;
            
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
                    alert(data.message || 'Error');
                }
            } catch (err) {
                console.error('Error creating user:', err);
            }
        });
    }

    // --- Редактирование пользователя ---
    if (editForm) {
        editForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('editTargetUsername').value;
            const password = document.getElementById('editPassword').value.trim();
            const status = document.getElementById('editStatus').value;

            const roles = [];
            document.querySelectorAll('input[name="editRoles"]:checked').forEach(cb => {
                roles.push(cb.value);
            });

            try {
                const res = await fetch('/admin/api/users/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password, roles, status })
                });

                const data = await res.json();

                if (data.success) {
                    window.location.reload();
                } else {
                    alert(data.message || 'Error');
                }
            } catch (err) {
                console.error('Error updating user:', err);
            }
        });
    }

    // --- Удаление пользователя ---
    if (deleteUserBtn) {
        deleteUserBtn.addEventListener('click', async () => {
            const username = document.getElementById('editTargetUsername').value;
            if (!confirm(`${username}?`)) return;

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
                    alert(data.message || 'Error');
                }
            } catch (err) {
                console.error('Error deleting user:', err);
            }
        });
    }
});