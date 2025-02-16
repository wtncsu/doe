#!/usr/bin/env python3
import tomllib
from argparse import ArgumentParser
from pathlib import Path
from time import time

import pandas as pd

from ngboost import NGBoost

parser = ArgumentParser()
parser.add_argument('--config', required=True, type=Path)
parser.add_argument('--train-feature', required=True, type=Path)
parser.add_argument('--train-target', required=True, type=Path)
parser.add_argument('--test-feature', required=True, type=Path)
parser.add_argument('--predict-mean', required=True, type=Path)
parser.add_argument('--predict-std', required=True, type=Path)
parser.add_argument('--train-time', type=Path)
parser.add_argument('--test-time', type=Path)

args = parser.parse_args()
args.predict_mean.parent.mkdir(parents=True, exist_ok=True)
args.predict_std.parent.mkdir(parents=True, exist_ok=True)

with open(args.config, 'rb') as config_file:
    config = tomllib.load(config_file)

train_feature = pd.read_csv(args.train_feature, index_col=['date'])
train_target = pd.read_csv(args.train_target, index_col=['date'])
test_feature = pd.read_csv(args.test_feature, index_col=['date'])

model = NGBoost(base_params=config['model'], **config['ensemble'])

train_start = time()
model.fit(train_feature, train_target)
train_end = time()

test_start = time()
predict_mean, predict_std = model.predict(test_feature)
test_end = time()

predict_mean = pd.DataFrame(predict_mean,
                            columns=train_target.columns,
                            index=test_feature.index)

predict_std = pd.DataFrame(predict_std,
                           columns=train_target.columns,
                           index=test_feature.index)

predict_mean.to_csv(args.predict_mean)
predict_std.to_csv(args.predict_std)

train_time = train_end - train_start
test_time = test_end - test_start

if args.train_time is not None:
    args.train_time.parent.mkdir(parents=True, exist_ok=True)

    with open(args.train_time, 'w') as file:
        file.write(f'{train_time}')

if args.test_time is not None:
    args.test_time.parent.mkdir(parents=True, exist_ok=True)

    with open(args.test_time, 'w') as file:
        file.write(f'{test_time}')
