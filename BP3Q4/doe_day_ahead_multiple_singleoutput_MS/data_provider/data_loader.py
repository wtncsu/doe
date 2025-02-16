import os
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from utils.timefeatures import time_features
import warnings

warnings.filterwarnings('ignore')


class Dataset_DOE_hour(Dataset):
    def __init__(self, root_path, data_path, features, target,
                 flag='train', size=None, scale=True, timeenc=0, freq='h'):

        # Size -> [seq_len, label_len, pred_len, interval_len]
        if size is None:
            self.seq_len = 24 * 7
            self.label_len = 12
            self.pred_len = 24
            self.interval_len = 24
        else:
            self.seq_len = size[0]
            self.label_len = size[1]
            self.pred_len = size[2]
            self.interval_len = size[3]

        # Initialization
        assert flag in ['train', 'val', 'test']
        type_map = {'train': 0, 'val': 1, 'test': 2}
        self.set_type = type_map[flag]

        self.features = features
        self.target = target
        self.scale = scale
        self.timeenc = timeenc
        self.freq = freq

        self.root_path = root_path
        self.data_path = data_path
        self.__read_data__()

    def __read_data__(self):

        self.scaler = StandardScaler()
        df_raw = pd.read_csv(os.path.join(self.root_path, self.data_path), parse_dates=['date'])
        '''
        Need to process the raw input data -> load + DR potentials for each zone collected towards the end
        df_raw.columns: ['date', ...(other features), target feature]
        '''

        # Fetching the length for the train, validation and test splits
        num_train = len(df_raw[df_raw.date.dt.year.between(2015, 2018)])
        num_vali = len(df_raw[df_raw.date.dt.year.isin([2019])])
        num_test = len(df_raw[df_raw.date.dt.year.isin([2019])])

        border1s = [0, num_train - self.seq_len, num_train - self.seq_len]
        border2s = [num_train, len(df_raw), len(df_raw)]
        border1 = border1s[self.set_type]
        border2 = border2s[self.set_type]

        # Filtering the data based on forecasting task
        if self.features == 'M' or self.features == 'MS':
            cols_data = df_raw.columns[1:]
            df_data = df_raw[cols_data]

            # Modifying the column ordering for MS task predicting demand and potential individually
            if self.target == 'demand':
                col_order = ['potential', 'temperature', 'demand']
                df_data = df_data.reindex(columns=col_order)
            elif self.target == 'potential':
                col_order = ['demand', 'temperature', 'potential']
                df_data = df_data.reindex(columns=col_order)
            else:
                raise ValueError('Wrong target selected, should be either demand or potential.')

        elif self.features == 'S':
            df_data = df_raw[[self.target]]

        # Scaling the data
        if self.scale:
            train_data = df_data[border1s[0]:border2s[0]]
            self.scaler.fit(train_data.values)
            data = self.scaler.transform(df_data.values)
        else:
            data = df_data.values

        df_stamp = df_raw[['date']][border1:border2]
        df_stamp['date'] = pd.to_datetime(df_stamp.date)

        # Experiment with different time encodings
        if self.timeenc == 0:
            df_stamp['month'] = df_stamp.date.apply(lambda row: row.month, 1)
            df_stamp['day'] = df_stamp.date.apply(lambda row: row.day, 1)
            df_stamp['weekday'] = df_stamp.date.apply(lambda row: row.weekday(), 1)
            df_stamp['hour'] = df_stamp.date.apply(lambda row: row.hour, 1)
            data_stamp = df_stamp.drop(['date'], axis=1).values
        elif self.timeenc == 1:
            data_stamp = time_features(pd.to_datetime(df_stamp['date'].values), freq=self.freq)
            data_stamp = data_stamp.transpose(1, 0)

        self.data_x = data[border1:border2]
        self.data_y = data[border1:border2]
        self.data_stamp = data_stamp

    # Label length sets different overlaps
    def __getitem__(self, index):
        s_begin = index
        s_end = s_begin + self.seq_len
        r_begin = s_end - self.label_len + self.interval_len
        r_end = r_begin + self.label_len + self.pred_len

        seq_x = self.data_x[s_begin:s_end]
        seq_y = self.data_y[r_begin:r_end]
        seq_x_mark = self.data_stamp[s_begin:s_end]
        seq_y_mark = self.data_stamp[r_begin:r_end]

        return seq_x, seq_y, seq_x_mark, seq_y_mark

    # Check the len issue here.
    def __len__(self):
        return len(self.data_x) - self.seq_len - self.pred_len - self.interval_len + 1

    def inverse_transform(self, data):
        return self.scaler.inverse_transform(data)