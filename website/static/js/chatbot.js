class Chatbot {

    constructor(botName) {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button'),
            
        }

    this.state = false;
    this.messages = [];
    this.name = botName;
    
}

display() {

    const {openButton, chatBox, sendButton} = this.args;


    openButton.addEventListener('click', () => this.toggleState(chatBox));

    sendButton.addEventListener('click', () => this.onSendButton(chatBox));

    const node = chatBox.querySelector('input');
    node.addEventListener('keyup', (keyEvent) => {
       
        if (keyEvent.key === "Enter") {
            this.onSendButton(chatBox);
        }
    })
}

toggleState(chatbox) {
    this.state = !this.state;
    // console.log("i'm toggling the state " + this.state);

    //show or hide the box
    if(this.state){
        
        chatbox.classList.add('chatbox--active');
    } else {
        chatbox.classList.remove('chatbox--active');
    }

}

onSendButton(chatbox) {

    var textField = chatbox.querySelector('input');

    let text1 = textField.value;

    if(text1 == "") {
        return;
     }


     let msg1 = {name: "User", message: text1};

     this.messages.push(msg1);
     let botName = this.name;

     fetch('/chatbot',  {
        method: 'POST',
        body:JSON.stringify({message: text1}),
        headers: {
            'Content-Type' : 'application/json'
        },
     })
     .then(r=> r.json())
     .then(r=> {
        let answers = r.answers

        for (let index in answers) {
            console.log("answer: " + answers[index]);
            let msg2 = {name: botName, message: answers[index]};
            this.messages.push(msg2);
        }
        this.updateChatText(chatbox);
        textField.value = "";
     }).catch((error) => {
        console.error("Error:", error);
        this.updateChatText(chatbox);
        textField.value="";
     });
}


updateChatText(chatbox) {
    var html = "";

    // let imageHeader = '<div class="chatbox__image--header"><img src="https://img.icons8.com/color/48/000000/circled-user-female-skin-type-5--v1.png"' +
    //  'alt="image"></div><div class="chatbox__content--header">';

   let botName = this.name;
    this.messages.slice().reverse().forEach(function(item) {
        if (item.name === botName) {
            html += '<div class="messages__item messages__item--operator">' + item.message + '</div>';
        } else {
            html +='<div class="messages__item messages__item--visitor">' + item.message + '</div>';
        }
    });

    const chatmessage = chatbox.querySelector('.chatbox__messages');
    chatmessage.innerHTML = html;
}


}


const chatbot = new Chatbot("Eleos");

// chatbot.state = true;
chatbot.display();
chatbot.toggleState(chatbot.args.chatBox);
chatbot.messages.push({name:chatbot.name, message: "Hi, I'm " +chatbot.name + ". How are you?"});

chatbot.updateChatText(chatbot.args.chatBox);


