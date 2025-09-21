/**
 * Admin Panel JavaScript for CricVerse
 * Handles all admin functionality and interactions
 */

// Admin Dashboard Class
class AdminDashboard {
    constructor() {
        this.init();
        this.bindEvents();
        this.loadDashboardData();
    }

    init() {
        console.log('Admin Dashboard initialized');
        this.setupSidebar();
        this.setupModals();
        this.setupDataTables();
        this.setupCharts();
    }

    bindEvents() {
        // Sidebar toggle
        $(document).on('click', '.sidebar-toggle', this.toggleSidebar);
        
        // Form submissions
        $(document).on('submit', '.admin-form', this.handleFormSubmission);
        
        // Delete confirmations
        $(document).on('click', '.btn-delete', this.confirmDelete);
        
        // Search functionality
        $(document).on('input', '.admin-search input', this.handleSearch);
        
        // Bulk actions
        $(document).on('change', '.select-all', this.handleSelectAll);
        $(document).on('click', '.bulk-action-btn', this.handleBulkAction);
        
        // Real-time updates
        this.setupRealTimeUpdates();
    }

    setupSidebar() {
        // Highlight active menu item
        const currentPath = window.location.pathname;
        $('.admin-sidebar-menu .nav-link').each(function() {
            const href = $(this).attr('href');
            if (currentPath.includes(href)) {
                $(this).addClass('active');
            }
        });

        // Collapsible menu items
        $('.nav-link[data-bs-toggle="collapse"]').on('click', function() {
            const icon = $(this).find('i.fa-chevron-right');
            icon.toggleClass('fa-rotate-90');
        });
    }

    toggleSidebar() {
        $('.admin-sidebar').toggleClass('show');
        $('.admin-content').toggleClass('sidebar-open');
    }

    setupModals() {
        // Auto-focus first input in modals
        $('.modal').on('shown.bs.modal', function() {
            $(this).find('input:first').focus();
        });

        // Clear form data when modal is closed
        $('.modal').on('hidden.bs.modal', function() {
            $(this).find('form')[0]?.reset();
            $(this).find('.alert').remove();
        });
    }

    setupDataTables() {
        // Initialize DataTables for admin tables
        if ($.fn.DataTable) {
            $('.admin-datatable').DataTable({
                responsive: true,
                pageLength: 25,
                order: [[0, 'desc']],
                language: {
                    search: "Search:",
                    lengthMenu: "Show _MENU_ entries",
                    info: "Showing _START_ to _END_ of _TOTAL_ entries",
                    paginate: {
                        first: "First",
                        last: "Last",
                        next: "Next",
                        previous: "Previous"
                    }
                },
                dom: '<"row"<"col-sm-6"l><"col-sm-6"f>>rtip',
                columnDefs: [
                    { orderable: false, targets: 'no-sort' }
                ]
            });
        }
    }

    setupCharts() {
        // Initialize Chart.js charts
        this.initBookingChart();
        this.initRevenueChart();
        this.initStadiumChart();
    }

    initBookingChart() {
        const ctx = document.getElementById('bookingChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Bookings',
                    data: [12, 19, 3, 5, 2, 3],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    initRevenueChart() {
        const ctx = document.getElementById('revenueChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['MCG', 'SCG', 'Adelaide Oval', 'Gabba', 'Perth Stadium'],
                datasets: [{
                    label: 'Revenue ($)',
                    data: [12000, 19000, 8000, 15000, 10000],
                    backgroundColor: [
                        '#3498db',
                        '#e74c3c',
                        '#f39c12',
                        '#27ae60',
                        '#9b59b6'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    initStadiumChart() {
        const ctx = document.getElementById('stadiumChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Occupied', 'Available', 'Maintenance'],
                datasets: [{
                    data: [65, 30, 5],
                    backgroundColor: ['#27ae60', '#3498db', '#e74c3c']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    handleFormSubmission(e) {
        e.preventDefault();
        const form = $(this);
        const submitBtn = form.find('button[type="submit"]');
        const originalText = submitBtn.text();

        // Show loading state
        submitBtn.prop('disabled', true).html('<span class="admin-loading"></span> Processing...');

        // Get form data
        const formData = new FormData(this);
        const url = form.attr('action') || window.location.href;
        const method = form.attr('method') || 'POST';

        // Submit form via AJAX
        $.ajax({
            url: url,
            method: method,
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    AdminDashboard.showAlert('success', response.message || 'Operation completed successfully');
                    
                    // Close modal if form is in modal
                    form.closest('.modal').modal('hide');
                    
                    // Reload page or update content
                    if (response.reload) {
                        setTimeout(() => window.location.reload(), 1000);
                    }
                } else {
                    AdminDashboard.showAlert('danger', response.message || 'An error occurred');
                }
            },
            error: function(xhr) {
                let message = 'An error occurred';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    message = xhr.responseJSON.message;
                }
                AdminDashboard.showAlert('danger', message);
            },
            complete: function() {
                submitBtn.prop('disabled', false).text(originalText);
            }
        });
    }

    confirmDelete(e) {
        e.preventDefault();
        const btn = $(this);
        const url = btn.attr('href') || btn.data('url');
        const itemName = btn.data('name') || 'this item';

        if (confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`)) {
            // Show loading state
            btn.prop('disabled', true).html('<span class="admin-loading"></span>');

            $.ajax({
                url: url,
                method: 'DELETE',
                success: function(response) {
                    if (response.success) {
                        AdminDashboard.showAlert('success', response.message || 'Item deleted successfully');
                        
                        // Remove row from table
                        btn.closest('tr').fadeOut(300, function() {
                            $(this).remove();
                        });
                    } else {
                        AdminDashboard.showAlert('danger', response.message || 'Failed to delete item');
                        btn.prop('disabled', false).html('<i class="fas fa-trash"></i>');
                    }
                },
                error: function() {
                    AdminDashboard.showAlert('danger', 'An error occurred while deleting');
                    btn.prop('disabled', false).html('<i class="fas fa-trash"></i>');
                }
            });
        }
    }

    handleSearch() {
        const searchTerm = $(this).val().toLowerCase();
        const table = $(this).closest('.admin-search').next('.admin-table').find('tbody');
        
        table.find('tr').each(function() {
            const text = $(this).text().toLowerCase();
            $(this).toggle(text.includes(searchTerm));
        });
    }

    handleSelectAll() {
        const isChecked = $(this).prop('checked');
        $(this).closest('table').find('tbody input[type="checkbox"]').prop('checked', isChecked);
        AdminDashboard.updateBulkActions();
    }

    handleBulkAction() {
        const action = $(this).data('action');
        const selectedIds = [];
        
        $('.admin-table tbody input[type="checkbox"]:checked').each(function() {
            selectedIds.push($(this).val());
        });

        if (selectedIds.length === 0) {
            AdminDashboard.showAlert('warning', 'Please select at least one item');
            return;
        }

        if (confirm(`Are you sure you want to ${action} ${selectedIds.length} item(s)?`)) {
            $.ajax({
                url: `/admin/bulk-action`,
                method: 'POST',
                data: {
                    action: action,
                    ids: selectedIds
                },
                success: function(response) {
                    if (response.success) {
                        AdminDashboard.showAlert('success', response.message);
                        setTimeout(() => window.location.reload(), 1000);
                    } else {
                        AdminDashboard.showAlert('danger', response.message);
                    }
                },
                error: function() {
                    AdminDashboard.showAlert('danger', 'An error occurred');
                }
            });
        }
    }

    static updateBulkActions() {
        const selectedCount = $('.admin-table tbody input[type="checkbox"]:checked').length;
        $('.bulk-actions').toggle(selectedCount > 0);
        $('.selected-count').text(selectedCount);
    }

    setupRealTimeUpdates() {
        // Connect to WebSocket for real-time updates
        if (typeof io !== 'undefined') {
            const socket = io();
            
            socket.on('booking_update', (data) => {
                this.updateBookingStats(data);
            });
            
            socket.on('revenue_update', (data) => {
                this.updateRevenueStats(data);
            });
            
            socket.on('system_alert', (data) => {
                AdminDashboard.showAlert(data.type, data.message);
            });
        }
    }

    updateBookingStats(data) {
        $('#total-bookings').text(data.total_bookings);
        $('#pending-bookings').text(data.pending_bookings);
        $('#confirmed-bookings').text(data.confirmed_bookings);
    }

    updateRevenueStats(data) {
        $('#total-revenue').text('$' + data.total_revenue.toLocaleString());
        $('#monthly-revenue').text('$' + data.monthly_revenue.toLocaleString());
    }

    loadDashboardData() {
        // Load dashboard statistics
        $.get('/admin/api/stats', (data) => {
            if (data.success) {
                this.updateDashboardStats(data.stats);
            }
        });

        // Load recent activities
        $.get('/admin/api/recent-activities', (data) => {
            if (data.success) {
                this.updateRecentActivities(data.activities);
            }
        });
    }

    updateDashboardStats(stats) {
        $('#stat-customers').text(stats.customers || 0);
        $('#stat-stadiums').text(stats.stadiums || 0);
        $('#stat-events').text(stats.events || 0);
        $('#stat-bookings').text(stats.bookings || 0);
        $('#stat-revenue').text('$' + (stats.revenue || 0).toLocaleString());
    }

    updateRecentActivities(activities) {
        const container = $('#recent-activities');
        container.empty();
        
        activities.forEach(activity => {
            const item = $(`
                <div class="activity-item">
                    <div class="activity-icon">
                        <i class="fas ${activity.icon}"></i>
                    </div>
                    <div class="activity-content">
                        <div class="activity-text">${activity.text}</div>
                        <div class="activity-time">${activity.time}</div>
                    </div>
                </div>
            `);
            container.append(item);
        });
    }

    static showAlert(type, message, duration = 5000) {
        const alertHtml = `
            <div class="alert admin-alert admin-alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        $('.admin-alerts').prepend(alertHtml);
        
        // Auto-dismiss after duration
        setTimeout(() => {
            $('.admin-alerts .alert:first').fadeOut(300, function() {
                $(this).remove();
            });
        }, duration);
    }

    static formatCurrency(amount) {
        return new Intl.NumberFormat('en-AU', {
            style: 'currency',
            currency: 'AUD'
        }).format(amount);
    }

    static formatDate(date) {
        return new Intl.DateTimeFormat('en-AU', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }
}

// Utility Functions
const AdminUtils = {
    // Export data to CSV
    exportToCSV: function(data, filename) {
        const csv = this.convertToCSV(data);
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    },

    convertToCSV: function(data) {
        if (!data.length) return '';
        
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => 
                JSON.stringify(row[header] || '')
            ).join(','))
        ].join('\n');
        
        return csvContent;
    },

    // Generate random colors for charts
    generateColors: function(count) {
        const colors = [];
        for (let i = 0; i < count; i++) {
            const hue = (i * 137.508) % 360;
            colors.push(`hsl(${hue}, 70%, 60%)`);
        }
        return colors;
    },

    // Debounce function for search
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Initialize when document is ready
$(document).ready(function() {
    // Only initialize on admin pages
    if ($('.admin-wrapper').length) {
        window.adminDashboard = new AdminDashboard();
    }
    
    // Setup tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Setup popovers
    $('[data-bs-toggle="popover"]').popover();
    
    // Auto-hide alerts after 5 seconds
    setTimeout(() => {
        $('.alert:not(.alert-permanent)').fadeOut();
    }, 5000);
});

// Export for global access
window.AdminDashboard = AdminDashboard;
window.AdminUtils = AdminUtils;
