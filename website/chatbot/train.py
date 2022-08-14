import json
from preprocessing import tokenize, stem
from model import NeuralNet
from preprocessing import bag_of_words
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader


with open('website/chatbot/intents.json', 'r') as f:
    intents = json.load(f)
    
    
all_words = []
tags = []    
xy=[]


for intent in intents['intents']:
    tag = intent['tag']
    tags.append(tag)
    
    for pattern in intent['patterns']:
        words = tokenize(pattern)
        all_words.extend(words)
        xy.append((words, tag))
        
ignore_words = ['?', '!', '.', ',']

all_words = [stem(w) for w in all_words if w not in ignore_words]
all_words = sorted(set(all_words))
tags = sorted(set(tags))

x_train = []
y_train = []

for (pattern_sentence, tag) in xy:
    bag = bag_of_words(pattern_sentence, all_words)
    x_train.append(bag)
    
    label = tags.index(tag)
    y_train.append(label) # CrossInteropyLoss
    
 
x_train = np.array(x_train)
y_train = np.array(y_train)
    
# print(all_words)        
 
 
class ChatDataset(Dataset):
    
    def __init__(self):
        self.n_samples = len(x_train)
        self.x_data = x_train
        self.y_data = y_train
        
    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]
    
    def __len__(self):
         return self.n_samples


# hyper paramters
batch_size = 8 # for the example
hidden_size = 8
output_size = len(tags)
input_size = len(all_words) # equals to len(x_train[0])
learning_rate = 0.001
num_epochs = 2000

# print(input_size, len(all_words))
# print(output_size, tags)
     
dataset = ChatDataset()    
train_loader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=True, num_workers=0) #num_workers are for threading (causes problems on windwos)

# gpu support
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

model = NeuralNet(input_size=input_size,hidden_size=hidden_size, output_size=output_size).to(device)

 
# loss and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)     

for epoch in range(num_epochs):
    for (words, labels) in train_loader:
        words = words.to(device)
        
        labels = labels.to(device, dtype=torch.long)
        
        #forward
        outputs = model(words)
        loss = criterion(outputs, labels)
        
        #backward and optimizer step
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
    if (epoch+1) % 100 == 0:
        print(f'epoch {epoch+1}/{num_epochs}, loss={loss.item():.4f}')    
        
print(f'final loss, loss={loss.item():.4f}')    

## save the model
data = {
    "model_state": model.state_dict(),
    "input_size": input_size,
    "output_size": output_size,
    "hidden_size": hidden_size,
    "all_words": all_words,
    "tags": tags
}    

FILE = "website/chatbot/data.pth"

torch.save(data, FILE)

print(f'training complete. File saved to {FILE}')
       