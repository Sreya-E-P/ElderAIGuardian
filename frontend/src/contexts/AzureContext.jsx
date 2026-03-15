import React, { createContext, useContext, useState } from 'react';
import { useAuthStore } from '../stores/authStore';

const AzureContext = createContext(undefined);

export const useAzure = () => {
  const context = useContext(AzureContext);
  if (!context) {
    throw new Error('useAzure must be used within an AzureProvider');
  }
  return context;
};

export const AzureProvider = ({ children }) => {
  const [chatClient] = useState(null);
  const [callClient] = useState(null);
  const [userToken] = useState(null);
  const [userId] = useState(null);
  const [isInitialized] = useState(false);

  // ACS not configured - using WebSocket for real-time communication instead
  // Removing the /azure/acs/token call that was causing 30-second timeouts

  const createChatThread = async () => null;
  const joinChatThread = async () => null;
  const startCall = async () => null;

  const value = {
    chatClient,
    callClient,
    userToken,
    userId,
    isInitialized,
    createChatThread,
    joinChatThread,
    startCall,
  };

  return (
    <AzureContext.Provider value={value}>
      {children}
    </AzureContext.Provider>
  );
};