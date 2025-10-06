// Frame rate throttling script to reduce CPU usage on trading charts
// This limits animations to ~30fps instead of 60fps

(function() {
    'use strict';
    
    // Only throttle if not already throttled
    if (window._fpsThrottled) return;
    window._fpsThrottled = true;
    
    // Store original requestAnimationFrame
    const originalRAF = window.requestAnimationFrame;
    
    // Throttle to ~30fps (33ms per frame)
    const FPS_LIMIT = 30;
    const FRAME_DURATION = 1000 / FPS_LIMIT;
    let lastFrameTime = 0;
    
    // Override requestAnimationFrame
    window.requestAnimationFrame = function(callback) {
        const now = Date.now();
        const timeSinceLastFrame = now - lastFrameTime;
        
        if (timeSinceLastFrame >= FRAME_DURATION) {
            lastFrameTime = now;
            return originalRAF.call(window, callback);
        } else {
            // Schedule for next available frame
            return setTimeout(() => {
                lastFrameTime = Date.now();
                callback(lastFrameTime);
            }, FRAME_DURATION - timeSinceLastFrame);
        }
    };
    
    // Also throttle CSS animations
    const style = document.createElement('style');
    style.textContent = `
        * {
            animation-duration: calc(var(--original-duration, 1s) * 2) !important;
            transition-duration: calc(var(--original-duration, 0.3s) * 2) !important;
        }
    `;
    document.head.appendChild(style);
    
    console.log('FPS throttling enabled - limited to 30fps for CPU optimization');
})();