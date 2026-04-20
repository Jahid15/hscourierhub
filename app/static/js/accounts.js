document.addEventListener('DOMContentLoaded', () => {
    loadAccounts();
    loadSettings();
    initSettingsListeners();
});

async function loadSettings() {
    try {
        const resp = await fetch('/api/v1/settings/cache');
        const data = await resp.json();
        const toggle = document.getElementById('globalCacheToggle');
        if (toggle) toggle.checked = data.enabled;
    } catch (err) {
        console.error("Failed to load cache settings", err);
    }
}

function initSettingsListeners() {
    const toggle = document.getElementById('globalCacheToggle');
    if(toggle) {
        toggle.addEventListener('change', async (e) => {
            const enabled = e.target.checked;
            try {
                const resp = await fetch('/api/v1/settings/cache', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ enabled: enabled })
                });
                if(!resp.ok) {
                    alert('Failed to update global cache setting');
                    e.target.checked = !enabled; // revert on failure
                }
            } catch(err) {
                alert('Network error updating setting');
                e.target.checked = !enabled; // revert on failure
            }
        });
    }
}

async function loadAccounts() {
    const tbody = document.getElementById('accountsTableBody');
    tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-gray-500">Loading accounts...</td></tr>';
    
    try {
        const resp = await fetch('/api/v1/accounts/fraud-check');
        const accounts = await resp.json();
        
        tbody.innerHTML = '';
        if(accounts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-gray-500">No Steadfast accounts found.</td></tr>';
            return;
        }

        accounts.forEach(acc => {
            const loginStatusClass = acc.status_login === 'ok' ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50';
            const consigStatusClass = acc.status_consignment === 'active' ? 'text-green-600 bg-green-50' : (acc.status_consignment === 'inactive' ? 'text-gray-600 bg-gray-100' : 'text-yellow-600 bg-yellow-50');
            const fraudStatusClass = acc.status_fraud === 'active' ? 'text-green-600 bg-green-50' : (acc.status_fraud === 'inactive' ? 'text-gray-600 bg-gray-100' : 'text-yellow-600 bg-yellow-50');
            
            const lastUsed = acc.last_used ? new Date(acc.last_used + (!acc.last_used.endsWith('Z') ? 'Z' : '')).toLocaleString() : 'Never';
            
            // Usage visuals
            const cPct = acc.consignment_limit > 0 ? (acc.consignment_current / acc.consignment_limit) * 100 : 0;
            const fPct = acc.fraud_limit > 0 ? (acc.fraud_current / acc.fraud_limit) * 100 : 0;
            
            const cColor = cPct >= 100 ? 'bg-red-500' : 'bg-blue-500';
            const fColor = fPct >= 100 ? 'bg-red-500' : 'bg-purple-500';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="px-4 py-3 font-medium text-gray-800">${acc.email}</td>
                <td class="px-4 py-3 text-center border-l border-gray-200">
                    <span class="inline-block px-2 py-1 rounded-full text-xs font-semibold ${loginStatusClass}">${acc.status_login || 'ok'}</span>
                </td>
                <td class="px-4 py-3 text-center border-l border-gray-200">
                    <span class="inline-block px-2 py-1 rounded-full text-xs font-semibold ${consigStatusClass}">${acc.status_consignment || 'active'}</span>
                </td>
                <td class="px-4 py-3 text-center border-l border-gray-200">
                    <span class="inline-block px-2 py-1 rounded-full text-xs font-semibold ${fraudStatusClass}">${acc.status_fraud || 'active'}</span>
                </td>
                <td class="px-4 py-3 border-l border-gray-200">
                    <div class="flex justify-between text-xs mb-1">
                        <span>${acc.consignment_current} / ${acc.consignment_limit}</span>
                        <span>${Math.round(cPct)}%</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-1.5">
                        <div class="${cColor} h-1.5 rounded-full" style="width: ${Math.min(cPct, 100)}%"></div>
                    </div>
                </td>
                <td class="px-4 py-3 border-l border-gray-200">
                    <div class="flex justify-between text-xs mb-1">
                        <span>${acc.fraud_current} / ${acc.fraud_limit}</span>
                        <span>${Math.round(fPct)}%</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-1.5">
                        <div class="${fColor} h-1.5 rounded-full" style="width: ${Math.min(fPct, 100)}%"></div>
                    </div>
                </td>
                <td class="px-4 py-3 text-center text-xs text-gray-800 border-l border-gray-200 font-semibold">${acc.login_skip_minutes || 60}m</td>
                <td class="px-4 py-3 text-center text-xs text-gray-500 border-l border-gray-200">${lastUsed}</td>
                <td class="px-4 py-3 text-center border-l border-gray-200">
                    <button onclick='editAccount(${JSON.stringify(acc)})' class="text-blue-600 hover:text-blue-800 mr-2" title="Edit">✏️</button>
                    <button onclick="deleteAccount('${acc.id}')" class="text-red-500 hover:text-red-700" title="Delete">🗑️</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch(err) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-red-500">Error loading accounts: ${err.message}</td></tr>`;
    }
}

function openAddModal() {
    document.getElementById('editAccountId').value = '';
    document.getElementById('accEmail').value = '';
    document.getElementById('accPassword').value = '';
    document.getElementById('accConsLimit').value = '10';
    document.getElementById('accFraudLimit').value = '5';
    document.getElementById('accLoginSkip').value = '60';
    
    document.getElementById('modalTitle').textContent = 'Add Account';
    document.getElementById('pwRequiredStar').classList.remove('hidden');
    document.getElementById('pwNote').classList.add('hidden');
    
    document.getElementById('accountModal').classList.remove('hidden');
}

window.editAccount = function(acc) {
    document.getElementById('editAccountId').value = acc.id;
    document.getElementById('accEmail').value = acc.email;
    document.getElementById('accPassword').value = acc.password; // masked usually
    document.getElementById('accConsLimit').value = acc.consignment_limit;
    document.getElementById('accFraudLimit').value = acc.fraud_limit;
    document.getElementById('accLoginSkip').value = acc.login_skip_minutes || 60;
    
    document.getElementById('modalTitle').textContent = 'Edit Account';
    document.getElementById('pwRequiredStar').classList.add('hidden');
    document.getElementById('pwNote').classList.remove('hidden');
    
    document.getElementById('accountModal').classList.remove('hidden');
}

window.closeModal = function() {
    document.getElementById('accountModal').classList.add('hidden');
}

document.getElementById('accountForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('editAccountId').value;
    const isEdit = id !== '';
    
    const payload = {
        email: document.getElementById('accEmail').value,
        consignment_limit: parseInt(document.getElementById('accConsLimit').value),
        fraud_limit: parseInt(document.getElementById('accFraudLimit').value),
        login_skip_minutes: parseInt(document.getElementById('accLoginSkip').value)
    };
    
    const pw = document.getElementById('accPassword').value;
    if(!isEdit || (pw !== '' && !pw.includes('*'))) {
        payload.password = pw;
    }

    try {
        const url = isEdit ? `/api/v1/accounts/fraud-check/${id}` : `/api/v1/accounts/fraud-check`;
        const method = isEdit ? 'PUT' : 'POST';
        
        const resp = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        if(resp.ok) {
            closeModal();
            loadAccounts();
        } else {
            const data = await resp.json();
            alert('Error: ' + data.detail);
        }
    } catch(err) {
        alert('Network error');
    }
});

window.deleteAccount = async function(id) {
    if(!confirm('Are you sure you want to delete this account?')) return;
    
    try {
        const resp = await fetch(`/api/v1/accounts/fraud-check/${id}`, { method: 'DELETE' });
        if(resp.ok) {
            loadAccounts();
        } else {
            alert('Failed to delete');
        }
    } catch(err) {
        alert('Error deleting');
    }
}

window.resetAllCounters = async function() {
    if(!confirm('This will reset usage counters for ALL Steadfast accounts. Continue?')) return;
    
    try {
        const resp = await fetch(`/api/v1/accounts/fraud-check/reset-all`, { method: 'POST' });
        if(resp.ok) {
            loadAccounts();
        } else {
            alert('Failed to reset counters');
        }
    } catch(err) {
        alert('Error resetting');
    }
}
