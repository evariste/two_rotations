"""
Created by: Paul Aljabar
Date: 08/06/2023
"""

import numpy as np
from utilities import ensure_vec_3d, ensure_vec_2d, ensure_unit_vec_3d, ensure_unit_vec_2d
from vtk_utils import run_triangle_filter
from vtk_io import make_vtk_polydata, polydata_save
from matplotlib.patches import Polygon

class Plane:
    def __init__(self, normal, pt):
        self.normal = ensure_vec_3d(normal)

        d = np.sqrt(np.sum(self.normal * self.normal))
        assert d > 0, 'Normal is zero vector'
        self.normal = self.normal / d

        self.pt = ensure_vec_3d(pt)

        self.const = np.sum(self.normal * self.pt)

        return
    def intersection(self, other):

        cosine = np.abs(np.sum(self.normal * other.normal))

        if np.isclose(cosine, 1.0):
            raise Exception('Planes are parallel.')

        direction = np.cross(self.normal.flatten(), other.normal.flatten())

        M = np.zeros((2,3))
        M[0, :] = self.normal.flatten()
        M[1, :] = other.normal.flatten()

        b = np.zeros((2, 1))
        b[0] = self.const
        b[1] = other.const

        pt_inter, residuals, rank, sing_vals = np.linalg.lstsq(M, b, rcond=None)

        intersection = Line(pt_inter, direction)

        return intersection






class Line(object):
    def __init__(self, pt, direction):
        self.pt = ensure_vec_3d(pt)
        self.direction = ensure_vec_3d(direction)

        d_norm = np.sqrt(np.sum(self.direction * self.direction))
        assert d_norm > 0, 'Zero vector given as direction.'

        self.direction /= d_norm

        return

    def nearest(self, point):

        v = ensure_vec_3d(point)

        cent_to_v = v - self.pt

        coeff_along = np.sum(cent_to_v * self.direction)
        comp_along = coeff_along * self.direction

        nearest_pt = self.pt + comp_along

        return nearest_pt

class Glyph(object):
    def __init__(self):
        pass

class Glyph3D(object):
    labelled_points = {
        'A': [0,0,0],
        'B': [2,0,0],
        'C': [1.5,1,0],
        'D': [0,1,0],
        'E': [2,0,1],
        'F': [1.5,1,1],
        'G': [1,1,1],
        'H': [1,1,2],
        'I': [0,1,2],
        'J': [1,0,1],
        'K': [0,0,3],
        'L': [1,0,3],
    }
    labelled_polys = [
        'BEFC',
        'JGFE',
        'CFGHID',
        'KLJEBA',
        'JLHG',
        'DIKA',
        'HLKI',
        'ABCD'
    ]
    def __init__(self, points=None, cells=None):
        if points is None:
            self.points = self.get_default_points()
        else:
            self.points = points

        if cells is None:
            self.cells = self.get_default_cells()
        else:
            self.cells = cells

    def get_default_points(self):
        ordered_point_labels = sorted(list(self.labelled_points.keys()))
        pts = []
        for l in ordered_point_labels:
            pts.append(self.labelled_points[l])
        return np.transpose(np.asarray(pts)).astype(np.float64)

    def get_default_cells(self):
        if self.points is None:
            self.points = self.get_default_points()

        cells = []
        ordered_point_labels = sorted(list(self.labelled_points.keys()))
        for poly_vertex_labels in self.labelled_polys:
            vertex_inds = [ordered_point_labels.index(l) for l in poly_vertex_labels]
            cells.append(vertex_inds)

        return cells

    def save(self, file_name):
        pd = make_vtk_polydata(self.points.T, self.cells)
        pd = run_triangle_filter(pd)
        polydata_save(pd, file_name)

    def apply_transformation(self, transform, in_place=False, t=1.0):
        new_points = transform.apply(self.points, t=t)
        if in_place:
            self.points = new_points
            return self
        else:
            return Glyph3D(new_points)


class Glyph2D(object):
    default_points = np.asarray(
        [
            [0, 0],
            [2, 0],
            [2, 2],
            [1, 1],
            [1, 4],
            [0, 4]
        ]
    ).T

    def __init__(self, points=None, facecolor='blue'):
        if points is None:
            self.points = self.default_points
        else:
            self.points = points

        self.facecolor = facecolor


    def apply_transformation(self, transform, in_place=False):
        new_points = transform.apply(self.points)
        if in_place:
            self.points = new_points
            return self
        else:
            return Glyph2D(new_points)

    def get_patch(self, facecolor=None, label=None):
        if facecolor is None:
            facecolor = self.facecolor

        return Polygon(self.points.T, closed=True, facecolor=facecolor, label=label)

    def bounds(self):
        min_vals = np.min(self.points, axis=1)
        max_vals = np.max(self.points, axis=1)
        x0 = min_vals[0]
        y0 = min_vals[1]
        x1 = max_vals[0]
        y1 = max_vals[1]

        return x0, y0, x1, y1


def get_glyph_bounds(glyphs):
    all_bounds = [list(g.bounds()) for g in glyphs]
    all_bounds = np.asarray(all_bounds)
    min_vals = np.min(all_bounds, axis=0)
    max_vals = np.max(all_bounds, axis=0)
    x0 = min_vals[0]
    y0 = min_vals[1]
    x1 = max_vals[2]
    y1 = max_vals[3]
    return x0, y0, x1, y1

class Line2D:
    parallel_tol_angle = 0.001

    def __init__(self, pt, direction):
        self.point = ensure_vec_2d(pt)
        self.direction = ensure_unit_vec_2d(direction)

        u, v = self.direction
        p0, p1 = self.point

        # ax + by = c
        self.a = float(v)
        self.b = -1.0 * float(u)
        self.c = v * float(p0) - u * float(p1)

        return

    def f_x(self, x):
        if np.abs(self.b) > 0:
            y = (self.c - self.a * x) / self.b
        else:
            raise Exception('Line is of form x = constant')
        return y

    def angle_to(self, other):

        u =  self.direction
        v = other.direction

        angle = np.arccos(
            np.abs(u.T @ v)
        )[0][0]

        return angle

    def parallel_to(self, other):

        return self.angle_to(other) < self.parallel_tol_angle

    def intersection(self, other):

        M = np.asarray([
            [self.a, self.b],
            [other.a, other.b]
        ])

        consts = ensure_vec_2d([self.c, other.c])

        det = M[0, 0] * M[1, 1] - M[0, 1] * M[1, 0]

        if np.abs(det) < 0.001:
            raise Exception('Lines are parallel or near to it.')


        Minv = np.array([
            [other.b, -1 * self.b],
            [-1 * other.a, self.a]
        ]) / det

        xy = Minv @ consts

        return xy


