var mediumLength = 100; // sentence avg. length: 20 words, a word on avg. is 5 letters

class Chatbot {

    constructor(botName) {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button'),
            
            
        }
    this.dots =  this.createDots(),    
    
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
     this.updateChatText([msg1]);
    

     fetch('/chatbot',  {
        method: 'POST',
        body:JSON.stringify({message: text1}),
        headers: {
            'Content-Type' : 'application/json'
        },
     })
     .then(r=> r.json())
     .then(r=> {
        var ans = [];

        for (let index in r.answers) {
            // console.log("answer: " + answers[index]);
            let msg2 = {name: botName, message: r.answers[index]};
            this.messages.push(msg2);
            ans.push(msg2);
        }
        this.updateChatText(ans);
        textField.value = "";
     }).catch((error) => {
        console.error("Error:", error);
        // this.updateChatText(chatbox);
        textField.value="";
     });
}


updateChatText(messages) {

    if(messages.length == 0) {
        return;
    }

    if(messages[0].name === this.name) {
        this.writeOperatorMessage(messages, 0, true); 
    } else {
        this.writeVisitorMessage(messages, 0); 
    }

}



writeOperatorMessage(messages, index, delay) {
	if(index === messages.length) return;
  
//   for (let index = 0;index<messages.length;index++) {
    const msg = messages[index];

    if(delay) {
        const duration = this.getMessageLoadingDuration(msg.message);
        this.showDots();
       this.scrollToBottom();
        setTimeout(() => {
            const div = document.createElement('div');
            div.className = 'messages__item messages__item--operator';
            div.innerHTML = msg.message;
            document.getElementById('chatbox_msgs').appendChild(div);
             this.hideDots();           
            this.scrollToBottom();
            this.writeOperatorMessage(messages, index+1, delay);
          }, duration);
    } else {
        const div = document.createElement('div');
        div.className = 'messages__item messages__item--operator';
        div.innerHTML = msg.message;
        document.getElementById('chatbox_msgs').appendChild(div);
        this.scrollToBottom();
        this.writeOperatorMessage(messages, index+1, delay);

    }
    
    
//   }  
 
}

writeVisitorMessage(messages, index) {

    if(index === messages.length) return;

    const msg = messages[index];

    const div = document.createElement('div');
    div.className = 'messages__item messages__item--visitor';
    div.innerHTML = msg.message;
    document.getElementById('chatbox_msgs').appendChild(div);
    this.scrollToBottom();
    this.writeVisitorMessage(messages, index+1);
}

scrollToBottom() {
    var element = document.getElementById("chatbox_msgs");
    element.scrollTop = element.scrollHeight;
}

// compute message loading duration
getMessageLoadingDuration(message) {

    let msgLen = message.length;
    let perc = Math.min(msgLen/mediumLength, 1.5);
	//in here you could use message.length to show dots for longer duration based on the length of the message
  const randomNum = 1000*perc + Math.random() * 1000;

//   console.log(`perc ${perc}, duration ${randomNum}`);

  return Math.round(randomNum / 100) * 100;
}


createDots() {
	const el = document.createElement('div');
  el.id = 'dotsDelay';
  el.style = "display: flex;align-items: center;"
	el.innerHTML = `
   
    <div class="dot"></div>
    <div class="dot"></div>
    <div class="dot"></div>
    <div id="invisibleColumn"></div>
  `
  el.classList.add("messages__item");
  el.classList.add("messages__item--operator");
//   el.classList.add("dot-shuttle")

	return el;
}

showDots() {
    
    document.getElementById('chatbox_msgs').appendChild(this.dots);
}

hideDots() {

    if(document.getElementById('dotsDelay')) {
        document.getElementById('dotsDelay').remove();
    }
    
}


}


// const dots = createDots();

const chatbot = new Chatbot("Eleos");

// chatbot.state = true;
chatbot.display();
chatbot.toggleState(chatbot.args.chatBox);
chatbot.messages.push({name:chatbot.name, message: "Hi, I'm " +chatbot.name + ". How are you?"});

chatbot.updateChatText([{name:chatbot.name, message: "Hi, I'm " +chatbot.name + ". How are you?"}]);
// setTimeout(chatbot.showDots(), 2000);
// chatbot.writeMessage([{name:"botName", message:"BBBBBBBBBBB"}, 
// {name:"botName", message:"WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"}], 0, true)


