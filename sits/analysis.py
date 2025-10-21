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

    Args:
        n_cores (bool, optional): Number of CPU cores. 
            Defaults to False (i.e. all available CPU cores).
        crs_out (int, optional): Number of threads per worker. Defaults to 1.

    Returns:
        Client: A Dask distributed client instance.

    Example:
        >>> client = initialize_dask_client()
    """
    import multiprocessing
    from dask.distributed import Client

    if n_cores:
        n_cores = n_cores
    else:
        n_cores = multiprocessing.cpu_count()
    client = Client(n_workers=n_cores, threads_per_worker=threads_per_worker)
    client.restart()

    return client


def date_range(start_date, end_date, freq='D'):
    """
    Generate a range of dates between two given dates with a specified frequency.

    Args:
        start_date (str): start date 'yyyy-mm-dd' of the range.
        end_date (str): end date 'yyyy-mm-dd' of the range.
        freq (str, optional): accepts any valid pandas frequency string.
            Default to 'D' for daily.

    Returns:
        date_range (pd.DatetimeIndex): pandas DatetimeIndex object
            representing the date range.

    Examples
    --------
        >>> ts_predict = date_range('2025-01-01', '2025-07-01', freq='D')
    """
    # Define start and end dates
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)
    # Create a date range
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

    return date_range


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
    """
    Reindex a time series DataFrame to a regular frequency,
    with optional aggregation and interpolation.

    Args:
        df(pd.DataFrame): input DataFrame with a datetime index.
        freq (str, optional): desired frequency for the output time series.
            Default to 'D' for daily.
        regular_freq (bool, optional): If True, enforces regular frequency.
            If `freq` is not 'D', this must be False, otherwise a ValueError
            is raised. Defaults to False.
        interpolate (bool, optional): If True, interpolates missing values using 
            the specified method. Defaults to False.
        method (str, optional): interpolation method to use. Accepts any method
            supported by `pandas.DataFrame.interpolate`. Defaults to 'linear'.

    Returns:
        df (pd.DataFrame): a DataFrame reindexed to the specified frequency, 
            with optional interpolation applied.

    Raises:
        ValueError: if `regular_freq` is True while `freq` is not 'D'.

    Notes:
        - The function uses internal helpers: `_ensure_datetime_index`,
            `_resample_df`, `_convert_to_period`, `_regularize_index`, and
            `_fill_nan`.
        - The index is normalized to remove time components before processing.

    Examples:
        >>> ts_train = reindexTS(df,
                                 freq='D',
                                 regular_freq=True,
                                 interpolate=True,
                                 method='linear')
    """
    df = df.copy()

    df = _ensure_datetime_index(df)
    df.index = df.index.normalize()

    if freq != 'D':
        if regular_freq:
            raise ValueError(
                "With 'freq' different than 'D', 'regular_freq' cannot be True."
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
    """
    Fit a time series forecasting model from sktime and predict future values.

    This function prepares a time series dataset, optionally reindexes it to a
    regular frequency, fits a forecasting model from the sktime library, and
    returns predictions for specified future timestamps.

    Args:
        ts (array-like): the time series values to be modeled.
        time_index (array-like): the corresponding datetime index for the
            time series values.
        predict_time (array-like): a list or array of future timestamps for
            which predictions are required.
        model_name (str, optional): name of the sktime forecasting model to use.
            Must be a valid forecaster registered in sktime. 
            Defaults to 'ThetaForecaster'.
        model_params (dict, optional): dictionary of parameters to initialize 
            the forecasting model. If None, default parameters are used.
        freq (str, optional): frequency string used to regularize the time index.
            Default to 'D' for daily.
        reindex_params (dict, optional): additional keyword arguments passed to
            the `reindexTS` function for time series reindexing.

    Returns:
        np.ndarray: array of predicted values corresponding to `predict_time`.

    Raises:
        ValueError if the specified `model_name` is not found in
        the sktime registry.

    Examples:
        >>> predict = sktime_fitpred(arr_train, time_train, time_pred)
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
    """
    Apply a sktime forecasting model to each pixel of a time series DataArray.

    This function performs pixel-wise time series forecasting on an
    xarray.DataArray using a specified sktime model. It applies
    the `sktime_fitpred` function across the spatial dimensions using
    `xarray.apply_ufunc`, enabling parallelized computation with Dask.

    Args:
        dataarray(xr.DataArray): a 3D xarray DataArray with dimensions
            ('time', 'y', 'x'), representing the time series data for
            each pixel.
        predict_time (array-like): a list or array of future timestamps for
            which predictions are required.
        model_name (str, optional): name of the sktime forecasting model to use.
            Must be a valid forecaster registered in sktime.
            Default to 'ThetaForecaster'.
        model_params (dict, optional): dictionary of parameters to initialize
            the forecasting model. If None, default parameters are used.
        reindex_params (dict, optional): additional keyword arguments passed to
            the `reindexTS` function for time series reindexing.
        freq (str, optional): frequency string used to regularize the time index.
            Default to 'D' for daily.

    Returns:
        result (xr.DataArray): a DataArray with dimensions ('time', 'y', 'x')
            containing the forecasted values for each pixel.

    Notes:
        - The function uses Dask for parallelized execution, making it suitable
            for large datasets.
        - The output time coordinate is replaced with `predict_time`.

    Examples:
        >>> result = xr_forecast(dataarray, predict_time)
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