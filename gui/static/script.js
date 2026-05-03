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
      `• Which exercises target my chest?\n` +
      `• What exercises help me the reduce/gain weight?\n\n` +
      `What would you like to work on first?`
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

  // Prediction Page
  const predictBtn = byId('predict-btn');
  if (predictBtn) {
    predictBtn.addEventListener('click', predictCalories);
    fetchWeather();
    
    const intensitySlider = byId('p-intensity');
    const intensityVal = byId('intensity-val');
    if (intensitySlider && intensityVal) {
      intensitySlider.addEventListener('input', (e) => {
        intensityVal.textContent = e.target.value;
      });
    }
  }
});

// Calorie Prediction 
let currentWeatherCondition = "Cloudy";

    // Indetify Geolocation with Users Permission falling back if to ip based location if the user denied or unsupported by not giving access to geolocation API
    function getUserLocation() {
      return new Promise((resolve) => {
        if (!navigator.geolocation) {
          console.warn('Geolocation not supported');
          resolve(null);
          return;
        }
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude });
          },
          (err) => {
            console.warn('Geolocation permission denied or error', err);
            resolve(null);
          }
        );
      });
    }

    async function fetchWeather() {
      const weatherCity = byId('weather-city');
      const weatherTemp = byId('weather-temp');
      const weatherDesc = byId('weather-desc');
      const weatherIcon = byId('weather-icon');

      if (!weatherCity) return;

      try {
        // Fetching location
        const clientPos = await getUserLocation();
        const payload = clientPos ? clientPos : {};
        const response = await fetch('/api/weather', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (response.ok && !data.error) {
          weatherCity.textContent = data.city;
          weatherTemp.textContent = Math.round(data.temp) + '°C';
          weatherDesc.textContent = data.description;
          currentWeatherCondition = data.condition;

          if (data.condition === "Sunny") {
            weatherIcon.textContent = "☀️";
            weatherIcon.style.color = "#fbbf24";
          } else if (data.condition === "Rainy") {
            weatherIcon.textContent = "🌧️";
            weatherIcon.style.color = "#60a5fa";
          } else {
            weatherIcon.textContent = "☁️";
            weatherIcon.style.color = "#94a3b8";
          }
        } else {
          weatherCity.textContent = "Weather unavailable";
          weatherDesc.textContent = data.error || "Could not fetch weather";
          weatherIcon.textContent = "⚠️";
        }
      } catch (err) {
        weatherCity.textContent = "Weather unavailable";
        weatherDesc.textContent = "Network error";
        weatherIcon.textContent = "⚠️";
      }
    }

async function predictCalories() {
  const predictBtn = byId('predict-btn');
  const errorText = byId('predict-error');

  if (!predictBtn) return;

  errorText.style.display = 'none';
  predictBtn.disabled = true;
  predictBtn.textContent = 'Predicting...';

  const gender = byId('p-gender').value;
  const age = Number(byId('p-age').value);
  const hr = Number(byId('p-hr').value);
  const duration = Number(byId('p-duration').value);
  const intensity = Number(byId('p-intensity').value);

  if (!age || age < 10 || age > 100) { 
    errorText.textContent = "Invalid age";
    errorText.style.display = 'block';
    predictBtn.disabled = false;
    predictBtn.textContent = 'Predict Calories Burned →';
    return; 
  }
  if (!hr || hr < 40 || hr > 220) { 
    errorText.textContent = "Invalid heart rate";
    errorText.style.display = 'block';
    predictBtn.disabled = false;
    predictBtn.textContent = 'Predict Calories Burned →';
    return;
  }
  if (!duration || duration <= 0 || duration > 10) { 
    errorText.textContent = "Invalid duration";
    errorText.style.display = 'block';
    predictBtn.disabled = false;
    predictBtn.textContent = 'Predict Calories Burned →';
    return; 
  }
  if (!intensity || intensity < 1 || intensity > 10) { 
    errorText.textContent = "Invalid intensity (1-10)"; 
    errorText.style.display = 'block'; 
    predictBtn.disabled = false; 
    predictBtn.textContent = 'Predict Calories Burned →'; 
    return; 
  }

  try {
    const response = await fetch('/api/predict_calorie', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gender, age, hr, duration, intensity, condition: currentWeatherCondition })
    });

    const data = await response.json();

    if (!response.ok || data.error) {
      errorText.textContent = data.error || "Prediction failed";
      errorText.style.display = 'block';
    } else {
      byId('result-placeholder').classList.add('hidden');
      byId('result-display').classList.remove('hidden');

      const targetVal = data.calories_burned;
      animateValue(byId('calorie-value'), 0, targetVal, 1500);

      const calorieValueEl = byId('calorie-value');
      calorieValueEl.style.webkitTextFillColor = 'transparent';

      if (targetVal < 200) {
        calorieValueEl.style.background = 'linear-gradient(135deg, #4ade80, #10b981)';
        calorieValueEl.style.textShadow = '0 0 20px rgba(16, 185, 129, 0.3)';
      } else if (targetVal < 400) {
        calorieValueEl.style.background = 'linear-gradient(135deg, #fbbf24, #f59e0b)';
        calorieValueEl.style.textShadow = '0 0 20px rgba(245, 158, 11, 0.3)';
      } else if (targetVal < 600) {
        calorieValueEl.style.background = 'linear-gradient(135deg, #f87171, #ef4444)';
        calorieValueEl.style.textShadow = '0 0 20px rgba(239, 68, 68, 0.3)';
      } else {
        calorieValueEl.style.background = 'linear-gradient(135deg, #c084fc, #a855f7)';
        calorieValueEl.style.textShadow = '0 0 20px rgba(168, 85, 247, 0.3)';
      }
      calorieValueEl.style.webkitBackgroundClip = 'text';
    }
  } catch (err) {
    errorText.textContent = "Network error";
    errorText.style.display = 'block';
  }

  predictBtn.disabled = false;
  predictBtn.textContent = 'Predict Calories Burned →';
}

function animateValue(obj, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const easeProgress = 1 - Math.pow(1 - progress, 4);
    obj.innerHTML = (easeProgress * (end - start) + start).toFixed(2);
    if (progress < 1) {
      window.requestAnimationFrame(step);
    } else {
      obj.innerHTML = end.toFixed(2);
    }
  };
  window.requestAnimationFrame(step);
}
