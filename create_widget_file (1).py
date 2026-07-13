"""
Run this once to (re)create templates/_chatbot_widget.html with the
correct content. This avoids copy/paste mistakes.

HOW TO USE:
1. Save this file into your project folder (same folder as app.py):
   C:\\Users\\EBL_SALES\\Downloads\\servicehub\\servicehub5\\servicehub\\create_widget_file.py
2. In PowerShell, from that folder, run:
   python create_widget_file.py
3. It will create/overwrite templates/_chatbot_widget.html correctly.
"""

import os

WIDGET_HTML = r"""<!--
  Chatbot widget include.
-->
<style>
  #chatbot-bubble {
    position: fixed;
    bottom: 24px;
    right: 24px;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: #2563eb;
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    cursor: pointer;
    box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    z-index: 9999;
    border: none;
  }
  #chatbot-window {
    position: fixed;
    bottom: 96px;
    right: 24px;
    width: 320px;
    max-width: 90vw;
    height: 420px;
    max-height: 70vh;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.25);
    display: none;
    flex-direction: column;
    overflow: hidden;
    z-index: 9999;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  }
  #chatbot-window.open { display: flex; }
  #chatbot-header {
    background: #2563eb;
    color: #fff;
    padding: 12px 16px;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  #chatbot-close { cursor: pointer; background: none; border: none; color: #fff; font-size: 18px; }
  #chatbot-messages {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    background: #f4f6fa;
    font-size: 14px;
  }
  .chatbot-msg { margin-bottom: 10px; max-width: 85%; padding: 8px 12px; border-radius: 10px; line-height: 1.4; }
  .chatbot-msg.bot { background: #e5e9f2; color: #111; border-bottom-left-radius: 2px; }
  .chatbot-msg.user { background: #2563eb; color: #fff; margin-left: auto; border-bottom-right-radius: 2px; }
  #chatbot-input-row { display: flex; border-top: 1px solid #e5e9f2; }
  #chatbot-input {
    flex: 1;
    border: none;
    padding: 12px;
    font-size: 14px;
    outline: none;
  }
  #chatbot-send {
    border: none;
    background: #2563eb;
    color: #fff;
    padding: 0 16px;
    cursor: pointer;
    font-size: 14px;
  }
</style>

<button id="chatbot-bubble" aria-label="Chat with us">Chat</button>

<div id="chatbot-window">
  <div id="chatbot-header">
    <span>ServiceHub Assistant</span>
    <button id="chatbot-close">X</button>
  </div>
  <div id="chatbot-messages"></div>
  <div id="chatbot-input-row">
    <input id="chatbot-input" type="text" placeholder="Type a message..." />
    <button id="chatbot-send">Send</button>
  </div>
</div>

<script>
(function () {
  const bubble = document.getElementById('chatbot-bubble');
  const win = document.getElementById('chatbot-window');
  const closeBtn = document.getElementById('chatbot-close');
  const messages = document.getElementById('chatbot-messages');
  const input = document.getElementById('chatbot-input');
  const sendBtn = document.getElementById('chatbot-send');

  let greeted = false;

  function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = 'chatbot-msg ' + sender;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function toggleChat() {
    win.classList.toggle('open');
    if (win.classList.contains('open') && !greeted) {
      addMessage("Hi! How can I help you today?", 'bot');
      greeted = true;
    }
  }

  bubble.addEventListener('click', toggleChat);
  closeBtn.addEventListener('click', toggleChat);

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    addMessage(text, 'user');
    input.value = '';

    try {
      const res = await fetch('/api/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      addMessage(data.reply, 'bot');
    } catch (err) {
      addMessage("Sorry, something went wrong. Please try again.", 'bot');
    }
  }

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') sendMessage();
  });
})();
</script>
"""

os.makedirs('templates', exist_ok=True)
path = os.path.join('templates', '_chatbot_widget.html')
with open(path, 'w', encoding='utf-8') as f:
    f.write(WIDGET_HTML)

print(f"Wrote correct widget file to: {os.path.abspath(path)}")
print(f"Length: {len(WIDGET_HTML)} characters")
