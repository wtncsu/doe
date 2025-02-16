import os
import torch
from models import Informer, Autoformer, Transformer, DLinear, NLinear, Linear, PatchTST, CARD


class Exp_Basic(object):
    def __init__(self, args):
        self.args = args
        self.model_dict = {
            'Informer': Informer,
            'Autoformer': Autoformer,
            'Transformer': Transformer,
            'DLinear': DLinear,
            'NLinear': NLinear,
            'Linear': Linear,
            'PatchTST': PatchTST,
            'CARD': CARD,
        }
        self.device = self._acquire_device()
        self.model = self._build_model().to(self.device)

    def _build_model(self):
        raise NotImplementedError
        return None

    def _acquire_device(self):
        if self.args.use_gpu:
            os.environ["CUDA_VISIBLE_DEVICES"] = str(
                self.args.gpu) if not self.args.use_multi_gpu else self.args.devices
            device = torch.device('cuda:{}'.format(self.args.gpu))
            msg = 'Use GPU: cuda:{}'.format(self.args.gpu)
            print(msg)

        elif self.args.use_mps:
            device = torch.device('mps')
            msg = 'Use MPS: True'
            print(msg)

        else:
            device = torch.device('cpu')
            msg = 'Use CPU: True'
            print(msg)

        return device

    def _get_data(self):
        pass

    def vali(self):
        pass

    def train(self):
        pass

    def test(self):
        pass
