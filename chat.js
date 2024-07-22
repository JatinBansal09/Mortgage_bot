document.addEventListener('DOMContentLoaded', function() {
    const chatIcon = document.getElementById('chat-icon');
    const chatWindow = document.getElementById('chat-window');
    const chatBody = document.getElementById('chat-body');
    const userInput = document.getElementById('userInput');
    const typingIndicator = document.getElementById('typing-indicator');

    function generateSessionId(length = 16) {
        const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let session_id = '';
        for (let i = 0; i < length; i++) {
            const randomIndex = Math.floor(Math.random() * charset.length);
            session_id += charset[randomIndex];
        }
        return session_id;
    }

    // Function to get or generate a session ID
    function getSessionId() {
        const storageKey = 'MY_SESSION_ID';
        let session_id = localStorage.getItem(storageKey);
        if (!session_id) {
            session_id = generateSessionId();
            localStorage.setItem(storageKey, session_id);
        }
        return session_id;
    }

    chatIcon.addEventListener('click', function() {
        chatWindow.style.display = 'flex';
        setTimeout(displayInitialMessage, 2000);  // Simulate typing delay
    });

    userInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            const message = userInput.value;
            if (message.trim() !== '') {
                addMessage('Guest', message);
                sendMessageToRasa(message);
                userInput.value = '';
            }
        }
    });

    function displayInitialMessage() {
        typingIndicator.style.display = 'none';
        addMessage('SS Mortgage', "Hello!");
        // Send "Hi" to the Rasa model 2 seconds after the initial message
        setTimeout(function() {
            sendMessageToRasa('Hi', true);
        }, 2000);
    }

    function addMessage(sender, text, buttons = []) {
        const messageElement = document.createElement('div');
        messageElement.className = 'chat-message';
        // Replace \n with <br> for proper formatting
        const formattedText = formatText(text);
        messageElement.innerHTML = `<strong>${sender}:</strong> ${formattedText}`;
        chatBody.appendChild(messageElement);

        if (buttons.length > 0) {
            const buttonsElement = document.createElement('div');
            buttonsElement.className = 'chat-buttons';
            buttons.forEach(button => {
                const buttonElement = document.createElement('button');
                buttonElement.innerHTML = button.title;
                buttonElement.addEventListener('click', () => {
                    addMessage('Guest', button.title);
                    sendMessageToRasa(button.payload);
                });
                buttonsElement.appendChild(buttonElement);
            });
            chatBody.appendChild(buttonsElement);
        }

        chatBody.scrollTop = chatBody.scrollHeight;

        if (text.includes("At Sandhu and Sran Mortgages, we provide swift and simple mortgage solutions, helping you save big on mortgage expenses with custom plans and lightning-fast approvals. Join our extended family of satisfied customers today!")) {
            sendMessageToRasa('/restart', false); // Send restart command to Rasa
        }
    }

    const session_id = getSessionId();
    
    // Function to send a message to Rasa
    async function sendMessageToRasa(message, displayInChat = true) {

        const typingIndicatorElement = document.createElement('div');
        typingIndicatorElement.className = 'chat-message typing-indicator';
        typingIndicatorElement.innerHTML = '<strong>S.S. Mortgages is typing...</strong>';
        chatBody.appendChild(typingIndicatorElement);
        chatBody.scrollTop = chatBody.scrollHeight;

        fetch('http://localhost:5005/webhooks/rest/webhook', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({sender: session_id, message: message })
        })
        .then(response => response.json())
        .then(data => {
            chatBody.removeChild(typingIndicatorElement);

            let fullResponse = '';
            data.forEach(reply => {
                if (reply.text) {
                    fullResponse += reply.text + '<br>\n';
                }
                if (reply.buttons) {
                    addMessage('<br><br>'+'SS Mortgage', fullResponse.trim(), reply.buttons);
                    fullResponse = ''; // Reset the full response after adding buttons
                }
            });
            if (fullResponse.trim() && displayInChat) {
                addMessage('<br><br>'+'SS Mortgage', fullResponse.trim());
            }
        })
        .catch(error => {
            chatBody.removeChild(typingIndicatorElement);
            console.error('Error:', error);
        });
    }

    function formatText(text) {
        // Convert Markdown links to HTML
        let formattedText = text.replace(/\n/g, '<br><br>');
        formattedText = formattedText.replace(/\u001B\[4m/g, '<u>').replace(/\u001B\[0m/g, '</u>');

        formattedText = formattedText.replace(/\[([^\]]+)\]\s*\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        // Convert underline ANSI escape codes to HTML underline tags

        return formattedText;
    }

    window.addEventListener('beforeunload', function() {
        sendMessageToRasa('/restart', false); // Send restart command to Rasa
    });
});