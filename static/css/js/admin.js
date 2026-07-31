document.addEventListener('DOMContentLoaded', () => {
    // --------------------------------------------------------------------------
    // 1. МГНОВЕННЫЙ ЖИВОЙ ПОИСК ПРИ ВВОДЕ БУКВ (INPUT EVENT)
    // --------------------------------------------------------------------------
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

    // --------------------------------------------------------------------------
    // 2. МОДАЛЬНЫЕ ОКНА (СОЗДАНИЕ И РЕДАКТИРОВАНИЕ)
    // --------------------------------------------------------------------------
    const createModal = document.getElementById('createModal');
    const editModal = document.getElementById('editModal');
    
    const openCreateBtn = document.getElementById('openCreateModalBtn');
    const closeCreateBtn = document.getElementById('closeCreateModal');
    const closeEditBtn = document.getElementById('closeEditModal');

    if (openCreateBtn && createModal) {
        openCreateBtn.addEventListener('click', () => {
            createModal.classList.add('active');
        });
    }

    if (closeCreateBtn && createModal) {
        closeCreateBtn.addEventListener('click', () => {
            createModal.classList.remove('active');
        });
    }

    if (closeEditBtn && editModal) {
        closeEditBtn.addEventListener('click', () => {
            editModal.classList.remove('active');
        });
    }

    // Клик по шестеренке для редактирования
    document.querySelectorAll('.btn-gear').forEach(btn => {
        btn.addEventListener('click', () => {
            const username = btn.getAttribute('data-username');
            const status = btn.getAttribute('data-status');
            const rolesAttr = btn.getAttribute('data-roles') || '';
            const roles = rolesAttr.split(',');

            document.getElementById('editModalUsername').textContent = username;
            document.getElementById('editTargetUsername').value = username;
            document.getElementById('editStatus').value = status;

            document.querySelectorAll('input[name="editRoles"]').forEach(cb => {
                cb.checked = roles.includes(cb.value);
            });

            if (editModal) {
                editModal.classList.add('active');
            }
        });
    });

    // --------------------------------------------------------------------------
    // 3. ОТПРАВКА ФОРМ НА СЕРВЕР (CREATE / UPDATE / DELETE)
    // --------------------------------------------------------------------------
    const createForm = document.getElementById('createForm');
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

            const res = await fetch('/admin/api/users/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, roles, status })
            });
            const data = await res.json();

            if (data.success) {
                window.location.reload();
            } else {
                alert(data.message || 'Ошибка создания');
            }
        });
    }

    const editForm = document.getElementById('editForm');
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

            const res = await fetch('/admin/api/users/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, roles, status })
            });
            const data = await res.json();

            if (data.success) {
                window.location.reload();
            } else {
                alert(data.message || 'Ошибка обновления');
            }
        });
    }

    const deleteUserBtn = document.getElementById('deleteUserBtn');
    if (deleteUserBtn) {
        deleteUserBtn.addEventListener('click', async () => {
            const username = document.getElementById('editTargetUsername').value;
            if (!confirm(`Удалить пользователя ${username}?`)) return;

            const res = await fetch('/admin/api/users/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username })
            });
            const data = await res.json();

            if (data.success) {
                window.location.reload();
            } else {
                alert(data.message || 'Ошибка удаления');
            }
        });
    }
});