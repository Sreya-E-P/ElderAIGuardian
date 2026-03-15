import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Avatar,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  Button,
  Alert,
} from '@mui/material';
import {
  Memory as MemoryIcon,
  Hub as HubIcon,
  Settings as SettingsIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
  Build as BuildIcon,
  Cloud as CloudIcon,
  SmartToy as AgentIcon,
  Security as SecurityIcon,
  AutoFixHigh as AutoHealIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useWebSocket } from '../contexts/WebSocketContext';

const techCards = [
  {
    id: 'foundry',
    title: 'Microsoft Foundry',
    icon: <MemoryIcon sx={{ fontSize: 40 }} />,
    color: '#0078d4',
    description: 'AI project hub powering Elder AI Guardian with GPT-4o model deployment, embeddings, and intelligent model routing.',
    features: [
      'GPT-4o deployment via Azure AI Foundry',
      'Dynamic Model Router — routes tasks by type (emergency, scam, wellness)',
      'text-embedding-ada-002 for semantic search',
      'Temperature tuning per agent (0.1 for emergency → 0.8 for conversation)',
    ],
    status: 'Active',
  },
  {
    id: 'mcp',
    title: 'Azure MCP',
    icon: <HubIcon sx={{ fontSize: 40 }} />,
    color: '#107c10',
    description: 'Model Context Protocol integration enabling agents to call real Azure services as tools during conversations.',
    features: [
      'Real-time tool discovery via WebSocket',
      'Cosmos DB read/write as MCP tool',
      'Azure Communication Services (SMS/voice) as MCP tool',
      'Agent-to-Azure service bridge with context preservation',
    ],
    status: 'Active',
  },
  {
    id: 'agent_framework',
    title: 'Microsoft Agent Framework',
    icon: <AgentIcon sx={{ fontSize: 40 }} />,
    color: '#5c2d91',
    description: 'Semantic Kernel-powered multi-agent system with a Supervisor orchestrating 6 specialized agents.',
    features: [
      'SupervisorAgent — intent detection & routing',
      'ScamDetectionAgent — real-time scam analysis',
      'EmergencyAgent — SOS + Azure Communication Services',
      'MedicationAgent, WellnessAgent, FamilyNotificationAgent',
    ],
    status: 'Active',
  },
  {
    id: 'devops',
    title: 'Agentic DevOps',
    icon: <AutoHealIcon sx={{ fontSize: 40 }} />,
    color: '#d83b01',
    description: 'Self-healing DevOps agent monitors system health and automatically remediates unhealthy components.',
    features: [
      'Real-time health monitoring of all agents & services',
      'Auto-heal triggers when components go unhealthy',
      'GitHub Copilot Agent Mode for code generation',
      'Uptime, request count, WebSocket metrics dashboard',
    ],
    status: 'Active',
  },
];

const agentFlow = [
  { from: 'User Message', to: 'SupervisorAgent', description: 'Intent detection' },
  { from: 'SupervisorAgent', to: 'ModelRouter', description: 'Route by task type' },
  { from: 'ModelRouter', to: 'Specialist Agent', description: 'Scam / Emergency / Wellness' },
  { from: 'Specialist Agent', to: 'MCP Tools', description: 'Call Azure services' },
  { from: 'MCP Tools', to: 'Cosmos DB / SMS', description: 'Persist & notify' },
  { from: 'Cosmos DB / SMS', to: 'User Response', description: 'Streamed via WebSocket' },
];

const HeroShowcase = () => {
  const { isConnected, heroTechnologies, mcpTools } = useWebSocket();
  const [activeCard, setActiveCard] = useState(null);

  return (
    <Box sx={{ flexGrow: 1, pb: 4 }}>
      {/* Header */}
      <Paper
        sx={{
          p: 3,
          mb: 3,
          background: 'linear-gradient(135deg, #0078d4 0%, #5c2d91 100%)',
          color: 'white',
        }}
      >
        <Typography variant="h4" gutterBottom fontWeight="bold">
          🚀 Microsoft Hero Technologies
        </Typography>
        <Typography variant="body1" sx={{ opacity: 0.9 }}>
          Elder AI Guardian is built on 4 Microsoft Hero Technologies working together
          to protect elderly users through AI-powered health monitoring, scam detection,
          emergency response, and family notifications.
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
          <Chip
            label={isConnected ? '🟢 WebSocket Live' : '🔴 WebSocket Offline'}
            sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
          />
          <Chip
            label={`${mcpTools?.length || 0} MCP Tools Available`}
            sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
          />
          <Chip
            label="6 AI Agents Running"
            sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
          />
          <Chip
            label="Azure Cosmos DB Connected"
            sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
          />
        </Box>
      </Paper>

      {/* Hero Tech Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {techCards.map((tech, index) => (
          <Grid item xs={12} md={6} key={tech.id}>
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.02 }}
            >
              <Card
                sx={{
                  height: '100%',
                  cursor: 'pointer',
                  border: activeCard === tech.id ? `2px solid ${tech.color}` : '2px solid transparent',
                  transition: 'border 0.2s',
                }}
                onClick={() => setActiveCard(activeCard === tech.id ? null : tech.id)}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: tech.color, width: 56, height: 56, mr: 2 }}>
                      {tech.icon}
                    </Avatar>
                    <Box>
                      <Typography variant="h6" fontWeight="bold">
                        {tech.title}
                      </Typography>
                      <Chip
                        label={tech.status}
                        size="small"
                        color="success"
                        icon={<CheckCircleIcon />}
                      />
                    </Box>
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {tech.description}
                  </Typography>

                  <Divider sx={{ mb: 2 }} />

                  <Typography variant="subtitle2" gutterBottom color="text.secondary">
                    How it's used in Elder AI Guardian:
                  </Typography>
                  <List dense>
                    {tech.features.map((feature, i) => (
                      <ListItem key={i} sx={{ px: 0, py: 0.25 }}>
                        <ListItemAvatar sx={{ minWidth: 28 }}>
                          <CheckCircleIcon sx={{ fontSize: 16, color: tech.color }} />
                        </ListItemAvatar>
                        <ListItemText
                          primary={feature}
                          primaryTypographyProps={{ variant: 'caption', component: 'div' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        ))}
      </Grid>

      {/* Agent Flow Diagram */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight="bold">
          🤖 Multi-Agent Orchestration Flow
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Every user message passes through this pipeline, combining all 4 hero technologies.
        </Typography>
        <Grid container spacing={1} alignItems="center">
          {agentFlow.map((step, index) => (
            <React.Fragment key={index}>
              <Grid item xs={12} sm="auto">
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.15 }}
                >
                  <Paper
                    elevation={3}
                    sx={{
                      p: 1.5,
                      textAlign: 'center',
                      minWidth: 130,
                      bgcolor: index === 0 ? '#e3f2fd' :
                               index === agentFlow.length - 1 ? '#e8f5e9' : '#f3e5f5',
                    }}
                  >
                    <Typography variant="caption" fontWeight="bold" component="div">
                      {step.from}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" component="div">
                      {step.description}
                    </Typography>
                  </Paper>
                </motion.div>
              </Grid>
              {index < agentFlow.length - 1 && (
                <Grid item xs={12} sm="auto">
                  <Typography variant="h6" color="text.secondary" sx={{ px: 1 }}>→</Typography>
                </Grid>
              )}
            </React.Fragment>
          ))}
        </Grid>
      </Paper>

      {/* Azure Services Used */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight="bold">
          ☁️ Azure Services Powering This App
        </Typography>
        <Grid container spacing={2}>
          {[
            { name: 'Azure AI Foundry', desc: 'GPT-4o + embeddings', icon: '🧠' },
            { name: 'Azure Cosmos DB', desc: 'User data, chat history, threats', icon: '🗄️' },
            { name: 'Azure Communication Services', desc: 'SMS + voice emergency alerts', icon: '📱' },
            { name: 'Azure Key Vault', desc: 'Secrets management', icon: '🔐' },
            { name: 'Azure App Insights', desc: 'Monitoring & telemetry', icon: '📊' },
            { name: 'Azure MCP Server', desc: 'Tool protocol bridge', icon: '🔗' },
          ].map((service) => (
            <Grid item xs={12} sm={6} md={4} key={service.name}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  p: 1.5,
                  borderRadius: 1,
                  bgcolor: 'grey.50',
                  border: '1px solid',
                  borderColor: 'grey.200',
                }}
              >
                <Typography variant="h5" sx={{ mr: 1.5 }}>{service.icon}</Typography>
                <Box>
                  <Typography variant="subtitle2" fontWeight="bold">{service.name}</Typography>
                  <Typography variant="caption" color="text.secondary">{service.desc}</Typography>
                </Box>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Box>
  );
};

export default HeroShowcase;