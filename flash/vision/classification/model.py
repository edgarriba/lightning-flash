# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Any, Callable, Mapping, Sequence, Tuple, Type, Union

import torch
from torch import nn
from torch.nn import functional as F
from torchmetrics import Accuracy

from flash.core.classification import ClassificationTask
from flash.vision.backbones import backbone_and_num_features
from flash.vision.classification.data import ImageClassificationData, ImageClassificationPreprocess


class ImageClassifier(ClassificationTask):
    """Task that classifies images.

    Use a built in backbone

    Example::

        from flash.vision import ImageClassifier

        classifier = ImageClassifier(backbone='resnet18')

    Or your own backbone (num_features is the number of features produced by your backbone)

    Example::

        from flash.vision import ImageClassifier
        from torch import nn

        # use any backbone
        some_backbone = nn.Conv2D(...)
        num_out_features = 1024
        classifier = ImageClassifier(backbone=(some_backbone, num_out_features))


    Args:
        num_classes: Number of classes to classify.
        backbone: A string or (model, num_features) tuple to use to compute image features, defaults to ``"resnet18"``.
        pretrained: Use a pretrained backbone, defaults to ``True``.
        loss_fn: Loss function for training, defaults to :func:`torch.nn.functional.cross_entropy`.
        optimizer: Optimizer to use for training, defaults to :class:`torch.optim.SGD`.
        metrics: Metrics to compute for training and evaluation,
            defaults to :class:`torchmetrics.Accuracy`.
        learning_rate: Learning rate to use for training, defaults to ``1e-3``.
    """

    @property
    def preprocess(self):
        return ImageClassificationPreprocess(predict_transform=ImageClassificationData.default_val_transforms())

    def __init__(
        self,
        num_classes: int,
        backbone: Union[str, Tuple[nn.Module, int]] = "resnet18",
        pretrained: bool = True,
        loss_fn: Callable = F.cross_entropy,
        optimizer: Type[torch.optim.Optimizer] = torch.optim.SGD,
        metrics: Union[Callable, Mapping, Sequence, None] = Accuracy(),
        learning_rate: float = 1e-3,
    ):
        super().__init__(
            model=None,
            loss_fn=loss_fn,
            optimizer=optimizer,
            metrics=metrics,
            learning_rate=learning_rate,
        )

        self.save_hyperparameters()

        if isinstance(backbone, tuple):
            self.backbone, num_features = backbone
        else:
            self.backbone, num_features = backbone_and_num_features(backbone, pretrained=pretrained)

        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(num_features, num_classes),
        )

    def forward(self, x) -> Any:
        x = self.backbone(x)
        return torch.softmax(self.head(x), -1)
