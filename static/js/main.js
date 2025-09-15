// CricVerse - Main JavaScript File
// Enhanced interactivity and AI chatbot functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeChatbot();
    initializeAnimations();
    initializeRecentlyViewed();
    initializeSeatSelection();
    initializeFormEnhancements();
    initializeLoadingStates();
});

// ================================
// CHATBOT FUNCTIONALITY
// ================================

function initializeChatbot() {
    const chatbotIcon = document.getElementById('chatbot-icon');
    const chatbotWindow = document.getElementById('chatbot-window');
    const closeChatbot = document.getElementById('close-chatbot');
    const sendButton = document.getElementById('send-button');
    const userInput = document.getElementById('user-input');
    const chatbotBody = document.getElementById('chatbot-body');

    if (!chatbotIcon || !chatbotWindow) return;

    // Toggle chatbot window
    chatbotIcon.addEventListener('click', function() {
        toggleChatbot();
    });

    closeChatbot?.addEventListener('click', function() {
        chatbotWindow.style.display = 'none';
    });

    // Send message functionality
    sendButton?.addEventListener('click', sendMessage);
    userInput?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function toggleChatbot() {
        if (chatbotWindow.style.display === 'none' || !chatbotWindow.style.display) {
            chatbotWindow.style.display = 'flex';
            userInput?.focus();
        } else {
            chatbotWindow.style.display = 'none';
        }
    }

    function sendMessage() {
        const message = userInput?.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessageToChat(message, 'user');
        userInput.value = '';

        // Show typing indicator
        showTypingIndicator();

        // Send to backend chatbot endpoint
        fetch('/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            hideTypingIndicator();
            addMessageToChat(data.response, 'bot');
        })
        .catch(error => {
            hideTypingIndicator();
            addMessageToChat('Sorry, I\'m having trouble right now. Please try again later!', 'bot');
            console.error('Chatbot error:', error);
        });
    }

    function addMessageToChat(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}-message fade-in`;
        
        // Preserve line breaks and formatting
        messageDiv.innerHTML = message.replace(/\n/g, '<br>');
        
        chatbotBody?.appendChild(messageDiv);
        chatbotBody?.scrollTo(0, chatbotBody.scrollHeight);
    }

    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message bot-message typing-indicator';
        typingDiv.innerHTML = '<div class="loading"></div> CricVerse is typing...';
        typingDiv.id = 'typing-indicator';
        
        chatbotBody?.appendChild(typingDiv);
        chatbotBody?.scrollTo(0, chatbotBody.scrollHeight);
    }

    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        typingIndicator?.remove();
    }
}

// ================================
// SEAT SELECTION ENHANCEMENT
// ================================

function initializeSeatSelection() {
    const seats = document.querySelectorAll('.seat.available');
    const selectedSeatsInput = document.querySelector('input[name="selected_seats"]');
    const totalPriceElement = document.getElementById('total-price');
    let selectedSeats = [];

    seats.forEach(seat => {
        seat.addEventListener('click', function() {
            const seatId = this.dataset.seatId;
            const seatPrice = parseFloat(this.dataset.price) || 0;

            if (this.classList.contains('selected')) {
                // Deselect seat
                this.classList.remove('selected');
                selectedSeats = selectedSeats.filter(s => s.id !== seatId);
            } else {
                // Select seat
                this.classList.add('selected');
                selectedSeats.push({ id: seatId, price: seatPrice });
            }

            updateSelectedSeats();
        });
    });

    function updateSelectedSeats() {
        // Update hidden input
        if (selectedSeatsInput) {
            selectedSeatsInput.value = selectedSeats.map(s => s.id).join(',');
        }

        // Update total price
        if (totalPriceElement) {
            const totalPrice = selectedSeats.reduce((sum, seat) => sum + seat.price, 0);
            totalPriceElement.textContent = `$${totalPrice.toFixed(2)}`;
        }

        // Update seat counter
        const seatCounter = document.getElementById('seat-counter');
        if (seatCounter) {
            seatCounter.textContent = `${selectedSeats.length} seat(s) selected`;
        }
    }
}

// ================================
// ANIMATIONS AND VISUAL ENHANCEMENTS
// ================================

function initializeAnimations() {
    // Animate cards on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);

    // Observe all cards and feature elements
    document.querySelectorAll('.card, .feature-card, .hero-section').forEach(el => {
        observer.observe(el);
    });

    // Add hover effects to team cards
    document.querySelectorAll('[data-team-id]').forEach(card => {
        card.addEventListener('mouseenter', function() {
            const teamId = this.dataset.teamId;
            this.classList.add(`team-${teamId}`);
        });
    });

    // Floating cricket balls animation
    createFloatingCricketBalls();
}

function createFloatingCricketBalls() {
    const heroSection = document.querySelector('.hero-section');
    if (!heroSection) return;

    for (let i = 0; i < 3; i++) {
        const ball = document.createElement('div');
        ball.className = 'cricket-ball floating-ball';
        ball.style.position = 'absolute';
        ball.style.left = `${Math.random() * 100}%`;
        ball.style.top = `${Math.random() * 100}%`;
        ball.style.animationDelay = `${i * 2}s`;
        heroSection.appendChild(ball);
    }
}

// ================================
// RECENTLY VIEWED FUNCTIONALITY
// ================================

function initializeRecentlyViewed() {
    const currentPath = window.location.pathname;
    const pageTitle = document.title;
    
    // Don't track admin pages or login/register
    if (currentPath.includes('/admin') || currentPath.includes('/login') || currentPath.includes('/register')) {
        return;
    }

    // Get recently viewed from localStorage
    let recentlyViewed = JSON.parse(localStorage.getItem('cricverse_recently_viewed') || '[]');

    // Add current page
    const currentPage = {
        path: currentPath,
        title: pageTitle,
        timestamp: new Date().toISOString()
    };

    // Remove if already exists
    recentlyViewed = recentlyViewed.filter(item => item.path !== currentPath);

    // Add to beginning
    recentlyViewed.unshift(currentPage);

    // Keep only last 5 items
    recentlyViewed = recentlyViewed.slice(0, 5);

    // Save back to localStorage
    localStorage.setItem('cricverse_recently_viewed', JSON.stringify(recentlyViewed));

    // Display recently viewed
    displayRecentlyViewed(recentlyViewed);
}

function displayRecentlyViewed(items) {
    const recentlyViewedSection = document.getElementById('recently-viewed-section');
    const recentlyViewedList = document.getElementById('recently-viewed-list');

    if (!recentlyViewedSection || !recentlyViewedList || items.length < 2) return;

    // Show section
    recentlyViewedSection.style.display = 'block';

    // Clear existing items
    recentlyViewedList.innerHTML = '';

    // Skip current page (first item)
    items.slice(1).forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'recently-viewed-item';
        itemDiv.innerHTML = `
            <a href="${item.path}" class="text-decoration-none">
                <div class="card" style="width: 200px;">
                    <div class="card-body">
                        <h6 class="card-title">${item.title}</h6>
                        <small class="text-muted">${formatTimeAgo(item.timestamp)}</small>
                    </div>
                </div>
            </a>
        `;
        recentlyViewedList.appendChild(itemDiv);
    });
}

function formatTimeAgo(timestamp) {
    const now = new Date();
    const then = new Date(timestamp);
    const diff = now - then;
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
}

// ================================
// FORM ENHANCEMENTS
// ================================

function initializeFormEnhancements() {
    // Add loading states to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitButton) {
                submitButton.innerHTML = '<div class="loading"></div> Processing...';
                submitButton.disabled = true;
            }
        });
    });

    // Enhanced form validation
    document.querySelectorAll('input[required], select[required]').forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
    });

    // Password strength indicator
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        input.addEventListener('input', function() {
            showPasswordStrength(this);
        });
    });
}

function validateField(field) {
    const isValid = field.checkValidity();
    
    if (!isValid) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
    } else {
        field.classList.add('is-valid');
        field.classList.remove('is-invalid');
    }
}

function showPasswordStrength(passwordInput) {
    const password = passwordInput.value;
    const strengthIndicator = passwordInput.parentNode.querySelector('.password-strength');
    
    if (!strengthIndicator) return;

    let strength = 0;
    let feedback = '';

    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;

    switch (strength) {
        case 0:
        case 1:
            feedback = 'Weak';
            strengthIndicator.className = 'password-strength weak';
            break;
        case 2:
        case 3:
            feedback = 'Medium';
            strengthIndicator.className = 'password-strength medium';
            break;
        case 4:
        case 5:
            feedback = 'Strong';
            strengthIndicator.className = 'password-strength strong';
            break;
    }

    strengthIndicator.textContent = feedback;
}

// ================================
// LOADING STATES AND FEEDBACK
// ================================

function initializeLoadingStates() {
    // Add loading states to navigation links
    document.querySelectorAll('a[href^="/"]').forEach(link => {
        link.addEventListener('click', function(e) {
            // Don't add loading for external links or anchors
            if (this.getAttribute('href').startsWith('#') || this.target === '_blank') {
                return;
            }

            // Add loading indicator
            showPageLoading();
        });
    });

    // Hide loading on page load
    hidePageLoading();
}

function showPageLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'page-loading';
    loadingDiv.innerHTML = `
        <div class="loading-overlay">
            <div class="loading-content">
                <div class="loading"></div>
                <p>Loading CricVerse...</p>
            </div>
        </div>
    `;
    loadingDiv.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(26, 27, 58, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        color: white;
        text-align: center;
    `;
    
    document.body.appendChild(loadingDiv);
}

function hidePageLoading() {
    const loadingDiv = document.getElementById('page-loading');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// ================================
// UTILITY FUNCTIONS
// ================================

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-AU', {
        style: 'currency',
        currency: 'AUD'
    }).format(amount);
}

// Format date for cricket matches
function formatMatchDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-AU', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Copy to clipboard functionality
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Copied to clipboard!', 'success');
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification fade-in`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        z-index: 1050;
        min-width: 250px;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ================================
// CRICKET-SPECIFIC FEATURES
// ================================

// Team color themes
const teamColors = {
    'adelaide-strikers': { primary: '#003d82', secondary: '#ffd100' },
    'brisbane-heat': { primary: '#e74c3c', secondary: '#f39c12' },
    'hobart-hurricanes': { primary: '#9b59b6', secondary: '#3498db' },
    'melbourne-renegades': { primary: '#e74c3c', secondary: '#2c3e50' },
    'melbourne-stars': { primary: '#2ecc71', secondary: '#f1c40f' },
    'perth-scorchers': { primary: '#e67e22', secondary: '#2c3e50' },
    'sydney-sixers': { primary: '#e91e63', secondary: '#9c27b0' },
    'sydney-thunder': { primary: '#9b59b6', secondary: '#f1c40f' }
};

// Apply team theme to elements
function applyTeamTheme(teamSlug, element) {
    const colors = teamColors[teamSlug];
    if (colors && element) {
        element.style.setProperty('--team-primary', colors.primary);
        element.style.setProperty('--team-secondary', colors.secondary);
        element.classList.add('team-themed');
    }
}

// Match countdown functionality
function startMatchCountdown(matchDateTime, elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const targetTime = new Date(matchDateTime).getTime();

    const interval = setInterval(function() {
        const now = new Date().getTime();
        const distance = targetTime - now;

        if (distance < 0) {
            clearInterval(interval);
            element.innerHTML = "MATCH STARTED!";
            return;
        }

        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        element.innerHTML = `${days}d ${hours}h ${minutes}m ${seconds}s`;
    }, 1000);
}

// Export functions for global use
window.CricVerse = {
    formatCurrency,
    formatMatchDate,
    copyToClipboard,
    showNotification,
    applyTeamTheme,
    startMatchCountdown
};

document.addEventListener('DOMContentLoaded', function() {

  // --- NEW: Pre-loader Logic ---
  const preloader = document.querySelector('.preloader');
  if (preloader) {
      window.addEventListener('load', () => {
          preloader.classList.add('fade-out');
          preloader.addEventListener('transitionend', () => {
              preloader.style.display = 'none';
          });
      });
  }

  // --- NEW: Navbar Scroll Effect ---
  const navbar = document.querySelector('.navbar');
  // Only apply this effect on the homepage
  if (document.querySelector('.hero')) {
      navbar.classList.add('bg-dark-transparent');

      window.addEventListener('scroll', () => {
          if (window.scrollY > 50) {
              navbar.classList.remove('bg-dark-transparent');
              navbar.classList.add('bg-dark-scrolled');
          } else {
              navbar.classList.remove('bg-dark-scrolled');
              navbar.classList.add('bg-dark-transparent');
          }
      });
  }

  // --- NEW: Theme Toggle ---
  const html = document.documentElement;
  const toggleBtn = document.getElementById('themeToggle');
  if (toggleBtn) {
    const saved = localStorage.getItem('theme');
    if (saved) html.dataset.bsTheme = saved;
    toggleBtn.addEventListener('click', () => {
      html.dataset.bsTheme = html.dataset.bsTheme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', html.dataset.bsTheme);
    });
  }

  // --- NEW: Chatbot Logic ---
  const chatbotIcon = document.getElementById('chatbot-icon');
  const chatbotWindow = document.getElementById('chatbot-window');
  const closeChatbot = document.getElementById('close-chatbot');
  const userInput = document.getElementById('user-input');
  const sendButton = document.getElementById('send-button');
  const chatbotBody = document.getElementById('chatbot-body');

  // Function to show/hide loading indicator
  function showLoadingIndicator() {
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('chat-message', 'bot-message', 'loading-indicator');
    loadingDiv.textContent = 'Typing...';
    loadingDiv.id = 'loading-indicator';
    chatbotBody.appendChild(loadingDiv);
    chatbotBody.scrollTop = chatbotBody.scrollHeight;
  }

  function hideLoadingIndicator() {
    const loadingDiv = document.getElementById('loading-indicator');
    if (loadingDiv) {
      loadingDiv.remove();
    }
  }

  chatbotIcon.addEventListener('click', () => {
    chatbotWindow.style.display = 'block';
  });

  closeChatbot.addEventListener('click', () => {
    chatbotWindow.style.display = 'none';
  });

  sendButton.addEventListener('click', sendMessage);
  userInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      sendMessage();
    }
  });

  function sendMessage() {
    const message = userInput.value.trim();
    if (message === '') return;

    // Display user message
    const userMessageDiv = document.createElement('div');
    userMessageDiv.classList.add('chat-message', 'user-message');
    userMessageDiv.textContent = message;
    chatbotBody.appendChild(userMessageDiv);

    userInput.value = '';
    chatbotBody.scrollTop = chatbotBody.scrollHeight; // Scroll to bottom

    showLoadingIndicator(); // Show loading indicator

    // Send message to backend
    fetch('/chatbot', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
      hideLoadingIndicator(); // Hide loading indicator
      const botMessageDiv = document.createElement('div');
      botMessageDiv.classList.add('chat-message', 'bot-message');
      botMessageDiv.innerHTML = data.response.replace(/\n/g, '<br>'); // Preserve line breaks and formatting
      chatbotBody.appendChild(botMessageDiv);
      chatbotBody.scrollTop = chatbotBody.scrollHeight; // Scroll to bottom
    })
    .catch(error => {
      hideLoadingIndicator(); // Hide loading indicator even on error
      console.error('Error:', error);
      const errorMessageDiv = document.createElement('div');
      errorMessageDiv.classList.add('chat-message', 'bot-message', 'error-message');
      errorMessageDiv.textContent = 'Oops! Something went wrong.';
      chatbotBody.appendChild(errorMessageDiv);
      chatbotBody.scrollTop = chatbotBody.scrollHeight; // Scroll to bottom
    });
  }

  // --- NEW: Recently Viewed Logic ---
  const MAX_RECENTLY_VIEWED = 5; // Limit the number of recently viewed items

  function addRecentlyViewed(type, id, name, imageUrl) {
    let recentlyViewed = JSON.parse(localStorage.getItem('recentlyViewed') || '[]');

    // Remove if already exists to move it to the top
    recentlyViewed = recentlyViewed.filter(item => !(item.type === type && item.id === id));

    // Add new item to the beginning
    recentlyViewed.unshift({ type, id, name, imageUrl, timestamp: Date.now() });

    // Trim to max limit
    if (recentlyViewed.length > MAX_RECENTLY_VIEWED) {
      recentlyViewed = recentlyViewed.slice(0, MAX_RECENTLY_VIEWED);
    }

    localStorage.setItem('recentlyViewed', JSON.stringify(recentlyViewed));
    displayRecentlyViewed(); // Refresh display after adding
  }

  function displayRecentlyViewed() {
    const recentlyViewed = JSON.parse(localStorage.getItem('recentlyViewed') || '[]');
    const recentlyViewedList = document.getElementById('recently-viewed-list');
    const recentlyViewedSection = document.getElementById('recently-viewed-section');

    if (recentlyViewed.length > 0) {
      recentlyViewedList.innerHTML = ''; // Clear existing items
      recentlyViewed.forEach(item => {
        const itemLink = document.createElement('a');
        itemLink.href = item.type === 'stadium' ? `/stadium/${item.id}` : `/event/${item.id}`;
        itemLink.classList.add('recently-viewed-item', 'card', 'p-2', 'd-flex', 'align-items-center', 'gap-2', 'text-decoration-none', 'text-white', 'bg-secondary', 'rounded');
        itemLink.style.width = '180px'; // Fixed width for consistency

        const itemImage = document.createElement('img');
        itemImage.src = item.imageUrl || (item.type === 'stadium' ? '/static/img/Stadium Image.jpg' : 'https://images.unsplash.com/photo-1531415074968-036ba1b575da?q=80&w=1600&auto=format&fit=crop');
        itemImage.alt = item.name;
        itemImage.classList.add('rounded', 'me-2');
        itemImage.style.width = '40px';
        itemImage.style.height = '40px';
        itemImage.style.objectFit = 'cover';

        const itemName = document.createElement('span');
        itemName.textContent = item.name;
        itemName.classList.add('flex-grow-1', 'text-truncate');

        itemLink.appendChild(itemImage);
        itemLink.appendChild(itemName);
        recentlyViewedList.appendChild(itemLink);
      });
      recentlyViewedSection.style.display = 'block'; // Show the section
    } else {
      recentlyViewedSection.style.display = 'none'; // Hide if no items
    }
  }

  // Check if we are on a stadium detail page
  const stadiumDetailElement = document.querySelector('.stadium-detail-page'); // Assuming a class on the stadium detail page
  if (stadiumDetailElement) {
    const stadiumId = stadiumDetailElement.dataset.stadiumId;
    const stadiumName = stadiumDetailElement.dataset.stadiumName;
    const stadiumImageUrl = stadiumDetailElement.dataset.stadiumImageUrl;
    if (stadiumId && stadiumName) {
      addRecentlyViewed('stadium', parseInt(stadiumId), stadiumName, stadiumImageUrl);
    }
  }

  // Check if we are on an event detail page
  const eventDetailElement = document.querySelector('.event-detail-page'); // Assuming a class on the event detail page
  if (eventDetailElement) {
    const eventId = eventDetailElement.dataset.eventId;
    const eventName = eventDetailElement.dataset.eventName;
    const eventImageUrl = eventDetailElement.dataset.eventImageUrl; // Assuming event has an image
    if (eventId && eventName) {
      addRecentlyViewed('event', parseInt(eventId), eventName, eventImageUrl);
    }
  }

  // Initial display of recently viewed items when page loads
  displayRecentlyViewed();
});


// --- ORIGINAL: AOS Refresh Logic (Kept as is) ---
document.addEventListener('visibilitychange', () => {
if (!document.hidden && window.AOS) { window.AOS.refreshHard(); }
});