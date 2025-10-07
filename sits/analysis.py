import xarray as xr
import pandas as pd
# sktime package
from sktime.forecasting.base import ForecastingHorizon
from sktime.registry import all_estimators


def date_range(start_date, end_date, freq='D'):
    """to fill
    """
    # Define start and end dates
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)
    # Create a date range
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

    return date_range


def reindexTS(df, freq='D', interpolate=False, method='linear'):
    """ to fill
    """
    df.index = df.index.normalize()
    if freq != 'D':
        df = df.resample(freq).mean()

    df = df.reindex(pd.date_range(df.index.min(), df.index.max(), freq=freq))

    if interpolate:
        df = df.interpolate(method=method).ffill().bfill()

    return df


def sktime_fitpred(ts,
                   time_index,
                   predict_time,
                   model_name='ThetaForecaster',
                   model_params=None,
                   regular_freq=True, freq='D'):
    """to fill
    """

    fh = ForecastingHorizon(predict_time,
                            is_relative=False)

    df = pd.DataFrame({'ds': time_index, 'y': ts})
    df.set_index('ds', inplace=True)
    if regular_freq:
        df = reindexTS(df, freq=freq)

    model_params = model_params or {}

    # Get forecaster class by name
    forecaster_cls = dict(
        all_estimators(estimator_types="forecaster")).get(model_name)

    if forecaster_cls is None:
        raise ValueError(f"Model '{model_name}' not found in sktime registry.")

    forecaster = forecaster_cls(**model_params)
    forecaster.fit(df)

    return forecaster.predict(fh)['y'].values


def xr_forecast(dataarray,
                predict_time,
                model_name='ThetaForecaster',
                model_params=None):
    """to fill
    """
    model_params = model_params or {}

    result = xr.apply_ufunc(
        sktime_fitpred,
        dataarray,
        dataarray['time'],
        input_core_dims=[['time'], ['time']],
        output_core_dims=[['forecast_time']],
        kwargs={
            "predict_time": predict_time,
            "model_name": model_name,
            "model_params": model_params},
        vectorize=True,
        dask='parallelized',
        dask_gufunc_kwargs={
            'output_sizes': {'forecast_time': len(predict_time)}
        },
        output_dtypes=[float]
    )

    result = result.rename({"forecast_time": "time"})
    result = result.assign_coords(time=("time", predict_time))

    return result