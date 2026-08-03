document.addEventListener('DOMContentLoaded', () => {
    // ==========================================================================
    // 1. УНИВЕРСАЛЬНАЯ ЛОГИКА ДЛЯ ВСЕХ КАСТОМНЫХ ВЫПАДАЮЩИХ СПИСКОВ
    // ==========================================================================
    
    // Переключение открытого/закрытого состояния любого дропдауна
    document.querySelectorAll('.custom-dropdown').forEach(dropdown => {
        const btn = dropdown.querySelector('.custom-dropdown-btn');
        if (btn) {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                // Закрываем все остальные открытые меню
                document.querySelectorAll('.custom-dropdown.active').forEach(other => {
                    if (other !== dropdown) other.classList.remove('active');
                });
                dropdown.classList.toggle('active');
            });
        }
    });

    // Закрываем все выпадающие списки при клике в любую точку экрана
    document.addEventListener('click', () => {
        document.querySelectorAll('.custom-dropdown.active').forEach(d => {
            d.classList.remove('active');
        });
    });

    // Предотвращаем закрытие при клике внутри меню с чекбоксами (фильтр ролей)
    const roleDropdownMenu = document.getElementById('roleDropdownMenu');
    if (roleDropdownMenu) {
        roleDropdownMenu.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    // Обработка выбора статуса в модальных окнах (Создание / Редактирование)
    document.querySelectorAll('.modal-dropdown').forEach(dropdown => {
        const hiddenInput = dropdown.querySelector('input[type="hidden"]');
        const label = dropdown.querySelector('.custom-dropdown-btn span');
        const options = dropdown.querySelectorAll('.status-option');

        options.forEach(option => {
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                const val = option.getAttribute('data-value');
                
                if (hiddenInput) hiddenInput.value = val;
                if (label) label.textContent = val;

                options.forEach(o => o.classList.remove('active'));
                option.classList.add('active');

                dropdown.classList.remove('active');
            });
        });
    });

    // ==========================================================================
    // 2. ЛОГИКА ФИЛЬТРАЦИИ И СОРТИРОВКИ В ВЕРХНЕЙ ПАНЕЛИ
    // ==========================================================================
    const roleDropdownLabel = document.getElementById('roleDropdownLabel');
    const selectAllRoles = document.getElementById('selectAllRoles');
    const roleFilterCbs = Array.from(document.querySelectorAll('.role-filter-cb'));

    const sortDropdown = document.getElementById('sortDropdown');
    const sortDropdownLabel = document.getElementById('sortDropdownLabel');
    const sortOptions = document.querySelectorAll('.sort-option');

    let activeSortValue = 'default';

    if (selectAllRoles) {
        selectAllRoles.addEventListener('change', () => {
            if (selectAllRoles.checked) {
                roleFilterCbs.forEach(cb => cb.checked = false);
            }
            updateRoleLabel();
            updateTable();
        });
    }

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

    function updateRoleLabel() {
        if (!roleDropdownLabel) return;
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

    sortOptions.forEach(option => {
        option.addEventListener('click', () => {
            sortOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');

            activeSortValue = option.getAttribute('data-value');
            if (sortDropdownLabel) sortDropdownLabel.textContent = option.textContent;
            if (sortDropdown) sortDropdown.classList.remove('active');

            updateTable();
        });
    });

    function parseAmountValue(rawAttrValue) {
        if (!rawAttrValue) return 0;
        const cleaned = rawAttrValue.replace(/[^0-9.-]+/g, '');
        const val = parseFloat(cleaned);
        return isNaN(val) ? 0 : val;
    }

    // ==========================================================================
    // 3. ЖИВОЙ ПОИСК И ТАБЛИЦА
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

        if (activeSortValue !== 'default') {
            visibleRows.sort((a, b) => {
                const amountA = parseAmountValue(a.getAttribute('data-amount'));
                const amountB = parseAmountValue(b.getAttribute('data-amount'));
                return activeSortValue === 'asc' ? amountA - amountB : amountB - amountA;
            });
        }

        visibleRows.forEach(row => tableBody.appendChild(row));

        if (emptyRow) {
            tableBody.appendChild(emptyRow);
            emptyRow.style.display = (visibleRows.length === 0) ? '' : 'none';
        }
        
        updateBulkSelection();
    }

    if (searchInput) searchInput.addEventListener('input', updateTable);

    // ==========================================================================
    // 4. МАССОВОЕ ВЫДЕЛЕНИЕ И УДАЛЕНИЕ (SELECTION MODE & BULK ACTIONS)
    // ==========================================================================
    const adminContainer = document.getElementById('adminContainer');
    const toggleSelectModeBtn = document.getElementById('toggleSelectModeBtn');
    const selectAllUsersCb = document.getElementById('selectAllUsers');
    const bulkActionsBar = document.getElementById('bulkActionsBar');
    const bulkSelectedCount = document.getElementById('bulkSelectedCount');
    const cancelSelectBtn = document.getElementById('cancelSelectBtn');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');

    function getVisibleUserCheckboxes() {
        return Array.from(document.querySelectorAll('.user-row:not(.hidden-row) .user-select-cb'));
    }

    function updateBulkSelection() {
        const visibleCbs = getVisibleUserCheckboxes();
        const checkedCbs = visibleCbs.filter(cb => cb.checked);

        checkedCbs.forEach(cb => {
            const row = cb.closest('.user-row');
            if (row) row.classList.add('selected-row');
        });

        visibleCbs.filter(cb => !cb.checked).forEach(cb => {
            const row = cb.closest('.user-row');
            if (row) row.classList.remove('selected-row');
        });

        if (bulkSelectedCount) {
            bulkSelectedCount.textContent = checkedCbs.length;
        }

        if (selectAllUsersCb) {
            selectAllUsersCb.checked = visibleCbs.length > 0 && checkedCbs.length === visibleCbs.length;
            selectAllUsersCb.indeterminate = checkedCbs.length > 0 && checkedCbs.length < visibleCbs.length;
        }

        if (adminContainer && adminContainer.classList.contains('selection-mode') && checkedCbs.length > 0) {
            if (bulkActionsBar) bulkActionsBar.classList.add('active');
        } else {
            if (bulkActionsBar) bulkActionsBar.classList.remove('active');
        }
    }

    function exitSelectMode() {
        if (adminContainer) adminContainer.classList.remove('selection-mode');
        if (toggleSelectModeBtn) toggleSelectModeBtn.classList.remove('active');
        if (bulkActionsBar) bulkActionsBar.classList.remove('active');
        
        document.querySelectorAll('.user-select-cb').forEach(cb => {
            cb.checked = false;
            const row = cb.closest('.user-row');
            if (row) row.classList.remove('selected-row');
        });
        if (selectAllUsersCb) {
            selectAllUsersCb.checked = false;
            selectAllUsersCb.indeterminate = false;
        }
    }

    if (toggleSelectModeBtn) {
        toggleSelectModeBtn.addEventListener('click', () => {
            const isSelectionMode = adminContainer.classList.toggle('selection-mode');
            toggleSelectModeBtn.classList.toggle('active', isSelectionMode);

            if (!isSelectionMode) {
                exitSelectMode();
            }
        });
    }

    if (cancelSelectBtn) {
        cancelSelectBtn.addEventListener('click', () => {
            exitSelectMode();
        });
    }

    if (selectAllUsersCb) {
        selectAllUsersCb.addEventListener('change', () => {
            const visibleCbs = getVisibleUserCheckboxes();
            visibleCbs.forEach(cb => {
                cb.checked = selectAllUsersCb.checked;
            });
            updateBulkSelection();
        });
    }

    document.addEventListener('change', (e) => {
        if (e.target && e.target.classList.contains('user-select-cb')) {
            updateBulkSelection();
        }
    });

    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', async () => {
            const visibleCbs = getVisibleUserCheckboxes();
            const checkedUsernames = visibleCbs.filter(cb => cb.checked).map(cb => cb.value);

            if (checkedUsernames.length === 0) return;

            const rawText = bulkDeleteBtn.getAttribute('data-confirm-text') || 'Удалить выбранных пользователей ({count})?';
            let confirmText = rawText;
            if (confirmText.includes('{count}')) {
                confirmText = confirmText.replace('{count}', checkedUsernames.length);
            } else {
                confirmText = confirmText + ` (${checkedUsernames.length})`;
            }

            if (!confirm(confirmText)) return;

            try {
                const res = await fetch('/admin/api/users/delete_bulk', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ usernames: checkedUsernames })
                });

                const data = await res.json();

                if (data.success) {
                    window.location.reload();
                } else {
                    alert(data.message || 'Ошибка массового удаления');
                }
            } catch (err) {
                console.error('Error bulk deleting users:', err);
            }
        });
    }

    // ==========================================================================
    // 5. УПРАВЛЕНИЕ МОДАЛЬНЫМИ ОКНАМИ
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

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (createModal?.classList.contains('active')) {
                createModal.classList.remove('active');
                resetCreateErrors();
            }
            if (editModal?.classList.contains('active')) {
                editModal.classList.remove('active');
                resetEditErrors();
            }
        }
    });

    // НАЖАТИЕ НА ШЕСТЕРЕНКУ (Открытие редактирования)
    document.querySelectorAll('.btn-gear').forEach(btn => {
        btn.addEventListener('click', () => {
            resetEditErrors();

            const username = btn.getAttribute('data-username');
            const status = btn.getAttribute('data-status');
            const rolesAttr = btn.getAttribute('data-roles') || '';
            const roles = rolesAttr.split(',');

            const modalUsernameLabel = document.getElementById('editModalUsername');
            const targetUsernameInput = document.getElementById('editTargetUsername');
            const editPasswordInput = document.getElementById('editPassword');

            if (modalUsernameLabel) modalUsernameLabel.textContent = username;
            if (targetUsernameInput) targetUsernameInput.value = username;
            if (editUsernameInput) editUsernameInput.value = username;
            if (editPasswordInput) editPasswordInput.value = '';

            // Установка статуса в кастомный выпадающий список модалки
            const editStatusDropdown = document.getElementById('editStatusDropdown');
            if (editStatusDropdown) {
                const hiddenStatusInput = editStatusDropdown.querySelector('#editStatus');
                const statusLabel = editStatusDropdown.querySelector('#editStatusLabel');
                const statusOptions = editStatusDropdown.querySelectorAll('.status-option');

                if (hiddenStatusInput) hiddenStatusInput.value = status;
                if (statusLabel) statusLabel.textContent = status;

                statusOptions.forEach(opt => {
                    if (opt.getAttribute('data-value') === status) {
                        opt.classList.add('active');
                    } else {
                        opt.classList.remove('active');
                    }
                });
            }

            // Выставление чекбоксов ролей
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
            const statusInput = document.getElementById('createStatus');
            const status = statusInput ? statusInput.value : '';
            
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
            const statusInput = document.getElementById('editStatus');
            const status = statusInput ? statusInput.value : '';

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