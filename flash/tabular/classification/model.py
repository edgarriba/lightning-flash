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
from typing import Any, Callable, List, Tuple, Type

import torch
from torch.nn import functional as F
from torchmetrics import Metric

from flash.core.classification import ClassificationTask
from flash.utils.imports import _TABNET_AVAILABLE

if _TABNET_AVAILABLE:
    from pytorch_tabnet.tab_network import TabNet


class TabularClassifier(ClassificationTask):
    """Task that classifies table rows.

    Args:
        num_features: Number of columns in table (not including target column).
        num_classes: Number of classes to classify.
        embedding_sizes: List of (num_classes, emb_dim) to form categorical embeddings.
        loss_fn: Loss function for training, defaults to cross entropy.
        optimizer: Optimizer to use for training, defaults to `torch.optim.Adam`.
        metrics: Metrics to compute for training and evaluation.
        learning_rate: Learning rate to use for training, defaults to `1e-3`
        **tabnet_kwargs: Optional additional arguments for the TabNet model, see
            `pytorch_tabnet <https://dreamquark-ai.github.io/tabnet/_modules/pytorch_tabnet/tab_network.html#TabNet>`_.
    """

    def __init__(
        self,
        num_features: int,
        num_classes: int,
        embedding_sizes: List[Tuple] = None,
        loss_fn: Callable = F.cross_entropy,
        optimizer: Type[torch.optim.Optimizer] = torch.optim.Adam,
        metrics: List[Metric] = None,
        learning_rate: float = 1e-3,
        **tabnet_kwargs,
    ):
        self.save_hyperparameters()

        cat_dims, cat_emb_dim = zip(*embedding_sizes) if len(embedding_sizes) else ([], [])
        model = TabNet(
            input_dim=num_features,
            output_dim=num_classes,
            cat_idxs=list(range(len(embedding_sizes))),
            cat_dims=list(cat_dims),
            cat_emb_dim=list(cat_emb_dim),
            **tabnet_kwargs
        )

        super().__init__(
            model=model,
            loss_fn=loss_fn,
            optimizer=optimizer,
            metrics=metrics,
            learning_rate=learning_rate,
        )

    def forward(self, x_in) -> torch.Tensor:
        # TabNet takes single input, x_in is composed of (categorical, numerical)
        x = torch.cat([x for x in x_in if x.numel()], dim=1)
        return F.softmax(self.model(x)[0], -1)

    def predict_step(self, batch: Any, batch_idx: int, dataloader_idx: int = 0) -> Any:
        return self(batch)

    @classmethod
    def from_data(cls, datamodule, **kwargs) -> 'TabularClassifier':
        model = cls(datamodule.num_features, datamodule.num_classes, datamodule.emb_sizes, **kwargs)
        return model
