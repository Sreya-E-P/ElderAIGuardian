import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { useAuthStore } from '../stores/authStore';

const WebSocketContext = createContext(undefined);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionId, setConnectionId] = useState(null);
  const [heroTechnologies, setHeroTechnologies] = useState({});
  const [mcpTools, setMcpTools] = useState([]);
  const { user, token } = useAuthStore();

  // Use refs instead of state for socket to avoid re-render loops
  const socketRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectTimeout = useRef(null);
  const pingInterval = useRef(null);
  const onPendingAlertRef = useRef(null);
  const hasRequestedTools = useRef(false);
  const isConnecting = useRef(false);
  const userRef = useRef(user);
  const tokenRef = useRef(token);

  // Keep refs in sync
  useEffect(() => {
    userRef.current = user;
    tokenRef.current = token;
  }, [user, token]);

  const connect = useCallback(() => {
    if (!userRef.current || !userRef.current.id) return;
    if (isConnecting.current) return;
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) return;

    isConnecting.current = true;

    try {
      const wsUrl = `ws://127.0.0.1:8000/ws/${userRef.current.id}`;
      console.log('🔌 Connecting to WebSocket:', wsUrl);

      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        isConnecting.current = false;
        setIsConnected(true);
        reconnectAttempts.current = 0;
        hasRequestedTools.current = false;

        // Send authentication
        ws.send(JSON.stringify({
          type: 'auth',
          token: tokenRef.current,
          userId: userRef.current.id,
        }));

        // Request MCP tools after connection
        setTimeout(() => {
          if (ws.readyState === WebSocket.OPEN && !hasRequestedTools.current) {
            console.log('🛠️ Requesting MCP tools...');
            ws.send(JSON.stringify({ type: 'mcp_tools' }));
            hasRequestedTools.current = true;
          }
        }, 500);

        // Start ping interval
        if (pingInterval.current) clearInterval(pingInterval.current);
        pingInterval.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📩 WebSocket message:', data.type);
          setLastMessage(data);

          if (data.type === 'connected') {
            setConnectionId(data.connection_id);
            setHeroTechnologies(data.hero_technologies || {});
            console.log('✅ Connected with hero technologies:', data.hero_technologies);
          }

          if (data.type === 'mcp_tools') {
            console.log('🛠️ Received MCP tools:', data.data);
            setMcpTools(data.data?.tools || []);
          }

          if (data.type === 'metrics') {
            console.log('📊 Metrics update:', data.data);
          }

          if (data.type === 'pending_alert') {
            console.log('🔔 Received pending alert:', data);
            if (onPendingAlertRef.current) {
              onPendingAlertRef.current(data);
            }
            if (Notification.permission === 'granted') {
              new Notification('🔔 New Alert', {
                body: data.data?.message || 'New alert for your loved one',
                icon: '/favicon.ico'
              });
            }
          }

          if (data.type === 'live_alert') {
            console.log('⚠️ Live alert:', data);
            if (data.data?.severity === 'CRITICAL' || data.data?.severity === 'HIGH') {
              if (Notification.permission === 'granted') {
                new Notification(`⚠️ ${data.data.title || 'Emergency Alert'}`, {
                  body: data.data.message || 'Immediate attention required',
                  icon: '/favicon.ico',
                  requireInteraction: true
                });
              }
            }
          }
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('🔌 WebSocket disconnected', event.reason);
        isConnecting.current = false;
        setIsConnected(false);
        setConnectionId(null);
        setMcpTools([]);
        hasRequestedTools.current = false;
        socketRef.current = null;

        if (pingInterval.current) {
          clearInterval(pingInterval.current);
          pingInterval.current = null;
        }

        // Only reconnect if not intentionally closed
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`🔄 Reconnecting... Attempt ${reconnectAttempts.current} in ${delay}ms`);

          reconnectTimeout.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        isConnecting.current = false;
      };

    } catch (error) {
      console.error('❌ Failed to connect WebSocket:', error);
      isConnecting.current = false;
    }
  }, []); // ← EMPTY deps array - connect never recreates

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    if (pingInterval.current) {
      clearInterval(pingInterval.current);
      pingInterval.current = null;
    }
    reconnectAttempts.current = maxReconnectAttempts; // prevent auto-reconnect

    if (socketRef.current) {
      socketRef.current.close(1000, 'Client disconnecting');
      socketRef.current = null;
    }

    isConnecting.current = false;
    setIsConnected(false);
    setConnectionId(null);
    setMcpTools([]);
    hasRequestedTools.current = false;
  }, []); // ← EMPTY deps array - disconnect never recreates

  const sendMessage = useCallback((type, data = {}) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type,
        ...data,
        timestamp: new Date().toISOString()
      }));
    } else {
      console.warn('⚠️ WebSocket not connected');
    }
  }, []);

  const sendChat = useCallback((content, sessionId, metadata = {}) => {
    sendMessage('chat', { content, sessionId, metadata });
  }, [sendMessage]);

  const sendEmergency = useCallback((message, location) => {
    sendMessage('emergency', { message, location });
  }, [sendMessage]);

  const sendSensorData = useCallback((sensorData, location) => {
    sendMessage('sensor_data', { sensor_data: sensorData, location });
  }, [sendMessage]);

  const getMCPTools = useCallback(() => {
    sendMessage('mcp_tools', {});
  }, [sendMessage]);

  const getMetrics = useCallback(() => {
    sendMessage('get_metrics', {});
  }, [sendMessage]);

  const subscribeToAlerts = useCallback((userId) => {
    sendMessage('subscribe_alerts', { user_id: userId });
  }, [sendMessage]);

  const unsubscribeFromAlerts = useCallback(() => {
    sendMessage('unsubscribe_alerts', {});
  }, [sendMessage]);

  const sendTestAlert = useCallback((alertData = {}) => {
    sendMessage('test_alert', alertData);
  }, [sendMessage]);

  const onPendingAlert = useCallback((callback) => {
    onPendingAlertRef.current = callback;
  }, []);

  // Request notification permission
  useEffect(() => {
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  // Connect only when user/token become available - NOT when connect/disconnect change
  useEffect(() => {
    if (user && user.id && token) {
      // Small delay to avoid React strict mode double-invoke
      const timer = setTimeout(() => {
        connect();
      }, 100);
      return () => clearTimeout(timer);
    }
    return () => {
      disconnect();
    };
  }, [user?.id, token]); // ← Only user.id and token - NOT connect/disconnect

  const value = {
    isConnected,
    lastMessage,
    connectionId,
    heroTechnologies,
    mcpTools,
    sendMessage,
    sendChat,
    sendEmergency,
    sendSensorData,
    getMCPTools,
    getMetrics,
    connect,
    disconnect,
    subscribeToAlerts,
    unsubscribeFromAlerts,
    sendTestAlert,
    onPendingAlert,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};