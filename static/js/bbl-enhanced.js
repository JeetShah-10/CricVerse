/**
 * Enhanced BBL Action Hub and Teams Carousel JavaScript
 * Provides dynamic data loading, interactive features, and real-time updates
 */

class BBLEnhanced {
    constructor() {
        this.apiBase = '/api/bbl';
        this.updateInterval = 30000; // 30 seconds
        this.currentTab = 'fixtures';
        this.currentSubtab = 'runs';
        this.teamsCarousel = null;
        this.currentSlide = 0;
        this.totalSlides = 3;
        
        this.init();
    }

    init() {
        this.initializeActionHub();
        this.initializeTeamsCarousel();
        this.startAutoUpdates();
        this.addClickableNames();
    }

    // Action Hub Methods
    async initializeActionHub() {
        await this.loadLiveScores();
        await this.loadStandings();
        await this.loadTopPerformers();
        this.setupActionHubTabs();
    }

    async loadLiveScores() {
        try {
            const response = await fetch(`${this.apiBase}/live-scores`);
            const data = await response.json();
            
            if (data.success) {
                this.renderLiveScores(data.matches);
            }
        } catch (error) {
            console.error('Error loading live scores:', error);
        }
    }

    async loadStandings() {
        try {
            const response = await fetch(`${this.apiBase}/standings`);
            const data = await response.json();
            
            if (data.success) {
                this.renderStandings(data.standings);
            }
        } catch (error) {
            console.error('Error loading standings:', error);
        }
    }

    async loadTopPerformers() {
        try {
            const response = await fetch(`${this.apiBase}/top-performers`);
            const data = await response.json();
            
            if (data.success) {
                this.renderTopPerformers(data.top_runs, data.top_wickets);
            }
        } catch (error) {
            console.error('Error loading top performers:', error);
        }
    }

    renderLiveScores(matches) {
        const fixturesGrid = document.querySelector('.fixtures-grid');
        if (!fixturesGrid) return;

        fixturesGrid.innerHTML = matches.map(match => `
            <div class="fixture-card" data-match-id="${match.id}">
                <div class="fixture-header">
                    <span class="match-status ${match.status.toLowerCase()}">${match.status}</span>
                    <span class="match-date">${match.date}</span>
                </div>
                <div class="teams-matchup">
                    <div class="team-side home">
                        <img src="${match.home_logo}" alt="${match.home_team}" class="team-logo">
                        <span class="team-name clickable-name" data-team="${match.home_team}">${match.home_team}</span>
                        ${match.home_score ? `<span class="team-score">${match.home_score}</span>` : ''}
                    </div>
                    <div class="vs-indicator">
                        <span>VS</span>
                        ${match.overs ? `
                            <div class="match-progress">
                                <span class="over-info">${match.overs} overs</span>
                            </div>
                        ` : ''}
                    </div>
                    <div class="team-side away">
                        <img src="${match.away_logo}" alt="${match.away_team}" class="team-logo">
                        <span class="team-name clickable-name" data-team="${match.away_team}">${match.away_team}</span>
                        ${match.away_score ? `<span class="team-score">${match.away_score}</span>` : ''}
                    </div>
                </div>
                <div class="fixture-venue">
                    <i class="bi bi-geo-alt"></i>
                    <span>${match.venue}</span>
                </div>
            </div>
        `).join('');

        // Add team logo backgrounds
        this.addTeamLogoBackgrounds();
    }

    renderStandings(standings) {
        const standingsTable = document.querySelector('.enhanced-standings-table tbody');
        if (!standingsTable) return;

        standingsTable.innerHTML = standings.map(team => `
            <tr class="${team.is_playoff ? 'playoff-position' : ''}" data-team="${team.team.toLowerCase().replace(/\s+/g, '-')}">
                <td class="position">${team.position}</td>
                <td class="team-cell">
                    <img src="${team.logo}" alt="${team.team}" class="team-logo-table">
                    <span class="team-name clickable-name" data-team="${team.team}">${team.team}</span>
                    ${team.is_playoff ? '<span class="playoff-indicator">🏆</span>' : ''}
                </td>
                <td>${team.played}</td>
                <td>${team.won}</td>
                <td>${team.lost}</td>
                <td>${team.nrr}</td>
                <td class="points">${team.points}</td>
            </tr>
        `).join('');
    }

    renderTopPerformers(topRuns, topWickets) {
        this.renderRunsPerformers(topRuns);
        this.renderWicketsPerformers(topWickets);
    }

    renderRunsPerformers(players) {
        const runsContainer = document.getElementById('runs-performers');
        if (!runsContainer) return;

        const playersGrid = runsContainer.querySelector('.player-cards-grid');
        if (!playersGrid) return;

        playersGrid.innerHTML = players.map((player, index) => `
            <div class="player-card ${index === 0 ? 'featured' : ''}" data-player-id="${player.id}">
                <div class="player-photo">
                    <div class="player-avatar">${player.avatar}</div>
                    <img src="${player.headshot}" alt="${player.name}" class="player-headshot" 
                         onerror="this.style.display='none'">
                    <div class="player-stats-overlay">
                        <span class="stat-number">${player.runs}</span>
                        <span class="stat-label">Runs</span>
                    </div>
                </div>
                <div class="player-info">
                    <h4 class="player-name clickable-name" data-player="${player.name}">${player.name}</h4>
                    <div class="team-badge ${player.team.toLowerCase().replace(/\s+/g, '-')}-badge">
                        <img src="${player.logo}" alt="${player.team}">
                        <span>${player.team}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderWicketsPerformers(players) {
        const wicketsContainer = document.getElementById('wickets-performers');
        if (!wicketsContainer) return;

        const playersGrid = wicketsContainer.querySelector('.player-cards-grid');
        if (!playersGrid) return;

        playersGrid.innerHTML = players.map((player, index) => `
            <div class="player-card ${index === 0 ? 'featured' : ''}" data-player-id="${player.id}">
                <div class="player-photo">
                    <div class="player-avatar">${player.avatar}</div>
                    <img src="${player.headshot}" alt="${player.name}" class="player-headshot" 
                         onerror="this.style.display='none'">
                    <div class="player-stats-overlay">
                        <span class="stat-number">${player.wickets}</span>
                        <span class="stat-label">Wickets</span>
                    </div>
                </div>
                <div class="player-info">
                    <h4 class="player-name clickable-name" data-player="${player.name}">${player.name}</h4>
                    <div class="team-badge ${player.team.toLowerCase().replace(/\s+/g, '-')}-badge">
                        <img src="${player.logo}" alt="${player.team}">
                        <span>${player.team}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    addTeamLogoBackgrounds() {
        const fixtureCards = document.querySelectorAll('.fixture-card');
        fixtureCards.forEach(card => {
            const homeLogo = card.querySelector('.team-side.home .team-logo');
            const awayLogo = card.querySelector('.team-side.away .team-logo');
            
            if (homeLogo && awayLogo) {
                const homeSrc = homeLogo.src;
                const awaySrc = awayLogo.src;
                
                card.style.backgroundImage = `
                    linear-gradient(135deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.5) 100%),
                    url('${homeSrc}'),
                    url('${awaySrc}')
                `;
                card.style.backgroundSize = 'cover, 60px 60px, 60px 60px';
                card.style.backgroundPosition = 'center, 20px 20px, calc(100% - 80px) 20px';
                card.style.backgroundRepeat = 'no-repeat, no-repeat, no-repeat';
                card.style.backgroundBlendMode = 'normal, overlay, overlay';
            }
        });
    }

    setupActionHubTabs() {
        const tabs = document.querySelectorAll('.hub-tab');
        const panels = document.querySelectorAll('.tab-panel');
        const performerTabs = document.querySelectorAll('.performer-tab');
        const performerPanels = document.querySelectorAll('.performer-panel');
        
        // Main tab switching
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const targetTab = tab.getAttribute('data-tab');
                
                // Remove active class from all tabs and panels
                tabs.forEach(t => t.classList.remove('active'));
                panels.forEach(p => p.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding panel
                tab.classList.add('active');
                const activePanel = document.getElementById(targetTab + '-panel');
                if (activePanel) {
                    activePanel.classList.add('active');
                    activePanel.style.animation = 'fadeInUp 0.5s ease-out';
                }
                
                this.currentTab = targetTab;
            });
        });
        
        // Performer sub-tab switching
        performerTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const targetSubtab = tab.getAttribute('data-subtab');
                
                // Remove active class from all performer tabs and panels
                performerTabs.forEach(t => t.classList.remove('active'));
                performerPanels.forEach(p => p.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding panel
                tab.classList.add('active');
                const activePanel = document.getElementById(targetSubtab + '-performers');
                if (activePanel) {
                    activePanel.classList.add('active');
                }
                
                this.currentSubtab = targetSubtab;
            });
        });
    }

    // Teams Carousel Methods
    async initializeTeamsCarousel() {
        await this.loadTeams();
        this.setupTeamsCarousel();
    }

    async loadTeams() {
        try {
            const response = await fetch(`${this.apiBase}/teams`);
            const data = await response.json();
            
            if (data.success) {
                this.renderTeamsCarousel(data.teams);
            }
        } catch (error) {
            console.error('Error loading teams:', error);
        }
    }

    renderTeamsCarousel(teams) {
        const carousel = document.getElementById('teamsCarousel');
        if (!carousel) return;

        carousel.innerHTML = teams.map(team => `
            <div class="team-carousel-card ${team.name.toLowerCase().replace(/\s+/g, '-')}" data-team="${team.name.toLowerCase().replace(/\s+/g, '-')}">
                <div class="team-card-content">
                    <div class="team-logo-container">
                        <img src="${team.logo}" alt="${team.name}" class="team-logo-carousel">
                        <div class="logo-glow ${team.name.toLowerCase().replace(/\s+/g, '-')}-glow"></div>
                    </div>
                    <div class="team-info-overlay">
                        <h3 class="team-full-name clickable-name" data-team="${team.name}">${team.name}</h3>
                        <p class="team-subtitle">${team.subtitle}</p>
                        <div class="team-stats">
                            <span class="stat-item">${team.position}${this.getOrdinalSuffix(team.position)} Position</span>
                            <span class="stat-divider">•</span>
                            <span class="stat-item">${team.points} Points</span>
                        </div>
                    </div>
                    <div class="player-reveal">
                        <div class="player-silhouette ${team.name.toLowerCase().replace(/\s+/g, '-')}-player"></div>
                    </div>
                </div>
                <div class="team-color-accent ${team.name.toLowerCase().replace(/\s+/g, '-')}-accent" style="background-color: ${team.color}"></div>
            </div>
        `).join('');

        this.setupTeamCardHoverEffects();
    }

    getOrdinalSuffix(num) {
        const j = num % 10;
        const k = num % 100;
        if (j === 1 && k !== 11) return 'st';
        if (j === 2 && k !== 12) return 'nd';
        if (j === 3 && k !== 13) return 'rd';
        return 'th';
    }

    setupTeamsCarousel() {
        const carousel = document.getElementById('teamsCarousel');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const indicators = document.querySelectorAll('.indicator');
        const cards = document.querySelectorAll('.team-carousel-card');
        
        if (!carousel) return;
        
        this.totalSlides = Math.ceil(cards.length / 3); // Show 3 cards per slide
        
        const updateCarousel = () => {
            const translateX = -this.currentSlide * (100 / this.totalSlides);
            carousel.style.transform = `translateX(${translateX}%)`;
            
            // Update indicators
            indicators.forEach((indicator, index) => {
                indicator.classList.toggle('active', index === this.currentSlide);
            });
        };
        
        const nextSlide = () => {
            this.currentSlide = (this.currentSlide + 1) % this.totalSlides;
            updateCarousel();
        };
        
        const prevSlide = () => {
            this.currentSlide = (this.currentSlide - 1 + this.totalSlides) % this.totalSlides;
            updateCarousel();
        };
        
        // Event listeners
        if (nextBtn) nextBtn.addEventListener('click', nextSlide);
        if (prevBtn) prevBtn.addEventListener('click', prevSlide);
        
        // Indicator clicks
        indicators.forEach((indicator, index) => {
            indicator.addEventListener('click', () => {
                this.currentSlide = index;
                updateCarousel();
            });
        });
        
        // Auto-advance carousel (disabled for user control)
        // setInterval(nextSlide, 5000);
        
        this.teamsCarousel = {
            next: nextSlide,
            prev: prevSlide,
            update: updateCarousel
        };
    }

    setupTeamCardHoverEffects() {
        const cards = document.querySelectorAll('.team-carousel-card');
        
        cards.forEach(card => {
            const logo = card.querySelector('.team-logo-carousel');
            const glow = card.querySelector('.logo-glow');
            const accent = card.querySelector('.team-color-accent');
            
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'scale(1.05) translateY(-10px)';
                card.style.borderColor = accent ? accent.style.backgroundColor : '#FFD700';
                card.style.boxShadow = `0 15px 35px ${accent ? accent.style.backgroundColor + '40' : 'rgba(255, 215, 0, 0.4)'}`;
                
                if (logo) {
                    logo.style.transform = 'scale(1.1)';
                    logo.style.filter = 'brightness(1.3) contrast(1.3)';
                }
                
                if (glow) {
                    glow.style.opacity = '0.8';
                    glow.style.transform = 'scale(1.2)';
                }
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'scale(1) translateY(0)';
                card.style.borderColor = 'transparent';
                card.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.2)';
                
                if (logo) {
                    logo.style.transform = 'scale(1)';
                    logo.style.filter = 'brightness(1.1) contrast(1.2)';
                }
                
                if (glow) {
                    glow.style.opacity = '0.4';
                    glow.style.transform = 'scale(1)';
                }
            });
        });
    }

    // Clickable Names
    addClickableNames() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('clickable-name')) {
                const name = e.target.textContent.trim();
                const type = e.target.getAttribute('data-team') ? 'team' : 'player';
                
                if (type === 'team') {
                    window.location.href = `/team-profile/${name.toLowerCase().replace(/\s+/g, '-')}`;
                } else {
                    window.location.href = `/player-profile/${name.toLowerCase().replace(/\s+/g, '-')}`;
                }
            }
        });
    }

    // Auto Updates
    startAutoUpdates() {
        setInterval(() => {
            if (this.currentTab === 'fixtures') {
                this.loadLiveScores();
            }
        }, this.updateInterval);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new BBLEnhanced();
});

// Export for potential external use
window.BBLEnhanced = BBLEnhanced;
