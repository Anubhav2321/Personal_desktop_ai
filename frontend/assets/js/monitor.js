// ==========================================
// 📊 ARIS SYSTEM MONITOR
// Real-time system stats polling and display
// ==========================================

const SystemMonitor = {
    pollInterval: 30000, // 30 seconds (was 5s — caused CPU overload)
    timer: null,
    lastStats: null,
    isPaused: false,

    async init() {
        // Initial fetch
        await this.fetchAndRender();
        // Start polling
        this.startPolling();

        // Pause polling when tab is hidden, resume when visible
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pause();
            } else {
                this.resume();
            }
        });
    },

    startPolling() {
        if (this.timer) clearInterval(this.timer);
        this.timer = setInterval(() => this.fetchAndRender(), this.pollInterval);
        this.isPaused = false;
    },

    pause() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        this.isPaused = true;
    },

    resume() {
        if (this.isPaused) {
            // Fetch immediately on resume, then restart interval
            this.fetchAndRender();
            this.startPolling();
        }
    },

    async fetchAndRender() {
        try {
            const response = await fetch('/api/system/stats');
            const data = await response.json();

            if (data.status === 'ok') {
                this.lastStats = data.stats;
                this.renderStats(data.stats);
            }
        } catch (error) {
            // Silently fail — don't spam console during initial setup
            this.renderOffline();
        }
    },

    renderStats(stats) {
        const container = document.getElementById('sys-monitor-live');
        if (!container) return;

        // CPU status class
        const cpuClass = stats.cpu_percent > 85 ? 'critical' : stats.cpu_percent > 60 ? 'warning' : '';
        // RAM status class
        const ramClass = stats.ram_percent > 85 ? 'critical' : stats.ram_percent > 60 ? 'warning' : '';
        // Disk status class
        const diskClass = stats.disk_percent > 90 ? 'critical' : stats.disk_percent > 75 ? 'warning' : '';

        // Battery
        let batteryHtml = '';
        if (stats.battery_percent !== null) {
            const battFillClass = stats.battery_percent <= 15 ? 'low' : stats.battery_percent <= 35 ? 'medium' : '';
            const chargingIcon = stats.battery_charging ? '<span class="charging-icon" style="color: #10b981;">⚡</span>' : '';
            const battStatus = stats.battery_charging ? 'CHARGING' : (stats.battery_time_left || 'ON BATTERY');
            
            batteryHtml = `
                <div class="battery-indicator">
                    <div class="battery-icon">
                        <div class="battery-fill ${battFillClass}" style="width: ${stats.battery_percent}%"></div>
                    </div>
                    <div class="battery-info">
                        <div class="battery-percent" style="color: ${stats.battery_percent <= 15 ? '#ef4444' : stats.battery_percent <= 35 ? '#f59e0b' : '#10b981'}">
                            ${stats.battery_percent}% ${chargingIcon}
                        </div>
                        <div class="battery-status">${battStatus}</div>
                    </div>
                </div>
            `;
        }

        container.innerHTML = `
            ${batteryHtml}
            <div class="stat-item">
                <span class="stat-label">CPU</span>
                <span class="stat-value ${cpuClass}">${stats.cpu_percent}%</span>
                <div class="stat-bar">
                    <div class="stat-bar-fill ${cpuClass}" style="width: ${stats.cpu_percent}%"></div>
                </div>
            </div>
            <div class="stat-item">
                <span class="stat-label">RAM</span>
                <span class="stat-value ${ramClass}">${stats.ram_used_gb}/${stats.ram_total_gb}GB</span>
                <div class="stat-bar">
                    <div class="stat-bar-fill ${ramClass}" style="width: ${stats.ram_percent}%"></div>
                </div>
            </div>
            <div class="stat-item">
                <span class="stat-label">DISK</span>
                <span class="stat-value ${diskClass}">${stats.disk_percent}%</span>
                <div class="stat-bar">
                    <div class="stat-bar-fill ${diskClass}" style="width: ${stats.disk_percent}%"></div>
                </div>
            </div>
            <div class="stat-item">
                <span class="stat-label">HOST</span>
                <span class="stat-value" style="font-size: 0.68rem; color: var(--text-main);">${stats.hostname || 'N/A'}</span>
            </div>
        `;
    },

    renderOffline() {
        const container = document.getElementById('sys-monitor-live');
        if (!container) return;

        container.innerHTML = `
            <div class="stat-item" style="grid-column: 1/-1;">
                <span class="stat-label">STATUS</span>
                <span class="stat-value" style="color: var(--text-muted); font-size: 0.72rem;">
                    <span class="network-indicator">
                        <span class="network-dot" style="background: #ef4444;"></span>
                    </span>
                    OFFLINE — Backend not connected
                </span>
            </div>
        `;
    },

    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
};

// Initialize on page load
window.addEventListener('load', () => {
    // Delay slightly so boot sequence finishes first
    setTimeout(() => SystemMonitor.init(), 3500);
});

// Expose globally
window.SystemMonitor = SystemMonitor;
