let allBusinesses = [];
let allCouriers = [];

document.addEventListener('DOMContentLoaded', () => {
    fetchBusinesses();
    fetchCouriers();
});

// ============================================
// BUSINESS NAMESPACES
// ============================================
async function fetchBusinesses() {
    try {
        const res = await fetch('/api/v1/merchant-id/all');
        const data = await res.json();
        if (data.success) {
            allBusinesses = data.data;
            renderBusinesses();
            populateBusinessDropdowns(); // updates courier modal options
        }
    } catch (e) {
        const el = document.getElementById('businessTableBody');
        if(el) el.innerHTML = `<tr><td colspan="4" class="px-6 py-8 text-center text-red-500">Failed to load</td></tr>`;
    }
}

function renderBusinesses() {
    const tbody = document.getElementById('businessTableBody');
    if (!tbody) return;
    if (allBusinesses.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="px-6 py-12 text-center text-gray-500">No Business configurations found.</td></tr>`;
        return;
    }

    let html = '';
    allBusinesses.forEach(seq => {
        html += `
            <tr class="hover:bg-gray-50/80 transition-colors">
                <td class="px-6 py-4 font-medium text-gray-800">${seq.business_name}</td>
                <td class="px-6 py-4 text-gray-600 font-mono">${seq.prefix}</td>
                <td class="px-6 py-4 text-center">
                    <span class="bg-blue-100 text-blue-700 font-mono font-bold px-3 py-1 rounded-full text-xs">
                        ${seq.current_number}
                    </span>
                </td>
                <td class="px-6 py-4 text-right space-x-2">
                    <button onclick="editBusiness('${seq._id}')" class="text-gray-400 hover:text-blue-600 transition">
                        <svg class="w-5 h-5 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
                    </button>
                    <button onclick="deleteBusiness('${seq._id}')" class="text-gray-400 hover:text-red-600 transition">
                        <svg class="w-5 h-5 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                </td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function populateBusinessDropdowns() {
    const sel = document.getElementById('courier_businessName');
    sel.innerHTML = '<option value="">Select Business...</option>';
    allBusinesses.forEach(b => {
        sel.innerHTML += `<option value="${b.business_name}">${b.business_name}</option>`;
    });
}

function openBusinessModal() {
    document.getElementById('businessModalTitle').innerText = "Create Business";
    document.getElementById('editBusinessId').value = "";
    document.getElementById('businessName').value = "";
    document.getElementById('businessName').disabled = false;
    document.getElementById('prefix').value = "";
    document.getElementById('currentNumber').value = "0";
    document.getElementById('businessModal').classList.remove('hidden');
}

function closeBusinessModal() {
    document.getElementById('businessModal').classList.add('hidden');
}

function editBusiness(id) {
    const seq = allBusinesses.find(s => s._id === id);
    if(!seq) return;
    document.getElementById('businessModalTitle').innerText = "Edit Sequence Setup";
    document.getElementById('editBusinessId').value = seq._id;
    document.getElementById('businessName').value = seq.business_name;
    document.getElementById('prefix').value = seq.prefix;
    document.getElementById('currentNumber').value = seq.current_number;
    document.getElementById('businessModal').classList.remove('hidden');
}

async function saveBusiness() {
    const id = document.getElementById('editBusinessId').value;
    const isEdit = id !== "";
    const payload = {
        business_name: document.getElementById('businessName').value.trim(),
        prefix: document.getElementById('prefix').value.trim(),
        starting_number: parseInt(document.getElementById('currentNumber').value),
        courier: "none" // DEPRECATED - Left for backward schema safety
    };
    
    if(!payload.business_name || !payload.prefix) return alert("Required fields missing");

    const url = isEdit ? `/api/v1/merchant-id/${id}` : `/api/v1/merchant-id/create-business`;
    const method = isEdit ? 'PUT' : 'POST';
    try {
        const res = await fetch(url, { method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
        const data = await res.json();
        if(data.success) {
            closeBusinessModal();
            fetchBusinesses();
        } else alert("Error: " + data.detail);
    } catch(e) { alert("Fatal saving."); }
}

async function deleteBusiness(id) {
    if(!confirm("Destroying this sequence may cause conflicting Merchant IDs if re-created. Are you sure?")) return;
    try {
        const res = await fetch(`/api/v1/merchant-id/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if(data.success) fetchBusinesses();
    } catch(e) { alert("Failed to delete"); }
}

// ============================================
// COURIER PROFILES
// ============================================
async function fetchCouriers() {
    try {
        const res = await fetch('/api/v1/courier-profiles');
        const data = await res.json();
        if (data.success) {
            allCouriers = data.data;
            renderCourierTable();
        }
    } catch (e) {
        const el = document.getElementById('courierTableBody');
        if(el) el.innerHTML = `<tr><td colspan="4" class="px-6 py-8 text-center text-red-500">Failed to load</td></tr>`;
    }
}

function renderCourierTable() {
    const tbody = document.getElementById('courierTableBody');
    if (!tbody) return;
    if (allCouriers.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="px-6 py-12 text-center text-gray-500">No Carrier integrations attached.</td></tr>`;
        return;
    }

    let html = '';
    allCouriers.forEach(c => {
        const cPill = c.courier === 'steadfast' ? 'bg-green-100 text-green-700' : c.courier === 'pathao' ? 'bg-red-100 text-red-700' : 'bg-purple-100 text-purple-700';

        html += `
            <tr class="hover:bg-gray-50/80 transition-colors">
                <td class="px-6 py-4 font-bold text-gray-800">${c.business_name}</td>
                <td class="px-6 py-4"><span class="px-2 py-1 ${cPill} rounded text-xs font-bold uppercase tracking-wider">${c.courier}</span></td>
                <td class="px-6 py-4 text-gray-400 font-mono text-xs">
                    <pre class="bg-gray-100 p-2 rounded"><code>${JSON.stringify(c.credentials || {}, null, 1)}</code></pre>
                </td>
                <td class="px-6 py-4 text-right space-x-2">
                    <button onclick="editCourier('${c._id}')" class="text-gray-400 hover:text-emerald-600 transition">
                        <svg class="w-5 h-5 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
                    </button>
                    <button onclick="deleteCourier('${c._id}')" class="text-gray-400 hover:text-red-600 transition">
                        <svg class="w-5 h-5 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                </td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function renderCredentialInputs(existingData = null) {
    const courier = document.getElementById('courier_network').value;
    const area = document.getElementById('credentialsArea');
    area.innerHTML = '';
    
    // Generate mapped schema
    let schema = [];
    if(courier === 'steadfast') {
        schema = [
            { id: 'base_url', label: 'Base URL', default: 'https://steadfast.com.bd/api/v1' },
            { id: 'api_key', label: 'API Key', type: 'text' },
            { id: 'secret_key', label: 'Secret Key', type: 'password' }
        ];
    } else if (courier === 'pathao') {
        schema = [
            { id: 'base_url', label: 'Base URL', default: 'https://api-hermes.pathao.com' },
            { id: 'client_id', label: 'Client ID', type: 'text' },
            { id: 'client_secret', label: 'Client Secret', type: 'password' },
            { id: 'username', label: 'Username (Email)', type: 'text' },
            { id: 'password', label: 'Password', type: 'password' },
            { id: 'store_id', label: 'Store ID', type: 'number' }
        ];
    } else if (courier === 'carrybee') {
        schema = [
            { id: 'base_url', label: 'Base URL', default: 'https://api-merchant.carrybee.com/' },
            { id: 'client_id', label: 'Client ID', type: 'text' },
            { id: 'client_secret', label: 'Client Secret', type: 'password' },
            { id: 'client_context', label: 'Client Context', type: 'text' },
            { id: 'store_id', label: 'Store ID', type: 'number' }
        ];
    }

    schema.forEach(field => {
        const val = (existingData && existingData[field.id]) ? existingData[field.id] : (field.default || '');
        const type = field.type || 'text';
        area.innerHTML += `
            <div>
                <label class="block text-xs font-semibold text-gray-500 mb-1 tracking-wider uppercase">${field.label}</label>
                <input type="${type}" id="cred_${field.id}" value="${val}" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500" required>
            </div>
        `;
    });
}

function openCourierModal() {
    document.getElementById('courierModalTitle').innerText = "Attach Courier Integration";
    document.getElementById('editCourierId').value = "";
    document.getElementById('courier_businessName').value = "";
    document.getElementById('courier_network').value = "steadfast";
    renderCredentialInputs();
    document.getElementById('courier_businessName').disabled = false;
    document.getElementById('courierModal').classList.remove('hidden');
}

function closeCourierModal() {
    document.getElementById('courierModal').classList.add('hidden');
}

function editCourier(id) {
    const prof = allCouriers.find(c => c._id === id);
    if(!prof) return;
    document.getElementById('courierModalTitle').innerText = "Update Courier Credentials";
    document.getElementById('editCourierId').value = prof._id;
    document.getElementById('courier_businessName').value = prof.business_name;
    document.getElementById('courier_network').value = prof.courier;
    renderCredentialInputs(prof.credentials);
    document.getElementById('courierModal').classList.remove('hidden');
}

async function saveCourierProfile() {
    const id = document.getElementById('editCourierId').value;
    const isEdit = id !== "";
    const courier = document.getElementById('courier_network').value;
    
    // Scrape credentials
    const credBox = document.getElementById('credentialsArea');
    const inputs = credBox.querySelectorAll('input');
    const credentials = {};
    inputs.forEach(inp => {
        const key = inp.id.replace('cred_', '');
        credentials[key] = inp.value.trim();
    });

    const payload = {
        business_name: document.getElementById('courier_businessName').value,
        courier: courier,
        credentials: credentials
    };
    if(!payload.business_name) return alert("Select a business namespace first");

    const url = isEdit ? `/api/v1/courier-profiles/${id}` : `/api/v1/courier-profiles`;
    const method = isEdit ? 'PUT' : 'POST';
    try {
        const res = await fetch(url, { method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
        const data = await res.json();
        if(data.success) {
            closeCourierModal();
            fetchCouriers();
        } else alert("Error: " + data.detail);
    } catch(e) { alert("Fatal saving."); }
}

async function deleteCourier(id) {
    if(!confirm("Destroying this connection will disable shipping for this profile! OK?")) return;
    try {
        const res = await fetch(`/api/v1/courier-profiles/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if(data.success) fetchCouriers();
    } catch(e) { alert("Failed to delete"); }
}
