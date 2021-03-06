"""
    Code to train a Universal Background Model
"""

import os
import sidekit
from .config import config


def ubmfile():
    """Return the name for the ubm file for this configuration

    config: MODEL_DIR, NUMBER_OF_MIXTURES
    """

    ubmfile = 'ubm_%s.h5' % config("NUMBER_OF_MIXTURES")
    return os.path.join(config("MODEL_DIR"), ubmfile)


def train_ubm(server, basenames):
    """Train a UBM given the configuration settings

    config: NUMBER_OF_MIXTURES, THREADS, SAVE_PARTIAL, MODEL_DIR
    """

    ubm = sidekit.Mixture()

    #iterations = (1, 2, 2, 4, 4, 4, 4, 8, 8, 8, 8, 8, 8)
    iterations = (1, 2, 2, 2)

    ubm.EM_split(features_server=server,
                 feature_list=basenames,
                 distrib_nb=int(config("NUMBER_OF_MIXTURES")),
                 iterations=iterations,
                 num_thread=int(config("THREADS")),
                 save_partial=config("SAVE_PARTIAL"),
                 ceil_cov=10,
                 floor_cov=1e-2
                 )

    # write out a copy of the trained UBM
    ubm.write(ubmfile())

    return ubm


def load_or_train_ubm(server, basenames):
    """Load a UBM from disk if present or train one
    if not"""

    uf = ubmfile()
    if os.path.exists(uf):
        ubm = sidekit.Mixture()
        ubm.read(uf)
    else:
        ubm = train_ubm(server, basenames)

    return ubm


def sufficient_stats(idmap, server, ubm):
    """
    Generate the sufficient statistics for speaker data given a UBM

    config: NUMBER_OF_MIXTURES, THREADS, FEATURE_SIZE
    :return:
    """
    sufstat = sidekit.StatServer(idmap,
                                 distrib_nb=int(config('NUMBER_OF_MIXTURES')),
                                 feature_size=int(config('FEATURE_SIZE')))
    sufstat.accumulate_stat(ubm=ubm,
                            feature_server=server,
                            seg_indices=range(sufstat.segset.shape[0]),
                            num_thread=int(config('THREADS')))

    filename = "sufstat_%s_%s.h5" % (config("NUMBER_OF_MIXTURES"), config("FEATURE_SIZE"))

    sufstat.write(os.path.join(config('MODEL_DIR'), filename))

    return sufstat


def adapt_models(ubm, sufstat):
    """
    Adapt a UBM to a number of speakers via MAP adaptation

    config: MODEL_DIR
    :return:
    """

    regulation_factor = 3
    speaker_models = sufstat.adapt_mean_map_multisession(ubm, regulation_factor)

    filename = "speakers_%s_%s.h5" % (config("NUMBER_OF_MIXTURES"), config("FEATURE_SIZE"))

    speaker_models.write(os.path.join(config('MODEL_DIR'), filename))

    return speaker_models
