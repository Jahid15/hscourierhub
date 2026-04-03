document.addEventListener('DOMContentLoaded', () => {
    const namespaceSelect = document.getElementById('business_namespace');
    const courierInput = document.getElementById('courier');
    const businessInput = document.getElementById('business');

    let allSequences = [];

    // Master configuration bootloader
    async function initNamespaces() {
        try {
            const resp = await fetch('/api/v1/courier-profiles');
            const data = await resp.json();
            if(data.success && data.data.length > 0) {
                allSequences = data.data;
                namespaceSelect.innerHTML = '<option value="">-- Connect to Sequence Protocol --</option>';
                data.data.forEach(s => {
                    namespaceSelect.innerHTML += `<option value="${s._id}">${s.business_name} | Courier: ${s.courier.toUpperCase()}</option>`;
                });
            } else {
                namespaceSelect.innerHTML = '<option value="">No merchant configs mapped locally.</option>';
            }
        } catch(e) {
            namespaceSelect.innerHTML = '<option value="">Fatal config extraction error.</option>';
        }
    }
    initNamespaces();
    const phoneInput = document.getElementById('recipient_phone');
    const miniFraudResult = document.getElementById('miniFraudResult');

    let phoneCheckTimeout;

    // Mini fraud check on typing phone (debounced)
    phoneInput.addEventListener('input', () => {
        clearTimeout(phoneCheckTimeout);
        const phone = phoneInput.value.trim();
        if(phone.length >= 10) {
            phoneCheckTimeout = setTimeout(async () => {
                try {
                    miniFraudResult.textContent = 'Checking delivery history...';
                    miniFraudResult.className = 'text-xs mt-1 text-blue-500 block cursor-pointer hover:underline';
                    
                    const resp = await fetch(`/api/v1/fraud-check/${encodeURIComponent(phone)}`);
                    if(resp.ok) {
                        const data = await resp.json();
                        const rate = data.summary.overall_success_rate;
                        const delivered = data.summary.total_delivered;
                        const total = data.summary.total_parcels;
                        
                        let colorClass = 'text-gray-500';
                        if(rate > 70) colorClass = 'text-green-600 font-medium';
                        else if(rate < 40) colorClass = 'text-red-500 font-bold';
                        
                        miniFraudResult.innerHTML = `🔍 History: <strong>${delivered}/${total}</strong> (${rate}% success)`;
                        miniFraudResult.className = `text-xs mt-1 block cursor-pointer hover:underline ${colorClass}`;
                        miniFraudResult.onclick = () => window.open(`/fraud-check?phone=${phone}`, '_blank');
                    } else {
                        miniFraudResult.classList.add('hidden');
                    }
                } catch(e) {
                    miniFraudResult.classList.add('hidden');
                }
            }, 800);
        } else {
            miniFraudResult.classList.add('hidden');
        }
    });

    // Handle Dynamic Routing Selection Change
    namespaceSelect.addEventListener('change', async () => {
        const id = namespaceSelect.value;
        const seq = allSequences.find(s => s._id === id);
        
        if(!seq) {
            courierInput.value = '';
            businessInput.value = '';
            return;
        }

        const courier = seq.courier;
        courierInput.value = courier;
        businessInput.value = seq.business_name;
        // The backend handles location logic auto-magically now!
    });

    // Form Submit
    document.getElementById('parcelForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const btn = document.getElementById('submitBtn');
        const loader = document.getElementById('submitLoader');
        const resultArea = document.getElementById('resultArea');
        const successBox = document.getElementById('successBox');
        const errorBox = document.getElementById('errorBox');
        
        btn.disabled = true;
        loader.classList.remove('hidden');
        resultArea.classList.add('hidden');
        successBox.classList.add('hidden');
        errorBox.classList.add('hidden');

        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        data.cod_amount = parseFloat(data.cod_amount);
        
        // Locations are parsed dynamically by CourierEntryManager and Carrybee parse_address()
        
        try {
            const resp = await fetch('/api/v1/parcel/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            const result = await resp.json();
            
            resultArea.classList.remove('hidden');
            
            if(resp.ok && result.success) {
                successBox.classList.remove('hidden');
                document.getElementById('resMerchantId').textContent = result.merchant_order_id;
                document.getElementById('resConsignment').textContent = result.consignment_id || result.tracking_code || 'N/A';
                
                if(result.delivery_fee) {
                    document.getElementById('resDeliveryFee').textContent = `Delivery Fee: ৳${result.delivery_fee}`;
                } else {
                    document.getElementById('resDeliveryFee').textContent = '';
                }
                
                // e.target.reset(); // Optionally reset form
            } else {
                errorBox.classList.remove('hidden');
                let errMsg = result.message || 'Unknown error occurred';
                if(result.raw_response && result.raw_response.message) errMsg += ` (${result.raw_response.message})`;
                // Attempt to parse validation array from pathao/carrybee if it exists
                try {
                    if(result.raw_response?.errors) errMsg += ' ' + JSON.stringify(result.raw_response.errors);
                } catch(err) {}
                document.getElementById('errMsg').textContent = errMsg;
            }
        } catch(error) {
            resultArea.classList.remove('hidden');
            errorBox.classList.remove('hidden');
            document.getElementById('errMsg').textContent = `Network error: ${error.message}`;
        } finally {
            btn.disabled = false;
            loader.classList.add('hidden');
        }
    });

    // We rely on initNamespaces to trigger changes, so no manual dispatch initially
});
