const root = document.documentElement;

document.addEventListener('pointermove', (event) => {
  root.style.setProperty('--mouse-x', `${event.clientX}px`);
  root.style.setProperty('--mouse-y', `${event.clientY}px`);
});

let sessionId = null;
let isSending = false;

function byId(id) {
  return document.getElementById(id);
}

function showFormError(message) {
  const error = byId('form-error');
  if (!error) return;
  error.textContent = message;
  error.style.display = 'block';
}

function hideFormError() {
  const error = byId('form-error');
  if (!error) return;
  error.textContent = '';
  error.style.display = 'none';
}

async function startSession() {
  const startBtn = byId('start-btn');
  if (!startBtn) return;

  hideFormError();

  const name = byId('f-name').value.trim() || 'User';
  const sex = byId('f-sex').value;
  const age = Number.parseInt(byId('f-age').value, 10);
  const height = Number.parseFloat(byId('f-height').value);
  const weight = Number.parseFloat(byId('f-weight').value);
  const hypertension = byId('f-hypertension').value;
  const diabetes = byId('f-diabetes').value;

  if (Number.isNaN(age) || age < 18 || age > 63) {
    showFormError('Age must be between 18 and 63.');
    return;
  }

  if (Number.isNaN(height) || height < 1.4 || height > 2.2) {
    showFormError('Height must be between 1.40 and 2.20 meters.');
    return;
  }

  if (Number.isNaN(weight) || weight < 30 || weight > 250) {
    showFormError('Weight must be between 30 and 250 kg.');
    return;
  }

  startBtn.textContent = 'Setting up your profile…';
  startBtn.disabled = true;

  try {
    const response = await fetch('/api/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, sex, age, height, weight, hypertension, diabetes })
    });

    const data = await response.json();

    if (!response.ok || data.error) {
      throw new Error(data.error || 'Server error. Please check the Flask backend.');
    }

    sessionId = data.session_id;
    showChat(name, sex, data.bmi, data.level, hypertension, diabetes, data.plans_found);

    addMessage('bot',
      `Hi ${name}! Welcome to your Calorie Sense AI coaching session.\n\n` +
      `Your BMI is ${data.bmi} (${data.level}). I loaded ${data.plans_found} matching plan(s) for your profile.\n\n` +
      `You can ask me things like:\n` +
      `• Give me a weekly workout plan\n` +
      `• What should I eat this week?\n` +
      `• How do I do a proper squat?\n` +
      `• Which exercises target my chest?\n\n` +
      `What would you like to work on first? 💪`
    );
  } catch (error) {
    showFormError(error.message || 'Could not reach the backend. Make sure app.py is running.');
    startBtn.textContent = 'Start My Coaching Session →';
    startBtn.disabled = false;
  }
}

async function sendMessage() {
  if (isSending || !sessionId) return;

  const input = byId('user-input');
  const sendBtn = byId('send-btn');
  const message = input.value.trim();
  if (!message) return;

  input.value = '';
  isSending = true;
  sendBtn.disabled = true;
  addMessage('user', message);
  setTyping(true);

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message })
    });

    const data = await response.json();
    setTyping(false);

    if (!response.ok || data.error) {
      addMessage('bot', `Error: ${data.error || 'Something went wrong.'}`);
    } else {
      addMessage('bot', data.reply);
    }
  } catch (error) {
    setTyping(false);
    addMessage('bot', 'Connection error. Please check that Flask is running and your internet connection is available.');
  }

  isSending = false;
  sendBtn.disabled = false;
  input.focus();
}

function showChat(name, sex, bmi, level, hypertension, diabetes, plans) {
  byId('profile-card').classList.add('hidden');
  byId('chat-card').classList.remove('hidden');

  const levelClass = level === 'Normal' ? 'badge-ok' : (level === 'Underweight' ? 'badge-warn' : 'badge-alert');
  const badges = byId('user-badges');

  badges.innerHTML = `
    <span class="badge badge-name">${escapeHtml(name)}</span>
    <span class="badge">BMI ${bmi}</span>
    <span class="badge ${levelClass}">${escapeHtml(level)}</span>
    <span class="badge">${escapeHtml(sex)}</span>
    ${hypertension === 'Yes' ? '<span class="badge badge-warn">Hypertension</span>' : ''}
    ${diabetes === 'Yes' ? '<span class="badge badge-warn">Diabetes</span>' : ''}
    <span class="badge">${plans} plan(s) matched</span>
  `;
}

function addMessage(role, text) {
  const chatBox = byId('chat-box');
  if (!chatBox) return;

  const messageWrapper = document.createElement('div');
  messageWrapper.className = `msg ${role}`;

  const label = document.createElement('div');
  label.className = 'msg-label';
  label.textContent = role === 'user' ? 'You' : 'Coach';

  const bubble = document.createElement('div');
  bubble.className = 'bubble markdown-body';
  if (role === 'bot' && typeof marked !== 'undefined') {
    bubble.innerHTML = marked.parse(text);
  } else {
    bubble.textContent = text;
  }

  messageWrapper.appendChild(label);
  messageWrapper.appendChild(bubble);
  chatBox.appendChild(messageWrapper);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function setTyping(isVisible) {
  const typing = byId('typing-row');
  const chatBox = byId('chat-box');
  if (!typing) return;
  typing.classList.toggle('hidden', !isVisible);
  if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

document.addEventListener('DOMContentLoaded', () => {
  const startBtn = byId('start-btn');
  const sendBtn = byId('send-btn');
  const input = byId('user-input');

  if (startBtn) startBtn.addEventListener('click', startSession);
  if (sendBtn) sendBtn.addEventListener('click', sendMessage);
  if (input) {
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') sendMessage();
    });
  }
});
