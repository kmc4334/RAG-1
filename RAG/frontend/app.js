const chatWindow = document.getElementById('chatWindow');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');


// Auto-focus input on load
userInput.focus();

// Chat Event Listeners
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendMessage();
});



function sendRecommendation(text) {
  userInput.value = text;
  sendMessage();
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  // 1. Add User Message
  addMessage(text, 'user');
  userInput.value = '';
  sendBtn.disabled = true;

  // 2. Show Typing Indicator
  const typingId = addTypingIndicator();
  scrollToBottom();

  try {
    // 3. Call API
    const response = await fetch('http://127.0.0.1:8000/chat/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: text
      })
    });

    if (!response.ok) throw new Error('API Error');

    const data = await response.json();

    // 4. Remove Typing Indicator & Add Assistant Message
    removeTypingIndicator(typingId);
    addMessage(data.answer, 'assistant');

  } catch (error) {
    removeTypingIndicator(typingId);
    addMessage("죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", 'assistant');
    console.error(error);
  } finally {
    sendBtn.disabled = false;
    userInput.focus();
    scrollToBottom();
  }
}

function addMessage(text, sender) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${sender}`;

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerText = text;

  msgDiv.appendChild(bubble);
  chatWindow.appendChild(msgDiv);
  scrollToBottom();
}

function addTypingIndicator() {
  const id = 'typing-' + Date.now();
  const msgDiv = document.createElement('div');
  msgDiv.className = 'message assistant';
  msgDiv.id = id;

  const bubble = document.createElement('div');
  bubble.className = 'typing';

  bubble.innerHTML = `
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    `;

  msgDiv.appendChild(bubble);
  chatWindow.appendChild(msgDiv);
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}
