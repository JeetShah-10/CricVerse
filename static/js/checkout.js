/**
 * Enhanced Professional Checkout System for CricVerse Stadium System
 * Multi-step checkout with unified payment processing
 * Big Bash League Cricket Platform
 * 
 * Features:
 * - Enhanced loading states and animations
 * - Improved error messaging with retry mechanisms
 * - Mobile-responsive design optimizations
 * - Progressive enhancement for offline scenarios
 * - Accessibility improvements
 */

class CheckoutManager {
    constructor() {
        this.currentStep = 1;
        this.orderData = {};
        this.selectedCurrency = 'USD';
        this.selectedMethod = null;
        this.selectedGateway = null;
        this.isLoading = false;
        this.isOnline = navigator.onLine;
        this.retryCount = 0;
        this.maxRetries = 3;
        this.loadingAnimations = new Map();
        this.touchStartX = 0;
        this.touchStartY = 0;
        
        this.initializeElements();
        this.bindEvents();
        this.setupOfflineHandling();
        this.setupMobileOptimizations();
        this.loadOrderData();
        this.setupAccessibility();
        
        console.log('🏏 Enhanced CricVerse Checkout Manager initialized');
        this.logDeviceInfo();
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
        
        // Enhanced UI elements
        this.loadingOverlay = this.createLoadingOverlay();
        this.errorContainer = this.createErrorContainer();
        this.offlineIndicator = this.createOfflineIndicator();
        
        // Create mobile-specific elements
        this.createMobileElements();
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
        
        // Enhanced mobile touch events
        this.bindTouchEvents();
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyNavigation(e));
        
        // Window resize for responsive adjustments
        window.addEventListener('resize', this.debounce(() => this.handleResize(), 250));
        
        // Form validation events
        this.bindFormValidation();
    }
    
    loadOrderData() {
        // Prefer context from URL query params if present (dashboard Pay Now)
        const params = new URLSearchParams(window.location.search);
        const type = params.get('type'); // 'order' | 'parking' | ...
        const amount = parseFloat(params.get('amount') || '0');
        const orderId = params.get('order_id');
        const bookingId = params.get('booking_id');

        if (type && amount > 0) {
            const name = type === 'order' ? 'Concession Order' : type === 'parking' ? 'Parking Booking' : 'BBL Payment';
            const desc = type === 'order' && orderId ? `Order #${orderId}` : type === 'parking' && bookingId ? `Parking Booking #${bookingId}` : 'BBL Payment';

            this.orderData = {
                items: [
                    {
                        id: 1,
                        name: name,
                        description: desc,
                        quantity: 1,
                        price: amount,
                        type: type
                    }
                ],
                eventId: '',
                seatIds: [],
                subtotal: amount,
                fee: 0.00,
                total: amount,
                _ctx: { type, amount, orderId, bookingId }
            };
        } else {
            // Fallback demo data
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
                total: 63.00,
                _ctx: null
            };
        }

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
        
        // Check if online for real payment processing
        if (!this.isOnline) {
            this.showError('Payment requires an internet connection. Please check your connection and try again.', 
                          () => this.initiatePayment());
            return;
        }
        
        // Show enhanced loading state
        this.showPaymentLoading(true);
        this.showLoadingOverlay('Initializing payment...', 10);
        
        try {
            // Validate form first
            if (!this.validateForm()) {
                throw new Error('Please fill in all required fields correctly.');
            }
            
            // Update loading progress
            this.showLoadingOverlay('Preparing payment data...', 25);
            
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
            
            // Update loading progress
            this.showLoadingOverlay('Contacting payment gateway...', 50);
            
            // Create payment order
            const response = await fetch('/api/create-payment-intent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrf_token]')?.value || ''
                },
                body: JSON.stringify(paymentData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.showLoadingOverlay('Processing payment...', 75);
                
                if (result.gateway === 'paypal') {
                    // Redirect to PayPal
                    if (result.approval_url) {
                        this.showLoadingOverlay('Redirecting to PayPal...', 90);
                        this.showPaymentMessage('Redirecting to PayPal...', 'success');
                        
                        // Store payment data for return handling
                        localStorage.setItem('cricverse_payment_data', JSON.stringify({
                            orderId: result.order_id,
                            amount: paymentData.amount,
                            currency: paymentData.currency,
                            timestamp: Date.now()
                        }));
                        
                        setTimeout(() => {
                            window.location.href = result.approval_url;
                        }, 1500);
                    } else {
                        throw new Error('PayPal approval URL not received');
                    }
                } else {
                    // Process with Razorpay
                    this.handleRazorpayPayment(result);
                }
            } else {
                throw new Error(result.error || 'Payment setup failed');
            }
            
        } catch (error) {
            console.error('Payment error:', error);
            
            // Enhanced error handling
            let errorMessage = 'Payment failed. Please try again.';
            let retryAction = () => this.initiatePayment();
            
            if (error.message.includes('network') || error.message.includes('fetch')) {
                errorMessage = 'Network error. Please check your connection and try again.';
            } else if (error.message.includes('400')) {
                errorMessage = 'Invalid payment data. Please check your details and try again.';
            } else if (error.message.includes('401')) {
                errorMessage = 'Session expired. Please refresh the page and try again.';
                retryAction = () => window.location.reload();
            } else if (error.message.includes('500')) {
                errorMessage = 'Server error. Our team has been notified. Please try again later.';
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            this.showError(errorMessage, retryAction);
            this.showPaymentMessage(errorMessage, 'error');
            
            // Add to pending operations if offline
            if (!this.isOnline) {
                this.pendingOperations.push(() => this.initiatePayment());
                this.showMessage('Payment will be processed when connection is restored.', 'info');
            }
            
        } finally {
            this.showPaymentLoading(false);
            this.hideLoadingOverlay();
        }
    }
    
    handleRazorpayPayment(paymentData) {
        // In a real implementation, this would integrate with Razorpay
        // For demo purposes, we'll simulate a payment process with enhanced loading states
        
        this.showLoadingOverlay('Connecting to Razorpay...', 80);
        
        // Simulate payment processing steps
        const steps = [
            { message: 'Verifying payment details...', progress: 85, delay: 1000 },
            { message: 'Processing payment...', progress: 90, delay: 1500 },
            { message: 'Confirming transaction...', progress: 95, delay: 1000 },
            { message: 'Payment successful!', progress: 100, delay: 500 }
        ];
        
        let currentStep = 0;
        
        const processNextStep = () => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                this.showLoadingOverlay(step.message, step.progress);
                
                setTimeout(() => {
                    currentStep++;
                    processNextStep();
                }, step.delay);
            } else {
                // Payment completed
                this.hideLoadingOverlay();
                this.showPaymentMessage('Payment processed successfully!', 'success');
                
                // Show success animation
                this.showPaymentSuccess();
                
                setTimeout(() => {
                    this.goToStep(3);
                    this.showConfirmation({
                        bookingId: 'BK-' + Math.floor(100000 + Math.random() * 900000),
                        amount: this.orderData.total,
                        method: this.selectedMethod,
                        date: new Date().toLocaleDateString(),
                        transactionId: 'TXN-' + Math.floor(1000000 + Math.random() * 9000000)
                    });

                    // If context provided from dashboard, auto-confirm server-side and redirect back to dashboard
                    if (this.orderData._ctx && this.orderData._ctx.type) {
                        const q = new URLSearchParams();
                        q.set('type', this.orderData._ctx.type);
                        q.set('amount', String(this.orderData.total.toFixed(2)));
                        if (this.orderData._ctx.orderId) q.set('order_id', this.orderData._ctx.orderId);
                        if (this.orderData._ctx.bookingId) q.set('booking_id', this.orderData._ctx.bookingId);
                        setTimeout(() => { window.location.href = `/payment/confirm?${q.toString()}`; }, 1200);
                    }
                }, 2000);
            }
        };
        
        processNextStep();
    }
    
    showPaymentSuccess() {
        // Create success animation overlay
        const successOverlay = document.createElement('div');
        successOverlay.className = 'payment-success-overlay';
        successOverlay.innerHTML = `
            <div class="success-content">
                <div class="success-icon">
                    <i class="bi bi-check-circle-fill"></i>
                </div>
                <h3>Payment Successful!</h3>
                <p>Your booking has been confirmed</p>
                <div class="success-animation">
                    <div class="checkmark">
                        <svg viewBox="0 0 52 52">
                            <circle cx="26" cy="26" r="25" fill="none" stroke="#28a745" stroke-width="2"/>
                            <path fill="none" stroke="#28a745" stroke-width="3" stroke-linecap="round" 
                                  stroke-linejoin="round" d="M14 27l8 8 16-16"/>
                        </svg>
                    </div>
                </div>
            </div>
        `;
        
        // Add styles for success animation
        const successStyle = document.createElement('style');
        successStyle.textContent = `
            .payment-success-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.9);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10001;
                animation: fadeIn 0.3s ease;
            }
            
            .success-content {
                background: white;
                padding: 3rem 2rem;
                border-radius: 16px;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                max-width: 400px;
                width: 90%;
                animation: slideUp 0.5s ease;
            }
            
            .success-icon {
                font-size: 4rem;
                color: #28a745;
                margin-bottom: 1rem;
                animation: bounceIn 0.6s ease 0.2s both;
            }
            
            .success-content h3 {
                color: #28a745;
                margin-bottom: 0.5rem;
                font-weight: 600;
            }
            
            .success-content p {
                color: #6c757d;
                margin-bottom: 2rem;
            }
            
            .checkmark {
                width: 60px;
                height: 60px;
                margin: 0 auto;
            }
            
            .checkmark svg {
                width: 100%;
                height: 100%;
            }
            
            .checkmark circle {
                stroke-dasharray: 166;
                stroke-dashoffset: 166;
                animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) 0.5s forwards;
            }
            
            .checkmark path {
                stroke-dasharray: 48;
                stroke-dashoffset: 48;
                animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideUp {
                from { transform: translateY(30px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            @keyframes bounceIn {
                0% { transform: scale(0); }
                50% { transform: scale(1.2); }
                100% { transform: scale(1); }
            }
            
            @keyframes stroke {
                100% { stroke-dashoffset: 0; }
            }
        `;
        
        document.head.appendChild(successStyle);
        document.body.appendChild(successOverlay);
        
        // Remove overlay after animation
        setTimeout(() => {
            successOverlay.remove();
            successStyle.remove();
        }, 3000);
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
        
        // Update mobile step indicator
        this.updateMobileStepIndicator();
        
        // Announce step change for accessibility
        const stepNames = {
            1: 'Order Summary',
            2: 'Payment Method Selection', 
            3: 'Confirmation'
        };
        
        if (this.announceToScreenReader) {
            this.announceToScreenReader(`Navigated to ${stepNames[step] || 'step ' + step}`);
        }
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
        // Focus management for accessibility
        setTimeout(() => {
            const stepContainer = this.stepContainers[step];
            if (stepContainer) {
                const firstFocusable = stepContainer.querySelector(
                    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled])'
                );
                if (firstFocusable) {
                    firstFocusable.focus();
                }
            }
        }, 100);
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
    
    // Enhanced UI Creation Methods
    createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'checkout-loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="spinner-container">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
                <div class="loading-text">Processing your request...</div>
                <div class="loading-progress">
                    <div class="progress">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 0%"></div>
                    </div>
                </div>
            </div>
        `;
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                display: none;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                backdrop-filter: blur(2px);
            }
            
            .loading-content {
                background: white;
                padding: 2rem;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                max-width: 300px;
                width: 90%;
            }
            
            .spinner-container {
                margin-bottom: 1rem;
            }
            
            .loading-text {
                font-weight: 500;
                color: #333;
                margin-bottom: 1rem;
            }
            
            .loading-progress {
                width: 100%;
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(overlay);
        
        return overlay;
    }
    
    createErrorContainer() {
        const container = document.createElement('div');
        container.id = 'checkout-error-container';
        container.className = 'error-container';
        container.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <div class="error-content">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    <span class="error-message"></span>
                </div>
                <div class="error-actions mt-2">
                    <button type="button" class="btn btn-sm btn-outline-danger retry-btn">
                        <i class="bi bi-arrow-clockwise me-1"></i>Retry
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary ms-2 dismiss-btn">
                        Dismiss
                    </button>
                </div>
            </div>
        `;
        
        container.style.display = 'none';
        
        // Bind events
        const retryBtn = container.querySelector('.retry-btn');
        const dismissBtn = container.querySelector('.dismiss-btn');
        
        if (retryBtn) {
            retryBtn.addEventListener('click', () => this.retryLastAction());
        }
        
        if (dismissBtn) {
            dismissBtn.addEventListener('click', () => this.hideError());
        }
        
        return container;
    }
    
    createOfflineIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'offline-indicator';
        indicator.className = 'offline-indicator';
        indicator.innerHTML = `
            <div class="alert alert-warning mb-0">
                <i class="bi bi-wifi-off me-2"></i>
                <strong>You're offline.</strong> Some features may not be available.
                <button type="button" class="btn btn-sm btn-outline-warning ms-2 refresh-btn">
                    <i class="bi bi-arrow-clockwise me-1"></i>Try Again
                </button>
            </div>
        `;
        
        indicator.style.display = 'none';
        
        const refreshBtn = indicator.querySelector('.refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                if (navigator.onLine) {
                    this.hideOfflineIndicator();
                    this.loadPaymentMethods();
                }
            });
        }
        
        return indicator;
    }
    
    createMobileElements() {
        // Create mobile-specific navigation
        const mobileNav = document.createElement('div');
        mobileNav.className = 'mobile-nav d-md-none';
        mobileNav.innerHTML = `
            <div class="mobile-step-indicator">
                <div class="step-dots">
                    <span class="dot active" data-step="1"></span>
                    <span class="dot" data-step="2"></span>
                    <span class="dot" data-step="3"></span>
                </div>
                <div class="step-title">Order Summary</div>
            </div>
        `;
        
        // Add mobile styles
        const mobileStyle = document.createElement('style');
        mobileStyle.textContent = `
            .mobile-nav {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: white;
                padding: 1rem;
                border-bottom: 1px solid #dee2e6;
                z-index: 1000;
            }
            
            .mobile-step-indicator {
                text-align: center;
            }
            
            .step-dots {
                display: flex;
                justify-content: center;
                gap: 0.5rem;
                margin-bottom: 0.5rem;
            }
            
            .dot {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #dee2e6;
                display: inline-block;
                transition: all 0.3s ease;
            }
            
            .dot.active {
                background: #0d6efd;
            }
            
            .step-title {
                font-size: 0.9rem;
                font-weight: 500;
                color: #6c757d;
            }
            
            @media (max-width: 767px) {
                .container {
                    padding-top: 80px;
                }
                
                .payment-method-card {
                    margin-bottom: 0.5rem;
                }
                
                .btn-lg {
                    padding: 0.75rem 1rem;
                    font-size: 1rem;
                }
            }
        `;
        document.head.appendChild(mobileStyle);
        
        // Insert mobile nav at the beginning of body
        document.body.insertBefore(mobileNav, document.body.firstChild);
        
        this.mobileNav = mobileNav;
    }
    
    // Enhanced Event Handling Methods
    bindTouchEvents() {
        // Swipe navigation for mobile
        let startX = 0;
        let startY = 0;
        
        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        }, { passive: true });
        
        document.addEventListener('touchend', (e) => {
            if (!startX || !startY) return;
            
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            
            const diffX = startX - endX;
            const diffY = startY - endY;
            
            // Only process horizontal swipes that are significant
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
                if (diffX > 0 && this.currentStep < 3) {
                    // Swipe left - next step
                    this.goToStep(this.currentStep + 1);
                } else if (diffX < 0 && this.currentStep > 1) {
                    // Swipe right - previous step
                    this.goToStep(this.currentStep - 1);
                }
            }
            
            startX = 0;
            startY = 0;
        }, { passive: true });
        
        // Enhanced touch feedback for buttons
        document.addEventListener('touchstart', (e) => {
            if (e.target.matches('.btn, .payment-method-card')) {
                e.target.style.transform = 'scale(0.95)';
            }
        }, { passive: true });
        
        document.addEventListener('touchend', (e) => {
            if (e.target.matches('.btn, .payment-method-card')) {
                setTimeout(() => {
                    e.target.style.transform = '';
                }, 150);
            }
        }, { passive: true });
    }
    
    handleKeyNavigation(e) {
        // Escape key to close overlays
        if (e.key === 'Escape') {
            this.hideLoadingOverlay();
            this.hideError();
        }
        
        // Arrow keys for step navigation
        if (e.altKey) {
            if (e.key === 'ArrowLeft' && this.currentStep > 1) {
                e.preventDefault();
                this.goToStep(this.currentStep - 1);
            } else if (e.key === 'ArrowRight' && this.currentStep < 3) {
                e.preventDefault();
                this.goToStep(this.currentStep + 1);
            }
        }
        
        // Enter key to proceed
        if (e.key === 'Enter' && e.target.matches('.payment-method-card')) {
            e.target.click();
        }
    }
    
    bindFormValidation() {
        const form = this.paymentForm;
        if (!form) return;
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input));
        });
        
        // Form submission validation
        form.addEventListener('submit', (e) => {
            if (!this.validateForm()) {
                e.preventDefault();
                return false;
            }
        });
    }
    
    validateField(field) {
        let isValid = true;
        let errorMessage = '';
        
        // Remove existing error styling
        field.classList.remove('is-invalid');
        
        // Required field validation
        if (field.hasAttribute('required') && !field.value.trim()) {
            isValid = false;
            errorMessage = 'This field is required.';
        }
        
        // Email validation
        if (field.type === 'email' && field.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(field.value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address.';
            }
        }
        
        // Amount validation
        if (field.name === 'amount' && field.value) {
            const amount = parseFloat(field.value);
            if (isNaN(amount) || amount <= 0) {
                isValid = false;
                errorMessage = 'Please enter a valid amount.';
            }
        }
        
        // Show/hide error
        if (!isValid) {
            field.classList.add('is-invalid');
            this.showFieldError(field, errorMessage);
        } else {
            this.clearFieldError(field);
        }
        
        return isValid;
    }
    
    validateForm() {
        const form = this.paymentForm;
        if (!form) return true;
        
        let isValid = true;
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        
        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    showFieldError(field, message) {
        let errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            field.parentNode.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
    }
    
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
    
    // Progressive Enhancement Methods
    setupOfflineHandling() {
        // Online/offline event listeners
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.hideOfflineIndicator();
            this.showMessage('Connection restored!', 'success');
            // Retry any pending operations
            if (this.pendingOperations && this.pendingOperations.length > 0) {
                this.processPendingOperations();
            }
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showOfflineIndicator();
            this.showMessage('You are currently offline. Some features may be limited.', 'warning');
        });
        
        // Initialize offline indicator if needed
        if (!navigator.onLine) {
            this.isOnline = false;
            this.showOfflineIndicator();
        }
        
        // Initialize pending operations array
        this.pendingOperations = [];
    }
    
    setupMobileOptimizations() {
        // Viewport meta tag for mobile
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            viewport.content = 'width=device-width, initial-scale=1, user-scalable=no';
            document.head.appendChild(viewport);
        }
        
        // Prevent zoom on input focus (iOS)
        if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
            document.querySelectorAll('input, select, textarea').forEach(input => {
                input.addEventListener('focus', () => {
                    if (parseFloat(input.style.fontSize) < 16) {
                        input.style.fontSize = '16px';
                    }
                });
            });
        }
        
        // Handle screen orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleResize();
            }, 100);
        });
        
        // Add mobile-specific CSS classes
        if (window.innerWidth <= 768) {
            document.body.classList.add('mobile-device');
        }
    }
    
    setupAccessibility() {
        // Add ARIA labels and roles
        const steppers = document.querySelectorAll('.stepper-item');
        steppers.forEach((stepper, index) => {
            stepper.setAttribute('role', 'tab');
            stepper.setAttribute('aria-label', `Step ${index + 1}`);
        });
        
        // Add focus management
        document.addEventListener('keydown', (e) => {
            // Tab key navigation enhancement
            if (e.key === 'Tab') {
                const focusableElements = this.getFocusableElements();
                const currentIndex = focusableElements.indexOf(document.activeElement);
                
                if (e.shiftKey) {
                    // Shift + Tab (backward)
                    if (currentIndex === 0) {
                        e.preventDefault();
                        focusableElements[focusableElements.length - 1].focus();
                    }
                } else {
                    // Tab (forward)
                    if (currentIndex === focusableElements.length - 1) {
                        e.preventDefault();
                        focusableElements[0].focus();
                    }
                }
            }
        });
        
        // Announce step changes to screen readers
        this.announceToScreenReader = (message) => {
            const announcement = document.createElement('div');
            announcement.setAttribute('aria-live', 'polite');
            announcement.setAttribute('aria-atomic', 'true');
            announcement.className = 'sr-only';
            announcement.textContent = message;
            document.body.appendChild(announcement);
            
            setTimeout(() => {
                document.body.removeChild(announcement);
            }, 1000);
        };
    }
    
    getFocusableElements() {
        return Array.from(document.querySelectorAll(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )).filter(el => {
            return el.offsetWidth > 0 && el.offsetHeight > 0;
        });
    }
    
    // Utility Methods
    handleResize() {
        // Update mobile nav visibility
        const isMobile = window.innerWidth <= 768;
        if (isMobile) {
            document.body.classList.add('mobile-device');
            if (this.mobileNav) {
                this.mobileNav.style.display = 'block';
            }
        } else {
            document.body.classList.remove('mobile-device');
            if (this.mobileNav) {
                this.mobileNav.style.display = 'none';
            }
        }
        
        // Update step indicator for mobile
        this.updateMobileStepIndicator();
    }
    
    updateMobileStepIndicator() {
        if (!this.mobileNav) return;
        
        const dots = this.mobileNav.querySelectorAll('.dot');
        const title = this.mobileNav.querySelector('.step-title');
        
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index + 1 === this.currentStep);
        });
        
        const stepTitles = {
            1: 'Order Summary',
            2: 'Payment Method',
            3: 'Confirmation'
        };
        
        if (title) {
            title.textContent = stepTitles[this.currentStep] || 'Checkout';
        }
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    showLoadingOverlay(message = 'Processing...', progress = 0) {
        if (this.loadingOverlay) {
            const loadingText = this.loadingOverlay.querySelector('.loading-text');
            const progressBar = this.loadingOverlay.querySelector('.progress-bar');
            
            if (loadingText) loadingText.textContent = message;
            if (progressBar) progressBar.style.width = `${progress}%`;
            
            this.loadingOverlay.style.display = 'flex';
        }
    }
    
    hideLoadingOverlay() {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'none';
        }
    }
    
    showError(message, retryAction = null) {
        if (this.errorContainer) {
            const errorMessage = this.errorContainer.querySelector('.error-message');
            const retryBtn = this.errorContainer.querySelector('.retry-btn');
            
            if (errorMessage) errorMessage.textContent = message;
            
            // Store retry action
            this.lastRetryAction = retryAction;
            
            if (retryBtn) {
                retryBtn.style.display = retryAction ? 'inline-block' : 'none';
            }
            
            this.errorContainer.style.display = 'block';
            
            // Insert error container at appropriate location
            const currentStepContainer = this.stepContainers[this.currentStep];
            if (currentStepContainer && !currentStepContainer.contains(this.errorContainer)) {
                currentStepContainer.insertBefore(this.errorContainer, currentStepContainer.firstChild);
            }
        }
    }
    
    hideError() {
        if (this.errorContainer) {
            this.errorContainer.style.display = 'none';
        }
    }
    
    retryLastAction() {
        if (this.lastRetryAction && typeof this.lastRetryAction === 'function') {
            this.hideError();
            this.retryCount++;
            
            if (this.retryCount <= this.maxRetries) {
                this.showLoadingOverlay('Retrying...', 25);
                setTimeout(() => {
                    this.lastRetryAction();
                }, 1000);
            } else {
                this.showError('Maximum retry attempts reached. Please refresh the page and try again.');
                this.retryCount = 0;
            }
        }
    }
    
    showOfflineIndicator() {
        if (this.offlineIndicator) {
            this.offlineIndicator.style.display = 'block';
            
            // Insert at top of current step
            const currentStepContainer = this.stepContainers[this.currentStep];
            if (currentStepContainer && !currentStepContainer.contains(this.offlineIndicator)) {
                currentStepContainer.insertBefore(this.offlineIndicator, currentStepContainer.firstChild);
            }
        }
    }
    
    hideOfflineIndicator() {
        if (this.offlineIndicator) {
            this.offlineIndicator.style.display = 'none';
        }
    }
    
    showMessage(message, type = 'info', duration = 5000) {
        // Create or update message element
        let messageEl = document.getElementById('global-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'global-message';
            messageEl.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 300px;
            `;
            document.body.appendChild(messageEl);
        }
        
        messageEl.innerHTML = `
            <div class="alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Auto-hide after duration
        if (duration > 0) {
            setTimeout(() => {
                if (messageEl.parentNode) {
                    messageEl.remove();
                }
            }, duration);
        }
    }
    
    processPendingOperations() {
        if (!this.pendingOperations || this.pendingOperations.length === 0) return;
        
        this.showLoadingOverlay('Processing pending operations...', 50);
        
        // Process operations one by one
        const processNext = () => {
            if (this.pendingOperations.length > 0) {
                const operation = this.pendingOperations.shift();
                operation().then(() => {
                    setTimeout(processNext, 500);
                }).catch((error) => {
                    console.error('Pending operation failed:', error);
                    setTimeout(processNext, 500);
                });
            } else {
                this.hideLoadingOverlay();
                this.showMessage('All pending operations completed!', 'success');
            }
        };
        
        processNext();
    }
    
    logDeviceInfo() {
        const deviceInfo = {
            userAgent: navigator.userAgent,
            screenWidth: window.screen.width,
            screenHeight: window.screen.height,
            windowWidth: window.innerWidth,
            windowHeight: window.innerHeight,
            pixelRatio: window.devicePixelRatio,
            online: navigator.onLine,
            language: navigator.language,
            platform: navigator.platform,
            touchSupport: 'ontouchstart' in window
        };
        
        console.log('🏏 CricVerse Checkout - Device Info:', deviceInfo);
    }
}

// Initialize checkout manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.checkout = new CheckoutManager();
});