import xarray as xr
import pandas as pd
import numpy as np
from scipy.ndimage import label
from skimage.filters.rank import modal
from skimage.morphology import square
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
        date_range (pd.DatetimeIndex): pandas DatetimeIndex object representing the date range.

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
        - The function uses internal helpers: `_ensure_datetime_index`, `_resample_df`, `_convert_to_period`, `_regularize_index`, and `_fill_nan`.
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
        result (xr.DataArray): a DataArray with dimensions ('time', 'y', 'x') containing the forecasted values for each pixel.

    Notes:
        - The function uses Dask for parallelized execution, making it suitable for large datasets.
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


class ClearCut:
    """
    This class aims to detect changes in univariate time series
    (e.g., spectral indices such as NDVI). It identifies potential
    change points by comparing values in two moving windows:
      - A **backward window** summarizes past observations.
      - A **forward window** summarizes upcoming observations.
    A change is flagged when the forward window shows a significant drop
    relative to the backward window, according to a configurable threshold.
    This method is an adaptation of the OTB ClearCutsMultitemporalDetection
    application (R. Cresson, INRAE).

    Typical use case: detecting vegetation loss or disturbance events in
    spectral index time series (NDVI, EVI, etc.), where sudden drops may
    indicate deforestation, fire, or degradation.

    Attributes:
        da (xr.Dataarray): index time series ('time', 'band', 'y', 'x')

    Args:
        da (xr.Dataarray): index time series ('time', 'band', 'y', 'x')

    Example:
            >>> ndvi_ts = ClearCut(Dataarray)
    """

    def __init__(self, da: xr.DataArray):
        self.da = da

    def season_of_interest(self, start: str = "06-01", end: str = "08-31", compute=True):
        """
        Filters the datacube to retain only dates between start and end (format: 'mm-dd').

        Args:
            start (str, optional): start date in 'mm-dd' format.
                Defaults to '06-01'.
            end (str, optional): end date in 'mm-dd' format.
                Defaults to '08-31'.

        Returns:
            ClearCut.da (xr.Dataarray): Filtered Dataarray with only dates in the specified range.

        Example:
            >>> ndvi_ts.season_of_interest()
        """
        mmdd = self.da['time'].dt.strftime('%m-%d')
        mask = (mmdd >= start) & (mmdd <= end)
        if compute:
            self.da = self.da.sel(time=self.da['time'][mask]).compute()
        else:
            self.da = self.da.sel(time=self.da['time'][mask])

    def __select_window(self, pivot_date, window: int, direction: str):
        d = np.datetime64(pivot_date)
        if direction == "forward":
            return self.da.sel(time=slice(d, d + np.timedelta64(window, 'D')))
        elif direction == "backward":
            return self.da.sel(time=slice(d - np.timedelta64(window, 'D'), d))
        else:
            raise ValueError("direction must be 'forward' or 'backward'")

    def __compute_mean_and_mask(self, da_sub: xr.DataArray, min_obs: int):
        valid_count = da_sub.notnull().sum(dim='time')
        mean_fixed = da_sub.mean(dim='time', skipna=True)
        mask = valid_count >= min_obs
        return mean_fixed.where(mask), mask

    def __extend_window(self, result: xr.DataArray, mask: xr.DataArray, start, end, min_obs: int, direction: str):
        if direction == "forward":
            time_iter = self.da.time.sel(time=slice(end, None))
            slice_fn = lambda t: slice(end, t)
        else:  # backward
            time_iter = self.da.time.sel(time=slice(None, start))[::-1]
            slice_fn = lambda t: slice(t, start)

        for t in time_iter:
            da_sub = self.da.sel(time=slice_fn(t.values))
            valid_count = da_sub.notnull().sum(dim='time')
            new_mask = (valid_count >= min_obs) & result.isnull()
            result = result.where(~new_mask, da_sub.mean(dim='time', skipna=True))
            if new_mask.sum() == 0:
                break
        return result

    def __mean_with_fallback(self, pivot_date, window: int, direction: str = 'forward', min_obs: int = 2):
        da_sub = self.__select_window(pivot_date, window, direction)
        start, end = da_sub['time'].min().values, da_sub['time'].max().values
        result, mask = self.__compute_mean_and_mask(da_sub, min_obs)
        result = self.__extend_window(result, mask, start, end, min_obs, direction)
        return result, mask

    def __classify_anomalies(self, mag_layer: xr.DataArray, thresholds: list):
        class_layer = xr.full_like(mag_layer, 0, dtype=int)
        for i, th in enumerate(thresholds, start=1):
            class_layer = xr.where(mag_layer > th, i, class_layer)
        class_layer.name = "anomaly_class"
        class_layer.attrs["thresholds"] = str(thresholds)
        return class_layer

    def detect_anomalies(self,
                         thresholds: list = [0.2, 0.3, 0.4],
                         window_backward: int = 720,
                         window_forward: int = 60,
                         min_obs_backward: int = 5,
                         min_obs_forward: int = 2,
                         out_crs: str = "epsg:3035"):
        """
        Detect anomalies in a univariate time series (e.g., spectral indices such as NDVI)
        by comparing values between backward and forward moving windows.

        For each date in the series (excluding margins defined by the window sizes),
        the method computes:
            - Mean of the backward window (past observations).
            - Mean of the forward window (future observations).
            - Magnitude of change as the absolute difference between the two means.

        An anomaly is flagged when the magnitude exceeds the first threshold. The
        function records the first, maximum, and last anomalies detected, along with
        their dates, and classifies anomalies based on the maximum magnitude relative
        to the provided thresholds.

        Args:
            thresholds (list, optional): list of float. Thresholds used to
                classify anomaly magnitudes. Defaults to [0.2, 0.3, 0.4].
            window_backward (int, optional): size of the backward window in days.
                Defaults to 720.
            window_forward (int, optional): size of the forward window in days.
                Defaults to 60.
            min_obs_backward (int, optional): minimum number of valid observations
                required in the backward window. Defaults to 5.
            min_obs_forward (int, optional): minimum number of valid observations
                required in the forward window. Defaults to 2.
            out_crs (str, optional): Coordinate Reference System (CRS) to assign
                to the output dataset. Defaults to "epsg:3035".

        Returns:
            ClearCut.detection (xr.Dataset):
                Results are stored with the following variables:
                - magnitude_first (float): Magnitude of the first anomaly detected.
                - date_first (Unix epoch): Date (days since epoch) of the first anomaly.
                - magnitude_max (float): Maximum anomaly magnitude detected.
                - date_max (Unix epoch): Date of the maximum anomaly.
                - magnitude_last (float): Magnitude of the last anomaly detected.
                - date_last (Unix epoch): Date of the last anomaly.
                - mask (binary): Boolean mask indicating anomaly presence.
                - inrange (binary): Boolean mask indicating whether sufficient observations were available in both windows.
                - classif (int): Classification layer based on thresholds.

        Notes:
            - Dates are stored as integer days since 1970-01-01.
            - The classification is performed using the maximum anomaly magnitude compared against the provided thresholds.
            - The output dataset is tagged with the specified CRS for spatial consistency in geospatial workflows.

        Example:
            >>> ndvi_ts.detect_anomalies()
    """

        da_window = self.da.sel(
            time=slice(
                self.da['time'].min().values + np.timedelta64(window_backward, 'D'),
                self.da['time'].max().values - np.timedelta64(window_forward, 'D')
            ))

        time = da_window['time'].values
        first_mag = xr.full_like(self.da.isel(time=0), np.nan)
        first_date = xr.full_like(self.da.isel(time=0), np.nan)
        max_mag = xr.full_like(self.da.isel(time=0), np.nan)
        max_date = xr.full_like(self.da.isel(time=0), np.nan)
        last_mag = xr.full_like(self.da.isel(time=0), np.nan)
        last_date = xr.full_like(self.da.isel(time=0), np.nan)
        in_range = xr.full_like(self.da.isel(time=0), False, dtype=bool)

        for d in time:
            mean_before, inrange_b = self.__mean_with_fallback(pivot_date = d,
                                                               window = window_backward,
                                                               direction='backward',
                                                               min_obs = min_obs_backward)
            mean_after, inrange_f = self.__mean_with_fallback(pivot_date = d,
                                                              window = window_forward,
                                                              direction='forward',
                                                              min_obs = min_obs_forward)

            mag = abs(mean_after - mean_before)

            mask = mag > thresholds[0]

            # First anomaly
            first_mask = mask & np.isnan(first_mag)
            first_mag = first_mag.where(~first_mask, mag)
            first_date = first_date.where(~first_mask,
                                  (pd.Timestamp(d) - pd.Timestamp("1970-01-01")) // pd.Timedelta(days=1),
                                  )

            # Max anomaly
            max_mask = mask & ((mag > max_mag) | np.isnan(max_mag))
            max_mag = max_mag.where(~max_mask, mag)
            max_date = max_date.where(~max_mask,
                                  (pd.Timestamp(d) - pd.Timestamp("1970-01-01")) // pd.Timedelta(days=1),
                                  )

            # Last anomaly
            last_mag = xr.where(mask, mag, last_mag)
            last_mag = last_mag.where(~mask, mag)
            last_date = last_date.where(~mask,
                                  (pd.Timestamp(d) - pd.Timestamp("1970-01-01")) // pd.Timedelta(days=1),
                                  )

            in_range = in_range | inrange_b | inrange_f

        # Classification based on max magnitude
        class_layer = self.__classify_anomalies(max_mag, thresholds)

        self.detection = xr.Dataset({
            'magnitude_first': first_mag,
            'date_first': first_date,
            'magnitude_max': max_mag,
            'date_max': max_date,
            'magnitude_last': last_mag,
            'date_last': last_date,
            'mask': ~np.isnan(first_mag),
            'inrange': in_range,
            'classif': class_layer,
        })
        self.detection = self.detection.rio.write_crs(out_crs)


def sieve_maj(dataarray,
              min_size=3,
              window_size=3,
              ignore_nan=True,
              connectivity=1,
              out_crs='epsg:3035'):
    """
    Remove small connected objects and replace them with local majority value.
    Preserves original coordinates and CRS.

    Args:
        dataarray (xr.DataArray): input array with integer classification values.
        min_size (int, optional): minimum size (number of pixels) to keep.
            Defaults to 3.
        window_size (int, optional): size of the moving window for majority filter.
            Defaults to 3
        ignore_nan (bool, optional): if True, NaNs are treated as background
            (converted to 0). Defaults to True.
        connectivity (int, optional): connectivity for labeling
            (1=4-connectivity, 2=8-connectivity). Defaults to 1
        out_crs (str, optional): output CRS. Defaults to 'epsg:3035'.

    Returns:
        xr.DataArray: filtered DataArray with original coords and CRS.

    Example:
        >>> sieve_maj(ndvi_ts.detection.classif)
    """
    # Force float for final output to allow NaNs
    arr_float = dataarray.values.astype(float).copy()

    # Handle NaNs
    nan_mask = np.isnan(arr_float) if ignore_nan else np.zeros_like(arr_float, dtype=bool)
    arr_int = arr_float.copy()
    if ignore_nan:
        arr_int[nan_mask] = 0  # treat NaN as background

    # Step 1: Identify small objects
    output = arr_int.copy()
    for cls in np.unique(arr_int):
        if cls == 0:  # skip background
            continue
        mask = arr_int == cls
        labeled, num_features = label(mask, structure=np.ones((3,3)) if connectivity == 2 else None)
        sizes = np.bincount(labeled.ravel())
        small_ids = np.where(sizes < min_size)[0]
        remove_mask = np.isin(labeled, small_ids)
        output[remove_mask] = 0  # mark small objects as background

    # Step 2: Compute majority filter using skimage (fast)
    arr_uint = output.astype(np.uint16)
    majority_neighborhood = modal(arr_uint, square(window_size))

    # Step 3: Replace zeros with local majority
    output[output == 0] = majority_neighborhood[output == 0]

    # Restore NaNs if needed
    if ignore_nan:
        output[nan_mask] = np.nan

    # Preserve coords and CRS
    return xr.DataArray(output, coords=dataarray.coords, dims=dataarray.dims, attrs=dataarray.attrs).rio.write_crs(out_crs)