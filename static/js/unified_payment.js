/**
 * Unified Payment Integration for CricVerse Stadium System
 * Supporting PayPal (International) + Indian Payment Gateways
 * Big Bash League Cricket Platform
 */

class UnifiedPaymentManager {
    constructor() {
        this.paypalClientId = window.PAYPAL_CLIENT_ID;
        this.razorpayKey = window.RAZORPAY_KEY_ID;
        this.currentPaymentData = null;
        this.selectedCurrency = 'USD';
        this.availableMethods = [];
        
        this.initializeEventHandlers();
        this.detectUserLocation();
        
        console.log('🌏 Unified Payment Manager initialized - PayPal + Indian Gateways');
        console.log('🏏 Ready for Big Bash League fans worldwide!');
    }
    
    async detectUserLocation() {
        try {
            // Try to detect user's location for currency suggestion
            const response = await fetch('https://ipapi.co/json/');
            const location = await response.json();
            
            if (location.country_code) {
                this.suggestCurrency(location.country_code);
            }
        } catch (error) {
            console.log('Location detection failed, using default currency');
            this.loadPaymentMethods('USD');
        }
    }
    
    suggestCurrency(countryCode) {
        const currencyMap = {
            'IN': 'INR',  // India
            'US': 'USD',  // United States
            'AU': 'AUD',  // Australia
            'GB': 'GBP',  // United Kingdom
            'CA': 'USD',  // Canada
            'EU': 'EUR'   // European Union
        };
        
        const suggestedCurrency = currencyMap[countryCode] || 'USD';
        this.selectedCurrency = suggestedCurrency;
        this.loadPaymentMethods(suggestedCurrency);
        
        // Update currency selector if exists
        const currencySelect = document.getElementById('currency-select');
        if (currencySelect) {
            currencySelect.value = suggestedCurrency;
        }
    }
    
    async loadPaymentMethods(currency) {
        try {
            const response = await fetch(`/api/get-payment-methods?currency=${currency}`);
            const result = await response.json();
            
            if (result.success) {
                this.availableMethods = result.methods;
                this.displayPaymentMethods(result.methods);
            }
        } catch (error) {
            console.error('Failed to load payment methods:', error);
        }
    }
    
    displayPaymentMethods(methods) {
        const container = document.getElementById('payment-methods-container');
        if (!container) return;
        
        container.innerHTML = `
            <div class=\"payment-methods\">
                <h4>🏏 Choose Your Payment Method</h4>
                <div class=\"currency-selector\">
                    <label for=\"currency-select\">Currency:</label>
                    <select id=\"currency-select\" onchange=\"unifiedPayment.onCurrencyChange(this.value)\">
                        <option value=\"USD\">USD - US Dollar</option>
                        <option value=\"AUD\">AUD - Australian Dollar</option>
                        <option value=\"INR\">INR - Indian Rupee</option>
                        <option value=\"EUR\">EUR - Euro</option>
                        <option value=\"GBP\">GBP - British Pound</option>
                    </select>
                </div>
                <div class=\"methods-grid\">
                    ${methods.map(method => this.createMethodCard(method)).join('')}
                </div>
            </div>
        `;
        
        // Set current currency
        const currencySelect = document.getElementById('currency-select');
        if (currencySelect) {
            currencySelect.value = this.selectedCurrency;
        }
    }
    
    createMethodCard(method) {
        return `
            <div class=\"payment-method-card\" data-method=\"${method.id}\" onclick=\"unifiedPayment.selectPaymentMethod('${method.id}', '${method.gateway}')\">
                <div class=\"method-icon\">
                    <img src=\"${method.icon}\" alt=\"${method.name}\" onerror=\"this.style.display='none'\">
                </div>
                <div class=\"method-info\">
                    <h5>${method.name}</h5>
                    <p>${method.description}</p>
                    ${method.conversion_required ? '<small class=\"conversion-note\">Amount will be converted to INR</small>' : ''}
                </div>
            </div>
        `;
    }
    
    initializeEventHandlers() {
        // Handle currency change
        document.addEventListener('change', (e) => {
            if (e.target.id === 'currency-select') {
                this.onCurrencyChange(e.target.value);
            }
        });
        
        // Handle payment form submission
        document.addEventListener('submit', (e) => {
            if (e.target.matches('#unified-payment-form')) {
                e.preventDefault();
                this.processPayment(e.target);
            }
        });
    }
    
    onCurrencyChange(currency) {
        this.selectedCurrency = currency;
        this.loadPaymentMethods(currency);
    }
    
    selectPaymentMethod(methodId, gateway) {
        // Update visual selection
        document.querySelectorAll('.payment-method-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        const selectedCard = document.querySelector(`[data-method=\"${methodId}\"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
        }
        
        // Store selection
        this.selectedMethod = methodId;
        this.selectedGateway = gateway;
        
        // Show payment details
        this.showPaymentDetails(methodId, gateway);
    }
    
    showPaymentDetails(methodId, gateway) {
        const container = document.getElementById('payment-details');
        if (!container) return;
        
        if (gateway === 'paypal') {
            container.innerHTML = `
                <div class=\"paypal-payment\">
                    <h4>💳 PayPal Payment</h4>
                    <p>You will be redirected to PayPal to complete your payment securely.</p>
                    <div class=\"paypal-info\">
                        <div class=\"currency-info\">
                            <strong>Currency:</strong> ${this.selectedCurrency}
                        </div>
                        <div class=\"security-info\">
                            <small>🔒 Secured by PayPal - Your payment information is never shared</small>
                        </div>
                    </div>
                </div>
            `;
        } else {
            this.showIndianPaymentDetails(methodId);
        }
        
        // Show payment button
        this.showPaymentButton();
    }
    
    showIndianPaymentDetails(methodId) {
        const container = document.getElementById('payment-details');
        
        const details = {
            'upi': {
                title: '📱 UPI Payment',
                description: 'Pay with PhonePe, Google Pay, Paytm, or any UPI app',
                features: ['Instant payment', 'No additional charges', 'Secure & fast']
            },
            'card': {
                title: '💳 Card Payment',
                description: 'Debit/Credit Cards, Visa, Mastercard, RuPay',
                features: ['All major cards accepted', 'Secure 3D verification', 'EMI options available']
            },
            'netbanking': {
                title: '🏦 Net Banking',
                description: 'Direct bank transfer from your account',
                features: ['All major banks', 'Direct bank transfer', 'Instant confirmation']
            },
            'wallet': {
                title: '👛 Digital Wallets',
                description: 'Paytm, Mobikwik, Amazon Pay, and more',
                features: ['Quick payment', 'Wallet balance', 'Cashback offers']
            }
        };
        
        const detail = details[methodId] || details.upi;
        
        container.innerHTML = `
            <div class=\"indian-payment\">
                <h4>${detail.title}</h4>
                <p>${detail.description}</p>
                <ul class=\"payment-features\">
                    ${detail.features.map(feature => `<li>✅ ${feature}</li>`).join('')}
                </ul>
                <div class=\"currency-info\">
                    <strong>Currency:</strong> INR (Indian Rupee)
                </div>
            </div>
        `;
    }
    
    showPaymentButton() {
        const container = document.getElementById('payment-button-container');
        if (!container) return;
        
        container.innerHTML = `
            <button type=\"button\" class=\"btn btn-primary btn-lg payment-btn\" onclick=\"unifiedPayment.initiatePayment()\">
                <span class=\"btn-text\">Pay Now - Complete Your BBL Booking</span>
                <span class=\"btn-loader\" style=\"display: none;\">Processing...</span>
            </button>
        `;
    }
    
    async initiatePayment() {
        if (!this.selectedMethod) {
            this.showPaymentMessage('Please select a payment method', 'error');
            return;
        }
        
        // Show loading state
        this.showPaymentLoading(true);
        
        try {
            // Get form data
            const form = document.getElementById('unified-payment-form');
            const formData = new FormData(form);
            
            // Add selected method and currency
            const paymentData = {
                amount: parseFloat(formData.get('amount')),
                currency: this.selectedCurrency,
                payment_method: this.selectedMethod,
                booking_type: formData.get('booking_type') || 'ticket',
                event_id: formData.get('event_id'),
                seat_ids: JSON.parse(formData.get('seat_ids') || '[]'),
                description: formData.get('description') || 'BBL Booking'
            };
            
            // Create payment order
            const response = await fetch('/api/create-payment-intent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrf_token]').value
                },
                body: JSON.stringify(paymentData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentPaymentData = result;
                
                if (result.gateway === 'paypal') {
                    // Redirect to PayPal
                    if (result.approval_url) {
                        window.location.href = result.approval_url;
                    } else {
                        throw new Error('PayPal approval URL not received');
                    }
                } else {
                    // Process with Razorpay
                    await this.processRazorpayPayment(result);
                }
            } else {
                throw new Error(result.error || 'Payment setup failed');
            }
            
        } catch (error) {
            console.error('Payment error:', error);
            this.showPaymentError(error.message);
        } finally {
            this.showPaymentLoading(false);
        }
    }
    
    async processRazorpayPayment(paymentData) {
        if (!window.Razorpay) {
            throw new Error('Razorpay SDK not loaded');
        }
        
        const options = {
            key: this.razorpayKey,
            amount: paymentData.amount * 100, // Convert to paise
            currency: paymentData.currency,
            name: 'CricVerse Stadium',
            description: 'Big Bash League Cricket Booking',
            image: '/static/images/cricverse-logo.png',
            order_id: paymentData.payment_id,
            handler: (response) => {
                this.handleRazorpaySuccess(response);
            },
            prefill: paymentData.payment_data?.prefill || {},
            theme: {
                color: '#FF6B35' // Big Bash League orange
            },
            modal: {
                ondismiss: () => {
                    this.handlePaymentDismiss();
                }
            }
        };
        
        const razorpay = new Razorpay(options);
        razorpay.open();
    }
    
    async handleRazorpaySuccess(response) {
        try {
            // Verify payment on server
            const verificationResponse = await fetch('/api/verify-payment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrf_token]').value
                },
                body: JSON.stringify({
                    gateway: 'razorpay',
                    razorpay_order_id: response.razorpay_order_id,
                    razorpay_payment_id: response.razorpay_payment_id,
                    razorpay_signature: response.razorpay_signature
                })
            });
            
            const result = await verificationResponse.json();
            
            if (result.success) {
                this.showPaymentSuccess(result);
                // Redirect to confirmation page
                setTimeout(() => {
                    window.location.href = `/booking/confirmation?payment_id=${result.payment_id}`;
                }, 2000);
            } else {
                throw new Error(result.error || 'Payment verification failed');
            }
            
        } catch (error) {
            console.error('Payment verification error:', error);
            this.showPaymentError(error.message);
        }
    }
    
    handlePaymentDismiss() {
        this.showPaymentMessage('Payment cancelled', 'warning');
        this.showPaymentLoading(false);
    }
    
    showPaymentLoading(show) {
        const button = document.querySelector('.payment-btn');
        const buttonText = button?.querySelector('.btn-text');
        const buttonLoader = button?.querySelector('.btn-loader');
        
        if (button && buttonText && buttonLoader) {
            button.disabled = show;
            buttonText.style.display = show ? 'none' : 'inline';
            buttonLoader.style.display = show ? 'inline' : 'none';
        }
    }
    
    showPaymentSuccess(result) {
        this.showPaymentMessage('🎉 Payment successful! Redirecting to confirmation...', 'success');
    }
    
    showPaymentError(message) {
        this.showPaymentMessage(`❌ ${message}`, 'error');
    }
    
    showPaymentMessage(message, type) {
        // Create or update payment message element
        let messageElement = document.getElementById('payment-message');
        if (!messageElement) {
            messageElement = document.createElement('div');
            messageElement.id = 'payment-message';
            messageElement.className = 'payment-message';
            
            const form = document.querySelector('#unified-payment-form');
            if (form) {
                form.appendChild(messageElement);
            }
        }
        
        messageElement.textContent = message;
        messageElement.className = `payment-message ${type}`;
        messageElement.style.display = 'block';
        
        // Auto-hide non-success messages
        if (type !== 'success') {
            setTimeout(() => {
                messageElement.style.display = 'none';
            }, 5000);
        }
    }
}

// Initialize Unified Payment Manager
let unifiedPayment;
document.addEventListener('DOMContentLoaded', () => {
    unifiedPayment = new UnifiedPaymentManager();
});

// Global functions for inline event handlers
window.unifiedPayment = {
    selectPaymentMethod: (method, gateway) => unifiedPayment?.selectPaymentMethod(method, gateway),
    onCurrencyChange: (currency) => unifiedPayment?.onCurrencyChange(currency),
    initiatePayment: () => unifiedPayment?.initiatePayment()
};