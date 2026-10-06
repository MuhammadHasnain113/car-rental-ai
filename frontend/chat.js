let sessionId = "session_" + Math.random().toString(36).substring(2, 9);
let ws = null;

const messagesContainer = document.getElementById("messages-container");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const newChatBtn = document.getElementById("new-chat-btn");
const welcomeHero = document.getElementById("welcome-hero");

function initWebSocket() {
  ws = new WebSocket(`ws://localhost:8000/ws/chat?session_id=${sessionId}`);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "token") {
      removeWelcomeHero();
      if (!currentAssistantBubble) {
        currentAssistantBubble = createAssistantRow();
      }
      currentAssistantBubble.textContent += data.token;
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } else if (data.type === "done") {
      if (currentAssistantBubble) {
        currentAssistantBubble.classList.remove("streaming-cursor");
      }
      currentAssistantBubble = null;
    } else if (data.type === "reset_ack") {
      resetViewToDefault();
    } else if (data.type === "error") {
      if (currentAssistantBubble) {
        currentAssistantBubble.textContent += `\n[Error: ${data.message}]`;
        currentAssistantBubble.classList.remove("streaming-cursor");
      }
      currentAssistantBubble = null;
    }
  };

  ws.onclose = () => {
    setTimeout(initWebSocket, 2000); // Reconnect if closed
  };
}

initWebSocket();

let currentAssistantBubble = null;

function removeWelcomeHero() {
  if (welcomeHero && welcomeHero.parentNode) {
    welcomeHero.remove();
  }
}

function resetViewToDefault() {
  messagesContainer.innerHTML = "";
  messagesContainer.appendChild(welcomeHero);
  currentAssistantBubble = null;
}

function createUserRow(text) {
  removeWelcomeHero();
  const row = document.createElement("div");
  row.className = "message-row user";
  row.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
  messagesContainer.appendChild(row);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function createAssistantRow() {
  const row = document.createElement("div");
  row.className = "message-row assistant";
  
  const avatar = document.createElement("div");
  avatar.className = "avatar bot";
  avatar.innerHTML = `
    <svg viewBox="0 0 24 24" width="18" height="18">
      <path fill="#7C5CFE" d="M12 0C12 6.627 6.627 12 0 12c6.627 0 12 5.373 12 12 0-6.627 5.373-12 12-12-6.627 0-12-5.373-12-12z"/>
    </svg>`;

  const bubble = document.createElement("div");
  bubble.className = "bubble streaming-cursor";

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesContainer.appendChild(row);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  return bubble;
}

function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function sendMessage(text) {
  if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;
  createUserRow(text);
  ws.send(JSON.stringify({ message: text }));
  userInput.value = "";
  userInput.style.height = "auto";
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage(userInput.value.trim());
});

// Auto-expand textarea on typing
userInput.addEventListener("input", () => {
  userInput.style.height = "auto";
  userInput.style.height = userInput.scrollHeight + "px";
});

// Allow Enter to send, Shift+Enter for newline
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event("submit"));
  }
});

// Suggestion card click handlers
document.querySelectorAll(".suggestion-card").forEach((btn) => {
  btn.addEventListener("click", () => {
    sendMessage(btn.dataset.prompt);
  });
});

// Reset Session Button
newChatBtn.addEventListener("click", () => {
  sessionId = "session_" + Math.random().toString(36).substring(2, 9);
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: "reset" }));
  }
  resetViewToDefault();
});