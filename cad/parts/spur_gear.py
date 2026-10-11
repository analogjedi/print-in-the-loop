"""Unshifted involute spur profiles. Radial root transitions are not load-rated fillets.

The involute flank uses r=rb*sqrt(1+t²), inv(t)=t-atan(t). Tooth thickness at
the pitch circle is pi*m/2 minus an explicit trial thinning. No print compensation.
"""
from math import atan, cos, pi, radians, sin, sqrt


def polar(r, angle):
    return (r*cos(angle), r*sin(angle), 0.)


def tooth_sections(teeth, module, pressure_deg, thinning, samples=32):
    if type(teeth) is not int or teeth < 20 or not 0 < module or not 0 < pressure_deg < 35:
        raise ValueError("require >=20 teeth, positive module and 0<pressure<35 degrees")
    if not 0 <= thinning < pi*module/4:
        raise ValueError("invalid tooth thinning")
    if type(samples) is not int or samples < 4:
        raise ValueError("at least four flank samples required")
    rp = module*teeth/2
    rb, rf, ra = rp*cos(radians(pressure_deg)), rp-1.25*module, rp+module
    tp = sqrt((rp/rb)**2-1)
    half = pi/(2*teeth)-thinning/(2*rp)
    start = sqrt(max(0., (rf/rb)**2-1))
    end = sqrt((ra/rb)**2-1)
    result = []
    for i in range(teeth):
        center = 2*pi*i/teeth
        low, high = [], []
        for j in range(samples+1):
            t = start+(end-start)*j/samples
            radius = rb*sqrt(1+t*t)
            angle = half+(tp-atan(tp))-(t-atan(t))
            low.append(polar(radius, center-angle))
            high.append(polar(radius, center+angle))
        base_half = half+(tp-atan(tp))-(start-atan(start))
        result.append((polar(rf, center-base_half), low, list(reversed(high)),
                       polar(rf, center+base_half), center, base_half))
    return result, rf, ra


def profile_points(teeth, module=1., pressure_deg=20., thinning=0.12, samples=128):
    sections, rf, ra = tooth_sections(teeth, module, pressure_deg, thinning, samples)
    points = []
    for root_a, low, high, root_b, center, base_half in sections:
        from math import atan2
        tip_half = abs(atan2(low[-1][1], low[-1][0])-center)
        # Avoid angular wrapping: obtain tip half from radial involute directly.
        rp = module*teeth/2; rb = rp*cos(radians(pressure_deg))
        tp = sqrt((rp/rb)**2-1); ta = sqrt((ra/rb)**2-1)
        tip_half = pi/(2*teeth)-thinning/(2*rp)+tp-atan(tp)-ta+atan(ta)
        points.extend([root_a, *low])
        points.extend(polar(ra, center-tip_half+2*tip_half*j/16) for j in range(1,16))
        points.extend([*high, root_b])
        gap = 2*pi/teeth-2*base_half
        points.extend(polar(rf, center+base_half+gap*j/16) for j in range(1,16))
    return [(x,y) for x,y,_ in points]


def gear_face(teeth, module=1., pressure_deg=20., thinning=0.12):
    from build123d import Edge, Face, Wire
    sections, rf, ra = tooth_sections(teeth, module, pressure_deg, thinning)
    edges = []
    for i, (root_a, low, high, root_b, center, base_half) in enumerate(sections):
        if rf < module*teeth/2*cos(radians(pressure_deg))-1e-9:
            edges.append(Edge.make_line(root_a, low[0]))
        edges.append(Edge.make_spline(low))
        edges.append(Edge.make_three_point_arc(low[-1], polar(ra,center), high[0]))
        edges.append(Edge.make_spline(high))
        if rf < module*teeth/2*cos(radians(pressure_deg))-1e-9:
            edges.append(Edge.make_line(high[-1], root_b))
        edges.append(Edge.make_three_point_arc(root_b, polar(rf, center+pi/teeth), sections[(i+1)%teeth][0]))
    return Face(Wire(edges))
