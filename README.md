# Stranger Loot Tester

## Overview
Stranger Loot Tester is a minimal hosted agent built on the Agent Chat Protocol. It serves as a simple connectivity test: send it any message and it confirms delivery by replying with a fixed prefix followed by your original text. It is useful for verifying chat protocol integration, message acknowledgements, and agent-to-user messaging end to end.

## Features
- Acknowledges every incoming chat message with a ChatAcknowledgement
- Replies with "Stranger Loot Tester received: " followed by the received message text
- Uses the standard Agent Chat Protocol for compatibility with ASI:One and Agentverse chat
- Publishes its protocol manifest for discovery
- No external APIs, API keys, or payments required