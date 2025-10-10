import xarray as xr
import pandas as pd
# sktime package
from sktime.forecasting.base import ForecastingHorizon
from sktime.registry import all_estimators


def initialize_dask_client(n_cores=False, threads_per_worker=1):
    """
    Initializes a Dask distributed client using by default all
    available CPU cores, with one thread per worker.
    Restarts the client to ensure a clean state.

    Returns:
        Client: A Dask distributed client instance.
    """
    import multiprocessing
    from dask.distributed import Client

    if n_cores:
        n_cores = n_cores
    else:
        n_cores = multiprocessing.cpu_count()
    client = Client(n_workers=n_cores, threads_per_worker=threads_per_worker)
    client.restart()


def date_range(start_date, end_date, freq='D'):
    """to fill
    """
    # Define start and end dates
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)
    # Create a date range
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

    return date_range


def reindexTS_old(df, freq='D', regular_freq=False,
              aggregate=False, interpolate=False, 
              method='linear'):
    """ to fill
    """
    df.index = df.index.normalize()

    if freq != 'D':
        df = df.resample(freq).mean()

    df = df.reindex(pd.date_range(df.index.min(), df.index.max(), freq=freq))

    if interpolate:
        df = df.interpolate(method=method).ffill().bfill()

    return df


def _ensure_datetime_index(df):
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    return df

def _resample_df(df, freq):
    df = df.resample(freq).mean()
    return df


def _convert_to_period(df, freq='M'):
    df.index = pd.PeriodIndex(df.index, freq=freq)
    return df


def _regularize_index(df, freq):
    new_index = pd.date_range(start=df.index.min(), end=df.index.max(),
                              freq=freq)
    return df.reindex(new_index)


def _fill_nan(df, method):
    df = df.interpolate(method=method)
    df = df.ffill().bfill()
    return df


def reindexTS(df, freq='D',
              regular_freq=False,
              interpolate=False,
              method='linear'):

    df = df.copy()

    df = _ensure_datetime_index(df)
    df.index = df.index.normalize()

    if freq != 'D':
        if regular_freq:
            raise ValueError(
                "With 'freq' different than 'D', 'regular_feq' cannot be True."
            )
        df = _resample_df(df, freq)
        df = _convert_to_period(df, freq)

    if regular_freq:
        df = _regularize_index(df, freq)

    if interpolate:
        df = _fill_nan(df, method=method)

    return df


def sktime_fitpred(ts,
                   time_index,
                   predict_time,
                   model_name='ThetaForecaster',
                   model_params=None,
                   freq='D',
                   reindex_params=None):
    """to fill
    """

    fh = ForecastingHorizon(predict_time,
                            is_relative=False)

    df = pd.DataFrame({'ds': time_index, 'y': ts})
    df.set_index('ds', inplace=True)

    reindex_params = reindex_params or {}
    df = reindexTS(df, freq=freq, **reindex_params)

    # Get forecaster class by name
    forecaster_cls = dict(
        all_estimators(estimator_types="forecaster")).get(model_name)

    if forecaster_cls is None:
        raise ValueError(f"Model '{model_name}' not found in sktime registry.")

    model_params = model_params or {}
    forecaster = forecaster_cls(**model_params)
    forecaster.fit(df)

    return forecaster.predict(fh)['y'].values


def xr_forecast(dataarray,
                predict_time,
                model_name='ThetaForecaster',
                model_params=None,
                reindex_params=None,
                freq='D'):
    """to fill
    """
    model_params = model_params or {}

    result = xr.apply_ufunc(
        sktime_fitpred,
        dataarray,
        dataarray['time'],
        input_core_dims=[['time'], ['time']],
        output_core_dims=[['forecast_time']],
        keep_attrs=True,
        kwargs={
            "predict_time": predict_time,
            "model_name": model_name,
            "model_params": model_params,
            "reindex_params": reindex_params,
            "freq": freq},
        vectorize=True,
        dask='parallelized',
        dask_gufunc_kwargs={
            'output_sizes': {'forecast_time': len(predict_time)}
        },
        output_dtypes=[float]
    )

    result = result.rename({"forecast_time": "time"})
    result = result.assign_coords(time=("time", predict_time))
    result = result.transpose('time', 'y', 'x')

    return result