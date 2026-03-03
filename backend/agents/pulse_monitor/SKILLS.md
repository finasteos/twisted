# Pulse Monitor Skills

## Progress Calculation
Total Work = Ingestion(10%) + Analysis(30%) + Debate(40%) + Synthesis(15%) + Delivery(5%)

## Heartbeat Protocol
- Every agent emits heartbeat every 10s while active
- Missing heartbeat × 3 = stall detection
- Stall → Escalate to Coordinator → Reroute or retry

## Event Log Categories
| Level | Color | Use Case |
|-------|-------|----------|
| INFO | Cyan | Routine progress |
| THINK | Amber | Agent reasoning snapshots |
| DEBATE | Purple | Swarm deliberation |
| SUCCESS | Green | Completion milestones |
| WARNING | Yellow | Delays, retries |
| ERROR | Red | Failures requiring attention |

## User Notifications
- WebSocket real-time for active users
- Email digest for long-running cases (>30 min)
- SMS for critical alerts (user-configured)
