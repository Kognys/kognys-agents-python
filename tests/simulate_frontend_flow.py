#!/usr/bin/env python3
"""
Simulate the frontend streaming flow against the local API using WebSocket or SSE.

Usage examples:
  WebSocket (default):
    python tests/simulate_frontend_flow.py --message "What are the latest developments in AI?"

  SSE:
    python tests/simulate_frontend_flow.py --mode sse --message "What are the latest developments in AI?"

  Custom server:
    python tests/simulate_frontend_flow.py --mode websocket --ws-url ws://127.0.0.1:8000/ws/research --message "Question"
    python tests/simulate_frontend_flow.py --mode sse --base-url http://127.0.0.1:8000 --message "Question"
"""

import argparse
import asyncio
import json
import sys
import time


# Lazy imports inside runners to avoid requiring both deps for both modes


def format_timestamp(epoch_seconds):
    """Return human-readable HH:MM:SS string for a unix timestamp."""
    if not epoch_seconds:
        return "--:--:--"
    try:
        return time.strftime("%H:%M:%S", time.localtime(epoch_seconds))
    except Exception:
        return "--:--:--"


def print_event(event, event_index):
    event_type = event.get("event_type") or event.get("type", "unknown")
    data = event.get("data", {})
    ts = format_timestamp(event.get("timestamp"))

    # Enhanced prefixes for agent events
    prefix = "📝"
    if "error" in event_type:
        prefix = "💥"
    elif "completed" in event_type:
        prefix = "🎉"
    elif "started" in event_type:
        prefix = "🚀"
    elif event_type == "agent_message":
        prefix = "🤖"
    elif event_type == "agent_debate":
        prefix = "💬"

    print(f"[{ts}] {prefix} Event #{event_index}: {event_type}")
    
    # Special handling for agent_message events
    if event_type == "agent_message" and isinstance(data, dict):
        agent_name = data.get("agent_name", "Unknown Agent")
        agent_role = data.get("agent_role", "Unknown Role") 
        message = data.get("message", "")
        message_type = data.get("message_type", "unknown")
        
        print(f"    🏷️  Agent: {agent_name} ({agent_role})")
        print(f"    📋 Type: {message_type}")
        if message:
            display_msg = message[:150] + "..." if len(message) > 150 else message
            print(f"    💭 Message: {display_msg}")
    
    # Special handling for agent_debate events
    elif event_type == "agent_debate" and isinstance(data, dict):
        agents = data.get("agents", [])
        topic = data.get("topic", "Unknown")
        status = data.get("status", "unknown")
        
        print(f"    🎯 Topic: {topic}")
        print(f"    📊 Status: {status}")
        print(f"    👥 Participants:")
        for agent in agents:
            if isinstance(agent, dict):
                name = agent.get("name", "Unknown")
                role = agent.get("role", "Unknown")
                print(f"      - {name} ({role})")
    
    # Standard data handling for other events
    elif isinstance(data, dict):
        for key in ("status", "question", "validated_question", "document_count", "draft_length", "criticism_count", "final_answer", "error", "message"):
            if key in data:
                value = data[key]
                if isinstance(value, str) and len(value) > 200:
                    value = value[:200] + "..."
                print(f"    {key}: {value}")
    
    print()


def is_terminal_event(event_type):
    return event_type in {"research_completed", "research_failed", "error"}


class AgentEventTracker:
    """Tracks and validates agent-specific events for frontend compatibility."""
    
    def __init__(self):
        self.agent_messages = []
        self.agent_debates = []
        self.expected_agents = {
            "Research Orchestrator": "Research Coordinator",
            "Input Validator": "Validation Expert", 
            "Research Agent": "Information Gatherer",
            "Challenger": "The Peer Reviewer"
        }
        self.valid_message_types = {"analyzing", "thinking", "speaking", "concluding"}
        self.event_sequence = []
    
    def track_event(self, event):
        event_type = event.get("event_type") or event.get("type", "unknown")
        data = event.get("data", {})
        
        self.event_sequence.append(event_type)
        
        if event_type == "agent_message":
            self.agent_messages.append({
                "agent_name": data.get("agent_name"),
                "agent_role": data.get("agent_role"),
                "message_type": data.get("message_type"),
                "message": data.get("message", "")
            })
        
        elif event_type == "agent_debate":
            self.agent_debates.append({
                "agents": data.get("agents", []),
                "topic": data.get("topic"),
                "status": data.get("status")
            })
    
    def validate_frontend_requirements(self):
        """Validate events against frontend requirements."""
        issues = []
        
        # Check if we received any agent_message events
        if not self.agent_messages:
            issues.append("❌ No agent_message events found - Frontend expects agent communications")
        
        # Validate agent message types
        for msg in self.agent_messages:
            msg_type = msg.get("message_type")
            if msg_type and msg_type not in self.valid_message_types:
                issues.append(f"❌ Invalid message_type '{msg_type}' - Frontend expects: {self.valid_message_types}")
        
        # Check for expected research flow sequence
        expected_sequence = ["research_started", "question_validated", "documents_retrieved"]
        for expected in expected_sequence:
            if expected not in self.event_sequence:
                issues.append(f"❌ Missing expected event '{expected}' in sequence")
        
        # Validate agent names consistency
        agent_names = {msg.get("agent_name") for msg in self.agent_messages if msg.get("agent_name")}
        for name in agent_names:
            if name and name not in self.expected_agents:
                issues.append(f"❌ Unexpected agent name '{name}' - Frontend expects: {list(self.expected_agents.keys())}")
        
        return issues
    
    def print_summary(self):
        """Print a summary of agent events for frontend validation."""
        print("\n" + "="*60)
        print("🤖 AGENT EVENT SUMMARY (Frontend Validation)")
        print("="*60)
        
        print(f"\n📊 Event Statistics:")
        print(f"   Total events: {len(self.event_sequence)}")
        print(f"   Agent messages: {len(self.agent_messages)}")
        print(f"   Agent debates: {len(self.agent_debates)}")
        
        if self.agent_messages:
            print(f"\n🏷️  Agent Messages Received:")
            for i, msg in enumerate(self.agent_messages, 1):
                agent = msg.get("agent_name", "Unknown")
                role = msg.get("agent_role", "Unknown")
                msg_type = msg.get("message_type", "unknown")
                message = msg.get("message", "")[:50] + "..." if len(msg.get("message", "")) > 50 else msg.get("message", "")
                print(f"   {i}. {agent} ({role}) [{msg_type}]: {message}")
        
        if self.agent_debates:
            print(f"\n💬 Agent Debates:")
            for i, debate in enumerate(self.agent_debates, 1):
                topic = debate.get("topic", "Unknown")
                status = debate.get("status", "unknown")
                agents = [a.get("name", "Unknown") for a in debate.get("agents", [])]
                print(f"   {i}. Topic: {topic} | Status: {status} | Agents: {', '.join(agents)}")
        
        # Validation results
        issues = self.validate_frontend_requirements()
        if issues:
            print(f"\n⚠️  Frontend Compatibility Issues:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print(f"\n✅ All frontend requirements validated successfully!")
        
        print("="*60)


async def run_websocket_flow(ws_url, message, user_id):
    import websockets  # type: ignore

    print(f"🔌 Connecting WebSocket: {ws_url}")
    event_index = 0
    start_time = time.time()
    agent_tracker = AgentEventTracker()

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected")
            request = {"message": message, "user_id": user_id}
            await websocket.send(json.dumps(request))
            print("📤 Sent research request\n")

            async for raw in websocket:
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    print("❌ Failed to parse JSON message from WebSocket\n")
                    continue

                event_index += 1
                event_type = event.get("event_type") or event.get("type", "unknown")
                
                # Track agent events for frontend validation
                agent_tracker.track_event(event)
                
                print_event(event, event_index)

                if is_terminal_event(event_type):
                    break

    except websockets.exceptions.ConnectionClosed as e:  # type: ignore
        print(f"❌ WebSocket connection closed unexpectedly: {e}")
        return 1
    except websockets.exceptions.InvalidURI as e:  # type: ignore
        print(f"❌ Invalid WebSocket URI: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected WebSocket error: {e}")
        return 1
    finally:
        elapsed = time.time() - start_time
        print(f"⏱️  Total time: {elapsed:.2f}s | 📊 Events: {event_index}")
        
        # Print agent validation summary
        agent_tracker.print_summary()

    return 0


async def run_sse_flow(base_url, message, user_id):
    import aiohttp  # type: ignore

    url = base_url.rstrip("/") + "/papers/stream"
    print(f"🌐 POST {url} (SSE)")

    payload = {"message": message, "user_id": user_id}
    event_index = 0
    start_time = time.time()
    agent_tracker = AgentEventTracker()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    print(f"❌ SSE request failed: {response.status} - {text}")
                    return 1

                async for line_bytes in response.content:
                    line = line_bytes.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue

                    raw = line[6:]
                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        print("❌ Failed to parse JSON line from SSE\n")
                        continue

                    event_index += 1
                    event_type = event.get("event_type") or event.get("type", "unknown")
                    
                    # Track agent events for frontend validation
                    agent_tracker.track_event(event)
                    
                    print_event(event, event_index)

                    if is_terminal_event(event_type):
                        break

    except Exception as e:
        print(f"❌ Unexpected SSE error: {e}")
        return 1
    finally:
        elapsed = time.time() - start_time
        print(f"⏱️  Total time: {elapsed:.2f}s | 📊 Events: {event_index}")
        
        # Print agent validation summary
        agent_tracker.print_summary()

    return 0


async def async_main(args):
    if args.mode == "websocket":
        ws_url = args.ws_url or "ws://localhost:8000/ws/research"
        return await run_websocket_flow(ws_url=ws_url, message=args.message, user_id=args.user_id)
    elif args.mode == "sse":
        base_url = args.base_url or "http://localhost:8000"
        return await run_sse_flow(base_url=base_url, message=args.message, user_id=args.user_id)
    else:
        print(f"❌ Unsupported mode: {args.mode}")
        return 2


def build_parser():
    parser = argparse.ArgumentParser(description="Simulate frontend streaming flow via WebSocket or SSE")
    parser.add_argument("--mode", choices=["websocket", "sse"], default="websocket", help="Transport to use (default: websocket)")
    parser.add_argument("--message", required=True, help="Research question to submit")
    parser.add_argument("--user-id", default="test_user", help="User ID to attach to the request")

    # WebSocket options
    parser.add_argument("--ws-url", help="Full WebSocket URL (e.g., ws://localhost:8000/ws/research)")

    # SSE options
    parser.add_argument("--base-url", help="Base HTTP URL for API (e.g., http://localhost:8000)")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        exit_code = asyncio.run(async_main(args))
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        exit_code = 130
    except RuntimeError as e:
        # Handle 'asyncio.run() cannot be called from a running event loop' (e.g., in notebooks)
        if "asyncio.run() cannot be called" in str(e):
            loop = asyncio.get_event_loop()
            exit_code = loop.run_until_complete(async_main(args))
        else:
            raise

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
