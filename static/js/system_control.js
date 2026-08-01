document.addEventListener('DOMContentLoaded', () => {
    const openBtn = document.getElementById('openSystemControlBtn');
    const modal = document.getElementById('systemControlModal');
    const closeBtn = document.getElementById('closeSystemControlModal');
    const form = document.getElementById('systemControlForm');
    const matrixContainer = document.getElementById('permissionsMatrix');

    // Разделы страниц сайта для матрицы доступности
    const SECTIONS = [
        { id: 'dashboard', title: 'DASHBOARD' },
        { id: 'logs', title: 'LOGS' },
        { id: 'actions', title: 'ACTIONS' },
        { id: 'replacements', title: 'REPLACEMENTS' },
        { id: 'admin', title: 'ADMIN PANEL' }
    ];

    if (openBtn && modal) {
        openBtn.addEventListener('click', () => {
            loadSettingsAndRender();
            modal.classList.add('active');
        });
    }

    if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => {
            modal.classList.remove('active');
        });
    }

    // Загрузка настроек с бэкенда и динамический рендеринг матрицы
    async function loadSettingsAndRender() {
        try {
            const res = await fetch('/admin/api/settings');
            if (!res.ok) return;

            const data = await res.json();
            const settings = data.settings || {};
            const validRoles = data.valid_roles || [];
            const permissions = settings.page_permissions || {};

            // Переключатель закрытия сайта
            const siteClosedToggle = document.getElementById('siteClosedToggle');
            if (siteClosedToggle) {
                siteClosedToggle.checked = !!settings.site_closed;
            }

            // Динамическая генерация чекбоксов с локализацией категорий
            if (matrixContainer) {
                matrixContainer.innerHTML = '';

                SECTIONS.forEach(sec => {
                    const secRoles = permissions[sec.id] || [];
                    const groupEl = document.createElement('div');
                    groupEl.className = 'perm-page-group';

                    // Получаем переведенный заголовок категории или резервное имя
                    const translatedTitle = (window.NAV_TRANSLATIONS && window.NAV_TRANSLATIONS[sec.id])
                        ? window.NAV_TRANSLATIONS[sec.id].toUpperCase()
                        : sec.title;

                    const rolesHtml = validRoles.map(role => {
                        const isChecked = secRoles.includes(role) ? 'checked' : '';
                        return `
                            <label class="custom-checkbox">
                                <input type="checkbox" data-section="${sec.id}" value="${role}" ${isChecked}>
                                <span class="checkmark"></span>
                                <span>${role}</span>
                            </label>
                        `;
                    }).join('');

                    groupEl.innerHTML = `
                        <div class="perm-page-header">${translatedTitle}</div>
                        <div class="perm-roles-grid">${rolesHtml}</div>
                    `;

                    matrixContainer.appendChild(groupEl);
                });
            }
        } catch (err) {
            console.error('Ошибка при загрузке настроек:', err);
        }
    }

    // Сохранение настроек
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const siteClosed = document.getElementById('siteClosedToggle')?.checked || false;
            const pagePermissions = {};

            const checkboxes = document.querySelectorAll('#permissionsMatrix input[type="checkbox"]');
            checkboxes.forEach(cb => {
                const secId = cb.dataset.section;
                if (!pagePermissions[secId]) {
                    pagePermissions[secId] = [];
                }
                if (cb.checked) {
                    pagePermissions[secId].push(cb.value);
                }
            });

            try {
                const res = await fetch('/admin/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        site_closed: siteClosed,
                        page_permissions: pagePermissions
                    })
                });

                const result = await res.json();
                if (result.success) {
                    modal.classList.remove('active');
                    location.reload();
                } else {
                    alert('Ошибка сохранения настроек');
                }
            } catch (err) {
                console.error('Ошибка сохранения:', err);
            }
        });
    }
});