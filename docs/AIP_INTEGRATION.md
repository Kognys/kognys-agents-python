# AIP Agent Integration for Kognys

This document explains how the AIP (AI Agent Protocol) integration enhances the Kognys research framework.

## Overview

The AIP integration adds intelligent agent capabilities to the existing Kognys LangGraph workflow. When enabled, AIP agents work alongside the traditional agents to provide:

- **Enhanced Intelligence**: Additional LLM-powered insights
- **Inter-Agent Communication**: Agents can share information directly
- **Smart Routing**: Intelligent decision-making for research paths
- **Persistent Memory**: Conversation history across research sessions

## Configuration

Add these variables to your `.env` file:

```bash
# Membase API Configuration
MEMBASE_API_URL=https://kognys-membaseaip-api-production.up.railway.app
MEMBASE_API_KEY=your-api-key-here

# AIP Agent Configuration
ENABLE_AIP_AGENTS=true          # Enable AIP features
AIP_AGENT_PREFIX=kognys         # Prefix for agent IDs
AIP_USE_ROUTING=true            # Enable intelligent routing
AIP_AGENT_TIMEOUT=30            # Timeout in seconds
```

## Architecture

### AIP Agents Created

When `ENABLE_AIP_AGENTS=true`, the system creates four specialized AIP agents:

1. **kognys-retriever**: Enhances document search with intelligent query refinement
2. **kognys-synthesizer**: Provides synthesis suggestions and improvements
3. **kognys-challenger**: Offers critical analysis perspectives
4. **kognys-orchestrator**: Makes strategic workflow decisions

### Integration Points

The AIP agents integrate at key points in the workflow:

```
Standard Flow:
Input → Retriever → Synthesizer → Challenger → Orchestrator → Publisher

With AIP Enhancement:
Input → Retriever (+AIP guidance) → Synthesizer (+AIP suggestions) → 
Challenger (+AIP critique) → Orchestrator (+AIP routing) → Publisher
```

## Features

### 1. Enhanced Retrieval

The retriever agent can:
- Use `/api/v1/route` to identify the best search strategies
- Query the AIP retriever for search term suggestions
- Get recommendations for related topics to explore

### 2. Collaborative Synthesis

The synthesizer agent can:
- Get enhancement suggestions from the AIP synthesizer
- Send notifications to other agents about synthesis progress
- Receive feedback on draft quality

### 3. Inter-Agent Messaging

Agents communicate using:
- `/api/v1/agents/{agent_id}/message` for direct messaging
- Structured actions: "inform", "request", "ask"
- Automatic authorization setup between agents

### 4. Smart Authorization

The system automatically:
- Registers agents on the blockchain
- Sets up authorization pairs for data sharing
- Allows synthesizer to access retriever data
- Enables orchestrator to coordinate all agents

## Usage

### Basic Usage (AIP Disabled)

```bash
# Standard operation without AIP
python main.py
```

### Enhanced Usage (AIP Enabled)

```bash
# Set in .env file
ENABLE_AIP_AGENTS=true

# Run with AIP enhancement
python main.py
```

### Testing AIP Integration

```bash
# Run the test script
python test_aip_integration.py
```

### API Usage with AIP

```python
import requests

# The API automatically uses AIP if enabled
response = requests.post(
    "http://localhost:8000/research",
    json={
        "question": "What are the latest advances in quantum computing?",
        "paper_id": "quantum-2024"
    }
)
```

## Benefits

1. **Backward Compatible**: Works with existing code without changes
2. **Progressive Enhancement**: AIP features enhance but don't replace core functionality
3. **Fault Tolerant**: If AIP fails, research continues with standard agents
4. **Configurable**: Enable/disable features via environment variables
5. **Transparent**: All AIP interactions are logged for debugging

## Monitoring

Watch for these log messages:

```
--- 🚀 Initializing AIP Agents ---
--- 🤖 Creating AIP Agent ---
--- 💬 Querying AIP Agent ---
--- 📨 Sending Inter-Agent Message ---
--- 🔐 Buying Agent Authorization ---
--- 🚦 Routing Request ---
```

## Troubleshooting

### AIP Agents Not Working

1. Check `ENABLE_AIP_AGENTS=true` in `.env`
2. Verify `MEMBASE_API_KEY` is set correctly
3. Ensure `MEMBASE_API_URL` is accessible
4. Look for initialization errors in logs

### Authorization Issues

- Agents are automatically registered on first run
- Authorization pairs are set up during initialization
- Check logs for "Authorization granted" messages

### Performance Considerations

- AIP calls add latency (configurable via `AIP_AGENT_TIMEOUT`)
- Failures are handled gracefully without blocking research
- Consider disabling for time-critical operations

## Future Enhancements

Potential improvements:
- Dynamic agent creation based on research topics
- Learning from previous research sessions
- Custom agent personalities for different domains
- Integration with more external knowledge sources