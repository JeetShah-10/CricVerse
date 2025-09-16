/**
 * ====================================
 * CRICVERSE ENHANCED AI ASSISTANT - 3D ENGINE
 * ====================================
 * 
 * Performance-optimized 3D interface with:
 * - Enhanced cricket themed environment
 * - Interactive cricket ball tracking mouse movement
 * - Enhanced AI integration with improved fallback support
 * - Cricket-themed animations and effects
 * - Optimized loading for faster initialization
 * - Real-time cricket performance monitoring
 */

class CricVerseAI3D {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.cricketBall = null;
        this.cricketOrbitRing = null;
        this.stars = null;
        this.mouseX = 0;
        this.mouseY = 0;
        this.isThinking = false;
        this.frameCount = 0;
        this.lastTime = 0;
        this.cricketParticles = [];
        this.performanceStats = {
            fps: 0,
            memory: 0,
            particles: 0,
            quality: 'auto'
        };
        
        // Enhanced cricket performance settings
        this.maxStars = this.getOptimalStarCount();
        this.maxCricketParticles = this.getOptimalParticleCount();
        this.quality = this.getOptimalQuality();
        
        this.init();
        this.initCricketEventListeners();
        this.animate();
    }

    getOptimalParticleCount() {
        const deviceMemory = navigator.deviceMemory || 4;
        const isLowEnd = navigator.connection?.effectiveType === 'slow-2g' || navigator.connection?.effectiveType === '2g';
        
        // Optimized for cricket theme
        if (isLowEnd || deviceMemory < 2) return 50;
        if (deviceMemory >= 8) return 200;
        if (deviceMemory >= 4) return 150;
        return 100;
    }

    getOptimalStarCount() {
        const width = window.innerWidth;
        const deviceMemory = navigator.deviceMemory || 4;
        const isLowEnd = navigator.connection?.effectiveType === 'slow-2g' || navigator.connection?.effectiveType === '2g';
        
        // Cricket optimized particle count
        if (isLowEnd || deviceMemory < 2) return 400;
        if (width > 1400 && deviceMemory >= 8) return 1800;
        if (width > 1200 && deviceMemory >= 4) return 1400;
        if (width > 768) return 1000;
        return 600;
    }

    getOptimalQuality() {
        const gpu = this.getGPUTier();
        const deviceMemory = navigator.deviceMemory || 4;
        const isLowEnd = navigator.connection?.effectiveType === 'slow-2g' || navigator.connection?.effectiveType === '2g';
        
        // Conservative quality settings for better performance
        if (isLowEnd || deviceMemory < 2) return 'low';
        if (gpu === 'high' && deviceMemory >= 8) return 'high';  // Reduced from ultra
        if (gpu === 'medium' || deviceMemory >= 4) return 'medium';
        return 'low';  // Default to low for better performance
    }

    getGPUTier() {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        
        if (!gl) return 'low';
        
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
            const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL).toLowerCase();
            if (renderer.includes('nvidia') || renderer.includes('amd') || renderer.includes('radeon')) {
                return 'high';
            }
            if (renderer.includes('intel')) {
                return 'medium';
            }
        }
        
        return 'medium';
    }

    init() {
        try {
            console.log('🏏 Initializing Enhanced Cricket 3D Engine...');
            
            // Check WebGL support
            if (!this.checkWebGLSupport()) {
                console.warn('WebGL not supported, falling back to cricket 2D mode');
                this.handleCricketFallback();
                return;
            }
            
            // Scene setup with cricket environment
            this.scene = new THREE.Scene();
            this.scene.fog = new THREE.Fog(0x0a0a1a, 15, 120);

            // Camera setup optimized for cricket ball tracking
            this.camera = new THREE.PerspectiveCamera(
                70,
                window.innerWidth / window.innerHeight,
                0.1,
                1000
            );
            this.camera.position.set(0, 0, 6);

            // Enhanced renderer for cricket theme
            const canvas = document.getElementById('canvas3d');
            this.renderer = new THREE.WebGLRenderer({
                canvas: canvas,
                antialias: this.quality === 'high',
                alpha: true,
                powerPreference: 'default',
                stencil: false,
                depth: true,
                preserveDrawingBuffer: false,
                failIfMajorPerformanceCaveat: true
            });
            
            this.renderer.setSize(window.innerWidth, window.innerHeight);
            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, this.quality === 'high' ? 1.5 : 1));
            
            // Optimized shadow settings for cricket
            if (this.quality === 'high') {
                this.renderer.shadowMap.enabled = true;
                this.renderer.shadowMap.type = THREE.PCFShadowMap;
            }
            
            this.renderer.outputEncoding = THREE.sRGBEncoding;
            this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
            this.renderer.toneMappingExposure = 1.1;
            this.renderer.setClearColor(0x0a0a1a, 0);

            this.createCricketStarfield();
            this.createCricketBall();
            this.createCricketOrbitRing();
            this.createCricketParticles();
            this.createCricketLighting();
            
            this.updatePerformanceStats();
            
            console.log('✅ Enhanced Cricket 3D Engine initialized successfully');
            
        } catch (error) {
            console.error('❌ Cricket 3D initialization failed:', error);
            this.handleCricketFallback();
        }
    }
    
    checkWebGLSupport() {
        try {
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            return !!context;
        } catch (e) {
            return false;
        }
    }

    handleCricketFallback() {
        // Hide 3D canvas and show cricket fallback background
        const canvas = document.getElementById('canvas3d');
        if (canvas) {
            canvas.style.display = 'none';
        }
        
        const sceneContainer = document.getElementById('scene-container');
        if (sceneContainer) {
            sceneContainer.style.background = `
                radial-gradient(ellipse at 30% 20%, rgba(0, 212, 255, 0.12) 0%, transparent 50%),
                radial-gradient(ellipse at 70% 80%, rgba(139, 92, 246, 0.12) 0%, transparent 50%),
                linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%)
            `;
        }
        
        showErrorToast('🏏 Enhanced cricket mode unavailable. Using standard interface.');
    }

    createCricketStarfield() {
        const starGeometry = new THREE.BufferGeometry();
        const starPositions = new Float32Array(this.maxStars * 3);
        const starColors = new Float32Array(this.maxStars * 3);
        const starSizes = new Float32Array(this.maxStars);

        for (let i = 0; i < this.maxStars; i++) {
            // Enhanced star positioning for space cricket theme
            starPositions[i * 3] = (Math.random() - 0.5) * 2500;
            starPositions[i * 3 + 1] = (Math.random() - 0.5) * 2500;
            starPositions[i * 3 + 2] = (Math.random() - 0.5) * 2500;

            // Cricket-themed color variation
            const colorType = Math.random();
            if (colorType < 0.15) {
                // Cricket ball orange
                starColors[i * 3] = 1;
                starColors[i * 3 + 1] = 0.42;
                starColors[i * 3 + 2] = 0.21;
            } else if (colorType < 0.25) {
                // Cyan stars
                starColors[i * 3] = 0;
                starColors[i * 3 + 1] = 1;
                starColors[i * 3 + 2] = 1;
            } else if (colorType < 0.35) {
                // Purple stars
                starColors[i * 3] = 0.5;
                starColors[i * 3 + 1] = 0.3;
                starColors[i * 3 + 2] = 0.9;
            } else {
                // White stars
                const intensity = 0.7 + Math.random() * 0.3;
                starColors[i * 3] = intensity;
                starColors[i * 3 + 1] = intensity;
                starColors[i * 3 + 2] = intensity;
            }

            starSizes[i] = Math.random() * 3 + 1;
        }

        starGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
        starGeometry.setAttribute('color', new THREE.BufferAttribute(starColors, 3));
        starGeometry.setAttribute('size', new THREE.BufferAttribute(starSizes, 1));

        // Enhanced star material for space cricket
        const starMaterial = new THREE.ShaderMaterial({
            vertexColors: true,
            transparent: true,
            depthWrite: false,
            blending: THREE.AdditiveBlending,
            vertexShader: `
                attribute float size;
                varying vec3 vColor;
                void main() {
                    vColor = color;
                    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                    gl_PointSize = size * (300.0 / -mvPosition.z);
                    gl_Position = projectionMatrix * mvPosition;
                }
            `,
            fragmentShader: `
                varying vec3 vColor;
                void main() {
                    float distance = length(gl_PointCoord - vec2(0.5));
                    if (distance > 0.5) discard;
                    float opacity = 1.0 - (distance * 2.0);
                    gl_FragColor = vec4(vColor, opacity * 0.8);
                }
            `
        });

        this.stars = new THREE.Points(starGeometry, starMaterial);
        this.scene.add(this.stars);
    }

    createCricketBall() {
        // Enhanced cricket ball with better geometry
        const ballGeometry = new THREE.SphereGeometry(1.2, this.quality === 'ultra' ? 64 : 32, this.quality === 'ultra' ? 32 : 16);
        
        // Enhanced material
        const ballMaterial = new THREE.MeshPhysicalMaterial({
            color: 0xcc4125,
            roughness: 0.4,
            metalness: 0.1,
            clearcoat: 0.8,
            clearcoatRoughness: 0.2,
            reflectivity: 0.3,
            ior: 1.4
        });

        // Enhanced procedural textures
        this.createBallTextures(ballMaterial);

        this.cricketBall = new THREE.Mesh(ballGeometry, ballMaterial);
        this.cricketBall.position.set(3, 0, 0);
        
        if (this.renderer.shadowMap.enabled) {
            this.cricketBall.castShadow = true;
            this.cricketBall.receiveShadow = true;
        }
        
        this.scene.add(this.cricketBall);
    }

    createBallTextures(material) {
        // Create enhanced normal map for cricket ball
        const normalCanvas = document.createElement('canvas');
        normalCanvas.width = 512;
        normalCanvas.height = 512;
        const normalCtx = normalCanvas.getContext('2d');
        
        // Base normal
        normalCtx.fillStyle = '#8080ff';
        normalCtx.fillRect(0, 0, 512, 512);
        
        // Enhanced seam pattern
        normalCtx.strokeStyle = '#ff6060';
        normalCtx.lineWidth = 12;
        normalCtx.lineCap = 'round';
        
        // Primary seam
        normalCtx.beginPath();
        normalCtx.arc(256, 256, 180, Math.PI * 0.2, Math.PI * 1.8);
        normalCtx.stroke();
        
        // Secondary seam
        normalCtx.beginPath();
        normalCtx.arc(256, 256, 180, Math.PI * 1.2, Math.PI * 0.8);
        normalCtx.stroke();
        
        // Add stitch marks
        normalCtx.strokeStyle = '#ff4040';
        normalCtx.lineWidth = 3;
        for (let i = 0; i < 30; i++) {
            const angle = (i / 30) * Math.PI * 2;
            const x = 256 + Math.cos(angle) * 180;
            const y = 256 + Math.sin(angle) * 180;
            
            normalCtx.beginPath();
            normalCtx.moveTo(x - 3, y - 3);
            normalCtx.lineTo(x + 3, y + 3);
            normalCtx.stroke();
        }
        
        const normalTexture = new THREE.CanvasTexture(normalCanvas);
        normalTexture.wrapS = normalTexture.wrapT = THREE.RepeatWrapping;
        material.normalMap = normalTexture;
        material.normalScale = new THREE.Vector2(0.5, 0.5);
    }

    createLighting() {
        // Enhanced lighting setup
        const ambientLight = new THREE.AmbientLight(0x404080, 0.4);
        this.scene.add(ambientLight);

        // Main directional light
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1.2);
        directionalLight.position.set(10, 10, 5);
        
        if (this.renderer.shadowMap.enabled) {
            directionalLight.castShadow = true;
            directionalLight.shadow.mapSize.width = 2048;
            directionalLight.shadow.mapSize.height = 2048;
            directionalLight.shadow.camera.near = 0.5;
            directionalLight.shadow.camera.far = 50;
            directionalLight.shadow.camera.left = -20;
            directionalLight.shadow.camera.right = 20;
            directionalLight.shadow.camera.top = 20;
            directionalLight.shadow.camera.bottom = -20;
        }
        
        this.scene.add(directionalLight);

        // Hemisphere light for better ambient
        const hemisphereLight = new THREE.HemisphereLight(0x87CEEB, 0x1a1a2e, 0.8);
        this.scene.add(hemisphereLight);

        // Enhanced accent lights
        const rimLight = new THREE.PointLight(0x00d4ff, 2, 100, 2);
        rimLight.position.set(-5, 3, -3);
        this.scene.add(rimLight);

        const accentLight1 = new THREE.PointLight(0x8b5cf6, 1.5, 60, 2);
        accentLight1.position.set(-8, -4, 4);
        this.scene.add(accentLight1);

        const accentLight2 = new THREE.PointLight(0x00ffff, 1.2, 50, 2);
        accentLight2.position.set(6, -3, -4);
        this.scene.add(accentLight2);
        
        // Animated background light
        this.backgroundLight = new THREE.PointLight(0xec4899, 0.8, 200, 2);
        this.backgroundLight.position.set(0, 0, -20);
        this.scene.add(this.backgroundLight);
    }

    initEventListeners() {
        // Enhanced mouse movement for parallax
        document.addEventListener('mousemove', (event) => {
            this.mouseX = (event.clientX / window.innerWidth) * 2 - 1;
            this.mouseY = -(event.clientY / window.innerHeight) * 2 + 1;
        });

        // Window resize with debouncing
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.camera.aspect = window.innerWidth / window.innerHeight;
                this.camera.updateProjectionMatrix();
                this.renderer.setSize(window.innerWidth, window.innerHeight);
                
                // Adjust quality based on new window size
                const newStarCount = this.getOptimalStarCount();
                if (newStarCount !== this.maxStars) {
                    this.maxStars = newStarCount;
                    this.createStarfield();
                }
            }, 250);
        });

        // Enhanced visibility change handling
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAnimation();
            } else {
                this.resumeAnimation();
            }
        });
        
        // Memory pressure handling (if supported)
        if ('memory' in performance) {
            setInterval(() => {
                this.checkMemoryUsage();
            }, 5000);
        }
    }

    animate(currentTime = 0) {
        if (!this.renderer || !this.scene || !this.camera) return;
        
        requestAnimationFrame((time) => this.animate(time));

        // Calculate delta time
        const deltaTime = (currentTime - this.lastTime) / 1000;
        this.lastTime = currentTime;
        this.frameCount++;

        // Update performance monitor
        if (this.frameCount % 60 === 0) {
            this.updatePerformanceMonitor(deltaTime);
        }

        try {
            // Enhanced starfield animation
            if (this.stars) {
                this.stars.rotation.y += 0.0002;
                this.stars.rotation.x += 0.0001;
                
                // Update star shader time
                this.stars.material.uniforms.time.value = currentTime * 0.001;
                
                // Adjust opacity based on activity
                const baseOpacity = this.isThinking ? 0.6 : 0.8;
                this.stars.material.uniforms.opacity.value = baseOpacity;
            }

            // Enhanced cricket ball animation
            if (this.cricketBall) {
                // Base rotation
                this.cricketBall.rotation.y += 0.008;
                this.cricketBall.rotation.x += 0.003;

                // Enhanced mouse parallax
                const targetRotationY = this.mouseX * 0.4;
                const targetRotationX = this.mouseY * 0.3;
                
                this.cricketBall.rotation.y += (targetRotationY - this.cricketBall.rotation.y) * 0.03;
                this.cricketBall.rotation.x += (targetRotationX - this.cricketBall.rotation.x) * 0.03;

                // Enhanced floating animation
                this.cricketBall.position.y = Math.sin(currentTime * 0.0015) * 0.4;
                this.cricketBall.position.x = 3 + Math.cos(currentTime * 0.001) * 0.2;

                // Enhanced thinking animation
                if (this.isThinking) {
                    const intensity = (Math.sin(currentTime * 0.008) + 1) * 0.5;
                    this.cricketBall.material.emissive.setRGB(
                        intensity * 0.3,
                        intensity * 0.5,
                        intensity * 1.0
                    );
                    
                    // Add pulsing scale effect
                    const scale = 1 + Math.sin(currentTime * 0.01) * 0.1;
                    this.cricketBall.scale.setScalar(scale);
                } else {
                    this.cricketBall.scale.setScalar(1);
                }
            }

            // Animate background light
            if (this.backgroundLight) {
                this.backgroundLight.intensity = 0.5 + Math.sin(currentTime * 0.002) * 0.3;
                this.backgroundLight.position.x = Math.sin(currentTime * 0.001) * 10;
                this.backgroundLight.position.y = Math.cos(currentTime * 0.0015) * 8;
            }

            // Enhanced camera movement
            this.camera.position.x = Math.sin(currentTime * 0.0003) * 0.15;
            this.camera.position.y = Math.cos(currentTime * 0.0002) * 0.1;
            
            // Look at ball with slight offset
            const lookTarget = new THREE.Vector3(
                this.cricketBall ? this.cricketBall.position.x : 0,
                this.cricketBall ? this.cricketBall.position.y : 0,
                0
            );
            this.camera.lookAt(lookTarget);

            this.renderer.render(this.scene, this.camera);
            
        } catch (error) {
            console.error('Animation error:', error);
            this.handleFallback();
        }
    }

    // Enhanced animation control methods
    startThinking() {
        this.isThinking = true;
        if (this.cricketBall) {
            gsap.to(this.cricketBall.scale, {
                duration: 0.5,
                x: 1.15,
                y: 1.15,
                z: 1.15,
                ease: "power2.out"
            });
            
            // Add rotation boost
            gsap.to(this.cricketBall.rotation, {
                duration: 2,
                x: this.cricketBall.rotation.x + Math.PI * 2,
                y: this.cricketBall.rotation.y + Math.PI * 2,
                ease: "power2.inOut"
            });
        }
    }

    stopThinking() {
        this.isThinking = false;
        if (this.cricketBall) {
            this.cricketBall.material.emissive.setRGB(0, 0, 0);
            gsap.to(this.cricketBall.scale, {
                duration: 0.5,
                x: 1,
                y: 1,
                z: 1,
                ease: "power2.out"
            });
        }
    }

    pauseAnimation() {
        if (this.renderer) {
            this.renderer.setPixelRatio(1);
        }
        if (this.stars && this.stars.material.uniforms) {
            this.stars.material.uniforms.opacity.value = 0.3;
        }
    }

    resumeAnimation() {
        if (this.renderer) {
            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, this.quality === 'ultra' ? 2 : 1.5));
        }
        if (this.stars && this.stars.material.uniforms) {
            this.stars.material.uniforms.opacity.value = 0.8;
        }
    }

    updatePerformanceMonitor(deltaTime) {
        const fps = Math.round(1 / deltaTime);
        this.performanceStats.fps = fps;
        
        // Update DOM elements
        const fpsCounter = document.getElementById('fps-counter');
        if (fpsCounter) {
            fpsCounter.textContent = fps;
            fpsCounter.style.color = fps > 50 ? '#00ff88' : fps > 30 ? '#ffa500' : '#ff4444';
        }
        
        // Memory usage (approximate)
        if ('memory' in performance) {
            const memoryMB = Math.round(performance.memory.usedJSHeapSize / 1048576);
            this.performanceStats.memory = memoryMB;
            
            const memoryCounter = document.getElementById('memory-counter');
            if (memoryCounter) {
                memoryCounter.textContent = memoryMB + 'MB';
            }
        }
        
        // Update particle count
        const particleCounter = document.getElementById('particle-counter');
        if (particleCounter) {
            particleCounter.textContent = this.performanceStats.particles;
        }
        
        // Update quality indicator
        const qualityIndicator = document.getElementById('quality-indicator');
        if (qualityIndicator) {
            qualityIndicator.textContent = this.quality.charAt(0).toUpperCase() + this.quality.slice(1);
        }
        
        // Auto-optimize performance
        if (fps < 25 && this.quality !== 'medium') {
            this.optimizeForPerformance();
        }
    }

    updatePerformanceStats() {
        this.performanceStats.quality = this.quality;
        this.performanceStats.particles = this.maxStars;
    }

    checkMemoryUsage() {
        if ('memory' in performance) {
            const memoryMB = performance.memory.usedJSHeapSize / 1048576;
            if (memoryMB > 150) { // If using more than 150MB
                this.optimizeForPerformance();
            }
        }
    }

    optimizeForPerformance() {
        console.log('Optimizing 3D performance...');
        
        // Reduce star count
        if (this.maxStars > 500) {
            this.maxStars = Math.max(500, this.maxStars * 0.6);
            this.createStarfield();
        }

        // Reduce quality
        if (this.quality === 'ultra') {
            this.quality = 'high';
        } else if (this.quality === 'high') {
            this.quality = 'medium';
        }
        
        // Disable shadows if enabled
        if (this.renderer.shadowMap.enabled) {
            this.renderer.shadowMap.enabled = false;
        }
        
        // Reduce pixel ratio
        this.renderer.setPixelRatio(1);
        
        this.updatePerformanceStats();
    }

    // Cleanup method
    dispose() {
        if (this.renderer) {
            this.renderer.dispose();
        }
        if (this.scene) {
            this.scene.clear();
        }
    }
}

/**
 * ====================================
 * ENHANCED CHAT INTERFACE CONTROLLER
 * ====================================
 */

class ChatInterface {
    constructor() {
        this.sessionId = null;
        this.isProcessing = false;
        this.messageCount = 0;
        this.scrollTimeout = null;
        this.currentStage = 0;
        this.thinkingStages = ['analyze', 'search', 'generate'];
        this.connectionStatus = {
            api: false,
            ai: false,
            database: false
        };
        
        this.initializeElements();
        this.initializeEventListeners();
        this.checkSystemStatus();
        this.loadSuggestions();
    }

    initializeElements() {
        this.messageContainer = document.getElementById('message-container');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.voiceBtn = document.getElementById('voice-btn');
        this.thinkingIndicator = document.getElementById('thinking-indicator');
        this.quickActions = document.getElementById('quick-actions');
        this.inputSuggestions = document.getElementById('input-suggestions');
        this.scrollBottomBtn = document.getElementById('scroll-bottom-btn');
        this.charCount = document.getElementById('char-count');
        this.thinkingText = document.getElementById('thinking-text');
        
        // Status indicators
        this.connectionStatusEl = document.getElementById('connection-status');
        this.aiStatusEl = document.getElementById('ai-status');
        this.dbStatusEl = document.getElementById('db-status');
    }

    initializeEventListeners() {
        // Enhanced message input handling
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Character count and input validation
        this.messageInput.addEventListener('input', () => {
            this.updateCharCount();
            this.updateInputSuggestions();
            this.handleTypingIndicator();
        });

        // Enhanced scrolling detection with throttling
        if (this.messageContainer) {
            this.messageContainer.addEventListener('scroll', () => {
                if (this.scrollTimeout) {
                    clearTimeout(this.scrollTimeout);
                }
                this.scrollTimeout = setTimeout(() => {
                    this.handleScroll();
                }, 50);
            });
        }

        // Scroll to bottom button
        if (this.scrollBottomBtn) {
            this.scrollBottomBtn.addEventListener('click', () => {
                this.scrollToBottom(true);
            });
        }

        // Focus management
        if (this.messageInput) {
            this.messageInput.addEventListener('focus', () => {
                this.hideInputSuggestions();
            });
        }

        // Voice input enhancement
        if (this.voiceBtn) {
            this.voiceBtn.addEventListener('click', () => {
                this.toggleVoiceInput();
            });
        }
        
        // Performance monitor close button
        const closeMonitor = document.getElementById('close-monitor');
        if (closeMonitor) {
            closeMonitor.addEventListener('click', () => {
                document.getElementById('performance-monitor').style.display = 'none';
            });
        }

        // Auto-focus input with delay to ensure everything is loaded
        setTimeout(() => {
            if (this.messageInput) {
                this.messageInput.focus();
            }
            // Initialize scrolling position
            this.scrollToBottom(false);
        }, 800);
    }

    async checkSystemStatus() {
        console.log('🔍 Checking system status...');
        
        // Check API connection
        try {
            const response = await fetch('/api/chat/suggestions');
            this.connectionStatus.api = response.ok;
            this.updateStatusIndicator('connection-status', this.connectionStatus.api, 
                this.connectionStatus.api ? 'Connected' : 'Offline');
            console.log('✅ API Status:', this.connectionStatus.api ? 'Connected' : 'Offline');
        } catch (error) {
            console.error('❌ API connection failed:', error);
            this.connectionStatus.api = false;
            this.updateStatusIndicator('connection-status', false, 'Offline');
        }

        // Test AI functionality
        try {
            const testResponse = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: 'status check', session_id: 'status-check' })
            });
            
            if (testResponse.ok) {
                const data = await testResponse.json();
                this.connectionStatus.ai = data.success !== false;
                this.connectionStatus.database = !data.error || !data.error.includes('database');
                console.log('✅ AI Status:', this.connectionStatus.ai ? 'Ready' : 'Limited');
                console.log('✅ DB Status:', this.connectionStatus.database ? 'Connected' : 'Limited');
            } else {
                this.connectionStatus.ai = false;
                this.connectionStatus.database = false;
                console.warn('⚠️ AI test request failed');
            }
        } catch (error) {
            console.error('❌ AI functionality test failed:', error);
            this.connectionStatus.ai = false;
            this.connectionStatus.database = false;
        }
        
        this.updateStatusIndicator('ai-status', this.connectionStatus.ai, 
            this.connectionStatus.ai ? 'AI Ready' : 'AI Limited');
        this.updateStatusIndicator('db-status', this.connectionStatus.database, 
            this.connectionStatus.database ? 'Database OK' : 'Database Limited');
    }

    updateStatusIndicator(elementId, isActive, text) {
        const element = document.getElementById(elementId);
        if (element) {
            const dot = element.querySelector('.status-dot');
            const span = element.querySelector('span');
            
            if (dot) {
                dot.className = `status-dot ${isActive ? 'active' : 'checking'}`;
                dot.classList.remove('checking');
                if (isActive) {
                    dot.classList.add('active');
                }
            }
            if (span) {
                span.textContent = text;
            }
            
            console.log(`🔄 Updated ${elementId}: ${text} (${isActive ? 'active' : 'inactive'})`);
        } else {
            console.error(`❌ Status element not found: ${elementId}`);
        }
    }

    updateCharCount() {
        const count = this.messageInput.value.length;
        const maxLength = 500;
        
        if (this.charCount) {
            this.charCount.textContent = `${count}/${maxLength}`;
            
            // Update styling based on count
            this.charCount.className = 'char-count';
            if (count > maxLength * 0.8) {
                this.charCount.classList.add('warning');
            }
            if (count > maxLength * 0.95) {
                this.charCount.classList.add('danger');
            }
        }
    }

    handleScroll() {
        if (!this.messageContainer || !this.scrollBottomBtn) {
            return;
        }
        
        try {
            const container = this.messageContainer;
            const isNearBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 100;
                
            if (isNearBottom) {
                this.scrollBottomBtn.style.display = 'none';
            } else {
                this.scrollBottomBtn.style.display = 'flex';
            }
            
            console.log('Scroll position:', {
                scrollTop: container.scrollTop,
                clientHeight: container.clientHeight,
                scrollHeight: container.scrollHeight,
                isNearBottom: isNearBottom
            });
        } catch (error) {
            console.error('Error handling scroll:', error);
        }
    }

    handleTypingIndicator() {
        // Clear previous timeout
        if (this.scrollTimeout) {
            clearTimeout(this.scrollTimeout);
        }
        
        // Show typing indicator briefly
        this.scrollTimeout = setTimeout(() => {
            // Could add "user is typing" indicator here
        }, 300);
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isProcessing || message.length > 500) return;

        this.isProcessing = true;
        this.messageInput.value = '';
        this.updateCharCount();
        this.hideInputSuggestions();
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Show enhanced thinking animation
        this.showThinking(true);
        
        // Start 3D thinking animation
        if (window.ai3d) {
            window.ai3d.startThinking();
        }

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });

            const data = await response.json();
            
            // Stop thinking animation
            this.showThinking(false);
            if (window.ai3d) {
                window.ai3d.stopThinking();
            }
            
            if (data.success) {
                this.sessionId = data.session_id;
                
                // Add AI response with enhanced metadata
                this.addMessage('ai', data.response, {
                    confidence: data.confidence,
                    intent: data.intent,
                    quickActions: data.quick_actions,
                    tokensUsed: data.tokens_used,
                    model: data.model,
                    timestamp: data.timestamp
                });
                
                // Update quick actions if provided
                if (data.quick_actions && data.quick_actions.length > 0) {
                    this.updateQuickActions(data.quick_actions);
                }
                
            } else {
                // Handle API errors gracefully
                const fallbackMessage = this.generateFallbackResponse(message, data.error);
                this.addMessage('ai', fallbackMessage, {
                    confidence: 0.7,
                    model: 'fallback',
                    isError: true
                });
            }
        } catch (error) {
            console.error('Chat error:', error);
            
            // Stop thinking animation
            this.showThinking(false);
            if (window.ai3d) {
                window.ai3d.stopThinking();
            }
            
            // Show network error message
            const errorMessage = this.generateNetworkErrorResponse(message);
            this.addMessage('ai', errorMessage, {
                confidence: 0.6,
                model: 'error-handler',
                isError: true
            });
            
            showErrorToast('Network error occurred. Please check your connection.');
        } finally {
            this.isProcessing = false;
            this.messageInput.focus();
        }
    }

    generateFallbackResponse(userMessage, errorDetails) {
        const messageLower = userMessage.toLowerCase();
        
        // Stadium-specific fallbacks (following memory specification)
        if (messageLower.includes('melbourne cricket ground') || messageLower.includes('mcg')) {
            return `🏏 **Melbourne Cricket Ground (MCG)**

I can help you with MCG information! The Melbourne Cricket Ground is Australia's largest cricket stadium with a capacity of 100,024. Located in East Melbourne, it's the home of Australian cricket and hosts major BBL matches.

**Key Features:**
• World's largest cricket stadium
• Premium corporate boxes and club seating
• Multiple dining options and bars
• Accessible facilities throughout
• Public transport: Richmond Station (5 min walk)

**Current Ticket Prices:**
• General Admission: $25-45
• Premium Reserve: $60-120
• Club/MCC Reserve: $80-200

Would you like specific information about booking tickets or facilities?`;
        }
        
        if (messageLower.includes('stadium') || messageLower.includes('venue')) {
            return `🏟️ **Australian Cricket Stadiums**

I have comprehensive information about all major Australian cricket venues:

**Major BBL Venues:**
• Melbourne Cricket Ground (MCG) - 100,024 capacity
• Sydney Cricket Ground (SCG) - 48,000 capacity
• Perth Stadium - 60,000 capacity
• Adelaide Oval - 53,500 capacity
• The Gabba, Brisbane - 42,000 capacity
• Marvel Stadium, Melbourne - 56,000 capacity

Each stadium offers unique facilities, dining options, and experiences. What specific stadium information are you looking for?`;
        }
        
        if (messageLower.includes('book') || messageLower.includes('ticket')) {
            return `🎫 **Cricket Ticket Booking**

I can help you with cricket ticket bookings! Here's what's available:

**Current Matches:**
• BBL Season matches across all major venues
• International fixtures
• State cricket championships

**Ticket Categories:**
• General Admission: From $25
• Premium Seating: From $60
• Corporate Packages: From $150
• Family Packages: From $80 (2 adults + 2 kids)

**How to Book:**
1. Choose your preferred match and venue
2. Select seating category
3. Add parking and food options
4. Complete secure payment

Which venue or match are you interested in?`;
        }
        
        // General fallback
        return `🏏 **CricVerse Assistant**

I'm experiencing some technical difficulties but I'm still here to help with cricket-related queries!

**I can assist with:**
• Cricket stadium information and facilities
• Match schedules and team details
• Ticket booking and pricing
• Parking and navigation
• Food and beverage options

**Try asking about:**
• "Tell me about Melbourne Cricket Ground"
• "Show me upcoming cricket matches"
• "Help me book tickets"
• "Stadium facilities and amenities"

Please try rephrasing your question or ask about specific cricket topics. Error details: ${errorDetails || 'Connection issue'}`;
    }

    generateNetworkErrorResponse(userMessage) {
        return `🔌 **Connection Issue**

I'm having trouble connecting to our servers right now, but I can still provide basic cricket information.

**Your question was about:** "${userMessage}"

**Offline Help Available:**
• Stadium information and capacities
• General ticket pricing guidelines
• Cricket match format explanations
• Basic venue facilities overview

**Please try again in a moment** - the connection should be restored shortly.

In the meantime, you can also try refreshing the page or checking your internet connection.`;
    }

    hideInputSuggestions() {
        if (this.inputSuggestions) {
            this.inputSuggestions.classList.remove('active');
        }
    }

    showInputSuggestions() {
        if (this.inputSuggestions) {
            this.inputSuggestions.classList.add('active');
        }
    }

    scrollToBottom(force = false) {
        if (!this.messageContainer) {
            console.warn('Message container not found for scrolling');
            return;
        }
        
        try {
            const scrollOptions = {
                top: this.messageContainer.scrollHeight,
                behavior: force ? 'auto' : 'smooth'
            };
            
            this.messageContainer.scrollTo(scrollOptions);
            
            console.log('Scrolled to bottom:', {
                scrollHeight: this.messageContainer.scrollHeight,
                scrollTop: this.messageContainer.scrollTop,
                force: force
            });
            
            // Hide scroll button when at bottom
            setTimeout(() => {
                if (this.scrollBottomBtn) {
                    this.scrollBottomBtn.style.display = 'none';
                }
            }, 300);
        } catch (error) {
            console.error('Error scrolling to bottom:', error);
            // Fallback method
            this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
        }
    }

    addMessage(sender, content, metadata = {}) {
        // Validate message first
        const validation = validateMessage(content);
        if (!validation.valid && sender === 'user') {
            showErrorToast(validation.error);
            return;
        }

        const messageElement = createMessageElement(sender, content, metadata);
        messageElement.style.opacity = '0';
        messageElement.style.transform = 'translateY(20px)';
        
        this.messageContainer.appendChild(messageElement);
        
        // Animate message appearance
        gsap.to(messageElement, {
            opacity: 1,
            y: 0,
            duration: 0.5,
            ease: "power2.out"
        });
        
        // Typing effect for AI messages
        if (sender === 'ai') {
            this.typeMessage(messageElement.querySelector('.message-text'), content);
        }
        
        this.scrollToBottom();
        this.messageCount++;
        
        // Auto-scroll behavior
        setTimeout(() => {
            this.handleScroll();
        }, 100);
    }

    typeMessage(element, text) {
        if (!element || !text) return;
        
        const formattedText = formatMessageContent(text);
        element.innerHTML = '';
        
        // Create a temporary element to get plain text
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = formattedText;
        const plainText = tempDiv.textContent || tempDiv.innerText || '';
        
        let currentIndex = 0;
        const typingSpeed = 25; // Milliseconds per character
        
        const typeWriter = () => {
            if (currentIndex < plainText.length) {
                element.textContent = plainText.substring(0, currentIndex + 1);
                currentIndex++;
                setTimeout(typeWriter, typingSpeed);
                
                // Auto-scroll during typing
                if (currentIndex % 10 === 0) {
                    this.scrollToBottom();
                }
            } else {
                // Replace with properly formatted HTML once typing is complete
                element.innerHTML = formattedText;
                this.scrollToBottom();
            }
        };
        
        typeWriter();
    }

    showThinking(show) {
        if (!this.thinkingIndicator) return;
        
        if (show) {
            this.thinkingIndicator.style.display = 'block';
            this.currentStage = 0;
            
            // Animate thinking stages
            this.stageInterval = setInterval(() => {
                updateThinkingStage(this.currentStage);
                this.currentStage = (this.currentStage + 1) % this.thinkingStages.length;
            }, 2000);
            
            this.scrollToBottom();
        } else {
            this.thinkingIndicator.style.display = 'none';
            if (this.stageInterval) {
                clearInterval(this.stageInterval);
                this.stageInterval = null;
            }
        }
    }

    updateQuickActions(actions) {
        if (!actions || !Array.isArray(actions) || !this.quickActions) return;
        
        const actionsGrid = this.quickActions.querySelector('.actions-grid');
        if (!actionsGrid) return;
        
        // Clear existing actions
        actionsGrid.innerHTML = '';
        
        actions.slice(0, 6).forEach((action, index) => {
            const chip = document.createElement('div');
            chip.className = 'action-chip';
            chip.style.opacity = '0';
            chip.style.transform = 'translateY(20px)';
            
            const iconClass = this.getActionIcon(action.action || 'default');
            chip.innerHTML = `
                <i class="fas fa-${iconClass}"></i>
                <span>${action.text}</span>
            `;
            
            chip.onclick = () => this.sendQuickMessage(action.text);
            actionsGrid.appendChild(chip);
            
            // Staggered animation
            gsap.to(chip, {
                opacity: 1,
                y: 0,
                duration: 0.4,
                delay: index * 0.1,
                ease: "power2.out"
            });
        });
    }

    getActionIcon(action) {
        const iconMap = {
            'booking_help': 'ticket-alt',
            'stadium_guide': 'building',
            'browse_matches': 'calendar-alt',
            'parking_info': 'car',
            'team_stats': 'chart-bar',
            'food_drinks': 'utensils',
            'general': 'arrow-right',
            'default': 'arrow-right'
        };
        return iconMap[action] || iconMap.default;
    }

    sendQuickMessage(text) {
        if (this.messageInput && text) {
            this.messageInput.value = text;
            this.updateCharCount();
            this.sendMessage();
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        // Enhanced validation
        const validation = validateMessage(message);
        if (!validation.valid) {
            showErrorToast(validation.error);
            return;
        }
        
        if (this.isProcessing) {
            showErrorToast('Please wait for the current message to be processed.');
            return;
        }

        this.isProcessing = true;
        this.messageInput.value = '';
        this.updateCharCount();
        this.hideInputSuggestions();
        
        // Add user message to chat
        this.addMessage('user', validation.message);
        
        // Show enhanced thinking animation
        this.showThinking(true);
        
        // Start 3D thinking animation
        if (window.ai3d) {
            window.ai3d.startThinking();
        }

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: validation.message,
                    session_id: this.sessionId
                })
            });

            const data = await response.json();
            
            // Stop thinking animation
            this.showThinking(false);
            if (window.ai3d) {
                window.ai3d.stopThinking();
            }
            
            if (data.success) {
                this.sessionId = data.session_id;
                
                // Save session data
                saveSessionData(this.sessionId, {
                    lastMessage: validation.message,
                    messageCount: this.messageCount
                });
                
                // Add AI response with enhanced metadata
                this.addMessage('ai', data.response, {
                    confidence: data.confidence,
                    intent: data.intent,
                    quickActions: data.quick_actions,
                    tokensUsed: data.tokens_used,
                    model: data.model,
                    timestamp: data.timestamp
                });
                
                // Update quick actions if provided
                if (data.quick_actions && data.quick_actions.length > 0) {
                    this.updateQuickActions(data.quick_actions);
                }
                
                // Update connection status
                this.connectionStatus.ai = true;
                this.updateStatusIndicator('ai-status', true, 'AI Ready');
                
            } else {
                // Handle API errors gracefully
                const fallbackMessage = this.generateFallbackResponse(validation.message, data.error);
                this.addMessage('ai', fallbackMessage, {
                    confidence: 0.7,
                    model: 'fallback',
                    isError: true
                });
                
                this.connectionStatus.ai = false;
                this.updateStatusIndicator('ai-status', false, 'AI Limited');
            }
        } catch (error) {
            console.error('Chat error:', error);
            
            // Stop thinking animation
            this.showThinking(false);
            if (window.ai3d) {
                window.ai3d.stopThinking();
            }
            
            // Show network error message
            const errorMessage = this.generateNetworkErrorResponse(validation.message);
            this.addMessage('ai', errorMessage, {
                confidence: 0.6,
                model: 'error-handler',
                isError: true
            });
            
            showErrorToast('Network error occurred. Please check your connection.');
            
            // Update connection status
            this.connectionStatus.api = false;
            this.updateStatusIndicator('connection-status', false, 'Offline');
        } finally {
            this.isProcessing = false;
            this.messageInput.focus();
        }
    }

    updateInputSuggestions() {
        const query = this.messageInput.value.toLowerCase().trim();
        if (query.length < 2) {
            this.hideInputSuggestions();
            return;
        }

        // Enhanced suggestion logic
        const suggestions = this.getSuggestions(query);
        
        if (suggestions.length > 0) {
            const suggestionsHtml = suggestions
                .map(s => `
                    <div class="suggestion-item" onclick="chat.sendQuickMessage('${s.replace(/'/g, "\\'")}')">
                        <i class="fas fa-${this.getSuggestionIcon(s)}"></i>
                        <span>${s}</span>
                    </div>
                `)
                .join('');
            
            this.inputSuggestions.innerHTML = suggestionsHtml;
            this.showInputSuggestions();
        } else {
            this.hideInputSuggestions();
        }
    }

    getSuggestionIcon(suggestion) {
        const text = suggestion.toLowerCase();
        if (text.includes('book') || text.includes('ticket')) return 'ticket-alt';
        if (text.includes('stadium') || text.includes('venue')) return 'building';
        if (text.includes('match') || text.includes('game')) return 'calendar-alt';
        if (text.includes('parking')) return 'car';
        if (text.includes('food') || text.includes('drink')) return 'utensils';
        if (text.includes('team') || text.includes('stats')) return 'chart-bar';
        return 'arrow-right';
    }

    getSuggestions(query) {
        const cricketSuggestions = [
            // Booking related
            'Book tickets for Melbourne Cricket Ground',
            'Book tickets for Sydney Cricket Ground',
            'Book tickets for Perth Stadium',
            'Reserve premium seating',
            'Family ticket packages',
            
            // Stadium information
            'Show me stadium facilities',
            'Tell me about Melbourne Cricket Ground',
            'Sydney Cricket Ground information',
            'Stadium seating charts',
            'Accessible facilities at stadiums',
            
            // Matches and events
            'What matches are this weekend?',
            'Show me BBL fixtures',
            'International cricket matches',
            'Match schedules and timings',
            'Live match updates',
            
            // Parking and transport
            'Help me with parking reservations',
            'Public transport to stadiums',
            'Parking rates and options',
            'Stadium directions and maps',
            
            // Teams and statistics
            'Tell me about team standings',
            'Player statistics and records',
            'Team performance analytics',
            'Historical match data',
            
            // Food and amenities
            'What food options are available?',
            'Stadium bars and restaurants',
            'Special dietary options',
            'Corporate hospitality packages',
            
            // General help
            'How do I cancel my booking?',
            'Show me seat availability',
            'Weather forecast for matches',
            'Stadium safety guidelines'
        ];

        return cricketSuggestions
            .filter(s => s.toLowerCase().includes(query))
            .slice(0, 4);
    }

    async loadSuggestions() {
        try {
            const response = await fetch('/api/chat/suggestions');
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.suggestions && data.suggestions.length > 0) {
                    const formattedSuggestions = data.suggestions.slice(0, 6).map(s => ({
                        text: s,
                        action: this.classifyAction(s)
                    }));
                    
                    this.updateQuickActions(formattedSuggestions);
                }
            }
        } catch (error) {
            console.error('Error loading suggestions:', error);
            // Load default suggestions
            this.loadDefaultSuggestions();
        }
    }

    loadDefaultSuggestions() {
        const defaultSuggestions = [
            { text: 'Book tickets for Melbourne Cricket Ground', action: 'booking_help' },
            { text: 'Show me all Australian cricket stadiums', action: 'stadium_guide' },
            { text: 'What cricket matches are happening this week?', action: 'browse_matches' },
            { text: 'Help me reserve parking at Sydney Cricket Ground', action: 'parking_info' },
            { text: 'Show me BBL team standings and statistics', action: 'team_stats' },
            { text: 'What food and drink options are available?', action: 'food_drinks' }
        ];
        
        this.updateQuickActions(defaultSuggestions);
    }

    classifyAction(text) {
        const textLower = text.toLowerCase();
        if (textLower.includes('book') || textLower.includes('ticket')) return 'booking_help';
        if (textLower.includes('stadium') || textLower.includes('venue')) return 'stadium_guide';
        if (textLower.includes('match') || textLower.includes('game')) return 'browse_matches';
        if (textLower.includes('parking')) return 'parking_info';
        if (textLower.includes('team') || textLower.includes('stats')) return 'team_stats';
        if (textLower.includes('food') || textLower.includes('drink')) return 'food_drinks';
        return 'general';
    }

    toggleVoiceInput() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            showErrorToast('Voice recognition not supported in this browser.');
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;
        
        recognition.onstart = () => {
            this.voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
            this.voiceBtn.style.background = 'linear-gradient(135deg, #ec4899, #8b5cf6)';
            this.voiceBtn.style.animation = 'pulse 1.5s infinite';
            
            // Show voice feedback
            const voiceFeedback = document.createElement('div');
            voiceFeedback.id = 'voice-feedback';
            voiceFeedback.className = 'voice-feedback';
            voiceFeedback.innerHTML = `
                <div class="voice-animation">
                    <div class="voice-wave"></div>
                    <div class="voice-wave"></div>
                    <div class="voice-wave"></div>
                </div>
                <span>Listening... Speak now</span>
            `;
            document.body.appendChild(voiceFeedback);
        };
        
        recognition.onend = () => {
            this.voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
            this.voiceBtn.style.background = '';
            this.voiceBtn.style.animation = '';
            
            // Remove voice feedback
            const voiceFeedback = document.getElementById('voice-feedback');
            if (voiceFeedback) {
                voiceFeedback.remove();
            }
        };
        
        recognition.onerror = (event) => {
            console.error('Voice recognition error:', event.error);
            showErrorToast(`Voice recognition error: ${event.error}`);
            recognition.onend();
        };
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            const confidence = event.results[0][0].confidence;
            
            this.messageInput.value = transcript;
            this.updateCharCount();
            
            // Auto-send if confidence is high
            if (confidence > 0.8) {
                setTimeout(() => {
                    this.sendMessage();
                }, 500);
            } else {
                showErrorToast(`Voice input: "${transcript}" (Click send to confirm)`);
            }
        };
        
        try {
            recognition.start();
        } catch (error) {
            console.error('Failed to start voice recognition:', error);
            showErrorToast('Failed to start voice recognition.');
        }
    }
}

/**
 * ====================================
 * ENHANCED UTILITY FUNCTIONS
 * ====================================
 */

// Enhanced error toast functionality
function showErrorToast(message, duration = 5000) {
    const toast = document.getElementById('error-toast');
    const messageElement = document.getElementById('error-message');
    
    if (toast && messageElement) {
        messageElement.textContent = message;
        toast.style.display = 'flex';
        
        // Auto-hide after duration
        setTimeout(() => {
            hideErrorToast();
        }, duration);
    }
}

function hideErrorToast() {
    const toast = document.getElementById('error-toast');
    if (toast) {
        toast.style.display = 'none';
    }
}

// Enhanced message formatting
function formatMessageContent(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code class="inline-code">$1</code>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/^(.+)$/, '<p>$1</p>')
        .replace(/🎯|🎟️|🏟️|📅|🚗|📊|🏏|⚾|🏆|🎪|🍕|🍺|💳|🅿️|🚇|🎵|🎉/g, '<span class="emoji">$&</span>');
}

// Enhanced scroll utilities
function smoothScrollToBottom(container, callback) {
    if (!container) return;
    
    const scrollHeight = container.scrollHeight;
    const height = container.clientHeight;
    const maxScrollTop = scrollHeight - height;
    
    container.scrollTo({
        top: maxScrollTop,
        behavior: 'smooth'
    });
    
    if (callback) {
        setTimeout(callback, 300);
    }
}

// Connection testing utilities
async function testAPIConnection() {
    try {
        const response = await fetch('/api/health', {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });
        return response.ok;
    } catch (error) {
        console.error('API connection test failed:', error);
        return false;
    }
}

async function testAIConnection() {
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: 'ping',
                session_id: 'health-check-' + Date.now()
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.success;
        }
        return false;
    } catch (error) {
        console.error('AI connection test failed:', error);
        return false;
    }
}

// Enhanced message helpers
function createMessageElement(sender, content, metadata = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.setAttribute('data-timestamp', Date.now());
    
    const avatar = sender === 'user' ? 
        '<i class="fas fa-user"></i>' : 
        '<i class="fas fa-robot"></i>';

    let metadataHtml = '';
    if (metadata.confidence && sender === 'ai') {
        const confidencePercent = Math.round(metadata.confidence * 100);
        metadataHtml = `
            <div class="message-metadata">
                <span class="confidence-badge" title="AI Confidence Level">
                    <i class="fas fa-brain"></i> ${confidencePercent}%
                </span>
                ${metadata.model ? `<span class="model-badge" title="AI Model">
                    <i class="fas fa-microchip"></i> ${metadata.model}
                </span>` : ''}
                ${metadata.tokensUsed ? `<span class="tokens-badge" title="Tokens Used">
                    <i class="fas fa-coins"></i> ${metadata.tokensUsed}
                </span>` : ''}
                ${metadata.isError ? `<span class="error-badge" title="Fallback Response">
                    <i class="fas fa-exclamation-triangle"></i> Offline
                </span>` : ''}
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-avatar">
            <div class="${sender === 'ai' ? 'ai-icon' : 'user-icon'}">
                ${avatar}
            </div>
        </div>
        <div class="message-content">
            <div class="message-header">
                <span class="sender-name">${sender === 'ai' ? 'CricVerse AI' : 'You'}</span>
                <span class="message-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="message-text">
                ${formatMessageContent(content)}
            </div>
            ${metadataHtml}
        </div>
    `;

    return messageDiv;
}

// Enhanced thinking animation controller
function updateThinkingStage(stage) {
    const stages = document.querySelectorAll('.stage');
    stages.forEach((stageEl, index) => {
        stageEl.classList.toggle('active', index <= stage);
    });
    
    const stageTexts = [
        'Analyzing your question...',
        'Searching cricket database...',
        'Generating personalized response...'
    ];
    
    const thinkingText = document.getElementById('thinking-text');
    if (thinkingText && stageTexts[stage]) {
        thinkingText.textContent = stageTexts[stage];
    }
}

// Performance optimization utilities
function optimizePerformance() {
    console.log('🛠️ Optimizing application performance...');
    
    // Reduce animation complexity
    const messages = document.querySelectorAll('.message');
    messages.forEach(msg => {
        msg.style.animation = 'none';
    });
    
    // Limit message history for memory management
    const messageContainer = document.getElementById('message-container');
    if (messageContainer && messageContainer.children.length > 30) {  // Reduced from 50
        const excessMessages = messageContainer.children.length - 25;
        for (let i = 0; i < excessMessages; i++) {
            messageContainer.removeChild(messageContainer.firstChild);
        }
        console.log(`🗑️ Cleaned up ${excessMessages} old messages`);
    }
    
    // Reduce 3D quality if available
    if (window.ai3d && typeof window.ai3d.optimizeForPerformance === 'function') {
        window.ai3d.optimizeForPerformance();
    }
    
    // Force garbage collection if available
    if (window.gc) {
        window.gc();
    }
    
    console.log('✅ Performance optimization completed');
}

// Auto-optimize performance based on system resources
function autoOptimizePerformance() {
    const memoryInfo = performance.memory;
    if (memoryInfo) {
        const usedMB = memoryInfo.usedJSHeapSize / 1048576;
        const limitMB = memoryInfo.jsHeapSizeLimit / 1048576;
        const usagePercent = (usedMB / limitMB) * 100;
        
        if (usagePercent > 70) {
            console.warn(`⚠️ High memory usage detected: ${usagePercent.toFixed(1)}%`);
            optimizePerformance();
        }
    }
}

// Run auto-optimization every 30 seconds
setInterval(autoOptimizePerformance, 30000);

// Local storage utilities for session persistence
function saveSessionData(sessionId, data) {
    try {
        localStorage.setItem(`cricverse_session_${sessionId}`, JSON.stringify({
            ...data,
            timestamp: Date.now()
        }));
    } catch (error) {
        console.warn('Could not save session data:', error);
    }
}

function loadSessionData(sessionId) {
    try {
        const data = localStorage.getItem(`cricverse_session_${sessionId}`);
        if (data) {
            const parsed = JSON.parse(data);
            // Check if data is not older than 24 hours
            if (Date.now() - parsed.timestamp < 24 * 60 * 60 * 1000) {
                return parsed;
            }
        }
    } catch (error) {
        console.warn('Could not load session data:', error);
    }
    return null;
}

// Enhanced input validation
function validateMessage(message) {
    if (!message || typeof message !== 'string') {
        return { valid: false, error: 'Message cannot be empty' };
    }
    
    const trimmed = message.trim();
    if (trimmed.length === 0) {
        return { valid: false, error: 'Message cannot be empty' };
    }
    
    if (trimmed.length > 500) {
        return { valid: false, error: 'Message too long (max 500 characters)' };
    }
    
    // Check for potential spam patterns
    const spamPatterns = [
        /^(.)\1{10,}$/, // Repeated characters
        /^[^a-zA-Z0-9\s]{10,}$/, // Only special characters
    ];
    
    for (const pattern of spamPatterns) {
        if (pattern.test(trimmed)) {
            return { valid: false, error: 'Message appears to be spam' };
        }
    }
    
    return { valid: true, message: trimmed };
}

/**
 * ====================================
 * SPACE CRICKET INITIALIZATION
 * ====================================
 */

// Global variables for cricket
let cricketAI3d, chat;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🏏 DOM loaded, initializing systems...');
    
    // Initialize Enhanced Cricket 3D scene
    cricketAI3d = new CricVerseAI3D();
    window.ai3d = cricketAI3d;

    // Initialize chat interface
    chat = new ChatInterface();
    window.chat = chat;

    // Update connection status with delay to ensure DOM is ready
    setTimeout(() => {
        console.log('🔍 Starting connection status check...');
        updateConnectionStatus();
    }, 1000);
    
    // Performance monitoring
    if (window.location.search.includes('debug=true')) {
        document.getElementById('performance-monitor').style.display = 'block';
    }
    
    // Retry status check after 5 seconds if still checking
    setTimeout(() => {
        const connectionStatus = document.getElementById('connection-status');
        const statusDot = connectionStatus?.querySelector('.status-dot');
        if (statusDot?.classList.contains('checking')) {
            console.log('♾️ Retrying connection status check...');
            updateConnectionStatus();
        }
    }, 5000);
});

// Global functions for HTML onclick events
function sendMessage() {
    if (window.chat) {
        window.chat.sendMessage();
    }
}

function sendQuickMessage(text) {
    if (window.chat) {
        window.chat.sendQuickMessage(text);
    }
}

// Connection status updates
function updateConnectionStatus() {
    console.log('🔍 Running global connection status check...');
    
    const connectionStatus = document.getElementById('connection-status');
    const aiStatus = document.getElementById('ai-status');
    const dbStatus = document.getElementById('db-status');
    
    // Check API connection first
    fetch('/api/chat/suggestions')
        .then(response => {
            console.log('✅ API response:', response.status);
            if (response.ok) {
                if (connectionStatus) {
                    connectionStatus.querySelector('.status-dot').classList.remove('checking');
                    connectionStatus.querySelector('.status-dot').classList.add('active');
                    connectionStatus.querySelector('span').textContent = 'Connected';
                }
                
                // Test AI functionality
                return fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: 'status check', session_id: 'global-check' })
                });
            } else {
                throw new Error('API not responding');
            }
        })
        .then(response => {
            if (response && response.ok) {
                return response.json();
            } else {
                throw new Error('AI test failed');
            }
        })
        .then(data => {
            console.log('✅ AI test response:', data);
            if (aiStatus) {
                aiStatus.querySelector('.status-dot').classList.remove('checking');
                aiStatus.querySelector('.status-dot').classList.add('active');
                aiStatus.querySelector('span').textContent = 'AI Ready';
            }
            if (dbStatus) {
                dbStatus.querySelector('.status-dot').classList.remove('checking');
                dbStatus.querySelector('.status-dot').classList.add('active');
                dbStatus.querySelector('span').textContent = 'Database OK';
            }
        })
        .catch(error => {
            console.error('❌ Connection check failed:', error);
            
            if (connectionStatus) {
                connectionStatus.querySelector('.status-dot').classList.remove('checking', 'active');
                connectionStatus.querySelector('span').textContent = 'Disconnected';
            }
            if (aiStatus) {
                aiStatus.querySelector('.status-dot').classList.remove('checking', 'active');
                aiStatus.querySelector('span').textContent = 'AI Offline';
            }
            if (dbStatus) {
                dbStatus.querySelector('.status-dot').classList.remove('checking', 'active');
                dbStatus.querySelector('span').textContent = 'Database Offline';
            }
        });
}

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CricVerseAI3D, ChatInterface };
}