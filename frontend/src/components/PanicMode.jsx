import React, { useEffect, useState } from 'react';
import { useEmergencyStore } from '../stores/emergencyStore';
import { useWebSocket } from '../contexts/WebSocketContext';
import './PanicMode.css';

const PanicMode = ({ children }) => {
  const { activeEmergency, severity, setActiveEmergency } = useEmergencyStore();
  const { lastMessage } = useWebSocket();
  const [panicActive, setPanicActive] = useState(false);
  const [highContrast, setHighContrast] = useState(false);

  // Listen for emergency alerts via WebSocket
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'emergency_response') {
      const emergency = lastMessage.data;
      if (emergency && emergency.severity) {
        setActiveEmergency(emergency);
      }
    }
    
    if (lastMessage && lastMessage.type === 'live_alert') {
      const alert = lastMessage.data;
      if (alert && alert.severity === 'CRITICAL') {
        // Auto-activate panic mode for critical alerts
        setPanicActive(true);
      }
    }
  }, [lastMessage, setActiveEmergency]);

  // Check if panic mode should be active
  useEffect(() => {
    const isEmergencyActive = activeEmergency !== null;
    const isHighSeverity = severity === 'CRITICAL' || severity === 'HIGH';
    
    setPanicActive(isEmergencyActive && isHighSeverity);
    setHighContrast(isEmergencyActive);
    
  }, [activeEmergency, severity]);

  // Apply CSS classes when panic mode changes
  useEffect(() => {
    if (panicActive) {
      // Enable panic mode
      document.body.classList.add('panic-mode-active');
      document.body.classList.add('high-contrast');
      
      // Force large text on all interactive elements
      document.querySelectorAll('button, a, input, .MuiButton-root').forEach(el => {
        el.classList.add('panic-button');
      });
      
      // Disable non-essential animations for accessibility
      document.body.style.animation = 'none';
      
      console.log('🚨 Panic mode activated - high contrast, large buttons');
      
      // Announce for screen readers
      const announcement = document.createElement('div');
      announcement.setAttribute('role', 'alert');
      announcement.setAttribute('aria-live', 'assertive');
      announcement.className = 'sr-only';
      announcement.textContent = 'Emergency mode activated. High contrast display enabled.';
      document.body.appendChild(announcement);
      setTimeout(() => announcement.remove(), 3000);
      
    } else if (highContrast) {
      // Just high contrast mode (for non-emergency accessibility)
      document.body.classList.add('high-contrast');
      document.body.classList.remove('panic-mode-active');
    } else {
      // Normal mode
      document.body.classList.remove('panic-mode-active');
      document.body.classList.remove('high-contrast');
      
      document.querySelectorAll('button, a, input, .MuiButton-root').forEach(el => {
        el.classList.remove('panic-button');
      });
    }
    
    return () => {
      // Cleanup
      document.body.classList.remove('panic-mode-active');
      document.body.classList.remove('high-contrast');
    };
  }, [panicActive, highContrast]);

  return (
    <div className={`panic-mode-container ${panicActive ? 'panic-active' : ''}`}>
      {panicActive && (
        <div className="panic-overlay" role="alert" aria-live="assertive">
          <div className="panic-header">
            <h1 className="panic-title">🚨 EMERGENCY MODE ACTIVE</h1>
            <p className="panic-subtitle">Immediate attention required</p>
          </div>
          
          <div className="panic-status">
            <div className="status-indicator pulse"></div>
            <span className="status-text">{severity} SEVERITY</span>
          </div>
          
          {activeEmergency && (
            <div className="panic-details">
              <p><strong>Type:</strong> {activeEmergency.type}</p>
              <p><strong>Message:</strong> {activeEmergency.message}</p>
              <p><strong>Time:</strong> {new Date(activeEmergency.timestamp).toLocaleTimeString()}</p>
            </div>
          )}
        </div>
      )}
      
      {children}
      
      {panicActive && (
        <div className="panic-footer">
          <button 
            className="panic-button emergency-button" 
            onClick={() => window.location.href = '/emergency'}
            aria-label="View emergency details"
          >
            🚨 VIEW EMERGENCY
          </button>
          <button 
            className="panic-button safe-button" 
            onClick={() => window.location.href = '/emergency/resolve'}
            aria-label="I am safe - cancel emergency"
          >
            ✅ I AM SAFE
          </button>
          <button 
            className="panic-button call-button" 
            onClick={() => window.location.href = 'tel:911'}
            aria-label="Call 911 immediately"
          >
            📞 CALL 911
          </button>
        </div>
      )}
    </div>
  );
};

export default PanicMode;