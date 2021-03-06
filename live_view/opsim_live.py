import argparse
import collections
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import SALPY_scheduler
import sys

PROJECTION = "aitoff"
NUM_FIELDS = 10

LSST_FOV_RADIUS = math.radians(1.75)
LSST_FOV = LSST_FOV_RADIUS * 2.0
MOON_SCALE = 6.0
MOON_DIA = math.radians(0.5 * MOON_SCALE)

ALPHA = 0.4
FILTER_DICT = collections.OrderedDict([('u', [0, 0, 1, 1]), ('g', [0, 1, 1, 1]),
                                       ('r', [0, 1, 0, 1]), ('i', [1, .5, 0, 1]),
                                       ('z', [1, 0, 0, 1]), ('y', [1, 0, 1, 1])])
MOON_ALPHA = 0.15
ASTRO_TWILIGHT = -18.0

def axisSetup(ax):
    ax.grid(True)
    ax.xaxis.set_ticklabels([])

def run(opts):
    manager = SALPY_scheduler.SAL_scheduler()
    manager.setDebugLevel(0)
    manager.salTelemetrySub("scheduler_observation")
    obs = SALPY_scheduler.scheduler_observationC()
    if opts.verbose > 0:
        print("After setting up subscriber")

    plt.ion()

    fig, ax1 = plt.subplots(subplot_kw={"projection": PROJECTION})
    axisSetup(ax1)

    for i, (band_filter, filter_color) in enumerate(FILTER_DICT.items()):
        fig.text(0.41 + i * 0.035, 0.15, band_filter, color=filter_color)

    fig.show()
    num_obs = 0
    try:
        if opts.verbose > 0:
            print("Starting topic loop.")
        field_list = []

        while True:
            rcode = manager.getNextSample_observation(obs)
            if opts.verbose > 1:
                print("A: {}, {}, {}".format(rcode, obs.num_exposures, obs.filter))
            if rcode == 0 and obs.num_exposures != 0 and obs.filter != '':
                plt.cla()

                ra = np.radians(obs.ra)
                dec = np.radians(obs.dec)
                color = FILTER_DICT[obs.filter]
                zenith_ra = np.radians(obs.observation_start_lst)
                ra = -(ra - zenith_ra - np.pi) % (np.pi * 2.) - np.pi

                ellipse = patches.Ellipse((ra, dec), LSST_FOV / np.cos(dec), LSST_FOV, edgecolor='k',
                                          facecolor=color)

                field_list.append(ellipse)

                for field in field_list:
                    ax1.add_patch(field)

                if obs.moon_alt > -0.25 * MOON_SCALE:
                    moon_ra = np.radians(obs.moon_ra)
                    moon_ra = -(moon_ra - zenith_ra - np.pi) % (np.pi * 2.) - np.pi
                    moon_dec = np.radians(obs.moon_dec)
                    alpha = np.max([obs.moon_phase / 100., MOON_ALPHA])
                    moon = patches.Ellipse((moon_ra, moon_dec), MOON_DIA / np.cos(moon_dec), MOON_DIA,
                                           color='k', alpha=alpha)
                    ax1.add_patch(moon)

                axisSetup(ax1)
                fig_title = "Night {}, MJD {}".format(obs.night, obs.observation_start_mjd)
                plt.text(0.5, 1.18, fig_title, horizontalalignment='center', transform=ax1.transAxes)
                moon_phase_text = "Moon Phase: {:.1f}%".format(obs.moon_phase)
                plt.text(0.8, 1.0, moon_phase_text, transform=ax1.transAxes)
                if obs.sun_alt <= ASTRO_TWILIGHT:
                    tom_text = "Night"
                else:
                    tom_text = "Twilight"
                plt.text(0.8, 0.0, tom_text, transform=ax1.transAxes)

                plt.draw()
                plt.pause(0.0001)

                field_list[-1].set_alpha(ALPHA)
                field_list[-1].set_edgecolor('none')
                if len(field_list) > opts.trail:
                    field_list.pop(0)
                num_obs += 1
                if opts.verbose > 1:
                    print("Observation number {}".format(num_obs))

    except KeyboardInterrupt:
        manager.salShutdown()
        if opts.verbose > 0:
            print("Total observations received: {}".format(num_obs))
        sys.exit(0)

if __name__ == "__main__":

    description = ["Python script to live view a running simulation or a survey database."]

    parser = argparse.ArgumentParser(description=" ".join(description))
    parser.add_argument("-v", "--verbose", dest="verbose", action='count', default=0,
                        help="Set the verbosity of the program.")
    parser.add_argument("-t", "--trail", dest="trail", default=10, type=int,
                        help="Set the number of fields to keep.")
    parser.set_defaults()
    args = parser.parse_args()

    run(args)
