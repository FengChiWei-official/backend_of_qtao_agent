'''import numpy as np
import pandas as pd

from sklearn.metrics import f1_score

from service.Dialogue_manage import DialogueManage, Act
from service.language_understand import ExtentLanguageUnderstand, LanguageUnderstand
from torch.utils.data import DataLoader, Dataset


"""class MyDataset(Dataset):
    def __init__(self, df):
        self.df = df
    def __len__(self):
        return len(self.df)
    def __getitem__(self, idx):
        raw_data = data_test["utt"].iloc[idx]
        raw_intent = data_test["intent"].iloc[idx]
        return raw_data, raw_intent


dataset = MyDataset(data_test)
dataloader = DataLoader(dataset, batch_size=1, shuffle=True, num_workers=2)"""

data = pd.read_json(r'../dataset/' + 'zh-CN(convert olly).jsonl', lines=True)
data_test = data[data["partition"] == "http_test"][:]
NLU = ExtentLanguageUnderstand()
NLU_improved = LanguageUnderstand("../saved/threshold.json")
DM = DialogueManage()


# begin with 0
n_classes = 5  # intent类别数
weather_query = 59
transport_ticket = 57
transport_query = 55
takeaway_order = 53
takeaway_query = 54
recommendation_locations = 49
positive_class_codes = [weather_query, transport_query, transport_ticket, takeaway_order, takeaway_query,
                        recommendation_locations]

# string -__dialog_manager.intentMap-> int - __dialog_manager.__call__ -> act
"""intent_mapping = {
    "weather_query": 59,
    "transport_ticket": 57,
    "transport_query": 55,
    "takeaway_order": 53,
    "takeaway_query": 54,
    "recommendation_locations": 49
}"""



pro_prob_dict = dict()
neg_prob_dict = dict()

# intent in action
label = []
hat = []
prop_matrix = []
# intent in action
imp_label = []
imp_hat = []
assert hat == imp_hat
imp_prop_matrix = []


# travel the dataset
for i in range(len(data_test)):
    raw_data = data_test["utt"].iloc[i]
    raw_intent = data_test["intent"].iloc[i]

    #NLU

    intent, _, raw_intent_props = NLU(raw_data)
    intent_props = raw_intent_props.detach().numpy().T
    hat.append(DM(intent, None))
    # need sub 1?
    label.append(DM(DM.intent_map.index(raw_intent), None))
    prop_matrix.append(intent_props)

    # imp NLU

    imp_intent, _ = NLU_improved(raw_data)
    imp_hat.append(DM(imp_intent, None))
    imp_label.append(label[-1])

for act in Act:
    # binarize
    action_based_binary_label = (np.array(label) == act)
    action_based_binary_hat = (np.array(hat) == act)

    action_based_binary_imp_label = (np.array(imp_label) == act)
    action_based_binary_imp_hat = (np.array(imp_hat) == act)

    print(f"original NLU in act {act}")
    # print(f1_score([1 if x else 0 for x in y_label_binary], [1 if x else 0 for x in y_probLB_binary], average='binary'))
    print(f1_score(action_based_binary_label, action_based_binary_hat))
    print(f" NLU improved in act {act}")
    print(f1_score(action_based_binary_imp_label, action_based_binary_imp_hat))
'''