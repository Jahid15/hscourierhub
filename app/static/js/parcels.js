let allParcels = [];

document.addEventListener('DOMContentLoaded', () => {
    fetchParcels();
    
    // Bind Filter Interactions
    const searchEl = document.getElementById('searchInput');
    const filterEl = document.getElementById('courierFilter');
    if(searchEl) searchEl.addEventListener('input', renderParcels);
    if(filterEl) filterEl.addEventListener('change', renderParcels);
});

async function fetchParcels() {
    try {
        const response = await fetch('/api/v1/parcels');
        const data = await response.json();
        
        if (data.success) {
            allParcels = data.data;
            renderParcels();
        } else {
            document.getElementById('parcelsTableBody').innerHTML = `
                <tr><td colspan="6" class="px-6 py-8 text-center text-red-500">Failed to load data.</td></tr>
            `;
        }
    } catch (error) {
        let el = document.getElementById('parcelsTableBody');
        if(el) el.innerHTML = `<tr><td colspan="7" class="px-6 py-8 text-center text-red-500">Failed to load payload.</td></tr>`;
        console.error("Error:", error);
    }
}

function getStatusBadge(status) {
    status = String(status).toLowerCase().trim();
    
    // Delivered
    if(status.includes('delivered') || status === 'success') {
        return `<span class="px-3 py-1 bg-green-100 text-green-700 rounded-full font-bold text-xs uppercase tracking-wider shadow-sm border border-green-200">Delivered</span>`;
    }
    // Failed/Returned/Cancelled
    if(status.includes('cancel') || status.includes('return') || status.includes('fail') || status.includes('rejected')) {
        return `<span class="px-3 py-1 bg-red-100 text-red-700 rounded-full font-bold text-xs uppercase tracking-wider shadow-sm border border-red-200">${status}</span>`;
    }
    // Hold/Wait/Reschedule
    if(status.includes('hold') || status.includes('wait') || status.includes('reschedule') || status.includes('exchange')) {
        return `<span class="px-3 py-1 bg-orange-100 text-orange-700 rounded-full font-bold text-xs uppercase tracking-wider shadow-sm border border-orange-200">${status}</span>`;
    }
    // Transit/Pickup/Progress
    if(status.includes('transit') || status.includes('pick') || status.includes('dispatch') || status.includes('progress') || status.includes('assign')) {
        return `<span class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full font-bold text-xs uppercase tracking-wider shadow-sm border border-blue-200">${status}</span>`;
    }
    // Created/Pending
    if(status.includes('pending') || status.includes('created') || status.includes('place')) {
        return `<span class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full font-bold text-xs uppercase tracking-wider shadow-sm border border-gray-200">${status}</span>`;
    }
    
    // Default Unknown
    return `<span class="px-3 py-1 bg-violet-100 text-violet-700 rounded-full font-bold text-xs uppercase tracking-wider shadow-sm border border-violet-200">${status}</span>`;
}

function renderParcels() {
    const tbody = document.getElementById('parcelsTableBody');
    if (!tbody) return;
    // Execute Filtering Engine
    const searchEl = document.getElementById('searchInput');
    const filterEl = document.getElementById('courierFilter');
    
    const searchVal = searchEl ? searchEl.value.toLowerCase() : '';
    const filterVal = filterEl ? filterEl.value.toLowerCase() : 'all';
    
    const filteredParcels = allParcels.filter(p => {
        // Courier Match
        if(filterVal !== 'all' && strSafe(p.courier) !== filterVal) return false;
        
        // Search Match
        if(searchVal) {
            const compoundStr = `${strSafe(p.consignment_id)} ${strSafe(p.merchant_order_id)} ${strSafe(p.recipient_name)} ${strSafe(p.recipient_phone)} ${strSafe(p.tracking_code)}`.toLowerCase();
            if(!compoundStr.includes(searchVal)) return false;
        }
        return true;
    });

    if (filteredParcels.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="px-6 py-12 text-center text-gray-500 font-medium">No parcels match your visual telemetry filters.</td></tr>`;
        return;
    }

    let html = '';
    filteredParcels.forEach(p => {
        // Parse Courier Icon + ID natively assigned to brand identities
        let courierPill = '';
        if(strSafe(p.courier) === 'steadfast') courierPill = `<span class="inline-flex w-3 h-3 bg-green-500 rounded-full border border-green-700 shadow-sm"></span> <span class="text-green-800 font-bold">Steadfast</span>`;
        if(strSafe(p.courier) === 'pathao') courierPill = `<span class="inline-flex w-3 h-3 bg-red-500 rounded-full border border-red-700 shadow-sm"></span> <span class="text-red-800 font-bold">Pathao</span>`;
        if(strSafe(p.courier) === 'carrybee') courierPill = `<span class="inline-flex w-3 h-3 bg-yellow-400 rounded-full border border-yellow-600 shadow-sm"></span> <span class="text-yellow-800 font-bold">Carrybee</span>`;

        // Check internal routing failures vs success
        const c_id = p.consignment_id || `<span class="text-gray-400">Not Dispatched</span>`;
        const t_code = p.tracking_code || `<span class="text-gray-400">N/A</span>`;

        html += `
            <tr class="hover:bg-gray-50/80 transition-colors">
                <td class="px-6 py-4 text-center">
                    ${getStatusBadge(p.status)}
                </td>
                <td class="px-6 py-4">
                    <div class="font-bold text-blue-600">#${p.merchant_order_id}</div>
                    <div class="text-xs text-gray-400 mt-1">${new Date(p.created_at).toLocaleString()}</div>
                </td>
                <td class="px-6 py-4">
                    <div class="flex items-center gap-2 font-medium text-gray-700">${courierPill}</div>
                    <div class="text-xs text-gray-500 mt-1 bg-gray-100 px-2 py-0.5 rounded w-max">${p.business_name}</div>
                </td>
                <td class="px-6 py-4">
                    <div class="font-medium text-gray-800">${p.recipient_name}</div>
                    <div class="text-xs text-gray-600 mt-0.5">${p.recipient_phone}</div>
                    <div class="text-xs text-gray-500 mt-0.5 font-bold text-gray-800">৳${p.cod_amount}</div>
                </td>
                <td class="px-6 py-4 text-xs font-mono">
                    <div class="text-gray-600">ID: ${c_id}</div>
                    <div class="text-gray-600">TRK: ${t_code}</div>
                </td>
                <td class="px-6 py-4 text-center">
                    <button onclick="viewLogistics('${p._id}')" class="bg-indigo-50 hover:bg-indigo-100 text-indigo-600 border border-indigo-200 px-4 py-2 rounded shadow-sm text-xs font-bold uppercase transition tracking-wider">
                        Logistics
                    </button>
                </td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function viewLogistics(parcelId) {
    const parcel = allParcels.find(p => p._id === parcelId);
    if(!parcel) return;

    document.getElementById('modalTitle').innerHTML = `Telemetry Timeline - <span class="text-blue-600">#${parcel.merchant_order_id}</span>`;
    
    let timelineHTML = '';
    
    // Sort history chronologically
    const history = [...(parcel.status_history || [])].sort((a,b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    if(history.length === 0) {
        timelineHTML = `<div class="text-gray-500">No Webhook telemetry isolated for this array.</div>`;
    } else {
        history.forEach((event, idx) => {
            const date = new Date(event.timestamp);
            const isLast = idx === history.length - 1;
            
            timelineHTML += `
            <div class="flex gap-4">
                <div class="flex flex-col items-center">
                    <div class="w-3 h-3 rounded-full ${isLast ? 'bg-blue-600' : 'bg-gray-400 mt-1'}"></div>
                    ${!isLast ? '<div class="w-0.5 h-full bg-gray-200 my-1"></div>' : ''}
                </div>
                <div class="pb-6">
                    <span class="text-xs text-gray-400 tracking-widest uppercase">${date.toLocaleString()}</span>
                    <div class="font-bold text-gray-800 text-lg capitalize mb-1 mt-0.5">${event.status}</div>
                    <pre class="bg-gray-800 text-green-400 p-3 rounded-md text-[11px] overflow-x-auto shadow-inner border border-gray-900 border-l-4 border-l-green-500 w-[500px]"><code>${JSON.stringify(event.raw || {}, null, 2)}</code></pre>
                </div>
            </div>
            `;
        });
    }

    document.getElementById('modalTimelineBody').innerHTML = timelineHTML;
    document.getElementById('historyModal').classList.remove('hidden');
}

function closeHistoryModal() {
    document.getElementById('historyModal').classList.add('hidden');
}

// Helper safely stringifies null properties
function strSafe(val) {
    if(val === null || val === undefined) return "";
    return String(val).toLowerCase();
}
