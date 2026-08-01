document.addEventListener('DOMContentLoaded', () => {
    // ==========================================================================
    // 1. ИНИЦИАЛИЗАЦИЯ И УПРАВЛЕНИЕ КАСТОМНЫМИ ВЫПАДАЮЩИМИ СПИСКАМИ (DROPDOWNS)
    // ==========================================================================
    const roleDropdown = document.getElementById('roleDropdown');
    const roleDropdownBtn = document.getElementById('roleDropdownBtn');
    const roleDropdownLabel = document.getElementById('roleDropdownLabel');
    const selectAllRoles = document.getElementById('selectAllRoles');
    const roleFilterCbs = Array.from(document.querySelectorAll('.role-filter-cb'));

    const sortDropdown = document.getElementById('sortDropdown');
    const sortDropdownBtn = document.getElementById('sortDropdownBtn');
    const sortDropdownLabel = document.getElementById('sortDropdownLabel');
    const sortOptions = document.querySelectorAll('.sort-option');

    let activeSortValue = 'default';

    // Открытие/закрытие списка ролей
    if (roleDropdownBtn && roleDropdown) {
        roleDropdownBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            sortDropdown?.classList.remove('active');
            roleDropdown.classList.toggle('active');
        });
    }

    // Открытие/закрытие списка сортировки
    if (sortDropdownBtn && sortDropdown) {
        sortDropdownBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            roleDropdown?.classList.remove('active');
            sortDropdown.classList.toggle('active');
        });
    }

    // Закрытие всех выпадающих списков при клике вне их области
    document.addEventListener('click', () => {
        roleDropdown?.classList.remove('active');
        sortDropdown?.classList.remove('active');
    });

    // Предотвращаем закрытие списка ролей при клике внутри меню
    const roleDropdownMenu = document.getElementById('roleDropdownMenu');
    if (roleDropdownMenu) {
        roleDropdownMenu.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    // ==========================================================================
    // 2. ЛОГИКА МУЛЬТИ-СЕЛЕКТА РОЛЕЙ И СОРТИРОВКИ
    // ==========================================================================
    
    // Переключение пункта "Все роли"
    if (selectAllRoles) {
        selectAllRoles.addEventListener('change', () => {
            if (selectAllRoles.checked) {
                roleFilterCbs.forEach(cb => cb.checked = false);
            }
            updateRoleLabel();
            updateTable();
        });
    }

    // Переключение отдельных чекбоксов ролей
    roleFilterCbs.forEach(cb => {
        cb.addEventListener('change', () => {
            const anyChecked = roleFilterCbs.some(c => c.checked);
            if (anyChecked) {
                if (selectAllRoles) selectAllRoles.checked = false;
            } else {
                if (selectAllRoles) selectAllRoles.checked = true;
            }
            updateRoleLabel();
            updateTable();
        });
    });

    // Обновление заголовка кнопки фильтра ролей
    function updateRoleLabel() {
        const checkedCbs = roleFilterCbs.filter(c => c.checked);
        const allText = roleDropdownLabel.getAttribute('data-text-all') || 'Все роли';

        if (!selectAllRoles || selectAllRoles.checked || checkedCbs.length === 0) {
            roleDropdownLabel.textContent = allText;
        } else if (checkedCbs.length === 1) {
            const spanText = checkedCbs[0].nextElementSibling.textContent;
            roleDropdownLabel.textContent = spanText;
        } else {
            roleDropdownLabel.textContent = `${allText} (${checkedCbs.length})`;
        }
    }

    // Выбор опции сортировки
    sortOptions.forEach(option => {
        option.addEventListener('click', () => {
            sortOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');

            activeSortValue = option.getAttribute('data-value');
            sortDropdownLabel.textContent = option.textContent;
            sortDropdown.classList.remove('active');

            updateTable();
        });
    });

    // ==========================================================================
    // 3. ЖИВОЙ ПОИСК, ФИЛЬТРАЦИЯ И СОРТИРОВКА ТАБЛИЦЫ
    // ==========================================================================
    const searchInput = document.getElementById('userSearchInput');
    const tableBody = document.getElementById('usersTableBody');
    const userRows = Array.from(document.querySelectorAll('.user-row'));
    const emptyRow = document.getElementById('emptyRow');

    function updateTable() {
        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const selectedRoles = roleFilterCbs.filter(c => c.checked).map(c => c.value);
        const isAllRoles = !selectAllRoles || selectAllRoles.checked || selectedRoles.length === 0;

        let visibleRows = [];

        userRows.forEach(row => {
            const username = row.getAttribute('data-username') || '';
            const rolesAttr = row.getAttribute('data-roles') || '';
            const userRolesList = rolesAttr.split(',').map(r => r.trim());

            const matchesSearch = username.includes(query);
            const matchesRole = isAllRoles || selectedRoles.some(r => userRolesList.includes(r));

            if (matchesSearch && matchesRole) {
                row.style.display = '';
                row.classList.remove('hidden-row');
                visibleRows.push(row);
            } else {
                row.style.display = 'none';
                row.classList.add('hidden-row');
            }
        });

        // Сортировка по балансу
        if (activeSortValue !== 'default') {
            visibleRows.sort((a, b) => {
                const amountA = parseFloat(a.getAttribute('data-amount') || '0') || 0;
                const amountB = parseFloat(b.getAttribute('data-amount') || '0') || 0;

                return activeSortValue === 'asc' ? amountA - amountB : amountB - amountA;
            });
        }

        visibleRows.forEach(row => tableBody.appendChild(row));

        if (emptyRow) {
            tableBody.appendChild(emptyRow);
            emptyRow.style.display = (visibleRows.length === 0) ? '' : 'none';
        }
    }

    if (searchInput) searchInput.addEventListener('input', updateTable);

    // ==========================================================================
    // 4. УПРАВЛЕНИЕ МОДАЛЬНЫМИ ОКНАМИ И ВАЛИДАЦИЯ
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
            if (editUsernameInput) editUsernameInput.value = username;
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