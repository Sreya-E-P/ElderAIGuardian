import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider,
  Chip,
  CircularProgress,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Send as SendIcon,
  Mic as MicIcon,
  AttachFile as AttachFileIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Warning as WarningIcon,
  LocalPharmacy as PharmacyIcon,
  Favorite as HeartIcon,
  Spa as WellnessIcon,
  Memory as MemoryIcon,
  Hub as HubIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation } from 'react-query';
import { useAuthStore } from '../stores/authStore';
import { useWebSocket } from '../contexts/WebSocketContext';
import api from '../services/api';
import { format } from 'date-fns';

const Chat = () => {
  const { user } = useAuthStore();
  const {
    sendChat,
    lastMessage,
    isConnected,
    heroTechnologies,
    getMCPTools,
    mcpTools
  } = useWebSocket();

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const hasRequestedTools = useRef(false);

  // Fetch chat history
  const { data: history, isLoading, refetch } = useQuery(
    ['chatHistory', sessionId],
    async () => {
      if (!sessionId) return [];
      try {
        const response = await api.get(`/chat/history/${sessionId}`);
        return response.data;
      } catch (error) {
        console.error('Failed to fetch history:', error);
        return [];
      }
    },
    {
      enabled: !!sessionId,
      retry: 2,
      retryDelay: 1000,
    }
  );

  // Send message mutation (REST fallback)
  const sendMessageMutation = useMutation(
    async (content) => {
      try {
        const response = await api.post('/chat/', {
          message: content,
          userId: user?.id || 'dev_user',
          sessionId: sessionId,
        });
        return response.data;
      } catch (error) {
        console.error('Chat API error:', error);
        throw error;
      }
    },
    {
      onMutate: () => {
        setIsTyping(true);
      },
      onSuccess: (data) => {
        setMessages((prev) => [
          ...prev,
          {
            id: data.request_id || Date.now().toString(),
            role: 'assistant',
            content: data.response || 'I understand.',
            timestamp: data.timestamp || new Date().toISOString(),
            intent: data.intent,
            confidence: data.confidence,
            agent: data.agent,
            data: data.data,
          },
        ]);
        setIsTyping(false);
      },
      onError: (error) => {
        console.error('Failed to send message:', error);
        setIsTyping(false);
        setMessages((prev) => [
          ...prev,
          {
            id: `error_${Date.now()}`,
            role: 'system',
            content: 'Sorry, I encountered an error. Please try again.',
            timestamp: new Date().toISOString(),
          },
        ]);
      },
    }
  );

  // Initialize session
  useEffect(() => {
    const newSessionId = localStorage.getItem('chatSessionId') ||
      `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('chatSessionId', newSessionId);
    setSessionId(newSessionId);
  }, []);

  // Request MCP tools when connected
  useEffect(() => {
    if (isConnected && !hasRequestedTools.current) {
      console.log('🛠️ Requesting MCP tools...');
      getMCPTools();
      hasRequestedTools.current = true;
    }
  }, [isConnected, getMCPTools]);

  // Load history
  useEffect(() => {
    if (history && history.length > 0) {
      setMessages(history);
    } else {
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: "Hello! I'm your Elder AI Guardian. How can I help you today?",
          timestamp: new Date().toISOString(),
          intent: 'greeting',
        },
      ]);
    }
  }, [history]);

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        if (lastMessage.type === 'chat_response') {
          // FIXED: backend sends {type, data: {response, agent, ...}, timestamp}
          const chatData = lastMessage.data || {};
          setMessages((prev) => [
            ...prev,
            {
              id: chatData.request_id || Date.now().toString(),
              role: 'assistant',
              content: chatData.response || chatData.message || 'I received your message.',
              timestamp: lastMessage.timestamp,
              intent: chatData.intent,
              confidence: chatData.confidence,
              agent: chatData.agent,
              data: chatData.data,
            },
          ]);
          setIsTyping(false);
        } else if (lastMessage.type === 'typing') {
          setIsTyping(true);
          setTimeout(() => setIsTyping(false), 3000);
        } else if (lastMessage.type === 'error') {
          console.error('WebSocket error:', lastMessage.error);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);

    if (isConnected) {
      sendChat(input, sessionId);
    } else {
      sendMessageMutation.mutate(input);
    }

    setInput('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      console.log('File selected:', file.name);
    }
  };

  const getAgentIcon = (agent) => {
    switch (agent) {
      case 'scam_agent':
        return <WarningIcon color="error" />;
      case 'medication_agent':
        return <PharmacyIcon color="success" />;
      case 'emergency_agent':
        return <WarningIcon color="error" />;
      case 'wellness_agent':
        return <WellnessIcon color="info" />;
      case 'supervisor':
        return <HubIcon color="primary" />;
      default:
        return <BotIcon color="primary" />;
    }
  };

  const getIntentColor = (intent) => {
    switch (intent) {
      case 'emergency':
        return 'error';
      case 'scam_detection':
        return 'warning';
      case 'medication':
        return 'success';
      case 'wellness':
        return 'info';
      default:
        return 'default';
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ height: 'calc(100vh - 180px)', display: 'flex', flexDirection: 'column' }}>
      {/* Hero Technologies Banner */}
      <Paper
        sx={{
          p: 1,
          mb: 2,
          bgcolor: 'primary.dark',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Typography variant="caption" sx={{ opacity: 0.9 }}>
            Hero Technologies:
          </Typography>
          {heroTechnologies?.foundry && (
            <Tooltip title="Microsoft Foundry Active">
              <Chip
                icon={<MemoryIcon />}
                label="Foundry"
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
            </Tooltip>
          )}
          {heroTechnologies?.mcp && (
            <Tooltip title="Azure MCP Active">
              <Chip
                icon={<HubIcon />}
                label="MCP"
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
            </Tooltip>
          )}
          {heroTechnologies?.agent_framework && (
            <Tooltip title="Microsoft Agent Framework Active">
              <Chip
                icon={<SettingsIcon />}
                label="Agent Framework"
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
            </Tooltip>
          )}
          {heroTechnologies?.devops && (
            <Tooltip title="Agentic DevOps Active">
              <Chip
                icon={<MemoryIcon />}
                label="DevOps"
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
            </Tooltip>
          )}
          {isConnected ? (
            <Chip
              label="WebSocket Connected"
              size="small"
              color="success"
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
            />
          ) : (
            <Chip
              label="WebSocket Disconnected"
              size="small"
              color="error"
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
            />
          )}
        </Box>
        <Box>
          <Typography variant="caption">
            MCP Tools: {mcpTools?.length || 0} available
          </Typography>
        </Box>
      </Paper>

      {/* Connection Status */}
      {!isConnected && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Using REST API (WebSocket disconnected). Real-time features limited.
        </Alert>
      )}

      {/* Messages */}
      <Paper
        sx={{
          flex: 1,
          overflow: 'auto',
          mb: 2,
          p: 2,
          bgcolor: 'grey.50',
        }}
      >
        <List>
          {messages.map((message, index) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <ListItem
                sx={{
                  flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                  alignItems: 'flex-start',
                }}
              >
                <ListItemAvatar>
                  <Avatar
                    sx={{
                      bgcolor: message.role === 'user' ? 'primary.main' :
                               message.role === 'system' ? 'grey.500' : 'secondary.main',
                    }}
                  >
                    {message.role === 'user' ? <PersonIcon /> :
                     message.role === 'system' ? <MemoryIcon /> : getAgentIcon(message.agent)}
                  </Avatar>
                </ListItemAvatar>
                {/* FIX: component="div" prevents <p> nesting violations */}
                <ListItemText
                  primaryTypographyProps={{ component: 'div' }}
                  secondaryTypographyProps={{ component: 'div' }}
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5, flexWrap: 'wrap' }}>
                      <Typography variant="subtitle2" component="span">
                        {message.role === 'user' ? 'You' :
                         message.role === 'system' ? 'System' :
                         message.agent ? `${message.agent.replace('_', ' ')} Agent` : 'AI Assistant'}
                      </Typography>
                      {message.intent && message.intent !== 'error' && (
                        <Chip
                          label={message.intent.replace('_', ' ')}
                          size="small"
                          color={getIntentColor(message.intent)}
                          variant="outlined"
                        />
                      )}
                      {message.confidence && (
                        <Chip
                          label={`${Math.round(message.confidence * 100)}% confidence`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                      <Typography variant="caption" color="text.secondary" component="span">
                        {format(new Date(message.timestamp), 'hh:mm a')}
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Box
                      sx={{
                        p: 2,
                        bgcolor: message.role === 'user' ? 'primary.light' :
                                message.role === 'system' ? 'grey.100' : 'background.paper',
                        color: message.role === 'user' ? 'white' : 'text.primary',
                        maxWidth: '80%',
                        display: 'inline-block',
                        borderRadius: 1,
                        boxShadow: 1,
                      }}
                    >
                      <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                        {message.content}
                      </Typography>
                      {message.data && Object.keys(message.data).length > 0 && message.intent === 'medication' && (
                        <Box sx={{ mt: 1, pt: 1, borderTop: 1, borderColor: 'divider' }}>
                          <Typography variant="caption" color="text.secondary">
                            {message.data.medication_name && `Medication: ${message.data.medication_name}`}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  }
                />
              </ListItem>
              <Divider variant="inset" component="li" />
            </motion.div>
          ))}

          {/* Typing Indicator */}
          <AnimatePresence>
            {isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <ListItem>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: 'secondary.main' }}>
                      <BotIcon />
                    </Avatar>
                  </ListItemAvatar>
                  {/* FIX: component="div" prevents <p> nesting violations */}
                  <ListItemText
                    primaryTypographyProps={{ component: 'div' }}
                    secondaryTypographyProps={{ component: 'div' }}
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle2" component="span">AI Assistant</Typography>
                        <Typography variant="caption" color="text.secondary" component="span">
                          typing...
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 1 }}>
                        <CircularProgress size={16} />
                        <CircularProgress size={16} sx={{ animationDelay: '0.2s' }} />
                        <CircularProgress size={16} sx={{ animationDelay: '0.4s' }} />
                      </Box>
                    }
                  />
                </ListItem>
              </motion.div>
            )}
          </AnimatePresence>

          <div ref={messagesEndRef} />
        </List>
      </Paper>

      {/* Input */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton
            color="primary"
            onClick={() => fileInputRef.current?.click()}
          >
            <AttachFileIcon />
          </IconButton>
          <IconButton color="primary">
            <MicIcon />
          </IconButton>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            variant="outlined"
            size="small"
          />
          <IconButton
            color="primary"
            onClick={handleSend}
            disabled={!input.trim() || sendMessageMutation.isLoading}
          >
            {sendMessageMutation.isLoading ? (
              <CircularProgress size={24} />
            ) : (
              <SendIcon />
            )}
          </IconButton>
        </Box>
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileUpload}
        />

        {/* MCP Tools Status */}
        {mcpTools && mcpTools.length > 0 && (
          <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            <Typography variant="caption" color="text.secondary">
              MCP Tools:
            </Typography>
            {mcpTools.map((tool) => (
              <Chip
                key={tool}
                label={tool.replace(/_/g, ' ')}
                size="small"
                variant="outlined"
                sx={{ height: 20, fontSize: '0.7rem' }}
              />
            ))}
          </Box>
        )}

        {(!mcpTools || mcpTools.length === 0) && isConnected && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Requesting MCP tools...
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default Chat;