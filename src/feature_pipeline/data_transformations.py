import numpy as np
import pandas as pd
from typing import Optional

from fire import Fire
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer

from src.feature_pipeline.feature_engineering import get_percentage_change, RSI, EMA


def get_cutoff_indices(
        data: pd.DataFrame,
        input_seq_len: int,
        step_size: int
) -> list:
    
    """
    This function will take a dataframe and will look at
    the first input_seq_len rows+1, and then records a tuple 
    consisting of:

    - the first index
    - index number "input_seq_len"
    - the last index.

    Returns:
        list: returns a list of tuples of these indices
    """

    indices = []
    stop_position = len(data) - 1

    subseq_first_index = 0
    subseq_mid_index = input_seq_len
    subseq_last_index = input_seq_len + 1

    while subseq_last_index <= stop_position:
        
        indices.append(
            (subseq_first_index, subseq_mid_index, subseq_last_index)
        )
        
        subseq_first_index += step_size
        subseq_mid_index += step_size
        subseq_last_index += step_size

    return indices


def transform_ts_data_into_features_and_target(
        original_data: pd.DataFrame,
        input_seq_len: Optional[int] = 30,
        step_size: Optional[int] = 1,
        base_currency: str = "GBP",
        target_currency: str = "GHS"
    ) -> list:
    
    """
    This transforms our time series data into a feature-target
    format that is conducive for training supervised training
    algorithms.

    Returns:
        tuple: consisting of the dataframe of features, and
               a pandas series of the target variable.
    """

    ts_data = original_data[
        ["Date", f"Closing rate ({base_currency}{target_currency})"]
    ]

    ts_data = ts_data.sort_values(by=["Date"])

    indices = get_cutoff_indices(
        data=ts_data, 
        input_seq_len=input_seq_len, 
        step_size=step_size
        )

    x = np.ndarray(
        shape=(len(indices), input_seq_len), dtype=np.float32
    )

    y = np.ndarray(
        shape=(len(indices)), dtype=np.float32
    )
    
    dates = []
    for i, idx in enumerate(indices):
        
        x[i,:] = ts_data.iloc[idx[0]: idx[1]][f"Closing rate ({base_currency}{target_currency})"].values
        y[i] = ts_data.iloc[idx[1]: idx[2]][f"Closing rate ({base_currency}{target_currency})"].values
        dates.append(ts_data.iloc[idx[1]]["Date"])

    features = pd.DataFrame(
        x, columns=[
            f"Closing_rate_{base_currency}{target_currency}_{i + 1}_day_ago" for i in reversed(range(input_seq_len))
        ]
    )

    targets = pd.DataFrame(
        y, columns=[f"Closing_rate_{base_currency}{target_currency}_next_day"]
    )

    return features, targets[f"Closing_rate_{base_currency}{target_currency}_next_day"]



def get_preprocessing_pipeline(rsi_length: int = 14, ema_length: int = 14) -> Pipeline:
    
    """ Returns a pipeline that combines all of the feature engineering steps """

    return make_pipeline(
        
        FunctionTransformer(
            func=get_percentage_change, 
            kw_args={"days": 2}
            ),
        
        FunctionTransformer(
            func=get_percentage_change, 
            kw_args={"days": 5}
            ),
        
        FunctionTransformer(
            func=get_percentage_change, 
            kw_args={"days": 14}
            ),
        
        FunctionTransformer(
            func=get_percentage_change, 
            kw_args={"days": 30}
            ),

        RSI(rsi_length=rsi_length),
        EMA(ema_length=ema_length)
    )


if __name__ == "__main__":
    
    features, target = Fire(transform_ts_data_into_features_and_target)

    pipe = get_preprocessing_pipeline()

    features = pipe.fit(features)

    X = pipe.transform(features)

    print(X.head())
