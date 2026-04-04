# UI Surfaces: Paperclip vs Hermes

## Paperclip

Paperclip has an upstream native dashboard UI.

In local upstream development, it is served by the Paperclip server itself.

## Hermes

Hermes Agent does not appear to ship a comparable upstream operator dashboard UI.

For browser access, the recommended integration path is:

- Hermes API server
- Open WebUI as frontend

## Why this matters

This repo should not misrepresent a custom placeholder page as an upstream-native Hermes dashboard.

When we want a browser-accessible Hermes experience, the honest and supported path is Open WebUI.
