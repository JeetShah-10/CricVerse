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
        this.reconnectDelay = 1000; // Start with 1 second delay
        
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
        console.log('🔌 Connecting to CricVerse real-time server...');
        
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
            console.log('✅ Connected to CricVerse real-time server');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            
            // Show connection status
            this.showNotification('Connected to live updates!', 'success');
            
            // Trigger connected event
            this.trigger('connected');
        });
        
        this.socket.on('disconnect', () => {
            console.log('❌ Disconnected from real-time server');
            this.isConnected = false;
            
            // Show disconnection status
            this.showNotification('Lost connection to live updates', 'warning');
            
            // Trigger disconnected event
            this.trigger('disconnected');
            
            // Attempt reconnection
            this.attemptReconnect();
        });
        
        this.socket.on('connection_status', (data) => {
            console.log('📡 Connection status:', data);
            this.trigger('connection_status', data);
        });
        
        // Match events
        this.socket.on('match_update', (data) => {
            console.log('🏏 Match update received:', data);
            this.handleMatchUpdate(data);
            this.trigger('match_update', data);
        });
        
        this.socket.on('current_match_status', (data) => {
            console.log('📊 Current match status:', data);
            this.handleCurrentMatchStatus(data);
            this.trigger('current_match_status', data);
        });
        
        // Stadium events
        this.socket.on('booking_notification', (data) => {
            console.log('🎫 Booking notification:', data);
            this.handleBookingNotification(data);
            this.trigger('booking_notification', data);
        });
        
        this.socket.on('occupancy_update', (data) => {
            console.log('🏟️ Occupancy update:', data);
            this.handleOccupancyUpdate(data);
            this.trigger('occupancy_update', data);
        });
        
        this.socket.on('current_occupancy', (data) => {
            console.log('📈 Current occupancy:', data);
            this.handleCurrentOccupancy(data);
            this.trigger('current_occupancy', data);
        });
        \n        // Subscription confirmations\n        this.socket.on('subscription_status', (data) => {\n            console.log('📝 Subscription status:', data);\n            this.trigger('subscription_status', data);\n        });\n        \n        // Error handling\n        this.socket.on('error', (data) => {\n            console.error('❌ WebSocket error:', data);\n            this.showNotification(data.message || 'Connection error', 'error');\n            this.trigger('error', data);\n        });\n        \n        this.socket.on('connect_error', (error) => {\n            console.error('❌ Connection error:', error);\n            this.showNotification('Failed to connect to live updates', 'error');\n        });\n    }\n    \n    // Match subscription methods\n    subscribeToMatch(matchId) {\n        if (!this.isConnected) {\n            console.warn('⚠️ Not connected to real-time server');\n            return false;\n        }\n        \n        if (this.subscribers.matches.has(matchId)) {\n            console.log(`Already subscribed to match ${matchId}`);\n            return true;\n        }\n        \n        this.socket.emit('join_match', { match_id: matchId });\n        this.subscribers.matches.add(matchId);\n        \n        console.log(`📺 Subscribed to match ${matchId}`);\n        return true;\n    }\n    \n    unsubscribeFromMatch(matchId) {\n        if (!this.isConnected) {\n            return false;\n        }\n        \n        if (!this.subscribers.matches.has(matchId)) {\n            console.log(`Not subscribed to match ${matchId}`);\n            return true;\n        }\n        \n        this.socket.emit('leave_match', { match_id: matchId });\n        this.subscribers.matches.delete(matchId);\n        \n        console.log(`📺 Unsubscribed from match ${matchId}`);\n        return true;\n    }\n    \n    // Stadium subscription methods\n    subscribeToStadium(stadiumId) {\n        if (!this.isConnected) {\n            console.warn('⚠️ Not connected to real-time server');\n            return false;\n        }\n        \n        if (this.subscribers.stadiums.has(stadiumId)) {\n            console.log(`Already subscribed to stadium ${stadiumId}`);\n            return true;\n        }\n        \n        this.socket.emit('join_stadium', { stadium_id: stadiumId });\n        this.subscribers.stadiums.add(stadiumId);\n        \n        console.log(`🏟️ Subscribed to stadium ${stadiumId}`);\n        return true;\n    }\n    \n    unsubscribeFromStadium(stadiumId) {\n        if (!this.isConnected) {\n            return false;\n        }\n        \n        if (!this.subscribers.stadiums.has(stadiumId)) {\n            console.log(`Not subscribed to stadium ${stadiumId}`);\n            return true;\n        }\n        \n        this.socket.emit('leave_stadium', { stadium_id: stadiumId });\n        this.subscribers.stadiums.delete(stadiumId);\n        \n        console.log(`🏟️ Unsubscribed from stadium ${stadiumId}`);\n        return true;\n    }\n    \n    // Event handling methods\n    handleMatchUpdate(data) {\n        const { match_id, type, data: updateData, timestamp } = data;\n        \n        switch (type) {\n            case 'score_update':\n                this.updateMatchScoreboard(match_id, updateData);\n                break;\n            case 'wicket':\n                this.showWicketNotification(match_id, updateData);\n                this.updateMatchScoreboard(match_id, updateData);\n                break;\n            case 'status_change':\n                this.updateMatchStatus(match_id, updateData);\n                break;\n            default:\n                console.log(`Unknown match update type: ${type}`);\n        }\n    }\n    \n    handleCurrentMatchStatus(data) {\n        this.updateMatchScoreboard(data.match_id, data);\n    }\n    \n    handleBookingNotification(data) {\n        const { stadium_id, data: bookingData } = data;\n        \n        if (bookingData.type === 'new_booking') {\n            this.showBookingNotification(bookingData);\n            this.updateBookingStats(stadium_id, bookingData);\n        }\n    }\n    \n    handleOccupancyUpdate(data) {\n        const { stadium_id, data: occupancyData } = data;\n        this.updateOccupancyDisplay(stadium_id, occupancyData);\n    }\n    \n    handleCurrentOccupancy(data) {\n        this.updateOccupancyDisplay(data.stadium_id, data);\n    }\n    \n    // UI Update methods\n    updateMatchScoreboard(matchId, data) {\n        const scoreboard = document.querySelector(`[data-match-id=\"${matchId}\"] .live-scoreboard`);\n        if (!scoreboard) return;\n        \n        // Update scores\n        if (data.home_score !== undefined) {\n            const homeScoreElement = scoreboard.querySelector('.home-score');\n            if (homeScoreElement) {\n                homeScoreElement.textContent = `${data.home_score}${data.home_wickets ? '/' + data.home_wickets : ''}`;\n                this.animateElement(homeScoreElement);\n            }\n        }\n        \n        if (data.away_score !== undefined) {\n            const awayScoreElement = scoreboard.querySelector('.away-score');\n            if (awayScoreElement) {\n                awayScoreElement.textContent = `${data.away_score}${data.away_wickets ? '/' + data.away_wickets : ''}`;\n                this.animateElement(awayScoreElement);\n            }\n        }\n        \n        // Update overs\n        if (data.current_over !== undefined || data.home_overs !== undefined) {\n            const oversElement = scoreboard.querySelector('.current-overs');\n            if (oversElement) {\n                const overs = data.current_over || data.home_overs || data.away_overs;\n                oversElement.textContent = `${overs} overs`;\n            }\n        }\n        \n        // Update status\n        if (data.status) {\n            const statusElement = scoreboard.querySelector('.match-status');\n            if (statusElement) {\n                statusElement.textContent = data.status;\n                statusElement.className = `match-status status-${data.status.toLowerCase().replace(' ', '-')}`;\n            }\n        }\n    }\n    \n    updateMatchStatus(matchId, data) {\n        const statusElement = document.querySelector(`[data-match-id=\"${matchId}\"] .match-status`);\n        if (statusElement) {\n            statusElement.textContent = data.status;\n            statusElement.className = `match-status status-${data.status.toLowerCase().replace(' ', '-')}`;\n            \n            if (data.winner) {\n                const winnerElement = document.querySelector(`[data-match-id=\"${matchId}\"] .match-winner`);\n                if (winnerElement) {\n                    winnerElement.textContent = `Winner: ${data.winner}`;\n                    winnerElement.style.display = 'block';\n                }\n            }\n        }\n    }\n    \n    updateOccupancyDisplay(stadiumId, data) {\n        const occupancyElement = document.querySelector(`[data-stadium-id=\"${stadiumId}\"] .occupancy-display`);\n        if (!occupancyElement) return;\n        \n        // Update occupancy percentage\n        const percentageElement = occupancyElement.querySelector('.occupancy-percentage');\n        if (percentageElement) {\n            percentageElement.textContent = `${data.occupancy_percentage}%`;\n        }\n        \n        // Update progress bar\n        const progressBar = occupancyElement.querySelector('.occupancy-progress-bar');\n        if (progressBar) {\n            progressBar.style.width = `${data.occupancy_percentage}%`;\n            \n            // Change color based on occupancy\n            if (data.occupancy_percentage > 90) {\n                progressBar.className = 'occupancy-progress-bar bg-danger';\n            } else if (data.occupancy_percentage > 70) {\n                progressBar.className = 'occupancy-progress-bar bg-warning';\n            } else {\n                progressBar.className = 'occupancy-progress-bar bg-success';\n            }\n        }\n        \n        // Update seat counts\n        const seatsAvailable = occupancyElement.querySelector('.seats-available');\n        if (seatsAvailable) {\n            seatsAvailable.textContent = data.available_seats;\n        }\n        \n        const seatsBooked = occupancyElement.querySelector('.seats-booked');\n        if (seatsBooked) {\n            seatsBooked.textContent = data.booked_seats;\n        }\n    }\n    \n    // Notification methods\n    showWicketNotification(matchId, data) {\n        const message = `🏏 WICKET! ${data.batsman} is out (${data.wicket_type}) - ${data.current_score}/${data.current_over} overs`;\n        this.showNotification(message, 'info', 8000);\n    }\n    \n    showBookingNotification(data) {\n        const message = `🎫 New booking: ${data.customer_name} booked ${data.seats_booked} seats for ${data.event_name}`;\n        this.showNotification(message, 'info', 5000);\n    }\n    \n    showNotification(message, type = 'info', duration = 3000) {\n        // Create notification element\n        const notification = document.createElement('div');\n        notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info'} realtime-notification`;\n        notification.innerHTML = `\n            <div class=\"d-flex align-items-center\">\n                <div class=\"me-2\">\n                    ${type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}\n                </div>\n                <div class=\"flex-grow-1\">${message}</div>\n                <button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"alert\"></button>\n            </div>\n        `;\n        \n        // Style the notification\n        notification.style.cssText = `\n            position: fixed;\n            top: 20px;\n            right: 20px;\n            z-index: 9999;\n            min-width: 300px;\n            max-width: 500px;\n            animation: slideInRight 0.3s ease-out;\n        `;\n        \n        // Add to page\n        document.body.appendChild(notification);\n        \n        // Auto-dismiss after duration\n        if (duration > 0) {\n            setTimeout(() => {\n                if (notification.parentNode) {\n                    notification.style.animation = 'slideOutRight 0.3s ease-in';\n                    setTimeout(() => {\n                        if (notification.parentNode) {\n                            notification.parentNode.removeChild(notification);\n                        }\n                    }, 300);\n                }\n            }, duration);\n        }\n    }\n    \n    // Utility methods\n    animateElement(element) {\n        element.classList.add('realtime-update');\n        setTimeout(() => {\n            element.classList.remove('realtime-update');\n        }, 1000);\n    }\n    \n    // Event subscription system\n    on(event, handler) {\n        if (!this.eventHandlers[event]) {\n            this.eventHandlers[event] = [];\n        }\n        this.eventHandlers[event].push(handler);\n    }\n    \n    off(event, handler) {\n        if (!this.eventHandlers[event]) return;\n        \n        const index = this.eventHandlers[event].indexOf(handler);\n        if (index > -1) {\n            this.eventHandlers[event].splice(index, 1);\n        }\n    }\n    \n    trigger(event, data) {\n        if (!this.eventHandlers[event]) return;\n        \n        this.eventHandlers[event].forEach(handler => {\n            try {\n                handler(data);\n            } catch (error) {\n                console.error(`Error in event handler for ${event}:`, error);\n            }\n        });\n    }\n    \n    // Reconnection logic\n    attemptReconnect() {\n        if (this.reconnectAttempts >= this.maxReconnectAttempts) {\n            console.log('❌ Max reconnection attempts reached');\n            this.showNotification('Failed to reconnect to live updates', 'error');\n            return;\n        }\n        \n        this.reconnectAttempts++;\n        console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);\n        \n        setTimeout(() => {\n            if (!this.isConnected) {\n                this.connect();\n            }\n        }, this.reconnectDelay);\n        \n        // Exponential backoff\n        this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);\n    }\n    \n    // Cleanup\n    disconnect() {\n        if (this.socket) {\n            this.socket.disconnect();\n        }\n        this.isConnected = false;\n    }\n}\n\n// CSS for animations and styling\nconst realtimeStyles = `\n    @keyframes slideInRight {\n        from {\n            transform: translateX(100%);\n            opacity: 0;\n        }\n        to {\n            transform: translateX(0);\n            opacity: 1;\n        }\n    }\n    \n    @keyframes slideOutRight {\n        from {\n            transform: translateX(0);\n            opacity: 1;\n        }\n        to {\n            transform: translateX(100%);\n            opacity: 0;\n        }\n    }\n    \n    .realtime-update {\n        background-color: #fff3cd !important;\n        border: 2px solid #ffc107 !important;\n        border-radius: 4px !important;\n        transition: all 0.3s ease !important;\n    }\n    \n    .realtime-notification {\n        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);\n        border: none;\n        border-left: 4px solid;\n    }\n    \n    .live-scoreboard {\n        border: 2px solid #28a745;\n        border-radius: 8px;\n        padding: 15px;\n        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);\n        position: relative;\n    }\n    \n    .live-scoreboard::before {\n        content: \"🔴 LIVE\";\n        position: absolute;\n        top: -10px;\n        right: 15px;\n        background: #dc3545;\n        color: white;\n        padding: 2px 8px;\n        border-radius: 10px;\n        font-size: 10px;\n        font-weight: bold;\n        animation: pulse 2s infinite;\n    }\n    \n    @keyframes pulse {\n        0% { opacity: 1; }\n        50% { opacity: 0.7; }\n        100% { opacity: 1; }\n    }\n    \n    .occupancy-progress-bar {\n        transition: width 0.5s ease, background-color 0.3s ease;\n        height: 20px;\n        border-radius: 10px;\n    }\n    \n    .match-status.status-in-progress {\n        color: #28a745;\n        font-weight: bold;\n    }\n    \n    .match-status.status-completed {\n        color: #6c757d;\n    }\n    \n    .match-status.status-scheduled {\n        color: #007bff;\n    }\n`;\n\n// Add styles to page\nconst styleElement = document.createElement('style');\nstyleElement.textContent = realtimeStyles;\ndocument.head.appendChild(styleElement);\n\n// Initialize global CricVerse realtime instance\nwindow.CricVerseRealtime = CricVerseRealtime;\n\n// Auto-initialize when DOM is ready\nif (document.readyState === 'loading') {\n    document.addEventListener('DOMContentLoaded', () => {\n        if (!window.cricVerseRealtime) {\n            window.cricVerseRealtime = new CricVerseRealtime();\n        }\n    });\n} else {\n    if (!window.cricVerseRealtime) {\n        window.cricVerseRealtime = new CricVerseRealtime();\n    }\n}