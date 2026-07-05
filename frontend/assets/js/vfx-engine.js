// ==========================================
// 🎬 ARIS VFX ENGINE — JavaScript
// Particle system, parallax, sound FX,
// boot sequence, cursor effects, and more.
// ==========================================

const VFX = {
    // ==========================================
    // ⚡ BOOT SEQUENCE
    // ==========================================
    bootMessages: [
        "Initializing quantum neural network...",
        "Loading ARIS Core v2.0...",
        "Establishing secure data channels...",
        "Calibrating voice synthesis engine...",
        "Mounting system control interface...",
        "Scanning hardware diagnostics...",
        "Activating holographic HUD...",
        "System ready. Welcome, Anubhav."
    ],

    async runBootSequence() {
        const overlay = document.getElementById('boot-overlay');
        const statusEl = document.getElementById('boot-status');
        if (!overlay || !statusEl) return;

        // Play boot sound
        VFX.playSound('boot');

        // Cycle through boot messages
        for (let i = 0; i < this.bootMessages.length; i++) {
            statusEl.textContent = this.bootMessages[i];
            statusEl.style.opacity = '0';
            statusEl.style.transform = 'translateY(5px)';
            
            // Animate in
            await this.sleep(50);
            statusEl.style.transition = 'all 0.3s ease';
            statusEl.style.opacity = '1';
            statusEl.style.transform = 'translateY(0)';
            
            await this.sleep(300);
        }

        // Fade out overlay
        await this.sleep(400);
        overlay.classList.add('fade-out');
        
        // Remove overlay after transition
        await this.sleep(800);
        overlay.style.display = 'none';
    },

    // ==========================================
    // 🌌 PARTICLE SYSTEM (Canvas)
    // ==========================================
    particles: [],
    mouseX: 0,
    mouseY: 0,
    animationRunning: true,

    initParticles() {
        const canvas = document.getElementById('particle-canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        // Create particles
        const particleCount = Math.min(40, Math.floor(window.innerWidth / 40));
        for (let i = 0; i < particleCount; i++) {
            this.particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                radius: Math.random() * 1.5 + 0.5,
                opacity: Math.random() * 0.4 + 0.1,
                hue: Math.random() > 0.7 ? 270 : 190, // Mix of cyan and purple
            });
        }

        // Track mouse
        document.addEventListener('mousemove', (e) => {
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;
        });

        // Handle resize
        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });

        // Pause/resume animation when tab visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.animationRunning = false;
            } else {
                this.animationRunning = true;
                animate();
            }
        });

        // Animation loop
        const animate = () => {
            if (!this.animationRunning) return; // Stop loop when hidden

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            this.particles.forEach((p, i) => {
                // Mouse interaction — gentle push
                const dx = this.mouseX - p.x;
                const dy = this.mouseY - p.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 120) {
                    const force = (120 - dist) / 120;
                    p.vx -= (dx / dist) * force * 0.02;
                    p.vy -= (dy / dist) * force * 0.02;
                }

                // Update position
                p.x += p.vx;
                p.y += p.vy;

                // Damping
                p.vx *= 0.99;
                p.vy *= 0.99;

                // Wrap around edges
                if (p.x < 0) p.x = canvas.width;
                if (p.x > canvas.width) p.x = 0;
                if (p.y < 0) p.y = canvas.height;
                if (p.y > canvas.height) p.y = 0;

                // Draw particle
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = `hsla(${p.hue}, 100%, 70%, ${p.opacity})`;
                ctx.fill();

                // Draw connections (reduced distance for performance)
                for (let j = i + 1; j < this.particles.length; j++) {
                    const p2 = this.particles[j];
                    const d = Math.sqrt(
                        (p.x - p2.x) ** 2 + (p.y - p2.y) ** 2
                    );
                    if (d < 70) {
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.strokeStyle = `hsla(190, 100%, 70%, ${0.06 * (1 - d / 70)})`;
                        ctx.lineWidth = 0.5;
                        ctx.stroke();
                    }
                }
            });

            requestAnimationFrame(animate);
        };
        animate();
    },

    // ==========================================
    // 🖱️ CUSTOM CURSOR
    // ==========================================
    initCursor() {
        // Don't init on touch devices
        if ('ontouchstart' in window) return;

        const dot = document.createElement('div');
        dot.className = 'cursor-dot';
        const ring = document.createElement('div');
        ring.className = 'cursor-ring';
        document.body.appendChild(dot);
        document.body.appendChild(ring);

        let curX = 0, curY = 0;
        let ringX = 0, ringY = 0;

        document.addEventListener('mousemove', (e) => {
            curX = e.clientX;
            curY = e.clientY;
            dot.style.left = curX - 3 + 'px';
            dot.style.top = curY - 3 + 'px';
        });

        // Smooth ring follow
        const followRing = () => {
            ringX += (curX - ringX) * 0.12;
            ringY += (curY - ringY) * 0.12;
            ring.style.left = ringX - 15 + 'px';
            ring.style.top = ringY - 15 + 'px';
            requestAnimationFrame(followRing);
        };
        followRing();

        // Hover effect on interactive elements
        document.querySelectorAll('button, a, input, .chat-session-card, .snippet-card, .new-chat-button').forEach(el => {
            el.addEventListener('mouseenter', () => ring.classList.add('hover'));
            el.addEventListener('mouseleave', () => ring.classList.remove('hover'));
        });
    },

    // ==========================================
    // 🌈 DATA STREAMS (Matrix Effect)
    // ==========================================
    initDataStreams() {
        const container = document.createElement('div');
        container.className = 'data-stream-container';
        document.body.appendChild(container);

        const chars = '01アイウエオカキクケコ>_{}[]=/\\<>';
        const streamCount = Math.floor(window.innerWidth / 120);

        for (let i = 0; i < streamCount; i++) {
            const stream = document.createElement('div');
            stream.className = 'data-stream';
            stream.style.left = (Math.random() * 100) + '%';
            stream.style.animationDuration = (8 + Math.random() * 15) + 's';
            stream.style.animationDelay = (Math.random() * 10) + 's';
            stream.style.fontSize = (8 + Math.random() * 4) + 'px';

            let text = '';
            const len = 10 + Math.floor(Math.random() * 20);
            for (let j = 0; j < len; j++) {
                text += chars[Math.floor(Math.random() * chars.length)] + '\n';
            }
            stream.textContent = text;
            container.appendChild(stream);
        }
    },

    // ==========================================
    // 🔊 SOUND EFFECTS ENGINE
    // ==========================================
    sounds: {},
    soundEnabled: true,
    brokenSounds: new Set(),  // Track sounds that failed to load

    initSounds() {
        // Store paths only — validate on first play
        this.soundPaths = {
            boot: './assets/sfx/boot.mp3',
            keystroke: './assets/sfx/keystroke.mp3',
            alarm: './assets/sfx/alarm.mp3',
        };

        // Pre-validate: fetch HEAD to check if files are usable
        Object.entries(this.soundPaths).forEach(([name, path]) => {
            fetch(path, { method: 'HEAD' }).then(res => {
                const size = parseInt(res.headers.get('content-length') || '0');
                if (!res.ok || size < 100) {
                    // File is missing, empty, or too small to be valid audio
                    this.brokenSounds.add(name);
                }
            }).catch(() => {
                this.brokenSounds.add(name);
            });
        });
    },

    playSound(name, volume = 0.2) {
        if (!this.soundEnabled) return;
        if (this.brokenSounds.has(name)) return; // Skip known broken files
        const path = this.soundPaths?.[name];
        if (!path) return;
        try {
            const audio = new Audio(path);
            audio.volume = volume;
            audio.play().catch(() => {
                // Mark as broken so we don't retry
                this.brokenSounds.add(name);
            });
        } catch (e) {
            this.brokenSounds.add(name);
        }
    },

    // ==========================================
    // 🎇 PARTICLE BURST EFFECT
    // ==========================================
    createBurst(x, y, color = '#00f3ff', count = 12) {
        const burst = document.createElement('div');
        burst.className = 'vfx-burst';
        burst.style.left = x + 'px';
        burst.style.top = y + 'px';
        document.body.appendChild(burst);

        for (let i = 0; i < count; i++) {
            const particle = document.createElement('div');
            particle.className = 'vfx-particle';
            particle.style.background = color;
            particle.style.boxShadow = `0 0 4px ${color}`;
            
            const angle = (i / count) * Math.PI * 2;
            const dist = 30 + Math.random() * 50;
            particle.style.setProperty('--px', Math.cos(angle) * dist + 'px');
            particle.style.setProperty('--py', Math.sin(angle) * dist + 'px');
            
            burst.appendChild(particle);
        }

        setTimeout(() => burst.remove(), 1000);
    },

    // ==========================================
    // 📢 TOAST NOTIFICATIONS
    // ==========================================
    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `aris-toast ${type}`;
        toast.innerHTML = `
            <div class="toast-title">${type === 'success' ? '✓ ACTION COMPLETE' : type === 'error' ? '✗ ERROR' : '◆ ARIS SYSTEM'}</div>
            <div>${message}</div>
        `;
        document.body.appendChild(toast);

        // Trigger animation
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                toast.classList.add('show');
            });
        });

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400);
        }, duration);
    },

    // ==========================================
    // 💥 SCREEN SHAKE
    // ==========================================
    screenShake() {
        document.body.classList.add('screen-shake');
        setTimeout(() => document.body.classList.remove('screen-shake'), 400);
    },

    // ==========================================
    // 🌊 RIPPLE EFFECT
    // ==========================================
    initRipples() {
        document.querySelectorAll('.new-chat-button, .voice-chat-btn, .chat-session-card').forEach(el => {
            el.classList.add('ripple-container');
            el.addEventListener('click', (e) => {
                const rect = el.getBoundingClientRect();
                const ripple = document.createElement('div');
                ripple.className = 'ripple';
                ripple.style.left = (e.clientX - rect.left) + 'px';
                ripple.style.top = (e.clientY - rect.top) + 'px';
                el.appendChild(ripple);
                setTimeout(() => ripple.remove(), 600);
            });
        });
    },

    // ==========================================
    // 🖥️ MOUSE PARALLAX
    // ==========================================
    initParallax() {
        document.addEventListener('mousemove', (e) => {
            const x = (e.clientX / window.innerWidth - 0.5) * 2;
            const y = (e.clientY / window.innerHeight - 0.5) * 2;

            // Shift background
            const bg = document.body;
            if (bg.style) {
                bg.style.setProperty('--parallax-x', x * 5 + 'px');
                bg.style.setProperty('--parallax-y', y * 5 + 'px');
            }
        });
    },

    // ==========================================
    // 🔧 UTILITIES
    // ==========================================
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    // ==========================================
    // 🚀 MASTER INIT
    // ==========================================
    async init() {
        // Initialize all VFX systems
        this.initSounds();
        this.initParticles();
        this.initDataStreams();
        this.initParallax();
        
        // Run boot sequence
        await this.runBootSequence();
        
        // Post-boot init (after panels are visible)
        setTimeout(() => {
            this.initCursor();
            this.initRipples();
        }, 500);
    }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    VFX.init();
});

// Expose VFX globally for other scripts
window.VFX = VFX;
