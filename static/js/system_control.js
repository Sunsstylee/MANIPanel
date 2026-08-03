document.addEventListener('DOMContentLoaded', () => {
    const openBtn = document.getElementById('openSystemControlBtn');
    const modal = document.getElementById('systemControlModal');
    const closeBtn = document.getElementById('closeSystemControlModal');
    const form = document.getElementById('systemControlForm');
    const matrixContainer = document.getElementById('permissionsMatrix');

    // Все категории сайта для матрицы прав
    const SECTIONS = [
        { id: 'dashboard', title: 'ГЛАВНАЯ' },
        { id: 'logs', title: 'ЛОГИ' },
        { id: 'actions', title: 'ДЕЙСТВИЯ' },
        { id: 'replacements', title: 'ПОДМЕНЫ' },
        { id: 'clients', title: 'КЛИЕНТЫ' },
        { id: 'techpanel', title: 'ТЕХ ПАНЕЛЬ' }
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

    // Закрытие при клике по фону за пределами карточки
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    }

    // Загрузка настроек и динамическая отрисовка ролей
    async function loadSettingsAndRender() {
        try {
            const res = await fetch('/techpanel/api/settings');
            if (!res.ok) return;

            const data = await res.json();
            const settings = data.settings || {};
            const validRoles = data.valid_roles || [];
            const permissions = settings.page_permissions || {};

            // Переключатель «Закрыть сайт»
            const siteClosedToggle = document.getElementById('siteClosedToggle');
            if (siteClosedToggle) {
                siteClosedToggle.checked = !!settings.site_closed;
            }

            // Динамический рендеринг категорий и их ролей в виде чипов
            if (matrixContainer) {
                matrixContainer.innerHTML = '';

                SECTIONS.forEach(sec => {
                    // Поддержка ключа admin для обратной совместимости
                    const secRoles = permissions[sec.id] || (sec.id === 'techpanel' ? permissions['admin'] : []) || [];
                    const groupEl = document.createElement('div');
                    groupEl.className = 'perm-page-group';

                    // Локализованное название категории из global JS window.NAV_TRANSLATIONS
                    const translatedTitle = (window.NAV_TRANSLATIONS && window.NAV_TRANSLATIONS[sec.id])
                        ? window.NAV_TRANSLATIONS[sec.id].toUpperCase()
                        : sec.title;

                    const rolesHtml = validRoles.map(role => {
                        const isChecked = secRoles.includes(role) ? 'checked' : '';
                        return `
                            <label class="role-chip">
                                <input type="checkbox" data-section="${sec.id}" value="${role}" ${isChecked}>
                                <span class="chip-inner">
                                    <span class="chip-dot"></span>
                                    <span class="role-name">${role}</span>
                                </span>
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
                const res = await fetch('/techpanel/api/settings', {
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
                    alert('Ошибка при сохранении настроек');
                }
            } catch (err) {
                console.error('Ошибка сохранения:', err);
            }
        });
    }
});