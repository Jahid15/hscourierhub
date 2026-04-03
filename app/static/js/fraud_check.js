document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('checkForm');
    const phoneInput = document.getElementById('phone');
    const searchBtn = document.getElementById('searchBtn');
    const loader = document.getElementById('loader');
    const resultsArea = document.getElementById('resultsArea');
    
    // Summary elements
    const sumTotal = document.getElementById('sumTotal');
    const sumDelivered = document.getElementById('sumDelivered');
    const sumCancelled = document.getElementById('sumCancelled');
    const sumRate = document.getElementById('sumRate');
    const sumFraudCard = document.getElementById('sumFraudCard');
    
    // UI elements
    const pasteBtn = document.getElementById('pasteBtn');
    
    // Table parts
    const tableBody = document.getElementById('courierTableBody');
    const timestamp = document.getElementById('timestamp');
    const cachedBadge = document.getElementById('cachedBadge');

    if(pasteBtn) {
        pasteBtn.addEventListener('click', async () => {
            try {
                phoneInput.focus();
                const text = await navigator.clipboard.readText();
                if (text && text.trim()) {
                    phoneInput.value = text.trim();
                    // Automatically trigger search robustly
                    searchBtn.click();
                }
            } catch (err) {
                console.error('Failed to read clipboard: ', err);
                alert('Browser blocked clipboard access. Please use Ctrl+V (or command+V) inside the search box instead!');
            }
        });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const phone = phoneInput.value.trim();
        if(!phone) return;

        // UI state: loading
        searchBtn.disabled = true;
        loader.classList.remove('hidden');
        resultsArea.classList.add('hidden');

        try {
            let url = `/api/v1/fraud-check/${encodeURIComponent(phone)}`;
            
            const resp = await fetch(url);
            const data = await resp.json();

            if(!resp.ok) {
                alert(data.detail || data.error || 'Failed to fetch data');
            } else {
                renderResults(data);
            }
        } catch(err) {
            alert('A network error occurred.');
            console.error(err);
        } finally {
            searchBtn.disabled = false;
            loader.classList.add('hidden');
        }
    });

    function renderResults(data) {
        // Summary
        sumTotal.textContent = data.summary.total_parcels;
        sumDelivered.textContent = data.summary.total_delivered;
        sumCancelled.textContent = data.summary.total_cancelled;
        sumRate.textContent = data.summary.overall_success_rate + '%';
        
        if (sumFraudCard) {
            sumFraudCard.textContent = data.summary.steadfast_fraud_reports;
        }

        const nameBadge = document.getElementById('customerNameBadge');
        if(nameBadge) {
            if(data.summary.customer_name) {
                nameBadge.textContent = '👤 ' + data.summary.customer_name;
                nameBadge.classList.remove('hidden');
            } else {
                nameBadge.classList.add('hidden');
            }
        }

        // Table
        tableBody.innerHTML = '';
        data.couriers.forEach(c => {
            let rowClass = '';
            if(c.status === 'error') rowClass = 'bg-red-50';
            
            let statusHtml = '';
            if(c.status === 'error') {
                statusHtml = `<span class="text-red-600 text-sm">${c.error_message || 'Error'}</span>`;
            } else {
                statusHtml = `<span class="text-gray-700 text-sm">${c.comment || '-'}</span>`;
            }
            
            // Icon logic based on courier
            let iconText = '';
            if(c.name.toLowerCase() === 'steadfast') iconText = '🟢';
            else if(c.name.toLowerCase() === 'pathao') iconText = '🔴';
            else if(c.name.toLowerCase() === 'carrybee') iconText = '🟣';
            else iconText = '🔵';

            tableBody.innerHTML += `
                <tr class="${rowClass}">
                    <td class="px-4 py-3 font-medium text-gray-800 flex items-center"><span class="mr-2">${iconText}</span> ${c.name}</td>
                    <td class="px-4 py-3 text-center font-semibold">${c.total}</td>
                    <td class="px-4 py-3 text-center text-green-600 font-semibold">${c.delivered}</td>
                    <td class="px-4 py-3 text-center text-red-500 font-semibold">${c.cancelled}</td>
                    <td class="px-4 py-3">${statusHtml}</td>
                </tr>
            `;
        });

        const dt = new Date(data.checked_at + (!data.checked_at.endsWith('Z') ? 'Z' : ''));
        timestamp.textContent = dt.toLocaleString();
        
        if(data.cached) {
            cachedBadge.classList.remove('hidden');
        } else {
            cachedBadge.classList.add('hidden');
        }

        resultsArea.classList.remove('hidden');
    }
});
