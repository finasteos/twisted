# High CPU Incident Report

**Date:** February 28, 2026

## Incident Description
The system experienced significant performance degradation due to background browser processes consuming excessive CPU resources. Several Google Chrome processes were running at over 100% CPU utilization, collectively monopolizing processing power. 

## Offending Processes
The high CPU usage was traced to an automated, headless-like instance of Google Chrome launched for debugging or background tasks.

| PID | %CPU | Command / Role |
|-----|------|----------------|
| **20779** | ~274% | Main `Google Chrome` process<br>`--remote-debugging-port=9222 --user-data-dir=/Users/perbrinell/.gemini/antigravity-browser-profile` |
| **20786** | ~149% | `Google Chrome Helper` (GPU process) |
| **25501** | ~98% | `Google Chrome Helper (Renderer)` (Renderer process) |

## Root Cause Analysis
- The Chrome instance was launched with a custom user data directory (`.gemini/antigravity-browser-profile`) and remote debugging enabled (`port 9222`), indicating it was spawned by an automated tool, extension, or test suite.
- The processes became unresponsive or stuck in an infinite loop, causing severe CPU hogging without providing active utility (no connected tabs were responding to diagnostic tools).

## Actions Taken
- Diagnosed the source of the high CPU usage.
- Killed the offending processes (`kill -9 20779 20786 25501`) to immediately restore system stability and performance.

## Recommendations for Prevention
1. **Process Lifecycle Management:** Ensure any scripts, extensions, or tests that spawn browser instances (like Puppeteer, Playwright, or custom toolkits) implement robust cleanup logic to terminate the browser on exit or upon encountering an unhandled exception.
2. **Timeouts:** Implement strict timeouts for automated browser interactions. If a page or script hangs, the driver should forcefully close the browser.
3. **Resource Limits:** If running background browsers frequently, consider applying CPU/Memory limits to these automated instances to prevent them from taking down the whole system in case of a runaway script.