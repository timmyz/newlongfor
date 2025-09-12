document.addEventListener('DOMContentLoaded', () => {
    // User Management Elements
    const userTableBody = document.getElementById('userTableBody');
    const userModal = new bootstrap.Modal(document.getElementById('userModal'));
    const userForm = document.getElementById('userForm');
    const userModalLabel = document.getElementById('userModalLabel');
    const addUserBtn = document.getElementById('addUserBtn');

    // Settings Elements
    const settingsForm = document.getElementById('settingsForm');
    const dingtalkWebhookInput = document.getElementById('dingtalk_webhook');
    const dingtalkSecretInput = document.getElementById('dingtalk_secret');

    const API_USERS_URL = '/api/users';
    const API_SETTINGS_URL = '/api/settings';

    // --- Settings Logic ---
    const fetchSettings = async () => {
        try {
            const response = await fetch(API_SETTINGS_URL);
            if (!response.ok) throw new Error('Failed to fetch settings');
            const settings = await response.json();
            dingtalkWebhookInput.value = settings.dingtalk_webhook || '';
            dingtalkSecretInput.value = settings.dingtalk_secret || '';
        } catch (error) {
            console.error('Error fetching settings:', error);
        }
    };

    settingsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const settingsData = {
            dingtalk_webhook: dingtalkWebhookInput.value,
            dingtalk_secret: dingtalkSecretInput.value,
        };
        try {
            const response = await fetch(API_SETTINGS_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settingsData),
            });
            if (!response.ok) throw new Error('Failed to save settings');
            alert('通知设置已保存！');
        } catch (error) {
            console.error('Error saving settings:', error);
            alert('保存通知设置失败。');
        }
    });

    // --- Password Management ---
    const passwordForm = document.getElementById('passwordForm');
    passwordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const currentPassword = document.getElementById('current_password').value;
        const newPassword = document.getElementById('new_password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        
        if (newPassword !== confirmPassword) {
            alert('新密码和确认密码不匹配！');
            return;
        }
        
        if (newPassword.length < 4) {
            alert('新密码长度至少为4位！');
            return;
        }
        
        try {
            const response = await fetch('/api/change-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                }),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert('密码修改成功！');
                passwordForm.reset();
            } else {
                alert(data.message || '密码修改失败');
            }
        } catch (error) {
            console.error('Error changing password:', error);
            alert('密码修改失败，请稍后重试。');
        }
    });

    // --- User Management Logic ---
    const fetchUsers = async () => {
        try {
            const response = await fetch(API_USERS_URL);
            if (!response.ok) throw new Error('Failed to fetch users');
            const users = await response.json();

            userTableBody.innerHTML = '';
            users.forEach(user => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${user.id}</td>
                    <td>${user.username}</td>
                    <td>${user.account_id}</td>
                    <td><span class="badge ${user.is_active ? 'bg-success' : 'bg-secondary'}">${user.is_active ? '启用' : '禁用'}</span></td>
                    <td>${user.checkin_time}</td>
                    <td>${user.last_checkin_time ? new Date(user.last_checkin_time).toLocaleString() : 'N/A'}</td>
                    <td class="${(user.last_checkin_status || '').includes('失败') || (user.last_checkin_status || '').includes('异常') ? 'text-danger' : ''}">${user.last_checkin_status}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary edit-btn" data-id="${user.id}"><i class="bi bi-pencil-square"></i></button>
                        <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${user.id}"><i class="bi bi-trash"></i></button>
                    </td>
                `;
                userTableBody.appendChild(tr);
            });
        } catch (error) {
            console.error('Error fetching users:', error);
            userTableBody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">加载用户数据失败</td></tr>`;
        }
    };

    userForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userId = document.getElementById('userId').value;
        
        const authDataFields = [
            'token', 'x-lf-usertoken', 'cookie', 'x-lf-dxrisk-token',
            'x-lf-channel', 'x-lf-bu-code', 'x-lf-dxrisk-source'
        ];

        const formData = {
            username: document.getElementById('username').value,
            account_id: document.getElementById('account_id').value,
            is_active: document.getElementById('is_active').checked,
            checkin_time: document.getElementById('checkin_time').value
        };

        authDataFields.forEach(field => {
            formData[field] = document.getElementById(field).value;
        });

        const method = userId ? 'PUT' : 'POST';
        const url = userId ? `${API_USERS_URL}/${userId}` : API_USERS_URL;

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });
            if (!response.ok) throw new Error('Failed to save user');
            userModal.hide();
            fetchUsers();
        } catch (error) {
            console.error('Error saving user:', error);
            alert('保存用户失败');
        }
    });

    addUserBtn.addEventListener('click', () => {
        userModalLabel.textContent = '添加新用户';
        userForm.reset();
        document.getElementById('userId').value = '';
        document.getElementById('checkin_time').value = '01:05';
    });

    userTableBody.addEventListener('click', async (e) => {
        const button = e.target.closest('button');
        if (!button) return;

        if (button.classList.contains('edit-btn')) {
            const userId = button.dataset.id;
            const response = await fetch(`${API_USERS_URL}`);
            const users = await response.json();
            const user = users.find(u => u.id == userId);

            if (user) {
                userModalLabel.textContent = `编辑用户: ${user.username}`;
                document.getElementById('userId').value = user.id;
                document.getElementById('username').value = user.username;
                document.getElementById('account_id').value = user.account_id;
                document.getElementById('is_active').checked = user.is_active;
                document.getElementById('checkin_time').value = user.checkin_time;

                // 填充认证信息字段
                document.getElementById('token').value = user.token || '';
                document.getElementById('x-lf-usertoken').value = user['x-lf-usertoken'] || '';
                document.getElementById('cookie').value = user.cookie || '';
                document.getElementById('x-lf-dxrisk-token').value = user['x-lf-dxrisk-token'] || '';
                document.getElementById('x-lf-channel').value = user['x-lf-channel'] || 'L0';
                document.getElementById('x-lf-bu-code').value = user['x-lf-bu-code'] || 'L00602';
                document.getElementById('x-lf-dxrisk-source').value = user['x-lf-dxrisk-source'] || '2';
                
                userModal.show();
            }
        }

        if (button.classList.contains('delete-btn')) {
            const userId = button.dataset.id;
            if (confirm('确定要删除这个用户吗？')) {
                try {
                    const response = await fetch(`${API_USERS_URL}/${userId}`, { method: 'DELETE' });
                    if (!response.ok) throw new Error('Failed to delete user');
                    fetchUsers();
                } catch (error) {
                    console.error('Error deleting user:', error);
                    alert('删除用户失败');
                }
            }
        }
    });

    // Initial Load
    fetchUsers();
    fetchSettings();
});
