# -*- coding: utf-8 -*-
import numpy as np
from scipy.ndimage import gaussian_filter


def rescale_pattern_intensity(pattern, imin=None, scale=None,
                              dtype_out=np.uint8):
    """Rescale electron backscatter diffraction pattern intensities to
    unsigned integer range or desired unsigned range specified by imin
    and scale. If imin and scale are passed the pattern intensities are
    stretched to a global min. and max. intensity according to these
    values. Otherwise they are stretched to between zero and maximum of
    dtype_out.

    Parameters
    ----------
    pattern : numpy array of unsigned integer dtype
        Input pattern.
    imin : int, optional
        Global min. intensity of patterns.
    scale : float, optional
        Global scaling factor for intensities of output pattern.
    dtype_out : numpy dtype
        Data type of output pattern.

    Returns
    -------
    pattern : numpy array
        Output pattern rescaled to specified range.
    """
    # TODO: Stop function from leaking memory when used with map
    if np.issubdtype(dtype_out, np.unsignedinteger) is False:
        raise ValueError("Data type is not unsigned integer.")

    if imin is None and scale is None:  # Local contrast stretching
        omax = np.iinfo(dtype_out).max
        imin = pattern.min()
        scale = float(omax / (pattern.max() - imin))

    # Set lowest intensity to zero
    pattern = pattern - imin

    # Scale intensities
    return np.array(pattern * scale, dtype=dtype_out)


def correct_background(pattern, static, dynamic, bg, sigma, imin, scale):
    """Perform background correction on an electron backscatter
    diffraction patterns.

    Parameters
    ----------
    pattern : numpy array of unsigned integer dtype
        Input pattern.
    static : bool, optional
        If True, static correction is performed.
    dynamic : bool, optional
        If True, dynamic correction is performed.
    bg : numpy array
        Background image for static correction.
    sigma : int, float
        Standard deviation for the gaussian kernel for dynamic
        correction.
    imin : int
        Global min. intensity of patterns.
    scale : int, float
        Global scaling factor for intensities of output pattern.

    Returns
    -------
    pattern : numpy array
        Output pattern with background corrected and intensities
        stretched to a desired range.
    """
    if static:
        # Change data types to avoid negative intensities in subtraction
        dtype = np.int8
        pattern = pattern.astype(dtype)
        bg = bg.astype(dtype)

        # Subtract static background
        pattern = pattern - bg

        # Rescale intensities, either keeping relative intensities or not
        pattern = rescale_pattern_intensity(pattern, imin=imin, scale=scale)

    if dynamic:
        # Create gaussian blurred version of pattern
        blurred = gaussian_filter(pattern, sigma, truncate=2.0)

        # Change data types to avoid negative intensities in subtraction
        dtype = np.int16
        pattern = pattern.astype(dtype)
        blurred = blurred.astype(dtype)

        # Subtract blurred background
        pattern = pattern - blurred

        # Rescale intensities, loosing relative intensities
        pattern = rescale_pattern_intensity(pattern)

    return pattern


def remove_dead(pattern, deadpixels, deadvalue="average", d=1):
    """Remove dead pixels from a pattern.

    NB! This function is slow for lazy signals and leaks memory.

    Parameters
    ----------
    pattern : numpy array or dask array
        Two-dimensional data array containing signal.
    deadpixels : numpy array
        Array containing the array indices of dead pixels in the
        pattern.
    deadvalue : string
        Specify how deadpixels should be treated, options are;
            'average': takes the average of adjacent pixels
            'nan':  sets the dead pixel to nan
    d : int, optional
        Number of adjacent pixels to average over.

    Returns
    -------
    new_pattern : numpy array or dask array
        Two-dimensional data array containing z with dead pixels
        removed.
    """
    # TODO: Stop function from leaking memory when used with map
    new_pattern = np.copy(pattern)
    if deadvalue == 'average':
        for (i, j) in deadpixels:
            neighbours = pattern[i - d:i + d + 1, j - d:j + d + 1].flatten()
            neighbours = np.delete(neighbours, 4)  # Exclude dead pixel
            new_pattern[i, j] = int(np.mean(neighbours))
    elif deadvalue == 'nan':
        for (i, j) in deadpixels:
            new_pattern[i, j] = np.nan
    else:
        raise NotImplementedError("The method specified is not implemented. "
                                  "See documentation for available "
                                  "implementations.")
    return new_pattern
