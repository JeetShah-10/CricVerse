/**
 * Professional Checkout System for CricVerse Stadium System
 * Multi-step checkout with unified payment processing
 * Big Bash League Cricket Platform
 */

class CheckoutManager {
    constructor() {
        this.currentStep = 1;
        this.orderData = {};
        this.selectedCurrency = 'USD';
        this.selectedMethod = null;
        this.selectedGateway = null;
        this.isLoading = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadOrderData();
        
        console.log('🏏 CricVerse Checkout Manager initialized');
    }
    
    initializeElements() {
        // Stepper elements
        this.stepElements = {
            1: document.getElementById('step1'),
            2: document.getElementById('step2'),
            3: document.getElementById('step3')
        };
        
        // Step containers
        this.stepContainers = {
            1: document.getElementById('order-summary-step'),
            2: document.getElementById('payment-step'),
            3: document.getElementById('confirmation-step')
        };
        
        // Buttons
        this.proceedButton = document.getElementById('proceed-to-payment');
        this.backButton = document.getElementById('back-to-order');
        
        // Form elements
        this.paymentForm = document.getElementById('unified-payment-form');
        this.currencySelect = document.getElementById('currency-select');
        this.amountInput = document.getElementById('amount-input');
        this.bookingTypeInput = document.getElementById('booking-type-input');
        this.eventIdInput = document.getElementById('event-id-input');
        this.seatIdsInput = document.getElementById('seat-ids-input');
        this.descriptionInput = document.getElementById('description-input');
        
        // Display elements
        this.orderItemsContainer = document.querySelector('.order-items');
        this.subtotalAmount = document.getElementById('subtotal-amount');
        this.feeAmount = document.getElementById('fee-amount');
        this.totalAmount = document.getElementById('total-amount');
    }
    
    bindEvents() {
        // Navigation events
        if (this.proceedButton) {
            this.proceedButton.addEventListener('click', () => this.goToStep(2));
        }
        
        if (this.backButton) {
            this.backButton.addEventListener('click', () => this.goToStep(1));
        }
        
        // Currency change event
        if (this.currencySelect) {
            this.currencySelect.addEventListener('change', (e) => {
                this.selectedCurrency = e.target.value;
                this.loadPaymentMethods();
            });
        }
        
        // Form submission
        if (this.paymentForm) {
            this.paymentForm.addEventListener('submit', (e) => this.handlePayment(e));
        }
    }
    
    loadOrderData() {
        // In a real implementation, this would load from the server or session
        // For now, we'll simulate with sample data
        this.orderData = {
            items: [
                {
                    id: 1,
                    name: "Melbourne Stars vs Sydney Thunder",
                    description: "General Admission - Section B, Row 12, Seat 5",
                    quantity: 1,
                    price: 45.00,
                    type: "ticket"
                },
                {
                    id: 2,
                    name: "Parking Pass",
                    description: "3 Hours Parking at MCG",
                    quantity: 1,
                    price: 15.00,
                    type: "parking"
                }
            ],
            eventId: 123,
            seatIds: [456],
            subtotal: 60.00,
            fee: 3.00,
            total: 63.00
        };
        
        this.renderOrderSummary();
        this.populateFormFields();
        this.loadPaymentMethods();
    }
    
    renderOrderSummary() {
        if (!this.orderItemsContainer) return;
        
        // Clear existing items
        this.orderItemsContainer.innerHTML = '';
        
        // Add items
        this.orderData.items.forEach(item => {
            const itemElement = document.createElement('div');
            itemElement.className = 'order-item mb-3 pb-3 border-bottom';
            itemElement.innerHTML = `
                <div class="d-flex justify-content-between">
                    <div>
                        <h5 class="mb-1">${item.name}</h5>
                        <p class="mb-1 text-muted">${item.description}</p>
                        <small class="text-muted">Qty: ${item.quantity}</small>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold">${this.formatCurrency(item.price * item.quantity, this.selectedCurrency)}</div>
                    </div>
                </div>
            `;
            this.orderItemsContainer.appendChild(itemElement);
        });
        
        // Update totals
        if (this.subtotalAmount) {
            this.subtotalAmount.textContent = this.formatCurrency(this.orderData.subtotal, this.selectedCurrency);
        }
        
        if (this.feeAmount) {
            this.feeAmount.textContent = this.formatCurrency(this.orderData.fee, this.selectedCurrency);
        }
        
        if (this.totalAmount) {
            this.totalAmount.textContent = this.formatCurrency(this.orderData.total, this.selectedCurrency);
        }
        
        // Update form amount
        if (this.amountInput) {
            this.amountInput.value = this.orderData.total.toFixed(2);
        }
    }
    
    populateFormFields() {
        if (this.eventIdInput) {
            this.eventIdInput.value = this.orderData.eventId || '';
        }
        
        if (this.seatIdsInput) {
            this.seatIdsInput.value = JSON.stringify(this.orderData.seatIds || []);
        }
    }
    
    async loadPaymentMethods() {
        try {
            this.showPaymentMessage('Loading payment methods...', 'info');
            const response = await fetch(`/api/get-payment-methods?currency=${this.selectedCurrency}`);
            const result = await response.json();
            
            if (result.success) {
                this.displayPaymentMethods(result.methods);
                this.hidePaymentMessage();
            } else {
                this.showPaymentMessage('Failed to load payment methods', 'error');
            }
        } catch (error) {
            console.error('Error loading payment methods:', error);
            this.showPaymentMessage('Failed to load payment methods. Please try again.', 'error');
        }
    }
    
    displayPaymentMethods(methods) {
        const container = document.getElementById('payment-methods-container');
        if (!container) return;
        
        if (methods.length === 0) {
            container.innerHTML = `
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    No payment methods available for selected currency. Please select a different currency.
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <label class="form-label fw-bold">Select Payment Method</label>
            <div class="payment-methods-grid">
                ${methods.map(method => this.createMethodCard(method)).join('')}
            </div>
        `;
        
        // Bind click events to method cards
        document.querySelectorAll('.payment-method-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const methodId = card.dataset.method;
                const gateway = card.dataset.gateway;
                this.selectPaymentMethod(methodId, gateway);
            });
        });
    }
    
    createMethodCard(method) {
        return `
            <div class="payment-method-card" data-method="${method.id}" data-gateway="${method.gateway}">
                <div class="method-content">
                    <div class="method-icon">
                        ${method.icon ? `<img src="${method.icon}" alt="${method.name}" onerror="this.style.display='none'">` : ''}
                        ${!method.icon ? `<i class="bi bi-credit-card"></i>` : ''}
                    </div>
                    <div class="method-info">
                        <h5 class="mb-1">${method.name}</h5>
                        <p class="mb-0 text-muted small">${method.description}</p>
                        ${method.conversion_required ? 
                            '<span class="badge bg-warning text-dark mt-1">Currency conversion applies</span>' : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    selectPaymentMethod(methodId, gateway) {
        // Update visual selection
        document.querySelectorAll('.payment-method-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        const selectedCard = document.querySelector(`[data-method="${methodId}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
        }
        
        // Store selection
        this.selectedMethod = methodId;
        this.selectedGateway = gateway;
        
        // Show payment details
        this.showPaymentDetails(methodId, gateway);
        
        // Show payment button
        this.showPaymentButton();
    }
    
    showPaymentDetails(methodId, gateway) {
        const container = document.getElementById('payment-details');
        if (!container) return;
        
        if (gateway === 'paypal') {
            container.innerHTML = `
                <div class="payment-details-card">
                    <h5><i class="bi bi-paypal me-2"></i>PayPal Payment</h5>
                    <p>You will be redirected to PayPal to complete your payment securely.</p>
                    <div class="security-info">
                        <small class="text-muted">
                            <i class="bi bi-shield-lock me-1"></i>
                            Secured by PayPal - Your payment information is never shared
                        </small>
                    </div>
                </div>
            `;
        } else {
            // Indian payment methods
            const methodDetails = {
                'upi': {
                    title: 'UPI Payment',
                    description: 'Pay with PhonePe, Google Pay, Paytm, or any UPI app',
                    features: ['Instant payment', 'No additional charges', 'Secure & fast']
                },
                'card': {
                    title: 'Card Payment',
                    description: 'Debit/Credit Cards, Visa, Mastercard, RuPay',
                    features: ['All major cards accepted', 'Secure 3D verification', 'EMI options available']
                },
                'netbanking': {
                    title: 'Net Banking',
                    description: 'Direct bank transfer from your account',
                    features: ['All major banks', 'Direct bank transfer', 'Instant confirmation']
                },
                'wallet': {
                    title: 'Digital Wallets',
                    description: 'Paytm, Mobikwik, Amazon Pay, and more',
                    features: ['Quick payment', 'Wallet balance', 'Cashback offers']
                }
            };
            
            const detail = methodDetails[methodId] || methodDetails.upi;
            
            container.innerHTML = `
                <div class="payment-details-card">
                    <h5><i class="bi bi-bank me-2"></i>${detail.title}</h5>
                    <p>${detail.description}</p>
                    <ul class="features-list">
                        ${detail.features.map(feature => `<li><i class="bi bi-check-circle-fill text-success me-2"></i>${feature}</li>`).join('')}
                    </ul>
                    <div class="currency-info">
                        <small class="text-muted">
                            <i class="bi bi-currency-exchange me-1"></i>
                            Currency: ${this.selectedCurrency} (${this.getCurrencyName(this.selectedCurrency)})
                        </small>
                    </div>
                </div>
            `;
        }
    }
    
    showPaymentButton() {
        const container = document.getElementById('payment-button-container');
        if (!container) return;
        
        container.innerHTML = `
            <button type="button" class="btn btn-primary btn-lg payment-btn" id="pay-now-button">
                <span class="btn-text">
                    <i class="bi bi-lock me-2"></i>Pay ${this.formatCurrency(this.orderData.total, this.selectedCurrency)}
                </span>
                <span class="btn-loader" style="display: none;">
                    <span class="spinner-border spinner-border-sm" role="status"></span>
                    Processing Payment...
                </span>
            </button>
        `;
        
        // Bind click event
        const payButton = document.getElementById('pay-now-button');
        if (payButton) {
            payButton.addEventListener('click', () => this.initiatePayment());
        }
    }
    
    async initiatePayment() {
        if (this.isLoading) return;
        
        if (!this.selectedMethod) {
            this.showPaymentMessage('Please select a payment method', 'error');
            return;
        }
        
        // Show loading state
        this.showPaymentLoading(true);
        
        try {
            // Get form data
            const formData = new FormData(this.paymentForm);
            
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
                if (result.gateway === 'paypal') {
                    // Redirect to PayPal
                    if (result.approval_url) {
                        this.showPaymentMessage('Redirecting to PayPal...', 'success');
                        setTimeout(() => {
                            window.location.href = result.approval_url;
                        }, 1500);
                    } else {
                        throw new Error('PayPal approval URL not received');
                    }
                } else {
                    // Process with Razorpay (simplified for demo)
                    this.handleRazorpayPayment(result);
                }
            } else {
                throw new Error(result.error || 'Payment setup failed');
            }
            
        } catch (error) {
            console.error('Payment error:', error);
            this.showPaymentMessage(error.message || 'Payment failed. Please try again.', 'error');
        } finally {
            this.showPaymentLoading(false);
        }
    }
    
    handleRazorpayPayment(paymentData) {
        // In a real implementation, this would integrate with Razorpay
        // For demo purposes, we'll simulate a successful payment
        setTimeout(() => {
            this.showPaymentMessage('Payment processed successfully!', 'success');
            setTimeout(() => {
                this.goToStep(3);
                this.showConfirmation({
                    bookingId: 'BK-' + Math.floor(100000 + Math.random() * 900000),
                    amount: this.orderData.total,
                    method: this.selectedMethod,
                    date: new Date().toLocaleDateString()
                });
            }, 1500);
        }, 2000);
    }
    
    showPaymentLoading(show) {
        this.isLoading = show;
        const button = document.querySelector('.payment-btn');
        const buttonText = button?.querySelector('.btn-text');
        const buttonLoader = button?.querySelector('.btn-loader');
        
        if (button && buttonText && buttonLoader) {
            button.disabled = show;
            buttonText.style.display = show ? 'none' : 'inline';
            buttonLoader.style.display = show ? 'inline' : 'none';
        }
    }
    
    showPaymentMessage(message, type) {
        const messageElement = document.getElementById('payment-message');
        if (!messageElement) return;
        
        // Set message content and type
        messageElement.textContent = message;
        messageElement.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : type === 'info' ? 'info' : 'warning'}`;
        messageElement.style.display = 'block';
        
        // Auto-hide non-success messages
        if (type !== 'success') {
            setTimeout(() => {
                messageElement.style.display = 'none';
            }, 5000);
        }
    }
    
    hidePaymentMessage() {
        const messageElement = document.getElementById('payment-message');
        if (messageElement) {
            messageElement.style.display = 'none';
        }
    }
    
    goToStep(step) {
        // Hide all steps
        Object.values(this.stepContainers).forEach(container => {
            container.classList.remove('active');
        });
        
        // Remove active class from all stepper items
        Object.values(this.stepElements).forEach(element => {
            element.classList.remove('active');
        });
        
        // Show current step
        if (this.stepContainers[step]) {
            this.stepContainers[step].classList.add('active');
        }
        
        // Mark stepper item as active
        if (this.stepElements[step]) {
            this.stepElements[step].classList.add('active');
        }
        
        // Update current step
        this.currentStep = step;
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    showConfirmation(data) {
        // Update confirmation details
        document.getElementById('confirmation-booking-id').textContent = data.bookingId;
        document.getElementById('confirmation-amount').textContent = 
            this.formatCurrency(data.amount, this.selectedCurrency);
        document.getElementById('confirmation-method').textContent = 
            this.getMethodDisplayName(this.selectedMethod);
    }
    
    // Helper methods
    formatCurrency(amount, currency) {
        const currencySymbols = {
            'USD': '$',
            'AUD': 'A$',
            'INR': '₹',
            'EUR': '€',
            'GBP': '£'
        };
        
        const symbol = currencySymbols[currency] || currency;
        return `${symbol}${amount.toFixed(2)}`;
    }
    
    getCurrencyName(currencyCode) {
        const currencyNames = {
            'USD': 'US Dollar',
            'AUD': 'Australian Dollar',
            'INR': 'Indian Rupee',
            'EUR': 'Euro',
            'GBP': 'British Pound'
        };
        
        return currencyNames[currencyCode] || currencyCode;
    }
    
    getMethodDisplayName(methodId) {
        const methodNames = {
            'paypal': 'PayPal',
            'upi': 'UPI',
            'card': 'Credit/Debit Card',
            'netbanking': 'Net Banking',
            'wallet': 'Digital Wallet'
        };
        
        return methodNames[methodId] || methodId;
    }
}

// Initialize checkout manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.checkout = new CheckoutManager();
});