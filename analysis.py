import numpy as np
def calculate_time_domain(raw_data, sampling_rate):
    """Calculates time values for the raw vibration data."""
    return np.arange(len(raw_data)) / sampling_rate

def perform_fft(raw_data, sampling_rate):
    """
    Performs a Fast Fourier Transform on the raw vibration data.
    Returns frequency bins and corresponding amplitudes.
    """
    N = len(raw_data)
    if N == 0 or sampling_rate == 0:
        return [], []

    T = 1.0 / sampling_rate
    yf = np.fft.fft(raw_data)
    xf = np.fft.fftfreq(N, T)[:N // 2]
    amplitude = 2.0 / N * np.abs(yf[0:N // 2])
    return xf, amplitude