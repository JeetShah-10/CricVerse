/**
 * CricVerse Stripe Payment Integration
 * Client-side payment processing for bookings and parking
 */

class CricVerseStripeIntegration {
    constructor() {
        this.stripe = null;
        this.elements = null;
        this.paymentElement = null;
        this.currentPaymentIntent = null;
        
        this.initializeStripe();
    }
    
    async initializeStripe() {
        // Load Stripe.js dynamically
        if (!window.Stripe) {
            const script = document.createElement('script');
            script.src = 'https://js.stripe.com/v3/';
            script.onload = () => {
                this.setupStripe();
            };
            document.head.appendChild(script);
        } else {
            this.setupStripe();
        }
    }
    
    setupStripe() {
        // Initialize Stripe with publishable key (will be set when creating payment intent)
        console.log('Stripe.js loaded and ready');
    }
    
    async createBookingPayment(bookingData) {
        try {
            console.log('Creating booking payment intent...');
            
            // Create payment intent on server
            const response = await fetch('/api/create-booking-payment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(bookingData)
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Payment setup failed');
            }
            
            // Initialize Stripe with the returned publishable key
            if (!this.stripe) {
                this.stripe = Stripe(data.publishable_key);
            }
            
            // Store payment intent details
            this.currentPaymentIntent = {
                client_secret: data.client_secret,
                payment_intent_id: data.payment_intent_id
            };
            
            return data;
            
        } catch (error) {
            console.error('Error creating booking payment:', error);
            throw error;
        }
    }
    
    async createParkingPayment(parkingData) {
        try {
            console.log('Creating parking payment intent...');
            
            // Create payment intent on server
            const response = await fetch('/api/create-parking-payment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(parkingData)
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Payment setup failed');
            }
            
            // Initialize Stripe with the returned publishable key
            if (!this.stripe) {
                this.stripe = Stripe(data.publishable_key);
            }
            
            // Store payment intent details
            this.currentPaymentIntent = {
                client_secret: data.client_secret,
                payment_intent_id: data.payment_intent_id
            };
            
            return data;
            
        } catch (error) {
            console.error('Error creating parking payment:', error);
            throw error;
        }
    }
    
    setupPaymentForm(containerId, options = {}) {
        if (!this.stripe || !this.currentPaymentIntent) {
            throw new Error('Payment intent not created. Call createBookingPayment or createParkingPayment first.');
        }
        
        // Create Elements instance
        this.elements = this.stripe.elements({
            clientSecret: this.currentPaymentIntent.client_secret,
            appearance: {
                theme: 'stripe',
                variables: {
                    colorPrimary: '#0570de',
                    colorBackground: '#ffffff',
                    colorText: '#30313d',
                    colorDanger: '#df1b41',
                    fontFamily: 'Ideal Sans, system-ui, sans-serif',
                    spacingUnit: '2px',
                    borderRadius: '4px',
                },
                rules: {
                    '.Tab': {
                        padding: '10px 12px 8px 12px',
                        border: '1px solid #E3E3E3',
                    },
                    '.Tab:hover': {
                        color: '#0570de',
                    },
                    '.Tab--selected': {
                        borderColor: '#0570de',
                        backgroundColor: '#f7f9ff',
                    }
                }
            }
        });
        
        // Create payment element
        this.paymentElement = this.elements.create('payment', {
            defaultValues: {
                billingDetails: options.billingDetails || {}
            }
        });
        
        // Mount payment element
        this.paymentElement.mount('#' + containerId);
        
        // Handle real-time validation errors from the payment element
        this.paymentElement.on('change', ({error}) => {
            const messageContainer = document.getElementById('payment-message');
            if (messageContainer) {
                if (error) {
                    messageContainer.textContent = error.message;
                    messageContainer.className = 'alert alert-danger';
                } else {
                    messageContainer.textContent = '';
                    messageContainer.className = '';
                }
            }
        });
        
        return this.paymentElement;
    }
    
    async processPayment(returnUrl = null) {
        if (!this.stripe || !this.currentPaymentIntent) {
            throw new Error('Payment not initialized');
        }
        
        try {
            // Show loading state
            this.setLoading(true);
            
            // Confirm payment with Stripe
            const {error, paymentIntent} = await this.stripe.confirmPayment({
                elements: this.elements,
                confirmParams: {
                    return_url: returnUrl || window.location.origin + '/payment/success'
                }
            });
            
            this.setLoading(false);
            
            if (error) {
                // Payment failed
                console.error('Payment failed:', error);
                this.showPaymentError(error.message);
                return { success: false, error: error.message };
            } else {
                // Payment succeeded
                console.log('Payment succeeded:', paymentIntent);
                this.showPaymentSuccess();
                return { success: true, paymentIntent: paymentIntent };
            }
            
        } catch (error) {
            this.setLoading(false);
            console.error('Error processing payment:', error);
            this.showPaymentError('An unexpected error occurred');
            return { success: false, error: error.message };
        }
    }
    
    async checkPaymentStatus(paymentIntentId = null) {
        try {
            const intentId = paymentIntentId || this.currentPaymentIntent?.payment_intent_id;
            
            if (!intentId) {
                throw new Error('No payment intent ID available');
            }
            
            const response = await fetch(`/api/payment-status/${intentId}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to check payment status');
            }
            
            return data;
            
        } catch (error) {
            console.error('Error checking payment status:', error);
            throw error;
        }
    }
    
    setLoading(isLoading) {
        const submitButton = document.getElementById('payment-submit-button');
        if (submitButton) {
            if (isLoading) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing...';
            } else {
                submitButton.disabled = false;
                submitButton.innerHTML = 'Complete Payment';
            }
        }
    }
    
    showPaymentError(message) {
        const messageContainer = document.getElementById('payment-message');
        if (messageContainer) {
            messageContainer.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                </div>
            `;
        }
        
        // Also show as notification if realtime system is available
        if (window.cricVerseRealtime) {
            window.cricVerseRealtime.showNotification(message, 'error');
        }
    }
    
    showPaymentSuccess() {
        const messageContainer = document.getElementById('payment-message');
        if (messageContainer) {
            messageContainer.innerHTML = `
                <div class="alert alert-success" role="alert">
                    <i class="fas fa-check-circle me-2"></i>
                    Payment successful! Redirecting...
                </div>
            `;
        }
        
        // Show success notification
        if (window.cricVerseRealtime) {
            window.cricVerseRealtime.showNotification('Payment successful!', 'success');
        }
    }
    
    // Utility methods
    formatCurrency(amount, currency = 'AUD') {
        return new Intl.NumberFormat('en-AU', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }
    
    // Handle payment form submission
    setupPaymentForm(formId, options = {}) {
        const form = document.getElementById(formId);
        if (!form) {
            console.error('Payment form not found:', formId);
            return;
        }
        
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            
            try {
                const result = await this.processPayment(options.returnUrl);
                
                if (result.success) {
                    // Payment successful - redirect or show success
                    if (options.onSuccess) {
                        options.onSuccess(result);
                    } else {
                        // Default success handling
                        setTimeout(() => {
                            window.location.href = options.successUrl || '/dashboard';
                        }, 2000);
                    }
                } else {
                    // Payment failed - show error
                    if (options.onError) {
                        options.onError(result.error);
                    }
                }
                
            } catch (error) {
                console.error('Form submission error:', error);
                this.showPaymentError('Payment processing failed');
                
                if (options.onError) {
                    options.onError(error.message);
                }
            }
        });
    }
}

// Booking-specific payment handling
class BookingPaymentHandler {
    constructor(stripeIntegration) {
        this.stripe = stripeIntegration;
        this.bookingData = null;
    }
    
    async initializeBookingPayment(bookingId, seats, eventData) {
        try {
            // Calculate total amount
            const pricing = this.calculateBookingTotal(seats, eventData);
            
            // Prepare booking data for payment
            this.bookingData = {
                booking_id: bookingId,
                customer_id: eventData.customer_id,
                event_id: eventData.event_id,
                event_name: eventData.event_name,
                seat_count: seats.length,
                total_amount: pricing.total,
                seats: seats.map(seat => ({
                    seat_id: seat.id,
                    section: seat.section,
                    row: seat.row_number,
                    number: seat.seat_number,
                    price: seat.price
                }))
            };
            
            // Create payment intent
            const paymentData = await this.stripe.createBookingPayment(this.bookingData);
            
            return {
                ...paymentData,
                pricing: pricing,
                bookingData: this.bookingData
            };
            
        } catch (error) {
            console.error('Error initializing booking payment:', error);
            throw error;
        }
    }
    
    calculateBookingTotal(seats, eventData) {
        const subtotal = seats.reduce((sum, seat) => sum + parseFloat(seat.price), 0);
        const serviceFee = subtotal * 0.05; // 5% service fee
        const processingFee = 2.50; // Fixed processing fee
        const total = subtotal + serviceFee + processingFee;
        
        return {
            subtotal: Math.round(subtotal * 100) / 100,
            serviceFee: Math.round(serviceFee * 100) / 100,
            processingFee: processingFee,
            total: Math.round(total * 100) / 100
        };
    }
    
    displayBookingSummary(containerId) {
        if (!this.bookingData) {
            console.error('No booking data available');
            return;
        }
        
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Summary container not found:', containerId);
            return;
        }
        
        const pricing = this.calculateBookingTotal(this.bookingData.seats, this.bookingData);
        
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Booking Summary</h5>
                </div>
                <div class="card-body">
                    <h6 class="fw-bold">${this.bookingData.event_name}</h6>
                    <p class="text-muted mb-3">Selected Seats:</p>
                    <div class="row">
                        ${this.bookingData.seats.map(seat => `
                            <div class="col-6 mb-2">
                                <small class="text-muted">${seat.section} ${seat.row}-${seat.number}</small>
                                <div class="fw-bold">${this.stripe.formatCurrency(seat.price)}</div>
                            </div>
                        `).join('')}
                    </div>
                    <hr>
                    <div class="d-flex justify-content-between">
                        <span>Subtotal:</span>
                        <span>${this.stripe.formatCurrency(pricing.subtotal)}</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span>Service Fee:</span>
                        <span>${this.stripe.formatCurrency(pricing.serviceFee)}</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span>Processing Fee:</span>
                        <span>${this.stripe.formatCurrency(pricing.processingFee)}</span>
                    </div>
                    <hr>
                    <div class="d-flex justify-content-between fw-bold fs-5">
                        <span>Total:</span>
                        <span>${this.stripe.formatCurrency(pricing.total)}</span>
                    </div>
                </div>
            </div>
        `;
    }
}

// Parking-specific payment handling
class ParkingPaymentHandler {
    constructor(stripeIntegration) {
        this.stripe = stripeIntegration;
        this.parkingData = null;
    }
    
    async initializeParkingPayment(parkingBookingId, parkingZone, hours, vehicleData) {
        try {
            // Calculate parking fee
            const pricing = this.calculateParkingFee(parkingZone, hours);
            
            // Prepare parking data for payment
            this.parkingData = {
                parking_booking_id: parkingBookingId,
                customer_id: vehicleData.customer_id,
                stadium_id: parkingZone.stadium_id,
                stadium_name: parkingZone.stadium_name,
                zone: parkingZone.zone,
                vehicle_number: vehicleData.vehicle_number,
                hours: hours,
                amount: pricing.total
            };
            
            // Create payment intent
            const paymentData = await this.stripe.createParkingPayment(this.parkingData);
            
            return {
                ...paymentData,
                pricing: pricing,
                parkingData: this.parkingData
            };
            
        } catch (error) {
            console.error('Error initializing parking payment:', error);
            throw error;
        }
    }
    
    calculateParkingFee(parkingZone, hours) {
        const baseFee = parseFloat(parkingZone.rate_per_hour) * hours;
        const tax = baseFee * 0.10; // 10% tax
        const total = baseFee + tax;
        
        return {
            baseFee: Math.round(baseFee * 100) / 100,
            tax: Math.round(tax * 100) / 100,
            total: Math.round(total * 100) / 100,
            hours: hours,
            hourlyRate: parseFloat(parkingZone.rate_per_hour)
        };
    }
    
    displayParkingSummary(containerId) {
        if (!this.parkingData) {
            console.error('No parking data available');
            return;
        }
        
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('Summary container not found:', containerId);
            return;
        }
        
        const pricing = this.calculateParkingFee(this.parkingData, this.parkingData.hours);
        
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Parking Summary</h5>
                </div>
                <div class="card-body">
                    <h6 class="fw-bold">${this.parkingData.stadium_name}</h6>
                    <p class="text-muted mb-1">Zone: ${this.parkingData.zone}</p>
                    <p class="text-muted mb-1">Vehicle: ${this.parkingData.vehicle_number}</p>
                    <p class="text-muted mb-3">Duration: ${this.parkingData.hours} hours</p>
                    <hr>
                    <div class="d-flex justify-content-between">
                        <span>Base Fee (${pricing.hours}h × ${this.stripe.formatCurrency(pricing.hourlyRate)}):</span>
                        <span>${this.stripe.formatCurrency(pricing.baseFee)}</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span>Tax (10%):</span>
                        <span>${this.stripe.formatCurrency(pricing.tax)}</span>
                    </div>
                    <hr>
                    <div class="d-flex justify-content-between fw-bold fs-5">
                        <span>Total:</span>
                        <span>${this.stripe.formatCurrency(pricing.total)}</span>
                    </div>
                </div>
            </div>
        `;
    }
}

// Initialize global instances
window.CricVerseStripeIntegration = CricVerseStripeIntegration;
window.BookingPaymentHandler = BookingPaymentHandler;
window.ParkingPaymentHandler = ParkingPaymentHandler;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.cricVerseStripe = new CricVerseStripeIntegration();
    });
} else {
    window.cricVerseStripe = new CricVerseStripeIntegration();
}