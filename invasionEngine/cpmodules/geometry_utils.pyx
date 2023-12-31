# geometry_utils.pyx
cimport cython

from libc.math cimport sqrt, pow
from libcpp.vector cimport vector
from libcpp cimport bool

# 类型定义，提高性能
ctypedef double DTYPE_t
ctypedef vector[DTYPE_t] Point2D
ctypedef vector[Point2D] Point2DVector

@cython.boundscheck(False) # 禁用边界检查以提高性能
@cython.wraparound(False)  # 禁用负索引
cdef class GeometryUtils:

    @staticmethod
    cdef double distance_point_to_line(Point2D point, Point2D line_start, Point2D line_end) nogil:
        cdef:
            DTYPE_t x = point[0]
            DTYPE_t y = point[1]
            DTYPE_t x1 = line_start[0]
            DTYPE_t y1 = line_start[1]
            DTYPE_t x2 = line_end[0]
            DTYPE_t y2 = line_end[1]
            DTYPE_t denominator = pow(y2 - y1, 2) + pow(x2 - x1, 2)

        if denominator == 0:
            return 0.0
        return abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / sqrt(denominator)

    @staticmethod
    cpdef Point2DVector douglas_peucker(Point2DVector points, DTYPE_t epsilon):
        cdef:
            size_t len_points = points.size()
            DTYPE_t d_max = 0
            size_t index = 0
            size_t i
            DTYPE_t d

        if len_points <= 2:
            return points

        for i in range(1, len_points - 1):
            d = GeometryUtils.distance_point_to_line(points[i], points[0], points[len_points - 1])
            if d > d_max:
                index = i
                d_max = d

        if d_max > epsilon:
            left_simplified = GeometryUtils.douglas_peucker(points[:index + 1], epsilon)
            right_simplified = GeometryUtils.douglas_peucker(points[index:], epsilon)
            left_simplified.pop()
            left_simplified.extend(right_simplified)
            return left_simplified
        else:
            return Point2DVector([points[0], points[len_points - 1]])
