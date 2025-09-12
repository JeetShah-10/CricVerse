/**
 * CricVerse Real-time WebSocket Client
 * Handles live match updates, booking notifications, and stadium occupancy tracking
 */

class CricVerseRealtime {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.subscribers = {
            matches: new Set(),
            stadiums: new Set()
        };
        this.eventHandlers = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        this.init();
    }
    
    init() {
        // Load Socket.IO from CDN if not already loaded
        if (typeof io === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://cdn.socket.io/4.7.2/socket.io.min.js';
            script.onload = () => {
                this.connect();
            };
            document.head.appendChild(script);
        } else {
            this.connect();
        }
    }
    
    connect() {
        console.log('Connecting to CricVerse real-time server...');
        
        this.socket = io({
            transports: ['websocket', 'polling'],
            timeout: 20000,
            forceNew: true
        });
        
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('Connected to CricVerse real-time server');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            
            this.showNotification('Connected to live updates!', 'success');
            this.trigger('connected');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from real-time server');
            this.isConnected = false;
            
            this.showNotification('Lost connection to live updates', 'warning');
            this.trigger('disconnected');
            this.attemptReconnect();
        });
        
        this.socket.on('connection_status', (data) => {
            console.log('Connection status:', data);
            this.trigger('connection_status', data);
        });
        
        // Match events
        this.socket.on('match_update', (data) => {
            console.log('Match update received:', data);
            this.handleMatchUpdate(data);
            this.trigger('match_update', data);
        });
        
        this.socket.on('current_match_status', (data) => {
            console.log('Current match status:', data);
            this.handleCurrentMatchStatus(data);
            this.trigger('current_match_status', data);
        });
        
        // Stadium events
        this.socket.on('booking_notification', (data) => {
            console.log('Booking notification:', data);
            this.handleBookingNotification(data);
            this.trigger('booking_notification', data);
        });
        
        this.socket.on('occupancy_update', (data) => {
            console.log('Occupancy update:', data);
            this.handleOccupancyUpdate(data);
            this.trigger('occupancy_update', data);
        });
        
        this.socket.on('current_occupancy', (data) => {
            console.log('Current occupancy:', data);
            this.handleCurrentOccupancy(data);
            this.trigger('current_occupancy', data);
        });
        
        // Subscription confirmations
        this.socket.on('subscription_status', (data) => {
            console.log('Subscription status:', data);
            this.trigger('subscription_status', data);
        });
        
        // Error handling
        this.socket.on('error', (data) => {
            console.error('WebSocket error:', data);
            this.showNotification(data.message || 'Connection error', 'error');
            this.trigger('error', data);
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.showNotification('Failed to connect to live updates', 'error');
        });
    }
    
    // Match subscription methods
    subscribeToMatch(matchId) {
        if (!this.isConnected) {
            console.warn('Not connected to real-time server');
            return false;
        }
        
        if (this.subscribers.matches.has(matchId)) {
            console.log('Already subscribed to match ' + matchId);
            return true;
        }
        
        this.socket.emit('join_match', { match_id: matchId });
        this.subscribers.matches.add(matchId);
        
        console.log('Subscribed to match ' + matchId);
        return true;
    }
    
    unsubscribeFromMatch(matchId) {
        if (!this.isConnected) {
            return false;
        }
        
        if (!this.subscribers.matches.has(matchId)) {
            console.log('Not subscribed to match ' + matchId);
            return true;
        }
        
        this.socket.emit('leave_match', { match_id: matchId });
        this.subscribers.matches.delete(matchId);
        
        console.log('Unsubscribed from match ' + matchId);
        return true;
    }
    
    // Stadium subscription methods
    subscribeToStadium(stadiumId) {
        if (!this.isConnected) {
            console.warn('Not connected to real-time server');
            return false;
        }
        
        if (this.subscribers.stadiums.has(stadiumId)) {
            console.log('Already subscribed to stadium ' + stadiumId);
            return true;
        }
        
        this.socket.emit('join_stadium', { stadium_id: stadiumId });
        this.subscribers.stadiums.add(stadiumId);
        
        console.log('Subscribed to stadium ' + stadiumId);
        return true;
    }
    
    unsubscribeFromStadium(stadiumId) {
        if (!this.isConnected) {
            return false;
        }
        
        if (!this.subscribers.stadiums.has(stadiumId)) {
            console.log('Not subscribed to stadium ' + stadiumId);
            return true;
        }
        
        this.socket.emit('leave_stadium', { stadium_id: stadiumId });
        this.subscribers.stadiums.delete(stadiumId);
        
        console.log('Unsubscribed from stadium ' + stadiumId);
        return true;
    }
    
    // Event handling methods
    handleMatchUpdate(data) {
        const { match_id, type, data: updateData, timestamp } = data;
        
        switch (type) {
            case 'score_update':
                this.updateMatchScoreboard(match_id, updateData);
                break;
            case 'wicket':
                this.showWicketNotification(match_id, updateData);
                this.updateMatchScoreboard(match_id, updateData);
                break;
            case 'status_change':
                this.updateMatchStatus(match_id, updateData);
                break;
            default:
                console.log('Unknown match update type: ' + type);
        }
    }
    
    handleCurrentMatchStatus(data) {
        this.updateMatchScoreboard(data.match_id, data);
    }
    
    handleBookingNotification(data) {
        const { stadium_id, data: bookingData } = data;
        
        if (bookingData.type === 'new_booking') {
            this.showBookingNotification(bookingData);
        }
    }
    
    handleOccupancyUpdate(data) {
        const { stadium_id, data: occupancyData } = data;
        this.updateOccupancyDisplay(stadium_id, occupancyData);
    }
    
    handleCurrentOccupancy(data) {
        this.updateOccupancyDisplay(data.stadium_id, data);
    }
    
    // UI Update methods
    updateMatchScoreboard(matchId, data) {
        const scoreboard = document.querySelector('[data-match-id="' + matchId + '"] .live-scoreboard');
        if (!scoreboard) return;
        
        // Update scores
        if (data.home_score !== undefined) {
            const homeScoreElement = scoreboard.querySelector('.home-score');
            if (homeScoreElement) {
                homeScoreElement.textContent = data.home_score + (data.home_wickets ? '/' + data.home_wickets : '');
                this.animateElement(homeScoreElement);
            }
        }
        
        if (data.away_score !== undefined) {
            const awayScoreElement = scoreboard.querySelector('.away-score');
            if (awayScoreElement) {
                awayScoreElement.textContent = data.away_score + (data.away_wickets ? '/' + data.away_wickets : '');
                this.animateElement(awayScoreElement);
            }
        }
        
        // Update overs
        if (data.current_over !== undefined || data.home_overs !== undefined) {
            const oversElement = scoreboard.querySelector('.current-overs');
            if (oversElement) {
                const overs = data.current_over || data.home_overs || data.away_overs;
                oversElement.textContent = overs + ' overs';
            }
        }
        
        // Update status
        if (data.status) {
            const statusElement = scoreboard.querySelector('.match-status');
            if (statusElement) {
                statusElement.textContent = data.status;
                statusElement.className = 'match-status status-' + data.status.toLowerCase().replace(' ', '-');
            }
        }
    }
    
    updateMatchStatus(matchId, data) {
        const statusElement = document.querySelector('[data-match-id="' + matchId + '"] .match-status');
        if (statusElement) {
            statusElement.textContent = data.status;
            statusElement.className = 'match-status status-' + data.status.toLowerCase().replace(' ', '-');
            
            if (data.winner) {
                const winnerElement = document.querySelector('[data-match-id="' + matchId + '"] .match-winner');
                if (winnerElement) {
                    winnerElement.textContent = 'Winner: ' + data.winner;
                    winnerElement.style.display = 'block';
                }
            }
        }
    }
    
    updateOccupancyDisplay(stadiumId, data) {
        const occupancyElement = document.querySelector('[data-stadium-id="' + stadiumId + '"] .occupancy-display');
        if (!occupancyElement) return;
        
        // Update occupancy percentage
        const percentageElement = occupancyElement.querySelector('.occupancy-percentage');
        if (percentageElement) {
            percentageElement.textContent = data.occupancy_percentage + '%';
        }
        
        // Update progress bar
        const progressBar = occupancyElement.querySelector('.occupancy-progress-bar');
        if (progressBar) {
            progressBar.style.width = data.occupancy_percentage + '%';
            
            // Change color based on occupancy
            if (data.occupancy_percentage > 90) {
                progressBar.className = 'occupancy-progress-bar bg-danger';
            } else if (data.occupancy_percentage > 70) {
                progressBar.className = 'occupancy-progress-bar bg-warning';
            } else {
                progressBar.className = 'occupancy-progress-bar bg-success';
            }
        }
        
        // Update seat counts
        const seatsAvailable = occupancyElement.querySelector('.seats-available');
        if (seatsAvailable) {
            seatsAvailable.textContent = data.available_seats;
        }
        
        const seatsBooked = occupancyElement.querySelector('.seats-booked');
        if (seatsBooked) {
            seatsBooked.textContent = data.booked_seats;
        }
    }
    
    // Notification methods
    showWicketNotification(matchId, data) {
        const message = 'WICKET! ' + data.batsman + ' is out (' + data.wicket_type + ') - ' + data.current_score + '/' + data.current_over + ' overs';
        this.showNotification(message, 'info', 8000);
    }
    
    showBookingNotification(data) {
        const message = 'New booking: ' + data.customer_name + ' booked ' + data.seats_booked + ' seats for ' + data.event_name;
        this.showNotification(message, 'info', 5000);
    }
    
    showNotification(message, type, duration) {
        type = type || 'info';
        duration = duration || 3000;
        
        // Create notification element
        const notification = document.createElement('div');
        const alertClass = type === 'error' ? 'danger' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info';
        notification.className = 'alert alert-' + alertClass + ' realtime-notification';
        
        const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️';
        
        notification.innerHTML = 
            '<div class="d-flex align-items-center">' +
                '<div class="me-2">' + icon + '</div>' +
                '<div class="flex-grow-1">' + message + '</div>' +
                '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
            '</div>';
        
        // Style the notification
        notification.style.cssText = 
            'position: fixed;' +
            'top: 20px;' +
            'right: 20px;' +
            'z-index: 9999;' +
            'min-width: 300px;' +
            'max-width: 500px;' +
            'animation: slideInRight 0.3s ease-out;';
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.style.animation = 'slideOutRight 0.3s ease-in';
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.parentNode.removeChild(notification);
                        }
                    }, 300);
                }
            }, duration);
        }
    }
    
    // Utility methods
    animateElement(element) {
        element.classList.add('realtime-update');
        setTimeout(() => {
            element.classList.remove('realtime-update');
        }, 1000);
    }
    
    // Event subscription system
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }
    
    off(event, handler) {
        if (!this.eventHandlers[event]) return;
        
        const index = this.eventHandlers[event].indexOf(handler);
        if (index > -1) {
            this.eventHandlers[event].splice(index, 1);
        }
    }
    
    trigger(event, data) {
        if (!this.eventHandlers[event]) return;
        
        this.eventHandlers[event].forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error('Error in event handler for ' + event + ':', error);
            }
        });
    }
    
    // Reconnection logic
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnection attempts reached');
            this.showNotification('Failed to reconnect to live updates', 'error');
            return;
        }
        
        this.reconnectAttempts++;
        console.log('Attempting to reconnect (' + this.reconnectAttempts + '/' + this.maxReconnectAttempts + ')...');
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.connect();
            }
        }, this.reconnectDelay);
        
        // Exponential backoff
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
    }
    
    // Cleanup
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
        this.isConnected = false;
    }
}

// CSS for animations and styling
const realtimeStyles = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .realtime-update {
        background-color: #fff3cd !important;
        border: 2px solid #ffc107 !important;
        border-radius: 4px !important;
        transition: all 0.3s ease !important;
    }
    
    .realtime-notification {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border: none;
        border-left: 4px solid;
    }
    
    .live-scoreboard {
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 15px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        position: relative;
    }
    
    .live-scoreboard::before {
        content: "🔴 LIVE";
        position: absolute;
        top: -10px;
        right: 15px;
        background: #dc3545;
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .occupancy-progress-bar {
        transition: width 0.5s ease, background-color 0.3s ease;
        height: 20px;
        border-radius: 10px;
    }
    
    .match-status.status-in-progress {
        color: #28a745;
        font-weight: bold;
    }
    
    .match-status.status-completed {
        color: #6c757d;
    }
    
    .match-status.status-scheduled {
        color: #007bff;
    }
`;

// Add styles to page
const styleElement = document.createElement('style');
styleElement.textContent = realtimeStyles;
document.head.appendChild(styleElement);

// Initialize global CricVerse realtime instance
window.CricVerseRealtime = CricVerseRealtime;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.cricVerseRealtime) {
            window.cricVerseRealtime = new CricVerseRealtime();
        }
    });
} else {
    if (!window.cricVerseRealtime) {
        window.cricVerseRealtime = new CricVerseRealtime();
    }
}