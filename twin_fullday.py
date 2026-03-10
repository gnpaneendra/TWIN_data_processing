# Author: G N PANEENDRA

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import matplotlib.ticker as mtick
from matplotlib.ticker import MaxNLocator
import os
import sys
import glob
from tqdm import tqdm

# Fucntions

def extract_ist_time_from_file(filename):
        basename = os.path.basename(filename)
        time_str = basename.split('_')[3] + '_' + basename.split('_')[4].split('.')[0]
        ist_time = datetime.strptime(time_str, '%Y-%m-%d_%H-%M-%S')
        return ist_time

def extract_utc_time_from_filename(filename):
	basename = os.path.basename(filename)
	time_str = basename.split('_')[3] + '_' + basename.split('_')[4].split('.')[0]
	ist_time = datetime.strptime(time_str, '%Y-%m-%d_%H-%M-%S')
	ist_offset = timedelta(seconds=19800)
	utc_time = ist_time - ist_offset
	return utc_time

def rfimit(bp_freq, bp_spec1, bp_spec2, bp_both, rfi_bands):

    clean_band = (320e6, 340e6)

    # clean band mask
    clean_mask = (bp_freq >= clean_band[0]) & (bp_freq <= clean_band[1])

    # median per time row
    rep1 = np.median(bp_spec1[:, clean_mask], axis=1, keepdims=True)
    rep2 = np.median(bp_spec2[:, clean_mask], axis=1, keepdims=True)
    repc = np.median(bp_both[:, clean_mask], axis=1, keepdims=True)

    # convert band list → arrays
    bands = np.array(rfi_bands)
    lows = bands[:,0]
    highs = bands[:,1]

    # vectorized band mask
    rfi_mask = ((bp_freq[:,None] >= lows) & (bp_freq[:,None] <= highs)).any(axis=1)

    # replace values (broadcasting handles shape automatically)
    bp_spec1[:, rfi_mask] = rep1
    bp_spec2[:, rfi_mask] = rep2
    bp_both[:, rfi_mask] = repc

    return bp_spec1, bp_spec2, bp_both

def plot(spec, freq, time, xmax_k, ymax_k, name):
	
	# Summing of the spectrum horizontally and vertically
	ver_sum_spec = np.mean(spec, axis = 1)
	hor_sum_spec = np.mean(spec, axis = 0)
	
	xm = np.std(hor_sum_spec)
	xmax_1 = 3*xm
	xmax_2 = xmax_k*xm
	xmin = np.min(spec)
	ym = np.std(ver_sum_spec)
	ymax = ymax_k*ym
	ymin = np.min(ver_sum_spec)
	
	# To convert datetime to Matplotlib numeric time
	time_num = mdates.date2num(time)
	
	desired_ticks = 10
	tick_times = np.linspace(time_num[0], time_num[-1], desired_ticks)
	
	T, F = np.meshgrid(time, freq)
	
	fig = plt.figure(figsize=(22, 12))
	gs = GridSpec(2, 2, width_ratios=[1, 3], height_ratios=[3, 1])
	fig.suptitle(f"{date}, {time_1} - {time_n}, TWIN (RRI) - {name}", fontsize=15)

	# Subplot - 1
	ax1 = fig.add_subplot(gs[0, 0])
	ax1.plot(hor_sum_spec, freq)
	ax1.set_xlabel('Power', fontsize=14)
	ax1.set_ylabel('Frequency (MHz)', fontsize=14)
	ax1.yaxis.set_major_locator(MaxNLocator(prune=None))
	ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x * 1e-6:.0f}'))
	ax1.set_ylim(freq[0], freq[len(freq)-1])
	ax1.tick_params(axis='both', labelsize=14)
	ax1.set_xlim(0, xmax_1)
	
	# Subplot - 2 (Waterfall plot)
	ax2 = fig.add_subplot(gs[0, 1])
	level = np.linspace(xmin, xmax_2, 50) 
	ax2.contourf(T, F, spec.T, levels=level, cmap='jet', vmin=xmin, vmax=xmax_2)
	ax2.set_xlabel('Time (UTC)', fontsize=14)
	ax2.set_ylabel('Frequency (MHz)', fontsize=14)
	ax2.yaxis.set_major_locator(MaxNLocator(prune=None))
	ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x * 1e-6:.0f}'))
	ax2.xaxis_date()
	ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
	ax2.set_xticks(tick_times)
	ax2.set_xticklabels([mdates.num2date(t).strftime('%H:%M') for t in tick_times])
	ax2.tick_params(axis='both', labelsize=14)
	#fig.colorbar(c, ax=ax2)

	# Subplot - 3
	ax3 = fig.add_subplot(gs[1, 1])
	ax3.plot(time, ver_sum_spec)
	ax3.set_xlabel('Time (UTC)', fontsize=14)
	ax3.set_ylabel('Power', fontsize=14)
	ax3.xaxis_date()
	ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
	ax3.set_xticks(tick_times)
	ax3.set_xticklabels([mdates.num2date(t).strftime('%H:%M') for t in tick_times])
	ax3.set_xlim(time[0], time[len(time)-1])
	ax3.set_ylim(ymin, ymax)
	ax3.tick_params(axis='both', labelsize=14)
	
	fig.tight_layout()
	
	filename = f'{date_name}_TWIN_GBD_{name}_{time_1_name}_{time_n_name}.png'
	full_path = os.path.join(output_directory, filename)
	plt.savefig(full_path)
	print(f'\nSpectrographs saved as "{filename}" in {output_directory}')
	
	#plt.show()



#path = r'data/twin/2024_02_22/'
path = str(sys.argv[1])

print(f"\nData directory: {path}")

n_files = int(os.popen(f"ls {path}/*.csv | wc -l").read().strip())
print(f"\nNo. of files: {n_files}")
if n_files == 0:
	sys.exit("There are no files in this folder")

# Sort the files based on the time and read each .csv file
files = glob.glob(os.path.join(path, '*.csv'))
files_sorted_by_time = sorted(files, key=extract_utc_time_from_filename)
print("\nFiles are sorted according to time")


date = extract_utc_time_from_filename(files_sorted_by_time[0]).strftime('%Y/%m/%d')
date_name = extract_utc_time_from_filename(files_sorted_by_time[0]).strftime('%Y-%m-%d')
date_name_dir = extract_utc_time_from_filename(files_sorted_by_time[0]).strftime('%Y_%m_%d')
time_1 = extract_utc_time_from_filename(files_sorted_by_time[0]).strftime('%H:%M:%S')
time_n = extract_utc_time_from_filename(files_sorted_by_time[-1]).strftime('%H:%M:%S')
time_1_name = extract_utc_time_from_filename(files_sorted_by_time[0]).strftime('%H-%M-%S')
time_n_name = extract_utc_time_from_filename(files_sorted_by_time[-1]).strftime('%H-%M-%S')
ist_time_1 = extract_ist_time_from_file(files_sorted_by_time[0]).strftime('%H:%M:%S')
ist_time_n = extract_ist_time_from_file(files_sorted_by_time[-1]).strftime('%H:%M:%S')

print(f"\nObservation date: {date}")
print(f"Observation time(IST): {ist_time_1} - {ist_time_n}")
print(f"Observation time(UT): {time_1} - {time_n}\n")

fft_length = 2048
sampling_rate = 1.25e9  # in Hz
frequencies = np.fft.fftfreq(fft_length, 1 / sampling_rate)[:fft_length // 2]
freq_mask = (frequencies >= 179e6) & (frequencies <= 361e6)
bp_frequencies = frequencies[freq_mask]

n_freq = np.sum(freq_mask)
element1_spec = np.zeros((n_files, n_freq))
element2_spec = np.zeros((n_files, n_freq))
cross_spec = np.zeros((n_files, n_freq))
utc_time = np.empty(n_files, dtype='datetime64[ns]')

norm = (fft_length/2)
norm_cross = (fft_length/2)**2
p_half = fft_length//2

print("Reading the files and performing fft...")
for i, filename in enumerate(tqdm(files_sorted_by_time)):

    data = np.loadtxt(filename, delimiter=',', skiprows=1)

    ch1 = data[:,0]
    ch2 = data[:,1]

    fft1 = np.fft.rfft(ch1, fft_length)
    fft2 = np.fft.rfft(ch2, fft_length)

    spec1 = ((np.abs(fft1)**2 / norm)[:p_half])[freq_mask]
    spec2 = ((np.abs(fft2)**2 / norm)[:p_half])[freq_mask]

    spec_cross = ((np.abs(fft1 * np.conj(fft2))**2 / norm_cross)[:p_half])[freq_mask]

    element1_spec[i, :] = spec1
    element2_spec[i, :] = spec2
    cross_spec[i, :] = spec_cross

    utc_time[i] = extract_utc_time_from_filename(filename)
print("\nDone")

# rfim_Band pass isolation
print("\nFrequency domaind RFI Mitigation...", end=" ")
rfi_bands = [(180e6, 181.5e6), (215e6, 225e6), (238.5e6, 271e6), (278e6, 283e6), (320e6, 322e6), (343.9e6, 345e6), (347e6, 351e6)]
element1_rfim_spec, element2_rfim_spec, cross_rfim_spec= rfimit(bp_frequencies, element1_spec, element2_spec, cross_spec, rfi_bands)
print("Done")

output_directory = os.path.expanduser(f'~/Downloads/TWIN_data_processing/spectrograph/')
os.makedirs(output_directory, exist_ok=True)

# Plotting
print("\nSaving spectrographs...")
plot(element1_rfim_spec, bp_frequencies, utc_time, 20, 20, name = 'Element_1')
plot(element2_rfim_spec, bp_frequencies, utc_time, 11, 16, name = 'Element_2')
plot(cross_rfim_spec, bp_frequencies, utc_time, 11, 2, name = 'Correlated')
print("\nDone\n")
