import xarray as xr
import numpy as np
import spyndex


class SpectralIndex:
    """
    This class aims to calculate various spectral indices for remote sensing data
    using the spyndex and awesome-spectral-indices libraries.

    This class assumes input data is provided as an xarray.Dataset,
    possibly an xarray.Dataarray.
    It handles mapping user-defined band names to the generic band names
    required by spyndex.

    Args:
    dataset (xr.Dataset): The xarray.Dataset containing spectral bands.
    band_mapping (dict, optional): A dictionary to map your dataset's
                                   band names to spyndex's standard band
                                   names (e.g., {'R': 'B04', 'N': 'B08'}).
                                   If None, it assumes your dataset's
                                   variable names are directly usable by spyndex.
    """

    def __init__(self, dataset: xr.Dataset, band_mapping: dict = None):
        if not isinstance(dataset, xr.Dataset):
            raise TypeError("Input 'dataset' must be an xarray.Dataset.")

        self.dataset = dataset
        self.band_mapping = band_mapping if band_mapping is not None else {}

    def calculate_indices(self, indices_to_compute: str | list[str],
                          band_mapping: dict = None,
                          scale_factor: float = 10000):
        """
        Calculates one or more spectral indices from the input data array.

        Args:
            data_array (xarray.DataArray): The input remote sensing data.
                It must have a 'band' dimension containing the names of the 
                spectral bands (e.g., 'B04', 'B08').
                Data values are expected to be reflectance (e.g., 0-1 or 0-10000).
            indices_to_compute (str or list[str]): The name(s) of the spectral
                index/indices to calculate (e.g., 'NDVI', 'EVI'). These names
                must correspond to indices recognized by the spyndex library.
                Refer to `spyndex.indices.keys()` for a full list.
            band_mapping (dict, optional): A dictionary to map generic band
                names (required by spyndex, e.g., 'NIR', 'Red') to the actual
                band names present in your `data_array`
                (e.g., {'R': 'B04', 'N': 'B08'}).
                If None, the function assumes that the band names in `xr.Dataset`
                directly match the generic band names expected by `spyndex`.

        Returns:
            xarray.DataArray or xarray.Dataset: Returns an xarray.DataArray
                if a single index is requested, or an xarray.Dataset if 
                multiple indices are requested.
                The calculated index values will have NaNs where division by 
                zero or other invalid operations occurred.
        """

        # Ensure indices_to_compute is a list for consistent processing
        if isinstance(indices_to_compute, str):
            indices_to_compute = [indices_to_compute]
        if band_mapping is not None:
            self.band_mapping = band_mapping

        # Prepare parameters for spyndex.computeIndex
        # This dictionary will hold the xarray.DataArray for each required band
        spyndex_params = {}

        # Iterate through each requested index to determine all unique required bands
        all_required_generic_bands = set()
        for index_name in indices_to_compute:
            try:
                # Retrieve the required generic band names from spyndex
                # e.g., for NDVI: ['NIR', 'Red']
                required_generic_bands = spyndex.indices[index_name].bands
                all_required_generic_bands.update(required_generic_bands)
            except KeyError:
                raise ValueError(f"Index '{index_name}' not found in spyndex. "
                                 f"Available indices: {', '.join(spyndex.indices.keys())}")

        # Populate the spyndex_params dictionary with actual band data
        for generic_band_name in all_required_generic_bands:
            # Determine the actual band name in the input data_array
            actual_band_name = self.band_mapping.get(generic_band_name)
            # Check if the actual band exists in the data_array
            if actual_band_name not in self.dataset.data_vars.keys():
                # Provide a helpful error message indicating what was expected vs. found
                if band_mapping:
                    expected_msg = f"Expected generic band '{generic_band_name}' to map to '{actual_band_name}'."
                else:
                    expected_msg = f"Expected generic band '{generic_band_name}'."
                raise ValueError(
                    f"Missing required band for calculating indices: '{actual_band_name}'. "
                    f"{expected_msg} \nAvailable bands in data_array: {self.dataset.data_vars.keys()}"
                )

            # Select the band data and add it to the parameters for spyndex
            spyndex_params[generic_band_name] = self.dataset[actual_band_name] / scale_factor

        # Perform the calculation using spyndex
        # Using np.errstate to suppress warnings for division by zero or invalid operations,
        with np.errstate(divide='ignore', invalid='ignore'):
            computed_indices = spyndex.computeIndex(
                index=indices_to_compute,
                params=spyndex_params
            )

        # Post-processing: Ensure NaNs from invalid operations are handled consistently.
        computed_indices = computed_indices.where(np.isfinite(computed_indices), 
                                                  other=np.nan)

        return computed_indices