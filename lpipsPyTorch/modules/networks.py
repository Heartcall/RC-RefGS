import os
from typing import Sequence

from itertools import chain

import torch
import torch.nn as nn
from torchvision import models

from .utils import normalize_activation


_CORRUPT_CHECKPOINT_MARKERS = (
    "PytorchStreamReader failed reading zip archive",
    "failed finding central directory",
)


def _checkpoint_path_from_weights(weights):
    url = getattr(weights, "url", None)
    if url is None:
        return None
    filename = url.rsplit("/", 1)[-1]
    return os.path.join(torch.hub.get_dir(), "checkpoints", filename)


def _load_features_with_retry(builder, weights):
    try:
        return builder(weights=weights).features
    except RuntimeError as exc:
        message = str(exc)
        if not any(marker in message for marker in _CORRUPT_CHECKPOINT_MARKERS):
            raise
        checkpoint_path = _checkpoint_path_from_weights(weights)
        if checkpoint_path is not None and os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
        return builder(weights=weights).features


def get_network(net_type: str):
    if net_type == 'alex':
        return AlexNet()
    elif net_type == 'squeeze':
        return SqueezeNet()
    elif net_type == 'vgg':
        return VGG16()
    else:
        raise NotImplementedError('choose net_type from [alex, squeeze, vgg].')


class LinLayers(nn.ModuleList):
    def __init__(self, n_channels_list: Sequence[int]):
        super(LinLayers, self).__init__([
            nn.Sequential(
                nn.Identity(),
                nn.Conv2d(nc, 1, 1, 1, 0, bias=False)
            ) for nc in n_channels_list
        ])

        for param in self.parameters():
            param.requires_grad = False


class BaseNet(nn.Module):
    def __init__(self):
        super(BaseNet, self).__init__()

        # register buffer
        self.register_buffer(
            'mean', torch.Tensor([-.030, -.088, -.188])[None, :, None, None])
        self.register_buffer(
            'std', torch.Tensor([.458, .448, .450])[None, :, None, None])

    def set_requires_grad(self, state: bool):
        for param in chain(self.parameters(), self.buffers()):
            param.requires_grad = state

    def z_score(self, x: torch.Tensor):
        return (x - self.mean) / self.std

    def forward(self, x: torch.Tensor):
        x = self.z_score(x)

        output = []
        for i, (_, layer) in enumerate(self.layers._modules.items(), 1):
            x = layer(x)
            if i in self.target_layers:
                output.append(normalize_activation(x))
            if len(output) == len(self.target_layers):
                break
        return output


class SqueezeNet(BaseNet):
    def __init__(self):
        super(SqueezeNet, self).__init__()

        self.layers = _load_features_with_retry(
            models.squeezenet1_1,
            models.SqueezeNet1_1_Weights.IMAGENET1K_V1,
        )
        self.target_layers = [2, 5, 8, 10, 11, 12, 13]
        self.n_channels_list = [64, 128, 256, 384, 384, 512, 512]

        self.set_requires_grad(False)


class AlexNet(BaseNet):
    def __init__(self):
        super(AlexNet, self).__init__()

        self.layers = _load_features_with_retry(
            models.alexnet,
            models.AlexNet_Weights.IMAGENET1K_V1,
        )
        self.target_layers = [2, 5, 8, 10, 12]
        self.n_channels_list = [64, 192, 384, 256, 256]

        self.set_requires_grad(False)


class VGG16(BaseNet):
    def __init__(self):
        super(VGG16, self).__init__()

        self.layers = _load_features_with_retry(
            models.vgg16,
            models.VGG16_Weights.IMAGENET1K_V1,
        )
        self.target_layers = [4, 9, 16, 23, 30]
        self.n_channels_list = [64, 128, 256, 512, 512]

        self.set_requires_grad(False)
