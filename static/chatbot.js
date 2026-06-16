function sendMessage() {

    let input = document.getElementById("userInput");
    let message = input.value;

    let chatBox = document.getElementById("chat-box");

    chatBox.innerHTML += `
        <div class="user-message">${message}</div>
    `;

    let response = "";

    if(message.toLowerCase().includes("fever")){
        response = "Fever may indicate an infection. Please stay hydrated and consult a doctor if symptoms persist.";
    }
    else if(message.toLowerCase().includes("cough")){
        response = "A cough may be caused by cold, flu, or allergies.";
    }
    else if(message.toLowerCase().includes("vaccine")){
        response = "Vaccination helps prevent many infectious diseases.";
    }
    else{
        response = "Please consult a healthcare professional for accurate advice.";
    }

    chatBox.innerHTML += `
        <div class="bot-message">${response}</div>
    `;

    input.value = "";
}
