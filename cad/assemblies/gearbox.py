"""Four compound gears on integral plastic shafts, horn adapter, removable servo cradle."""
from math import atan2, degrees, sqrt
from build123d import Align, Axis, Box, Color, Compound, Cone, Cylinder, Pos, Rot, extrude, import_step
from cad.parts.spur_gear import gear_face

MINZ = (Align.CENTER, Align.CENTER, Align.MIN)
COLORS = ["#2879ae", "#ce8b31", "#409479", "#9369ba"]
POSTS = [(5.,5.), (91.,5.), (5.,104.), (83.,104.)]


def layout():
    return [(37.,37.), (77.,37.), (97.,37.+20*sqrt(3)), (137.,37.+20*sqrt(3))]


def phases():
    points=layout(); angles=[0.]
    for i in range(3):
        a=degrees(atan2(points[i+1][1]-points[i][1],points[i+1][0]-points[i][0]))
        angles.append(a+180-180/60-(angles[-1]-a)/3)
    return angles


def cyl(radius, height, x=0., y=0., z=0.):
    return Pos(x,y,z)*Cylinder(radius,height,align=MINZ)


def box(x,y,z,dx,dy,dz):
    return Pos(x,y,z)*Box(dx,dy,dz,align=(Align.MIN,)*3)


def cs_hole(x,y,z,height,diameter):
    # 90-degree trial M3 flat-head seat at the underside; recess is within part.
    return cyl(diameter/2,height,x,y,z)+Pos(x,y,z)*Cone(3.,diameter/2,3.-diameter/2,align=MINZ)


def build_parts(spec, reference_report=None):
    parts={}
    def add(name,part,color):
        part.label=name; part.color=Color(color); parts[name]=part
    centers=layout(); initial=phases()
    base=box(0,0,0,174,109,5)
    for i,(x,y) in enumerate(centers):
        low=22-5*i; high=31-5*i
        top=high+spec.retainer_axial_clearance_mm if i else 30.8
        base += cyl(4.5,low-5,x,y,5)+cyl(spec.shaft_diameter_mm/2,top-5,x,y,5)
        if i:
            base -= cyl(spec.m3_tap_pilot_mm/2,8.,x,y,top-8.)
    for x,y in POSTS:
        base -= cyl(spec.m3_clearance_mm/2,5,x,y)
    for x,y in ((168,6),(168,103)):
        base -= cyl(2.2,5,x,y)
    add("backplate_with_plastic_shafts",base,"#acb7bf")
    large=extrude(gear_face(60,thinning=spec.tooth_thinning_mm),amount=4.)
    small=extrude(gear_face(20,thinning=spec.tooth_thinning_mm),amount=4.)
    for i,(x,y) in enumerate(centers):
        low=22-5*i; high=27-5*i
        g=Pos(0,0,high)*large+Pos(0,0,low)*small+cyl(5.,5.,z=low)
        g-=cyl((spec.shaft_diameter_mm+spec.shaft_diametral_clearance_mm)/2,9,z=low)
        if i==0:
            for hx,hy in ((20,0),(0,20),(-20,0),(0,-20)):
                g-=cs_hole(hx,hy,high,4,spec.m3_clearance_mm)
        add(f"compound_gear_{i+1}",Pos(x,y,0)*Rot(0,0,initial[i])*g,COLORS[i])
        if i:
            z=high+4+spec.retainer_axial_clearance_mm
            cap=cyl(5.,2,x,y,z)-cyl(spec.m3_clearance_mm/2,2,x,y,z)
            add(f"shaft_retainer_{i+1}",cap,"#e0c56d")
    # Adapter transfers torque through the supplied metal horn. No invented spline.
    adapter=cyl(25,4,37,37,31)-cyl(3.3,4,37,37,31)
    for dx,dy in ((7,0),(0,7),(-7,0),(0,-7)):
        adapter-=cs_hole(37+dx,37+dy,31,4,spec.m3_clearance_mm)
    from build123d import RegularPolygon
    for dx,dy in ((20,0),(0,20),(-20,0),(0,-20)):
        x,y=37+dx,37+dy
        adapter-=cyl(spec.m3_clearance_mm/2,4,x,y,31)
        # Captive M3 nut pockets: 5.8 mm across flats, 2.5 deep (trial fit).
        adapter-=Pos(x,y,32.5)*extrude(RegularPolygon(5.8/sqrt(3),6),amount=2.5)
    add("servo_horn_adapter",adapter,"#dfac49")
    for i,(x,y) in enumerate(POSTS):
        post=cyl(3.5,67.9,x,y,5)+cyl(5,3,x,y,32.2)
        post-=cyl(spec.m3_clearance_mm/2,67.9,x,y,5)
        add(f"cradle_post_{i+1}",post,"#667b8e")
    def platform(z,height):
        p=box(0,0,z,95,109,height)-box(10,10,z,75,89,height)
        p+=box(4,21,z,87,6,height)+box(4,47,z,87,6,height)+box(20,21,z,71,32,height)
        return p
    tray=platform(35.2,1.8)-cyl(11,1.8,37,37,35.2)
    lid=platform(72.9,3)-box(47,31,72.9,20,12,3)
    for x,y in POSTS:
        tray-=cyl(3.7,1.8,x,y,35.2)
        lid-=cyl(spec.m3_clearance_mm/2,3,x,y,72.9)
    # Side/end locating rails, with nominal clearance to the source servo case.
    tray+=box(24.5,21,37,51,3,35.9)+box(24.5,50,37,51,3,35.9)
    tray+=box(24.5,24,37,2,26,35.9)+box(72.5,24,37,3,26,35.9)
    add("servo_cradle_tray",tray,"#708c9f")
    add("servo_cradle_lid",lid,"#7e96a7")
    from cad.standard_components.servo_reference import load_servo_reference
    servo=load_servo_reference(spec.servo_step,reference_report if reference_report is not None else {})
    # Source output axis is (-25.5, y, 0); outer horn face y=9.6 -> world Z=35.
    servo=Pos(62.5,37,44.6)*Rot(-90,0,0)*servo
    servo.label="purchased_ST3215_reference"; servo.color=Color("#3c4147")
    return parts,servo
