# -*- coding: utf-8 -*-
"""
test_sink_filler:

Created on Tues Oct 20, 2015

@author: dejh
"""
import pytest

from numpy import sin, pi
import numpy as np  # for use of np.round
from numpy.testing import assert_array_equal, assert_array_almost_equal
from nose.tools import with_setup

import landlab
from landlab import BAD_INDEX_VALUE as XX
from landlab import RasterModelGrid, FieldError
from landlab.components.flow_routing import FlowRouter
from landlab.components.sink_fill import SinkFiller


def setup_dans_grid4():
    """
    Create a 10x10 test grid with two well defined holes in it, into an
    inclined surface. This time, one of the holes is a stupid shape, which
    will require the component to arrange flow back "uphill".
    """
    global hf, fr, mg
    global z, depr_outlet_target
    global lake, lake1, lake2, outlet, outlet_array

    lake1 = np.array([34, 35, 36, 44, 45, 46, 54, 55, 56, 65, 74])
    lake2 = np.array([78, 87, 88])
    guard_nodes = np.array([23, 33, 53, 63, 73, 83])
    lake = np.concatenate((lake1, lake2))
    outlet = 35  # shouldn't be needed
    outlet_array = np.array([outlet])

    mg = RasterModelGrid(10, 10, 1.)

    z = np.ones(100, dtype=float)
    # add slope
    z += mg.node_x
    z[guard_nodes] += 0.001  # forces the flow out of a particular node
    z[lake] = 0.

    depr_outlet_target = np.empty(100, dtype=float)
    depr_outlet_target.fill(XX)
    depr_outlet_target = XX  # not well defined in this simplest case...?

    mg.add_field("node", "topographic__elevation", z, units="-")

    fr = FlowRouter(mg)


def setup_dans_grid5():
    """
    Create a 10x10 test grid with two well defined holes in it, into an
    inclined surface. This time, one of the holes is a stupid shape, which
    will require the component to arrange flow back "uphill". Exactly as
    V4, but this version tests D4 routing.

    Notes
    -----
    Here is the elevation grid:

    1.      2.      3.      4.      5.      6.      7.      8.      9.     10.
    1.      2.      3.      4.      5.      6.      7.      8.      9.     10.
    1.      2.      3.      4.001   5.      6.      7.      8.      9.     10.
    1.      2.      3.      4.001   0.      0.      0.      8.      9.     10.
    1.      2.      3.      4.      5.      6.      7.      8.      9.     10.
    1.      2.      3.      4.001   0.      0.      0.      8.      9.     10.
    1.      2.      3.      4.001   5.      0.      7.      8.      9.     10.
    1.      2.      3.      4.001   0.      6.      7.      8.      0.     10.
    1.      2.      3.      4.001   5.      6.      7.      0.      0.     10.
    1.      2.      3.      4.      5.      6.      7.      8.      9.     10.
    """
    global hf, fr, mg
    global z, depr_outlet_target
    global lake, lake1, lake2, outlet, outlet_array

    lake1 = np.array([34, 35, 36, 44, 45, 46, 54, 55, 56, 65, 74])
    lake2 = np.array([78, 87, 88])
    guard_nodes = np.array([23, 33, 53, 63, 73, 83])
    lake = np.concatenate((lake1, lake2))
    outlet = 35  # shouldn't be needed
    outlet_array = np.array([outlet])

    mg = RasterModelGrid(10, 10, 1.)

    z = np.ones(100, dtype=float)
    # add slope
    z += mg.node_x
    z[guard_nodes] += 0.001  # forces the flow out of a particular node
    z[lake] = 0.

    depr_outlet_target = np.empty(100, dtype=float)
    depr_outlet_target.fill(XX)
    depr_outlet_target = XX  # not well defined in this simplest case...?

    mg.add_field("node", "topographic__elevation", z, units="-")

    fr = FlowRouter(mg)


def check_fields(sink_grid1):
    """
    Check to make sure the right fields have been created.
    """
    assert_array_equal(
        np.zeros(sink_grid1.number_of_nodes), sink_grid1.at_node["sediment_fill__depth"]
    )
    with pytest.raises(FieldError):
        sink_grid1.at_node["drainage_area"]


def test_get_lake_ext_margin(sink_grid1):
    hf = SinkFiller(sink_grid1)

    lake = np.array([16, 17, 23, 24, 25, 30, 31, 32])
    ext_margin_returned = hf._get_lake_ext_margin(lake)
    ext_margin = np.array(
        [8, 9, 10, 11, 15, 18, 19, 22, 26, 29, 33, 36, 37, 38, 39, 40]
    )
    assert_array_equal(ext_margin_returned, ext_margin)


def test_get_lake_int_margin(sink_grid1):
    hf = SinkFiller(sink_grid1)

    lake = np.array([16, 17, 18, 23, 24, 25, 26, 30, 31, 32])
    ext_margin = np.array(
        [8, 9, 10, 11, 12, 15, 19, 20, 22, 27, 29, 33, 34, 36, 37, 38, 39, 40]
    )
    int_margin_returned = hf._get_lake_int_margin(lake, ext_margin)
    int_margin = np.array([16, 17, 18, 23, 25, 26, 30, 31, 32])
    assert_array_equal(int_margin_returned, int_margin)


def test_drainage_directions_change(sink_grid1):
    hf = SinkFiller(sink_grid1)

    lake = np.array([22, 23])
    old_elevs = np.ones(49, dtype=float)
    old_elevs[lake] = 0.
    new_elevs = old_elevs.copy()
    new_elevs[40] = 2.
    cond = hf.drainage_directions_change(lake, old_elevs, new_elevs)
    assert not cond
    new_elevs[23] = 0.5
    cond = hf.drainage_directions_change(lake, old_elevs, new_elevs)
    assert not cond
    new_elevs[23] = 1.
    cond = hf.drainage_directions_change(lake, old_elevs, new_elevs)
    assert not cond
    new_elevs[23] = 1.2
    cond = hf.drainage_directions_change(lake, old_elevs, new_elevs)
    assert cond


def test_add_slopes(sink_grid1):
    z = sink_grid1.at_node["topographic__elevation"]
    hf = SinkFiller(sink_grid1)

    new_z = z.copy()
    outlet_elev = z[sink_grid1.outlet]
    hf._elev[sink_grid1.lake] = outlet_elev
    rt2 = np.sqrt(2.)
    slope_to_add = 0.1
    lake_map = np.empty_like(z)
    lake_map.fill(XX)
    lake_map[sink_grid1.lake] = sink_grid1.lake_code
    hf._lf._lake_map = lake_map
    hf.lake_nodes_treated = np.array([], dtype=int)
    dists = sink_grid1.calc_distances_of_nodes_to_point(
        (sink_grid1.node_x[sink_grid1.outlet], sink_grid1.node_y[sink_grid1.outlet])
    )
    new_z[sink_grid1.lake] = outlet_elev
    new_z[sink_grid1.lake] += dists[sink_grid1.lake] * slope_to_add
    # test the ones we can do easily analytically separately
    straight_north = np.array([23, 16])
    off_angle = 24
    elevs_out, lake_out = hf._add_slopes(
        slope_to_add, sink_grid1.outlet, sink_grid1.lake_code
    )
    assert_array_equal(
        slope_to_add * (np.arange(2.) + 1.) + outlet_elev, elevs_out[straight_north]
    )
    assert slope_to_add * rt2 + outlet_elev == pytest.approx(elevs_out[off_angle])
    assert_array_equal(new_z, elevs_out)
    assert_array_equal(sink_grid1.lake, lake_out)


def test_filler_flat(sink_grid2):
    """
    Very simple, though possibly degerate, case, filling a 3x3 hole up to
    the flat surface surrounding it.
    """
    hf = SinkFiller(sink_grid2)
    hf.fill_pits()
    assert_array_equal(hf._elev[sink_grid2.lake], np.ones(9, dtype=float))
    assert_array_equal(
        sink_grid2.at_node["topographic__elevation"][sink_grid2.lake],
        np.ones(9, dtype=float),
    )


# @with_setup(setup_dans_grid3)
def test_filler_inclined(sink_grid3):
    """
    Tests a flat fill into an inclined surface, with two holes.
    """
    hf = SinkFiller(sink_grid3)
    hf.fill_pits()
    assert_array_equal(
        sink_grid3.at_node["topographic__elevation"][sink_grid3.lake1],
        np.ones(9, dtype=float) * 4.,
    )
    assert_array_equal(
        sink_grid3.at_node["topographic__elevation"][sink_grid3.lake2],
        np.ones(4, dtype=float) * 7.,
    )


# @with_setup(setup_dans_grid3)
def test_filler_inclined2(sink_grid3):
    """
    Tests an inclined fill into an inclined surface, with two holes.
    """
    z_init = sink_grid3.at_node["topographic__elevation"].copy()
    fr = FlowRouter(sink_grid3)
    hf = SinkFiller(sink_grid3, apply_slope=True)

    hf.fill_pits()
    hole1 = np.array(
        [
            4.00009091,
            4.00018182,
            4.00027273,
            4.00036364,
            4.00045455,
            4.00054545,
            4.00063636,
            4.00072727,
            4.00081818,
        ]
    )
    hole2 = np.array([7.16666667, 7.33333333, 7.5, 7.66666667])
    assert_array_almost_equal(
        sink_grid3.at_node["topographic__elevation"][sink_grid3.lake1], hole1
    )
    assert_array_almost_equal(
        sink_grid3.at_node["topographic__elevation"][sink_grid3.lake2], hole2
    )
    fr.route_flow()
    assert sink_grid3.at_node["flow__sink_flag"][sink_grid3.core_nodes].sum() == 0


@with_setup(setup_dans_grid4)
def test_stupid_shaped_hole():
    """
    Tests inclined fill into a surface with a deliberately awkward shape.
    """
    hf = SinkFiller(mg, apply_slope=True)
    hf.fill_pits()
    hole1 = np.array(
        [
            4.00007692,
            4.00015385,
            4.00023077,
            4.00030769,
            4.00038462,
            4.00046154,
            4.00053846,
            4.00061538,
            4.00069231,
            4.00076923,
            4.00084615,
        ]
    )
    hole2 = np.array([7.4, 7.2, 7.6])

    assert_array_almost_equal(mg.at_node["topographic__elevation"][lake1], hole1)
    assert_array_almost_equal(mg.at_node["topographic__elevation"][lake2], hole2)
    fr.route_flow()
    assert mg.at_node["flow__sink_flag"][mg.core_nodes].sum() == 0


@with_setup(setup_dans_grid5)
def test_D4_routing():
    """
    Tests inclined fill into a surface with a deliberately awkward shape.
    This is testing D4 routing.
    """
    hf = SinkFiller(mg, routing="D4", apply_slope=True)
    hf.fill_pits()
    #    hole1 = np.array([4.00016667, 4.00025, 4.00033333, 4.00008333, 4.00041667,
    #                      4.0005, 4.00066667, 4.00058333, 4.00075,
    #                      4.334])
    hole1 = np.array(
        [
            4.00016667,
            4.00033333,
            4.0005,
            4.00008333,
            4.00025,
            4.00041667,
            4.000833,
            4.00066667,
            4.00058333,
            4.00075,
            4.334,
        ]
    )
    hole2 = np.array([7.6, 7.2, 7.4])

    assert_array_almost_equal(mg.at_node["topographic__elevation"][lake1], hole1)
    assert_array_almost_equal(mg.at_node["topographic__elevation"][lake2], hole2)
    fr.route_flow(method="D4")
    assert mg.at_node["flow__sink_flag"][mg.core_nodes].sum() == 0


@with_setup(setup_dans_grid5)
def test_D4_filling():
    """
    Tests inclined fill into a surface with a deliberately awkward shape.
    This is testing D4 without inclining the surface.
    """
    hf = SinkFiller(mg, routing="D4")
    hf.fill_pits()
    hole1 = 4. * np.ones_like(lake1, dtype=float)
    hole1[-1] += 0.001
    hole2 = 7. * np.ones_like(lake2, dtype=float)

    assert_array_almost_equal(mg.at_node["topographic__elevation"][lake1], hole1)
    assert_array_almost_equal(mg.at_node["topographic__elevation"][lake2], hole2)
