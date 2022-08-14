from msilib.schema import tables
import random
import json
import torch
from website.chatbot.model  import NeuralNet
from website.chatbot.preprocessing import bag_of_words, tokenize
from ..models import Aok


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

with open('website/chatbot/intents.json', 'r') as f:
     intents = json.load(f)
     
     
FILE = 'website/chatbot/data.pth'

data = torch.load(FILE)


input_size = data['input_size']
hidden_size = data['hidden_size']
output_size = data['output_size']     

all_words = data["all_words"]
tags = data["tags"]
model_state = data["model_state"]

model = NeuralNet(input_size=input_size, hidden_size=hidden_size, output_size=output_size)
model.load_state_dict(model_state)
model.eval()

bot_name = "Davi"

# print("let's chat! type 'quit' to exit")

# while True:
#     sentence = input("You: ")
    
#     if sentence == "quit":
#         break
    
#     tokenized_sentence = tokenize(sentence)
#     x = bag_of_words(tokenized_sentence, all_words)
#     x = x.reshape(1, x.shape[0]) # need to understand
#     x = torch.from_numpy(x).to(device)
    
#     output = model(x)
    
#     _, predicted = torch.max(output, dim=1)
    
#     tag = tags[predicted.item()]
    
#     ## check prob
#     probs = torch.softmax(output, dim=1)
#     prob = probs[0][predicted.item()]
    
#     if prob.item() > 0.75:
#         for intent in intents["intents"]:
#             if tag == intent["tag"]:
#                 print(f'{bot_name}: {random.choice(intent["responses"])}')   
#     else:
#         print(f'{bot_name}: Sorry, I don\'t understand')   
        
   
isAokSuggested = False
isAokSuggestedCounter = 5
        
def get_response(sentence):
    
    tokenized_sentence = tokenize(sentence)
    x = bag_of_words(tokenized_sentence, all_words)
    x = x.reshape(1, x.shape[0]) # need to understand
    x = torch.from_numpy(x).to(device)

    output = model(x)

    _, predicted = torch.max(output, dim=1)

    tag = tags[predicted.item()]

    ## check prob
    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]

    if prob.item() > 0.75:
        for intent in intents["intents"]:
            if tag == intent["tag"]:
                match tag:
                    case "suggestAok":
                        suggestedAok = suggestAoK(None)
                        return(suggestedAok)   
                    case _:
                        return [random.choice(intent["responses"])]

    return ["I don't understand..."]


def suggestAoK(categories):
    global isAokSuggested
    global isAokSuggestedCounter
    
    # get a random aok from the database
    query = Aok.query
    msgs = []  
    
    if categories is None:
    
        numOfRows = query.count()
         
        randIndex = random.randint(0, numOfRows-1)
        
        randAok = query.get(randIndex)
        
        if randAok is not None:
            # return randAok.act
            msgs.append(randAok.act)
            if not isAokSuggested:
                extraMsg = "Would you like another? You can specify a category by typing \"for friend, family, coworker, stranger\""
                isAokSuggested = True
                msgs.append(extraMsg)
                # return [randAok.act, extraMsg]                        
            else:
            #     return [randAok.act]  
                isAokSuggestedCounter = isAokSuggestedCounter-1
                if isAokSuggestedCounter == 0:
                    isAokSuggested = False
                    isAokSuggestedCounter = 5
            
            
    else:
        #TODO: search with categories
        msgs.append("TBD")
        
    if len(msgs) == 0:
        msgs.append("Sorry couldn't find one this time")
        
    return msgs         
   
   
   
   
    
# if __name__ == "__main__":
#     print("Let's chat! (type 'quit' to exit)")
#     while True:
#         # sentence = "do you use credit cards?"
#         sentence = input("You: ")
#         if sentence == "quit":
#             break

#         resp = get_response(sentence)
#         print(resp)
