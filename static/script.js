const themeToggle = document.querySelector('.theme-toggle');
const body = document.body;
const chatContainer = document.getElementById('chatContainer');
const messageInput = document.querySelector('.message-input');
const sendButton = document.querySelector('.send-button');
const typingIndicator = document.querySelector('.typing-indicator');

// Check if backend is available
let backendAvailable = true;

// Theme toggling
let isDarkTheme = false;
if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        isDarkTheme = !isDarkTheme;
        body.setAttribute('data-theme', isDarkTheme ? 'dark' : 'light');
        themeToggle.innerHTML = isDarkTheme ? 
            '<i class="fas fa-sun"></i>' : 
            '<i class="fas fa-moon"></i>';
    });
}

// Chat functionality
function createMessageElement(content, isUser = false, isFake = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    let statusIcon = '';
    if (!isUser && isFake !== null) {
        if (isFake === true) {
            statusIcon = '<div class="fake-indicator">⚠️</div>';
        } else if (isFake === false) {
            statusIcon = '<div class="real-indicator">✅</div>';
        }
    }
    
    messageDiv.innerHTML = `
        <div class="avatar">${isUser ? 'U' : 'AI'}</div>
        <div class="message-bubble">
            ${statusIcon}
            <div class="message-content">${content}</div>
        </div>
    `;
    
    return messageDiv;
}

function addMessage(content, isUser = false, isFake = null) {
    const messageElement = createMessageElement(content, isUser, isFake);
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return messageElement;
}

function showTypingIndicator() {
    if (typingIndicator) {
        typingIndicator.style.display = 'block';
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

function hideTypingIndicator() {
    if (typingIndicator) {
        typingIndicator.style.display = 'none';
    }
}

// Improved analyzeMessage with better error handling
async function analyzeMessage(userMessage) {
    // First check backend availability
    if (!backendAvailable) {
        return performBasicAnalysis(userMessage);
    }

    try {
        console.log('🔍 Sending analysis request...');
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: userMessage })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('✅ Analysis successful:', result);
            return result;
        } else {
            console.warn('⚠️ Backend response not OK, using fallback');
            backendAvailable = false;
            return performBasicAnalysis(userMessage);
        }
    } catch (error) {
        console.error('❌ Backend connection failed:', error);
        backendAvailable = false;
        return performBasicAnalysis(userMessage);
    }
}

// Enhanced fallback analysis
function performBasicAnalysis(text) {
    const lowerText = text.toLowerCase();
    console.log('🔄 Using fallback analysis for:', text);

    // Enhanced pattern detection
    const fakePatterns = {
        high: [
            'weather modification', 'chemtrails', 'government creating storms',
            'climate weapon', 'haarp', 'geoengineering',
            'make $', 'earn $', '$10000', '$10,000', 'weekly income',
            'make money from home', 'work from home', 'financial freedom',
            'get rich', 'become rich', 'money fast', 'easy money',
            'guaranteed income', 'millionaire', 'cash fast'
        ],
        medium: [
            'secret', 'hidden truth', 'they don\'t want you', 'shocking',
            'does the work of', 'replaces all', 'one gadget that',
            'but stores won\'t sell', 'banned by', 'doctors hate this',
            'lose weight fast', 'instant results', 'miracle',
            'big companies hate', 'never before seen', 'revolutionary',
            'simple trick', 'one weird trick', 'passive income'
        ]
    };

    const realPatterns = [
        'according to official data', 'research shows', 'study found',
        'official source', 'verified information', 'peer-reviewed',
        'clinical trial', 'Reuters', 'Associated Press', 'BBC', 'CNN',
        'study published in', 'research from', 'data from',
        'according to experts', 'scientists say', 'medical professionals'
    ];

    let fakeScore = 0;
    let realScore = 0;

    // Check high confidence fake patterns
    fakePatterns.high.forEach(pattern => {
        if (lowerText.includes(pattern)) fakeScore += 3;
    });

    // Check medium confidence fake patterns
    fakePatterns.medium.forEach(pattern => {
        if (lowerText.includes(pattern)) fakeScore += 2;
    });

    // Check real patterns
    realPatterns.forEach(pattern => {
        if (lowerText.includes(pattern)) realScore += 3;
    });

    // Additional checks
    if (/\$\d+/.test(text)) fakeScore += 2;
    if (text.includes('!!!') || text.includes('URGENT!')) fakeScore += 1;

    console.log(`📊 Fake score: ${fakeScore}, Real score: ${realScore}`);

    if (fakeScore >= 3) {
        const confidence = Math.min(95, 60 + (fakeScore * 5));
        return {
            result: `⚠️ This appears to be unreliable information (confidence: ${confidence}%). Common scam/fake news patterns detected.`,
            is_fake: true,
            confidence: confidence,
            source: "fallback_analysis"
        };
    } else if (realScore >= 3) {
        const confidence = Math.min(95, 60 + (realScore * 5));
        return {
            result: `✅ This appears to be reliable information (confidence: ${confidence}%). Contains credible source indicators.`,
            is_fake: false,
            confidence: confidence,
            source: "fallback_analysis"
        };
    } else {
        return {
            result: "🤔 Unable to determine reliability with basic analysis. Please verify with official sources.",
            is_fake: null,
            confidence: 50,
            source: "fallback_uncertain"
        };
    }
}

// Send message to server (optional)
async function sendMessageToServer(content, isUser = true) {
    if (!backendAvailable) return;

    try {
        await fetch('/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: content,
                is_user: isUser,
            })
        });
    } catch (error) {
        console.log('Message save failed, continuing without save');
    }
}

// Get messages from server (optional)
async function getMessagesFromServer() {
    if (!backendAvailable) {
        showWelcomeMessage();
        return;
    }

    try {
        const response = await fetch('/messages');
        if (response.ok) {
            const messages = await response.json();
            if (messages.length === 0) {
                showWelcomeMessage();
            } else {
                messages.forEach(message => {
                    addMessage(message.content, message.is_user, null);
                });
            }
        } else {
            showWelcomeMessage();
        }
    } catch (error) {
        showWelcomeMessage();
    }
}

function showWelcomeMessage() {
    addMessage("🔍 Hello! I'm an AI assistant for news verification. Send me a news story, and I'll analyze its reliability.", false);
}

// FEEDBACK AND TRAINING FUNCTIONS
function addFeedbackButtons(messageElement, userMessage, botResponse, isFake, confidence) {
    if (!backendAvailable) return;

    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'feedback-buttons';
    
    feedbackDiv.innerHTML = `
        <div class="feedback-container">
            <span class="feedback-question">Was this analysis correct?</span>
            <div class="feedback-buttons-group">
                <button class="feedback-btn correct" data-action="yes">✅ Yes</button>
                <button class="feedback-btn incorrect" data-action="no">❌ No</button>
                <button class="feedback-btn training" data-action="train">🎯 Add to Training</button>
            </div>
        </div>
    `;
    
    const buttons = feedbackDiv.querySelectorAll('.feedback-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            handleFeedback(action, userMessage, botResponse, isFake, confidence, this);
        });
    });
    
    messageElement.querySelector('.message-bubble').appendChild(feedbackDiv);
}

async function handleFeedback(action, userMessage, botResponse, isFake, confidence, buttonElement) {
    if (!backendAvailable) {
        alert('Backend unavailable. Feedback features disabled.');
        return;
    }

    const buttonsContainer = buttonElement.closest('.feedback-buttons-group');
    const allButtons = buttonsContainer.querySelectorAll('.feedback-btn');
    
    switch(action) {
        case 'yes':
            await sendFeedback(true, userMessage, botResponse, isFake, confidence, allButtons, buttonsContainer);
            break;
        case 'no':
            await sendFeedback(false, userMessage, botResponse, isFake, confidence, allButtons, buttonsContainer);
            break;
        case 'train':
            await addToTraining(userMessage, isFake, allButtons, buttonsContainer);
            break;
    }
}

async function sendFeedback(isCorrect, userMessage, botResponse, isFake, confidence, buttons, container) {
    try {
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.6';
        });

        const response = await fetch('/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_message: userMessage,
                bot_response: botResponse,
                is_fake: isFake,
                confidence: confidence,
                user_feedback: isCorrect
            })
        });
        
        if (response.ok) {
            const feedbackText = isCorrect ? 
                '<span style="color: green; font-size: 0.9em;">✓ Thanks for your feedback!</span>' :
                '<span style="color: orange; font-size: 0.9em;">✓ Noted - analysis was incorrect</span>';
            container.innerHTML = feedbackText;
        } else {
            throw new Error('Server error');
        }
    } catch (error) {
        console.error('Error sending feedback:', error);
        container.innerHTML = '<span style="color: red; font-size: 0.9em;">✗ Error sending feedback</span>';
    }
}

async function addToTraining(text, isFake, buttons, container) {
    try {
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.6';
        });

        const response = await fetch('/training-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                is_fake: isFake,
                category: 'user_added',
                source: 'user_feedback'
            })
        });
        
        if (response.ok) {
            container.innerHTML = '<span style="color: green; font-size: 0.9em;">✓ Added to training data!</span>';
        } else {
            throw new Error('Server error');
        }
    } catch (error) {
        console.error('Error adding to training:', error);
        container.innerHTML = '<span style="color: red; font-size: 0.9em;">✗ Error adding to training</span>';
    }
}

// Simulate bot response
async function simulateBotResponse(userMessage) {
    showTypingIndicator();
    
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    try {
        const analysis = await analyzeMessage(userMessage);
        hideTypingIndicator();
        
        const messageElement = addMessage(analysis.result, false, analysis.is_fake);
        
        if (analysis.is_fake !== null && backendAvailable) {
            addFeedbackButtons(messageElement, userMessage, analysis.result, analysis.is_fake, analysis.confidence);
        }
        
        await sendMessageToServer(analysis.result, false);
        
    } catch (error) {
        hideTypingIndicator();
        const errorMessage = "Sorry, an error occurred while analyzing the message. Please try again.";
        addMessage(errorMessage, false);
    }
}

// Handle sending messages
function handleSendMessage() {
    const message = messageInput.value.trim();
    if (message) {
        addMessage(message, true);
        sendMessageToServer(message, true);
        messageInput.value = '';
        simulateBotResponse(message);
    }
}

// Event listeners
if (sendButton) {
    sendButton.addEventListener('click', handleSendMessage);
}

if (messageInput) {
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing chat application...');
    getMessagesFromServer();
});