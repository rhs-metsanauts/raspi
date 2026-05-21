# UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle `templates/index.html` to a mission-control dark theme using the dashboard split layout from `UI_DESIGN - Copy.md`.

**Architecture:** The entire `<style>` block is replaced with a new CSS system using `#212121` backgrounds, `#2196F3` accent, Roboto fonts, and a three-zone layout (top bar / main-area split / telemetry bar). The HTML body is restructured: `.container` and `.header` are removed, replaced with `.top-bar`, `.main-area` (flex with `.main-viewport` left + `.right-panel` right), and `.telemetry-bar`. Config fields move from the Commands tab into the right panel. JavaScript is extended to propagate status to the new device cards and telemetry bar. No existing element IDs, `onclick` handlers, or Flask endpoints change.

**Tech Stack:** Plain HTML/CSS/JS, Roboto + Roboto Mono (Google Fonts), Three.js r128 (CDN, unchanged)

---

## File Structure

| File | Change |
|---|---|
| `templates/index.html` | Replace `<style>` block; restructure `<body>`; extend 3 JS functions |

---

## Task 1: Replace the `<style>` block

**Files:**
- Modify: `templates/index.html` (lines 7–770)

The current `<link>` for Space Grotesk + JetBrains Mono and the entire `<style>` block are replaced in one shot. No JavaScript changes in this task.

- [ ] **Step 1: Replace the Google Fonts `<link>` on line 7**

Replace:
```html
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

With:
```html
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
```

- [ ] **Step 2: Replace the entire `<style>` block (lines 8–770) with the new CSS below**

Replace everything from `    <style>` through `    </style>` (before the Three.js script tags) with:

```html
    <style>
        :root {
            --bg:          #212121;
            --bg-deep:     #1a1a1a;
            --surface:     #303030;
            --surface-2:   #252525;
            --border:      #333333;
            --border-soft: #444444;
            --connected:   #4CAF50;
            --warning:     #FF9800;
            --error:       #F44336;
            --active:      #2196F3;
            --rpi:         #9C27B0;
            --jetson:      #00BCD4;
            --text:        #ffffff;
            --text-muted:  #9E9E9E;
            --text-dim:    #666666;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Roboto', system-ui, sans-serif;
            font-size: 14px;
            background: var(--bg);
            color: var(--text);
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        /* ── Top bar ── */
        .top-bar {
            height: 56px;
            background: var(--bg);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            padding: 0 20px;
            gap: 16px;
            flex-shrink: 0;
            z-index: 10;
        }
        .top-bar-logo {
            display: flex;
            flex-direction: column;
            gap: 1px;
        }
        .top-bar-title {
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 2px;
            color: var(--text);
            text-transform: uppercase;
        }
        .top-bar-sub {
            font-size: 10px;
            letter-spacing: 1.5px;
            color: var(--text-dim);
            text-transform: uppercase;
            font-family: 'Roboto Mono', monospace;
        }
        .top-bar-spacer { flex: 1; }
        .system-health {
            display: flex;
            align-items: center;
            gap: 7px;
            font-family: 'Roboto Mono', monospace;
            font-size: 12px;
            color: var(--text-muted);
        }
        .health-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--text-dim);
        }
        .health-dot.green  { background: var(--connected); box-shadow: 0 0 6px var(--connected); }
        .health-dot.yellow { background: var(--warning);   box-shadow: 0 0 6px var(--warning); }
        .health-dot.red    { background: var(--error);     box-shadow: 0 0 6px var(--error); }

        /* ── Main area ── */
        .main-area {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        /* ── Main viewport (left) ── */
        .main-viewport {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background: var(--bg-deep);
        }

        .tab-bar {
            display: flex;
            background: var(--bg);
            border-bottom: 1px solid var(--border);
            flex-shrink: 0;
        }
        .tab-btn {
            flex: 1;
            padding: 14px 20px;
            border: none;
            border-bottom: 2px solid transparent;
            background: transparent;
            color: var(--text-muted);
            font-family: 'Roboto', sans-serif;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: color 0.15s, border-color 0.15s;
        }
        .tab-btn.active  { color: var(--active); border-bottom-color: var(--active); }
        .tab-btn:hover:not(.active) { color: var(--text); }

        .viewport-content {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            scrollbar-width: thin;
            scrollbar-color: var(--border) transparent;
        }
        .viewport-content::-webkit-scrollbar { width: 5px; }
        .viewport-content::-webkit-scrollbar-track { background: transparent; }
        .viewport-content::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

        /* ── Right panel ── */
        .right-panel {
            width: 340px;
            flex-shrink: 0;
            background: var(--bg);
            border-left: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: var(--border) transparent;
        }
        .panel-section {
            padding: 16px;
            border-bottom: 1px solid #2a2a2a;
        }
        .panel-section-title {
            font-family: 'Roboto Mono', monospace;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--text-dim);
            margin-bottom: 12px;
        }

        /* ── Device cards ── */
        .device-card {
            background: var(--surface);
            border-radius: 6px;
            padding: 14px;
            margin-bottom: 10px;
            border: 2px solid transparent;
            transition: box-shadow 0.2s;
        }
        .device-card:last-child { margin-bottom: 0; }
        .device-card.rpi    { border-color: var(--rpi); }
        .device-card.jetson { border-color: var(--jetson); }
        .device-card.offline {
            border-color: var(--error) !important;
            opacity: 0.7;
            background: var(--surface-2);
        }
        .device-card-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
            background: var(--text-dim);
        }
        .status-dot.green  { background: var(--connected); box-shadow: 0 0 5px var(--connected); }
        .status-dot.red    { background: var(--error);     box-shadow: 0 0 5px var(--error); }
        .status-dot.yellow { background: var(--warning);   box-shadow: 0 0 5px var(--warning); }
        .device-name {
            font-size: 13px;
            font-weight: 500;
            flex: 1;
        }
        .device-badge {
            font-family: 'Roboto Mono', monospace;
            font-size: 10px;
            padding: 2px 7px;
            border-radius: 3px;
        }
        .rpi-badge    { background: rgba(156,39,176,0.2);  color: #CE93D8; }
        .jetson-badge { background: rgba(0,188,212,0.15);  color: #80DEEA; }
        .device-rows { display: flex; flex-direction: column; gap: 5px; }
        .device-row  { display: flex; justify-content: space-between; font-size: 12px; }
        .device-row .key { color: var(--text-dim); }
        .device-row .val { font-family: 'Roboto Mono', monospace; color: var(--text); }
        .device-row .val.green { color: var(--connected); }
        .device-row .val.red   { color: var(--error); }
        .device-row .val.blue  { color: var(--active); }
        .device-row .val.cyan  { color: var(--jetson); }

        /* ── Config fields (right panel) ── */
        .config-field { margin-bottom: 12px; }
        .config-field:last-of-type { margin-bottom: 0; }
        .config-label {
            font-size: 11px;
            color: var(--text-dim);
            font-family: 'Roboto Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 4px;
        }
        .config-input {
            width: 100%;
            background: var(--surface-2);
            border: 1px solid #3a3a3a;
            border-radius: 4px;
            color: var(--text-muted);
            padding: 7px 10px;
            font-family: 'Roboto Mono', monospace;
            font-size: 11px;
            transition: border-color 0.15s;
        }
        .config-input:focus {
            outline: none;
            border-color: var(--active);
            color: var(--text);
        }
        .config-save-btn {
            width: 100%;
            margin-top: 12px;
            padding: 9px;
            background: transparent;
            border: 1px solid var(--border-soft);
            border-radius: 4px;
            color: var(--text-muted);
            font-size: 12px;
            font-family: 'Roboto', sans-serif;
            cursor: pointer;
            transition: border-color 0.15s, color 0.15s;
        }
        .config-save-btn:hover { border-color: var(--active); color: var(--active); }

        /* ── Telemetry bar ── */
        .telemetry-bar {
            height: 48px;
            background: var(--bg);
            border-top: 1px solid var(--border);
            display: flex;
            align-items: center;
            padding: 0 20px;
            flex-shrink: 0;
            gap: 0;
        }
        .telem-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 0 20px;
            border-right: 1px solid var(--border);
            font-family: 'Roboto Mono', monospace;
            font-size: 12px;
        }
        .telem-item:first-child { padding-left: 0; }
        .telem-label { color: var(--text-dim); font-size: 10px; text-transform: uppercase; letter-spacing: 1px; }
        .telem-val   { color: var(--text); }
        .telem-val.green { color: var(--connected); }
        .telem-val.red   { color: var(--error); }
        .telem-val.gray  { color: var(--text-dim); }
        .telem-val.cyan  { color: var(--jetson); }
        .mode-badge {
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-family: 'Roboto Mono', monospace;
            background: rgba(33,150,243,0.15);
            color: var(--active);
            border: 1px solid rgba(33,150,243,0.3);
        }
        .mode-badge.lora {
            background: rgba(156,39,176,0.15);
            color: #CE93D8;
            border-color: rgba(156,39,176,0.3);
        }

        /* ── Commands tab — mode switcher ── */
        .mode-switcher {
            display: flex;
            background: var(--surface);
            border: 1px solid var(--border-soft);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 20px;
        }
        .mode-btn {
            flex: 1;
            padding: 11px 20px;
            border: none;
            background: transparent;
            color: var(--text-muted);
            font-family: 'Roboto', sans-serif;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.15s, color 0.15s;
        }
        .mode-btn:first-child { border-right: 1px solid var(--border-soft); }
        .mode-btn.active { background: var(--active); color: #fff; }
        .mode-btn:hover:not(.active) { background: rgba(33,150,243,0.08); color: var(--text); }
        .mode-label { display: block; font-size: 10px; opacity: 0.7; margin-top: 2px; }

        /* ── Form elements ── */
        .form-group { margin-bottom: 18px; }
        .form-group label {
            display: block;
            font-size: 12px;
            font-weight: 500;
            color: var(--text-muted);
            margin-bottom: 6px;
            font-family: 'Roboto Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        input, select, textarea {
            width: 100%;
            background: var(--surface);
            border: 1px solid var(--border-soft);
            border-radius: 4px;
            color: var(--text);
            font-family: 'Roboto', sans-serif;
            padding: 9px 12px;
            font-size: 13px;
            transition: border-color 0.15s;
        }
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: var(--active);
            box-shadow: 0 0 0 2px rgba(33,150,243,0.15);
        }
        select { cursor: pointer; background-color: var(--surface); }
        textarea {
            min-height: 120px;
            resize: vertical;
            font-family: 'Roboto Mono', monospace;
            font-size: 12px;
        }

        .dynamic-fields {
            background: var(--surface);
            border: 1px solid var(--border-soft);
            border-radius: 4px;
            padding: 16px;
            margin-bottom: 16px;
        }

        /* ── Buttons ── */
        .btn {
            background: var(--active);
            color: #fff;
            border: none;
            border-radius: 4px;
            padding: 12px 24px;
            font-family: 'Roboto', sans-serif;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            width: 100%;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: background 0.15s, transform 0.1s;
        }
        .btn:hover    { background: #1976D2; }
        .btn:active   { transform: scale(0.99); }
        .btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

        .btn-secondary {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid var(--border-soft);
            border-radius: 4px;
            padding: 12px 18px;
            font-family: 'Roboto', sans-serif;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            white-space: nowrap;
            transition: border-color 0.15s, color 0.15s;
        }
        .btn-secondary:hover { border-color: var(--active); color: var(--active); }

        /* ── Response section ── */
        .response-section {
            background: var(--surface);
            border: 1px solid var(--border-soft);
            border-radius: 4px;
            padding: 16px;
            margin-top: 16px;
            display: none;
        }
        .response-section.show { display: block; }
        .response-section h3 {
            font-size: 11px;
            font-weight: 500;
            color: var(--text-dim);
            margin-bottom: 12px;
            font-family: 'Roboto Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }
        .response-content {
            background: var(--bg-deep);
            padding: 12px;
            border-radius: 4px;
            border-left: 3px solid var(--active);
        }
        .response-content.success { border-left-color: var(--connected); }
        .response-content.error   { border-left-color: var(--error); }
        .response-field {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 10px;
            margin-bottom: 8px;
        }
        .response-field.inline { display: flex; align-items: center; gap: 8px; }
        .response-field:last-child { margin-bottom: 0; }
        .field-label {
            font-family: 'Roboto Mono', monospace;
            font-weight: 500;
            color: var(--active);
            font-size: 10px;
            text-transform: uppercase;
            margin-bottom: 4px;
            letter-spacing: 1px;
        }
        .field-label.inline { margin-bottom: 0; flex-shrink: 0; }
        .field-value {
            color: var(--text);
            font-family: 'Roboto Mono', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.55;
        }
        .field-value.inline { margin-bottom: 0; }
        .field-value.collapsed { max-height: 120px; overflow: hidden; position: relative; }
        .field-value.collapsed::after {
            content: '';
            position: absolute;
            bottom: 0; left: 0; right: 0;
            height: 40px;
            background: linear-gradient(to bottom, transparent, var(--surface));
        }
        .expand-btn {
            background: rgba(33,150,243,0.1);
            border: 1px solid rgba(33,150,243,0.25);
            color: var(--active);
            padding: 4px 10px;
            border-radius: 3px;
            font-size: 11px;
            font-family: 'Roboto', sans-serif;
            cursor: pointer;
            margin-top: 6px;
            transition: background 0.15s;
        }
        .expand-btn:hover { background: rgba(33,150,243,0.18); }
        .image-container { margin-top: 8px; max-width: 100%; text-align: center; }
        .image-container img { max-width: 100%; height: auto; border-radius: 4px; border: 1px solid var(--border); }

        /* status-indicator inside labels (kept for JS compatibility) */
        .status-indicator { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 5px; }
        .status-online  { background: var(--connected); }
        .status-offline { background: var(--error); }

        .hidden { display: none !important; }

        /* ── AI FAB ── */
        .ai-fab {
            position: fixed;
            bottom: 68px;
            right: 360px;
            width: 52px;
            height: 52px;
            border-radius: 50%;
            background: var(--active);
            border: none;
            color: #fff;
            font-size: 22px;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(33,150,243,0.45);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .ai-fab:hover { transform: scale(1.08); box-shadow: 0 6px 28px rgba(33,150,243,0.6); }

        /* ── AI modal ── */
        .ai-overlay {
            position: fixed;
            inset: 0;
            background: rgba(10,10,10,0.75);
            z-index: 1001;
            display: none;
            align-items: center;
            justify-content: center;
        }
        .ai-overlay.open { display: flex; }
        .ai-modal {
            width: 520px;
            max-width: 94vw;
            max-height: 85vh;
            background: var(--surface);
            border: 1px solid var(--border-soft);
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 60px rgba(0,0,0,0.6);
        }
        .ai-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 18px;
            border-bottom: 1px solid var(--border);
        }
        .ai-modal-header h3 { font-size: 14px; font-weight: 500; }
        .ai-close-btn { background: none; border: none; color: var(--text-muted); font-size: 20px; cursor: pointer; padding: 0 4px; transition: color 0.15s; }
        .ai-close-btn:hover { color: var(--text); }
        .ai-chat-log {
            flex: 1;
            overflow-y: auto;
            padding: 14px 18px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            scrollbar-width: thin;
            scrollbar-color: var(--border) transparent;
        }
        .ai-chat-log::-webkit-scrollbar { width: 4px; }
        .ai-chat-log::-webkit-scrollbar-track { background: transparent; }
        .ai-chat-log::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
        .ai-msg {
            padding: 10px 13px;
            border-radius: 6px;
            font-size: 13px;
            line-height: 1.55;
            max-width: 92%;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .ai-msg.user      { align-self: flex-end; background: rgba(33,150,243,0.15); border: 1px solid rgba(33,150,243,0.3); color: var(--text); }
        .ai-msg.assistant { align-self: flex-start; background: var(--surface-2); border: 1px solid var(--border); color: var(--text-muted); }
        .ai-msg.thinking  { font-family: 'Roboto Mono', monospace; color: var(--text-muted); font-size: 12px; font-style: italic; }
        .ai-msg.error     { border-left: 3px solid var(--error); color: #ef9a9a; }
        .ai-msg .thinking-header {
            font-weight: 500;
            margin-bottom: 4px;
            color: var(--active);
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-style: normal;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .thinking-timer { font-weight: 400; font-style: normal; color: var(--text-muted); font-size: 10px; }
        .ai-msg .thinking-body { max-height: 150px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--border) transparent; }
        .ai-msg .thinking-body::-webkit-scrollbar { width: 3px; }
        .ai-msg .thinking-body::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
        .ai-msg .thinking-body.expanded { max-height: 400px; }
        .ai-msg .thinking-toggle { background: none; border: none; color: var(--active); font-size: 11px; font-family: 'Roboto Mono', monospace; cursor: pointer; padding: 4px 0 0; }
        .ai-autofill-bar { display: flex; gap: 8px; margin-top: 10px; }
        .ai-autofill-btn { padding: 5px 12px; border-radius: 4px; font-size: 12px; font-weight: 500; font-family: 'Roboto', sans-serif; cursor: pointer; transition: all 0.15s; }
        .ai-autofill-btn.apply { background: var(--active); color: #fff; border: none; }
        .ai-autofill-btn.apply:hover { background: #1976D2; }
        .ai-autofill-btn.dismiss { background: transparent; color: var(--text-muted); border: 1px solid var(--border-soft); }
        .ai-autofill-btn.dismiss:hover { border-color: var(--active); color: var(--active); }
        .ai-input-bar { display: flex; gap: 8px; padding: 12px 18px; border-top: 1px solid var(--border); }
        .ai-input-bar textarea { flex: 1; resize: none; min-height: 40px; max-height: 100px; font-family: 'Roboto', sans-serif; font-size: 13px; }
        .ai-send-btn { padding: 0 16px; border-radius: 4px; background: var(--active); border: none; color: #fff; font-size: 14px; cursor: pointer; transition: background 0.15s; }
        .ai-send-btn:hover { background: #1976D2; }
        .ai-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
        .ai-clear-btn { background: none; border: 1px solid rgba(239,154,154,0.35); color: #ef9a9a; font-size: 11px; font-family: 'Roboto', sans-serif; padding: 4px 10px; border-radius: 4px; cursor: pointer; transition: background 0.15s; }
        .ai-clear-btn:hover { background: rgba(239,154,154,0.1); }

        /* ── Map tab ── */
        .map-controls {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 0 16px;
            margin-bottom: 0;
        }
        .map-status { display: flex; align-items: center; gap: 8px; }
        .map-status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
        .map-status-dot.connected    { background: var(--connected); box-shadow: 0 0 5px var(--connected); }
        .map-status-dot.disconnected { background: var(--error); }
        .map-status-label { font-family: 'Roboto Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); }
        .map-canvas-wrap {
            position: relative;
            width: 100%;
            height: 480px;
            border-radius: 4px;
            overflow: hidden;
            border: 1px solid var(--border-soft);
            background: var(--bg-deep);
        }
        #mapCanvas { width: 100%; height: 100%; display: block; }
        #minimapCanvas {
            position: absolute;
            bottom: 10px; right: 10px;
            width: 160px; height: 160px;
            border-radius: 6px;
            border: 1px solid var(--border-soft);
            pointer-events: none;
        }
        .map-stats {
            display: flex;
            gap: 24px;
            padding: 12px 0 0;
        }
        .map-stat-item {
            font-family: 'Roboto Mono', monospace;
            font-size: 11px;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .map-stat-item span { color: var(--active); }
    </style>
```

- [ ] **Step 3: Verify the page still loads**

Start Flask if not running: `cd c:/Users/busyp/nasa-hera && python FlaskServer.py`

Open http://127.0.0.1:5000. The page should load. It will look wrong structurally (no layout changes yet) but should not show any broken CSS errors. The fonts will switch to Roboto.

- [ ] **Step 4: Commit**

```bash
git add templates/index.html
git commit -m "style: replace CSS with mission-control dark theme"
```

---

## Task 2: Restructure the HTML body

**Files:**
- Modify: `templates/index.html` (lines 774–952 of the current file — the entire `<body>` content before the AI modal + FAB and `<script>`)

This task replaces everything from `<body>` through the end of `</div><!-- end #tab-map -->` and `</div>` (closing container), plus the AI modal + FAB. The `<script>` block is NOT touched here.

- [ ] **Step 1: Replace the entire body HTML (from `<body>` through `</div>` closing `.container`, plus AI modal + FAB block)**

The current body runs from line 774 to approximately line 952. Replace everything from `<body>` through `    <!-- AI FAB -->` line with the following (leave the `<script>` block untouched):

```html
<body>

    <!-- Top bar -->
    <div class="top-bar">
        <div class="top-bar-logo">
            <span class="top-bar-title">🚀 HERA Rover Command Center</span>
            <span class="top-bar-sub">METSAnauts Mission Control</span>
        </div>
        <div class="top-bar-spacer"></div>
        <div class="system-health">
            <span class="health-dot" id="topBarDot"></span>
            <span id="topBarStatusText" style="font-size:11px;">STANDBY</span>
        </div>
    </div>

    <!-- Main area: viewport (left) + right panel -->
    <div class="main-area">

        <!-- Left: main viewport with tabs -->
        <div class="main-viewport">
            <div class="tab-bar">
                <button class="tab-btn active" id="tabCmdBtn" onclick="switchTab('commands')">Commands</button>
                <button class="tab-btn" id="tabMapBtn" onclick="switchTab('map')">Map</button>
            </div>

            <!-- Commands tab -->
            <div class="viewport-content" id="tab-commands">
                <!-- Mode Switcher -->
                <div class="mode-switcher">
                    <button class="mode-btn active" id="modeWifi" onclick="setMode('wifi')">
                        📡 WiFi
                        <span class="mode-label">Send via network</span>
                    </button>
                    <button class="mode-btn" id="modeLora" onclick="setMode('lora')">
                        📻 LoRa
                        <span class="mode-label">Send via radio</span>
                    </button>
                </div>

                <!-- Command Type Selection -->
                <div class="form-group">
                    <label for="commandType">Command Type</label>
                    <select id="commandType">
                        <option value="bash_command">Bash Command</option>
                        <option value="edit_file">Edit File</option>
                        <option value="basic_action">Python Action</option>
                        <option value="read_file">Read File</option>
                        <option value="read_image">Read Image</option>
                    </select>
                </div>

                <!-- Dynamic Fields -->
                <div class="dynamic-fields">
                    <div id="fields_bash_command" class="field-group">
                        <div class="form-group">
                            <label for="command">Command</label>
                            <input type="text" id="command">
                        </div>
                    </div>
                    <div id="fields_edit_file" class="field-group hidden">
                        <div class="form-group">
                            <label for="edit_file_name">File Name</label>
                            <input type="text" id="edit_file_name">
                        </div>
                        <div class="form-group">
                            <label for="file_content">File Content</label>
                            <textarea id="file_content"></textarea>
                        </div>
                    </div>
                    <div id="fields_basic_action" class="field-group hidden">
                        <div class="form-group">
                            <label for="action">Python Code</label>
                            <textarea id="action"></textarea>
                        </div>
                    </div>
                    <div id="fields_read_file" class="field-group hidden">
                        <div class="form-group">
                            <label for="read_file_name">File Name</label>
                            <input type="text" id="read_file_name">
                        </div>
                    </div>
                    <div id="fields_read_image" class="field-group hidden">
                        <div class="form-group">
                            <label for="image_file_name">Image File Path</label>
                            <input type="text" id="image_file_name">
                        </div>
                    </div>
                </div>

                <!-- Buttons Row -->
                <div style="display:flex;gap:10px;">
                    <button class="btn" id="sendBtn" onclick="sendCommand()" style="flex:1;">
                        Send Command
                    </button>
                    <button class="btn-secondary" id="aiBtn" onclick="openAiModal()">
                        ✨ AI Assist
                    </button>
                </div>

                <!-- Response Section -->
                <div class="response-section" id="responseSection">
                    <h3>Response</h3>
                    <div class="response-content" id="responseContent"></div>
                </div>
            </div><!-- end #tab-commands -->

            <!-- Map tab -->
            <div class="viewport-content hidden" id="tab-map">
                <div class="map-controls">
                    <div class="map-status">
                        <span class="map-status-dot disconnected" id="mapStatusDot"></span>
                        <span class="map-status-label" id="mapStatusText">DISCONNECTED</span>
                    </div>
                    <div style="display:flex;gap:8px;">
                        <button class="btn" style="width:auto;padding:9px 18px;" onclick="startMapping()">Start</button>
                        <button class="btn-secondary" onclick="stopMapping()">Stop</button>
                        <button class="btn-secondary" onclick="clearMapping()">Clear</button>
                    </div>
                </div>
                <div class="map-canvas-wrap">
                    <canvas id="mapCanvas"></canvas>
                    <canvas id="minimapCanvas" width="160" height="160"></canvas>
                </div>
                <div class="map-stats">
                    <span class="map-stat-item">Points: <span id="mapPointCount">0</span></span>
                    <span class="map-stat-item">Coverage: <span id="mapCoverage">0.0</span> m²</span>
                    <span class="map-stat-item">Time: <span id="mapElapsed">00:00</span></span>
                </div>
            </div><!-- end #tab-map -->
        </div><!-- end .main-viewport -->

        <!-- Right panel: device cards + config -->
        <div class="right-panel">

            <!-- Device cards -->
            <div class="panel-section">
                <div class="panel-section-title">Devices</div>

                <!-- Rover (Pi) card -->
                <div class="device-card rpi" id="roverCard">
                    <div class="device-card-header">
                        <span class="status-dot" id="roverStatusDot"></span>
                        <span class="device-name">Rover</span>
                        <span class="device-badge rpi-badge">Raspberry Pi</span>
                    </div>
                    <div class="device-rows">
                        <div class="device-row">
                            <span class="key">Connection</span>
                            <span class="val gray" id="roverStatusText">Unknown</span>
                        </div>
                        <div class="device-row">
                            <span class="key">Mode</span>
                            <span class="val blue" id="roverModeText">WiFi</span>
                        </div>
                        <div class="device-row">
                            <span class="key">Address</span>
                            <span class="val" id="roverAddressText">—</span>
                        </div>
                    </div>
                </div>

                <!-- Jetson card -->
                <div class="device-card jetson offline" id="jetsonCard">
                    <div class="device-card-header">
                        <span class="status-dot red" id="jetsonStatusDot"></span>
                        <span class="device-name">Mapper</span>
                        <span class="device-badge jetson-badge">Jetson Nano</span>
                    </div>
                    <div class="device-rows">
                        <div class="device-row">
                            <span class="key">Connection</span>
                            <span class="val red" id="jetsonStatusText">Offline</span>
                        </div>
                        <div class="device-row">
                            <span class="key">Points</span>
                            <span class="val cyan" id="jetsonPointsText">0</span>
                        </div>
                        <div class="device-row">
                            <span class="key">WebSocket</span>
                            <span class="val" id="jetsonWsText">:9001</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Configuration -->
            <div class="panel-section" style="flex:1;">
                <div class="panel-section-title">Configuration</div>

                <!-- WiFi config -->
                <div id="wifiConfig">
                    <div class="config-field">
                        <div class="config-label">Rover Server Host</div>
                        <input class="config-input" type="text" id="serverUrl" value="localhost" placeholder="IP or hostname">
                        <!-- hidden status-indicator kept for JS compatibility -->
                        <span class="status-indicator status-offline hidden" id="statusIndicator"></span>
                    </div>
                    <div class="config-field">
                        <div class="config-label">Timeout (seconds)</div>
                        <input class="config-input" type="number" id="timeout" value="35" min="1" max="300" style="width:100px;">
                    </div>
                </div>

                <!-- LoRa config -->
                <div id="loraConfig" class="hidden">
                    <div class="config-field">
                        <div class="config-label">LoRa Destination ID (0–255)</div>
                        <input class="config-input" type="number" id="loraDestination" value="0" min="0" max="255" style="width:100px;">
                    </div>
                </div>

                <div class="config-field">
                    <div class="config-label">Jetson WS URL</div>
                    <input class="config-input" type="text" id="jetsonWsUrl" placeholder="ws://192.168.1.100:9001">
                </div>

                <button class="config-save-btn" onclick="saveConfig()">Save Config</button>
            </div>

        </div><!-- end .right-panel -->
    </div><!-- end .main-area -->

    <!-- Telemetry bar -->
    <div class="telemetry-bar">
        <div class="telem-item">
            <span class="telem-label">Rover</span>
            <span class="status-dot" id="telemRoverDot"></span>
            <span class="telem-val gray" id="telemRoverText">—</span>
        </div>
        <div class="telem-item">
            <span class="telem-label">Mapper</span>
            <span class="status-dot red" id="telemMapperDot"></span>
            <span class="telem-val red" id="telemMapperText">Offline</span>
        </div>
        <div class="telem-item">
            <span class="telem-label">Mode</span>
            <span class="mode-badge" id="telemModeBadge">WiFi</span>
        </div>
        <div class="telem-item">
            <span class="telem-label">Points</span>
            <span class="telem-val cyan" id="telemPoints">0</span>
        </div>
    </div>

    <!-- AI Assistant Modal -->
    <div class="ai-overlay" id="aiOverlay" onclick="if(event.target===this)closeAiModal()">
        <div class="ai-modal">
            <div class="ai-modal-header">
                <h3>🤖 AI Command Assistant</h3>
                <div style="display:flex;gap:8px;align-items:center;">
                    <button class="ai-clear-btn" onclick="clearAiChat()">Clear Chat</button>
                    <button class="ai-close-btn" onclick="closeAiModal()">&times;</button>
                </div>
            </div>
            <div class="ai-chat-log" id="aiChatLog"></div>
            <div class="ai-input-bar">
                <textarea id="aiInput" placeholder="Describe what you want the rover to do…" rows="1"
                    onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendAiMessage();}"></textarea>
                <button class="ai-send-btn" id="aiSendBtn" onclick="sendAiMessage()">➤</button>
            </div>
        </div>
    </div>

    <!-- AI FAB -->
    <button class="ai-fab" onclick="openAiModal()" title="AI Command Assistant">✨</button>
```

- [ ] **Step 2: Verify layout in browser**

Open http://127.0.0.1:5000. Check:
- Three-zone layout: top bar visible, main area with left/right split, telemetry bar at bottom
- Right panel shows two device cards (Rover purple border, Mapper cyan/red border) and config fields below
- Commands tab shows mode switcher, command type dropdown, dynamic fields, send button
- Map tab accessible via tab button
- AI FAB visible above the telemetry bar (not over the right panel)

- [ ] **Step 3: Commit**

```bash
git add templates/index.html
git commit -m "feat: dashboard split layout — top bar, right panel, telemetry bar"
```

---

## Task 3: Update JavaScript for status propagation

**Files:**
- Modify: `templates/index.html` (the `<script>` block)

Three functions need extending. No existing functions are removed or renamed.

- [ ] **Step 1: Update `_pollMapStatus()` to propagate to Jetson card + telemetry bar**

Find the current `_pollMapStatus` function:
```javascript
        function _pollMapStatus() {
            fetch('/map_status')
                .then(r => r.json())
                .then(data => {
                    const dot = document.getElementById('mapStatusDot');
                    const txt = document.getElementById('mapStatusText');
                    if (!dot || !txt) return;
                    if (data.connected) {
                        dot.className = 'map-status-dot connected';
                        txt.textContent = 'CONNECTED';
                    } else {
                        dot.className = 'map-status-dot disconnected';
                        txt.textContent = 'DISCONNECTED';
                    }
                })
                .catch(() => {});
        }
```

Replace it with:
```javascript
        function _pollMapStatus() {
            fetch('/map_status')
                .then(r => r.json())
                .then(data => {
                    const dot = document.getElementById('mapStatusDot');
                    const txt = document.getElementById('mapStatusText');
                    if (!dot || !txt) return;

                    // Map tab status dot
                    if (data.connected) {
                        dot.className = 'map-status-dot connected';
                        txt.textContent = 'CONNECTED';
                    } else {
                        dot.className = 'map-status-dot disconnected';
                        txt.textContent = 'DISCONNECTED';
                    }

                    // Jetson device card
                    const jDot  = document.getElementById('jetsonStatusDot');
                    const jTxt  = document.getElementById('jetsonStatusText');
                    const jPts  = document.getElementById('jetsonPointsText');
                    const jCard = document.getElementById('jetsonCard');
                    if (jDot && jTxt && jCard) {
                        if (data.connected) {
                            jDot.className  = 'status-dot green';
                            jTxt.className  = 'val green';
                            jTxt.textContent = 'Connected';
                            jCard.classList.remove('offline');
                        } else {
                            jDot.className  = 'status-dot red';
                            jTxt.className  = 'val red';
                            jTxt.textContent = 'Offline';
                            jCard.classList.add('offline');
                        }
                    }
                    if (jPts) jPts.textContent = (data.point_count || 0).toLocaleString();

                    // Telemetry bar — mapper + points
                    const tmDot = document.getElementById('telemMapperDot');
                    const tmTxt = document.getElementById('telemMapperText');
                    const tPts  = document.getElementById('telemPoints');
                    if (tmDot && tmTxt) {
                        if (data.connected) {
                            tmDot.className  = 'status-dot green';
                            tmTxt.className  = 'telem-val green';
                            tmTxt.textContent = 'Connected';
                        } else {
                            tmDot.className  = 'status-dot red';
                            tmTxt.className  = 'telem-val red';
                            tmTxt.textContent = 'Offline';
                        }
                    }
                    if (tPts) tPts.textContent = (data.point_count || 0).toLocaleString();

                    _updateSystemHealth(data.connected);
                })
                .catch(() => {});
        }
```

- [ ] **Step 2: Add `_updateSystemHealth()` helper directly before `_pollMapStatus`**

Insert this function immediately before the existing `_pollMapStatus` function:
```javascript
        /* ── System health (top bar) ── */
        let _roverOnline = false;

        function _updateSystemHealth(jetsonConnected) {
            const dot = document.getElementById('topBarDot');
            const txt = document.getElementById('topBarStatusText');
            if (!dot || !txt) return;
            if (_roverOnline && jetsonConnected) {
                dot.className = 'health-dot green';
                txt.textContent = 'SYSTEMS NOMINAL';
            } else if (_roverOnline || jetsonConnected) {
                dot.className = 'health-dot yellow';
                txt.textContent = 'PARTIAL';
            } else {
                dot.className = 'health-dot red';
                txt.textContent = 'NO SIGNAL';
            }
        }
```

- [ ] **Step 3: Update `sendCommand()` to set rover status after a response**

Find this block inside `sendCommand()`:
```javascript
                if (result.success) {
                    displayResponse(result.data, false);
                    statusIndicator.classList.remove('status-offline');
                    statusIndicator.classList.add('status-online');
                } else {
                    displayResponse({ error: result.error }, true);
                    statusIndicator.classList.remove('status-online');
                    statusIndicator.classList.add('status-offline');
                }
```

Replace with:
```javascript
                if (result.success) {
                    displayResponse(result.data, false);
                    statusIndicator.classList.remove('status-offline');
                    statusIndicator.classList.add('status-online');
                    _setRoverStatus(true);
                } else {
                    displayResponse({ error: result.error }, true);
                    statusIndicator.classList.remove('status-online');
                    statusIndicator.classList.add('status-offline');
                    _setRoverStatus(false);
                }
```

Also find the catch block inside `sendCommand()`:
```javascript
            } catch (error) {
                responseSection.classList.add('show');
                displayResponse({ error: error.message }, true);
                statusIndicator.classList.remove('status-online');
                statusIndicator.classList.add('status-offline');
```

Replace with:
```javascript
            } catch (error) {
                responseSection.classList.add('show');
                displayResponse({ error: error.message }, true);
                statusIndicator.classList.remove('status-online');
                statusIndicator.classList.add('status-offline');
                _setRoverStatus(false);
```

- [ ] **Step 4: Add `_setRoverStatus()` helper directly before `_updateSystemHealth`**

Insert immediately before `_updateSystemHealth`:
```javascript
        function _setRoverStatus(online) {
            _roverOnline = online;
            const rDot  = document.getElementById('roverStatusDot');
            const rTxt  = document.getElementById('roverStatusText');
            const rCard = document.getElementById('roverCard');
            const trDot = document.getElementById('telemRoverDot');
            const trTxt = document.getElementById('telemRoverText');
            if (rDot && rTxt) {
                rDot.className = online ? 'status-dot green' : 'status-dot red';
                rTxt.className = online ? 'val green' : 'val red';
                rTxt.textContent = online ? 'Online' : 'Error';
            }
            if (rCard) rCard.classList.toggle('offline', !online);
            if (trDot && trTxt) {
                trDot.className = online ? 'status-dot green' : 'status-dot red';
                trTxt.className = online ? 'telem-val green' : 'telem-val red';
                trTxt.textContent = online ? 'Online' : 'Error';
            }
            _updateSystemHealth(document.getElementById('jetsonStatusDot')?.classList.contains('green') ?? false);
        }
```

- [ ] **Step 5: Update `setMode()` to propagate mode to rover card + telemetry bar**

Find the end of the existing `setMode()` function (it ends with `updateConfig();`). Add these two lines before `updateConfig()`:
```javascript
            // Sync rover card mode text and telemetry badge
            const rMode = document.getElementById('roverModeText');
            if (rMode) { rMode.textContent = mode === 'wifi' ? 'WiFi' : 'LoRa'; rMode.className = mode === 'wifi' ? 'val blue' : 'val'; }
            const badge = document.getElementById('telemModeBadge');
            if (badge) { badge.textContent = mode === 'wifi' ? 'WiFi' : 'LoRa'; badge.className = mode === 'wifi' ? 'mode-badge' : 'mode-badge lora'; }
```

- [ ] **Step 6: Add `saveConfig()` function and update config loading**

The right panel now has a `jetsonWsUrl` input and a Save Config button calling `saveConfig()`. Add this function near the existing `updateConfig()`:
```javascript
        function saveConfig() {
            const host = document.getElementById('serverUrl').value;
            const fullUrl = buildFullUrl(host);
            const jetsonWs = document.getElementById('jetsonWsUrl').value;
            fetch('/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    server_url: fullUrl,
                    timeout: parseInt(document.getElementById('timeout').value),
                    mode: currentMode,
                    lora_destination: parseInt(document.getElementById('loraDestination').value),
                    jetson_ws_url: jetsonWs || undefined
                })
            }).then(() => {
                const btn = document.querySelector('.config-save-btn');
                if (btn) { btn.textContent = 'Saved ✓'; setTimeout(() => { btn.textContent = 'Save Config'; }, 1500); }
                // Update jetson address display
                const jWs = document.getElementById('jetsonWsText');
                if (jWs && jetsonWs) jWs.textContent = jetsonWs.replace('ws://', '').split(':')[0] + ':9001';
            });
        }
```

Also update the config loading block (find `fetch('/config')` → `then(data => {`) to populate the new `#jetsonWsUrl` input and update `#roverAddressText`:
```javascript
        fetch('/config')
            .then(response => response.json())
            .then(data => {
                const host = extractHostname(data.server_url);
                document.getElementById('serverUrl').value = host;
                document.getElementById('timeout').value = data.timeout;
                document.getElementById('loraDestination').value = data.lora_destination || 0;
                if (data.jetson_ws_url) {
                    document.getElementById('jetsonWsUrl').value = data.jetson_ws_url;
                    const jWs = document.getElementById('jetsonWsText');
                    if (jWs) jWs.textContent = data.jetson_ws_url.replace('ws://', '').split('/')[0];
                }
                const rAddr = document.getElementById('roverAddressText');
                if (rAddr) rAddr.textContent = host;
                if (data.mode) setMode(data.mode);
            });
```

- [ ] **Step 7: Verify all status propagation in browser**

Open http://127.0.0.1:5000. Check:
1. **Initial state**: Top bar shows "STANDBY" (gray dot), Rover card shows "Unknown", Jetson card shows "Offline" (red)
2. **Send any command** (WiFi mode, any type): Rover card connection updates to "Online" (green) on success or "Error" (red) on failure. Top bar shows "PARTIAL" (yellow) if Jetson still offline.
3. **Telemetry bar**: Mode badge shows WiFi blue; switch to LoRa → badge turns purple
4. **Config save**: Fill Jetson WS URL field, click Save Config → button briefly shows "Saved ✓"
5. **Tab switching**: Commands ↔ Map works, Three.js scene still loads on Map tab

- [ ] **Step 8: Commit**

```bash
git add templates/index.html
git commit -m "feat: propagate device status to right panel and telemetry bar"
```

---

## Task 4: Run full test suite

**Files:** none new

- [ ] **Step 1: Run all tests**

```bash
cd c:/Users/busyp/nasa-hera
pytest tests/ -v
```

Expected: all 26 tests pass. The tests cover Flask endpoints and voxel logic only — no HTML/CSS tests exist. All 26 should still pass because no Python code changed.

Expected output (last line):
```
26 passed in X.XXs
```

- [ ] **Step 2: Final commit if tests pass**

```bash
git add templates/index.html
git commit -m "feat: complete UI redesign — mission-control dark theme with dashboard layout"
```

If tests fail, check that `FlaskServer.py` was not accidentally modified. The test suite does not test HTML.
