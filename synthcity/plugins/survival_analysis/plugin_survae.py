# stdlib
from typing import Any, List

# third party
import pandas as pd
# Necessary packages
from pydantic import validate_arguments

# synthcity absolute
import synthcity.logger as log
import synthcity.plugins as plugins
from synthcity.plugins.core.dataloader import DataLoader
from synthcity.plugins.core.distribution import Distribution
from synthcity.plugins.core.plugin import Plugin
from synthcity.plugins.core.schema import Schema
from synthcity.plugins.survival_analysis._survival_pipeline import SurvivalPipeline
from synthcity.utils.constants import DEVICE


class SurVAEPlugin(Plugin):
    """Survival VAE plugin.

    Example:
        >>> from synthcity.plugins import Plugins
        >>> from synthcity.plugins.core.dataloader import SurvivalAnalysisDataLoader
        >>> X = load_rossi()
        >>> data = SurvivalAnalysisDataLoader(
        >>>        X,
        >>>        target_column="arrest",
        >>>        time_to_event_column="week",
        >>> )
        >>> plugin = Plugins().get("survae")
        >>> plugin.fit(data)
        >>> plugin.generate()
    """

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def __init__(
        self,
        uncensoring_model: str = "survival_function_regression",
        dataloader_sampling_strategy: str = "imbalanced_time_censoring",  # none, imbalanced_censoring, imbalanced_time_censoring
        tte_strategy: str = "survival_function",
        censoring_strategy: str = "random",  # "covariate_dependent"
        device: Any = DEVICE,
        **kwargs: Any,
    ) -> None:
        super().__init__()

        valid_sampling_strategies = [
            "none",
            "imbalanced_censoring",
            "imbalanced_time_censoring",
        ]
        if dataloader_sampling_strategy not in valid_sampling_strategies:
            raise ValueError(
                f"Invalid sampling strategy {dataloader_sampling_strategy}. Supported values: {valid_sampling_strategies}",
            )
        self.tte_strategy = tte_strategy
        self.censoring_strategy = censoring_strategy
        self.uncensoring_model = uncensoring_model
        self.device = device
        self.kwargs = kwargs

        log.info(
            f"""
            Training SurVAE using
                tte_strategy = {self.tte_strategy};
                uncensoring_model={self.uncensoring_model}
                device={self.device}
            """,
        )

    @staticmethod
    def name() -> str:
        return "survae"

    @staticmethod
    def type() -> str:
        return "survival_analysis"

    @staticmethod
    def hyperparameter_space(**kwargs: Any) -> List[Distribution]:
        return plugins.Plugins().get_type("tvae").hyperparameter_space()

    def _fit(self, X: DataLoader, *args: Any, **kwargs: Any) -> "SurVAEPlugin":
        assert X.type() == "survival_analysis"

        self.model = SurvivalPipeline(
            "tvae",
            strategy=self.tte_strategy,
            uncensoring_model=self.uncensoring_model,
            censoring_strategy=self.censoring_strategy,
            device=self.device,
            **self.kwargs,
        )
        self.model.fit(X, **kwargs)

        return self

    def _generate(self, count: int, syn_schema: Schema, **kwargs: Any) -> pd.DataFrame:
        return self.model._generate(
            count,
            syn_schema=syn_schema,
            **kwargs,
        )


plugin = SurVAEPlugin
