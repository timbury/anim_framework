#+
# Framework for generating animations of trochoid patterns.
# For background on the maths, see <https://en.wikipedia.org/wiki/Spirograph>,
# <https://en.wikipedia.org/wiki/Epitrochoid> and <https://en.wikipedia.org/wiki/Hypotrochoid>.
#
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

from fractions import \
    Fraction
from turtle import \
    Vec2D
# import cairo

def constant_interpolator(y) :
    "returns a function of x that always returns the same constant value y."
    return \
        lambda x : y
#end constant_interpolator

def linear_interpolator(from_x, to_x, from_y, to_y) :
    "returns a function of x in the range [from_x .. to_x] which returns" \
    " the corresponding linearly-interpolated value in the range [from_y .. to_y]."
    return \
        lambda x : (x - from_x) / (to_x - from_x) * (to_y - from_y) + from_y
#end linear_interpolator

def piecewise_linear_interpolator(x_vals, y_vals) :
    "x_vals must be a monotonically-increasing sequence of x-values, defining" \
    " domain segments, and y_vals must be a monotically-increasing sequence of" \
    " the same length of corresponding y-values defining piecewise-linear" \
    " range segments. returns a function that will map an input x value to" \
    " the corresponding y value linearly-interpolated over the appropriate segment."

    def interpolate(x) :
        i = len(x_vals)
        while True :
            i -= 1
            if x_vals[i] <= x :
                break
        #end while
        return \
            (
                lambda : x_vals[i],
                lambda :
                            (x - x_vals[i])
                        /
                            (x_vals[i + 1] - x_vals[i])
                        *
                            (y_vals[i + 1] - y_vals[i])
                    +
                        y_vals[i],
            )[x > x_vals[i]]()
    #end interpolate

#begin piecewise_linear_interpolator
    assert len(x_vals) >= 2 and len(x_vals) == len(y_vals)
    return \
        interpolate
#end piecewise_linear_interpolator

def tuple_interpolator(interps) :
    "given a tuple of interpolators, returns a function of x which will yield the" \
    " corresponding tuple of interpolated y-values for a given x."
    function = type(lambda x : x)
    interps = tuple \
      (
        interp if type(interp) == function else constant_interpolator(interp)
        for interp in interps
      )
    return \
        lambda x : tuple(interp(x) for interp in interps)
#end tuple_interpolator

def draw(g, ring_radius, wheel_radius, wheel_frac, phase, nr_steps) :
    "draws a trochoid curve into the Cairo context g. ring_radius is the radius of the" \
    " stationary ring, while wheel_radius is the radius of the moving wheel; both must" \
    " be integers. frac is the fraction of the wheel radius that the actual" \
    " point on the curve is located from the centre of the wheel. nr_steps is the" \
    " number of straight-line segments to use to approximate the curve." \
    " Setting up pen size, draw pattern etc is left up to caller."
    ratio = Fraction(ring_radius, wheel_radius)
    nr_cycles = ratio.denominator # to produce one complete traversal of curve
    g.new_path()
    setpos = g.move_to # for first point
    for i in range(0, nr_steps + 1) :
        theta_ring = 360 * nr_cycles * i / nr_steps
        theta_wheel = theta_ring * (ring_radius / wheel_radius + 1)
        wheel_pos = Vec2D(ring_radius, 0).rotate(theta_ring + phase)
        curve_pos = wheel_pos + Vec2D(wheel_radius * wheel_frac, 0).rotate(theta_wheel)
        setpos(curve_pos[0], curve_pos[1])
        setpos = g.line_to # for subsequent points
    #end for
    g.stroke()
#end draw

def make_cairo_settings(anim_settings) :
    "anim_settings must be a tuple of 2-tuples; in each 2-tuple, the first element is" \
    " a Cairo context method name, and the second element is an interpolator function." \
    " returns a procedure of 2 arguments, a Cairo context g and the current time x," \
    " which will call each Cairo method on g with an argument list equal to the result" \
    " of the corresponding interpolator applied to that value of x."

    def apply_settings(g, x) :
        for method, interp in anim_settings :
            getattr(g, method)(*interp(x))
        #end for
    #end apply_settings

#begin make_cairo_settings
    function = type(lambda x : x)
    anim_settings = tuple \
      (
        (method, interp if type(interp) == function else constant_interpolator(interp))
        for method, interp in anim_settings
      )
    return \
        apply_settings
#end make_cairo_settings

class AnimCurve :
    "represents an animating trochoid curve. Pass interpolator functions to the constructor" \
    " which will evaluate to appropriate values for the curve parameters for given x." \
    " Then call the draw method, passing it a Cairo context and a value for x, and a curve" \
    " will be drawn into that context with the corresponding parameters."

    def __init__ \
      (
        self,
        ring_radius,
        wheel_radius,
        wheel_frac,
        phase,
        nr_steps,
        do_settings = None
      ) :
        function = type(lambda x : x)
        self.ring_radius_interp = ring_radius if type(ring_radius) == function else constant_interpolator(ring_radius)
        self.wheel_radius_interp = wheel_radius if type(wheel_radius) == function else constant_interpolator(wheel_radius)
        self.wheel_frac_interp = wheel_frac if type(wheel_frac) == function else constant_interpolator(wheel_frac)
        self.phase_interp = phase if type(phase) == function else constant_interpolator(phase)
        self.nr_steps_interp = nr_steps if type(nr_steps) == function else constant_interpolator(nr_steps)
        self.do_settings = do_settings
    #end __init__

    def draw(self, g, x) :
        "draws a trochoid into the Cairo context g with the animated settings" \
        " appropriate to time x."
        if self.do_settings != None :
            self.do_settings(g, x)
        #end if
        # note ring_radius, wheel_radius and nr_steps must be integers
        draw \
          (
            g = g,
            ring_radius = round(self.ring_radius_interp(x)),
            wheel_radius = round(self.wheel_radius_interp(x)),
            wheel_frac = self.wheel_frac_interp(x),
            phase = self.phase_interp(x),
            nr_steps = round(self.nr_steps_interp(x))
          )
    #end draw

#end AnimCurve
