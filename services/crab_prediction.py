import pandas as pd
import numpy as np
import os
import torch
import torch.nn as nn
import torch.optim as optim


class CrabModel(nn.Module):
    def __init__(self, input_size=2, hidden_size=16):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, input_size)
    
    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        return self.fc(out)
    
class CrabPrediction():
    def __init__(self):
        super().__init__()
        

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.PATH = os.path.join(BASE_DIR, "model", "crab_model.pt")

        self.model = CrabModel()
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.01)

        self.checkpoint = torch.load(self.PATH,weights_only=False)
        self.model.load_state_dict(self.checkpoint['model_state_dict'])
        self.model.eval()
        self.min_vals = self.checkpoint['min_vals']
        self.max_vals = self.checkpoint['max_vals']
        
    def __create_sequences(self, data, seq_len=5):
        X, Y = zip(*[(data[i:i+seq_len], data[i+seq_len]) for i in range(len(data) - seq_len)])
        return np.array(X), np.array(Y)
    
    def __normalize(self, data):
        dataframe = pd.DataFrame(data, columns=["crab_id", "created_at", "width", "weight"])
        dataframe["created_at"] = pd.to_datetime(dataframe["created_at"])
        dataframe = dataframe.sort_values("created_at")
        last_date = dataframe["created_at"].max()
        
        dataframe_daily = dataframe.groupby(["crab_id","created_at"]).agg({
            "width":"mean",
            "weight":"mean"
        }).reset_index()
        
        data = dataframe_daily[["width","weight"]].values.astype(np.float32)

        min_vals = data.min(axis=0)
        max_vals = data.max(axis=0)
        data_scaled = (data - min_vals) / (max_vals - min_vals + 1e-8)

        return data_scaled, min_vals, max_vals, last_date 
    
    def train(self, data_list,seq_len=5, epochs=200):
        
        data_scaled, min_vals, max_vals, __ = self.__normalize(data_list)
        X, Y = self.__create_sequences(data_scaled, seq_len)
        
        X_tensor = torch.tensor(X, dtype=torch.float32)
        Y_tensor = torch.tensor(Y, dtype=torch.float32)
        for epoch in range(epochs):
            self.model.train()
            self.optimizer.zero_grad()
            output = self.model(X_tensor)
            loss = self.criterion(output, Y_tensor)
            loss.backward()
            self.optimizer.step()

            if epoch % 20 == 0:
                print(f"Epoch {epoch}, Loss: {loss.item():.6f}")
                
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'min_vals': min_vals,
            'max_vals': max_vals
        }, self.PATH)
        
        return "Training complete. Model saved as crab_model.pt"
    
    def predict_next_days(self, data_list, days_ahead=5, seq_len=5):
        
        if len(data_list) < seq_len:
            raise Exception("Not enough data")
        
        data_scaled, min_vals, max_vals, last_date = self.__normalize(data_list)
        seq_input = torch.tensor(data_scaled[-seq_len:], dtype=torch.float32).unsqueeze(0)

        predictions_scaled = []
        for _ in range(days_ahead):
            
            pred = self.model(seq_input).detach().numpy()
            # crab_id_scaled = seq_input[0][-1][0]

            new_row = np.array([
                pred[0][0],
                pred[0][1]
            ])

            predictions_scaled.append(new_row)

            seq_input = torch.tensor(
                np.vstack((seq_input[0][1:].numpy(), new_row)),
                dtype=torch.float32
            ).unsqueeze(0)
            
        # inverse normalize
        predictions = np.array(predictions_scaled) * (max_vals - min_vals) + min_vals
        result = predictions.tolist()
        return [[(last_date + pd.Timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S'), width, weight] for day, (width, weight) in enumerate(result,1) ] 



# CrabPrediction = CrabPrediction()

# data_list = [
#     [1,"2026-02-22", 15.54, 0.00],
#     [1,"2026-02-23", 16.63, 0.00],
#     [1,"2026-02-24", 15.01, 0.00],
#     [1,"2026-02-25", 15.39, 0.20],
#     [1,"2026-02-26", 16.00, 0.30],
#     [1,"2026-02-27", 16.50, 0.50],
#     [1,"2026-02-28", 16.80, 0.55],
#     [1,"2026-03-01", 17.20, 0.65],
#     [1,"2026-03-02", 17.35, 0.70],
#     [1,"2026-03-03", 17.50, 0.75],
#     [1,"2026-03-04", 17.60, 0.78],
#     [1,"2026-03-05", 17.70, 0.80],
#     [1,"2026-03-06", 17.80, 0.82],
# ]
# result = CrabPrediction.train(data_list)
# print(result)


# data_list = [
#     [3,"2026-02-24 18:47:36", 15.01, 0.0],
#     [3,"2026-02-25 18:47:36", 15.39, 0.2],
#     [3,"2026-02-26 18:47:36", 16.0, 0.3],
#     [3,"2026-02-27 18:47:36", 16.5, 0.5],
#     [3,"2026-02-28 18:47:36", 16.8, 0.55],
#     [3,"2026-03-01 18:47:36", 15.01, 0.0],
#     [3,"2026-03-02 18:47:36", 15.39, 0.2],
#     [3,"2026-03-03 18:47:36", 16.0, 0.3],
#     [3,"2026-03-04 18:47:36", 16.5, 0.5],
#     [3,"2026-03-05 18:47:36", 16.8, 0.55],
# ]

# result = CrabPrediction.predict_next_days(data_list=data_list)
# for created_at, width, weight in result:
#     print(f"Crab ID: {14}, Date: {created_at}, Predicted Width: {width:.2f}, Predicted Weight: {weight:.2f}")
