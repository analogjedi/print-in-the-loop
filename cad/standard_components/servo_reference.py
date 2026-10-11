"""Dimensioned purchased-servo keep-out; the supplier STEP is preserved separately."""
from build123d import Align, Box, Compound, Cylinder, Pos, Rot, import_step


def load_servo_reference(path, report):
    source=import_step(path); original=list(source.solids())
    if len(original)!=8:
        raise ValueError('unexpected pinned vendor reference topology')
    # Case envelope is the union of the three housing bounds, excluding internals.
    boxes=[s.bounding_box() for s in original[:3]]
    low=[min(list(b.min)[i] for b in boxes) for i in range(3)]
    high=[max(list(b.max)[i] for b in boxes) for i in range(3)]
    case=(Pos(*low)*Box(*(b-a for a,b in zip(low,high)),align=(Align.MIN,)*3)).solids()[0]
    def axial_cylinder(radius,y,length,x=-25.5,z=0.):
        return Pos(x,y,z)*Rot(-90,0,0)*Cylinder(radius,length,align=(Align.CENTER,Align.CENTER,Align.MIN))
    horn=axial_cylinder(9.6,5.1,4.5)-axial_cylinder(3.1,5.1,4.5)
    for dx,dz in ((7,0),(0,7),(-7,0),(0,-7)):
        horn-=axial_cylinder(1.25,5.1,4.5,-25.5+dx,dz)
    rear=axial_cylinder(9.6,-27.65,3.35).solids()[0]
    horn=horn.solids()[0]
    case.label='ST3215_case_keepout'; horn.label='ST3215_supplied_horn_mounting_reference'; rear.label='ST3215_rear_wheel_keepout'
    report.update({'status':'PASS','scope':'dimensioned purchased-servo keepout preparation',
                   'raw_source_geometry_status':'FAIL' if not source.is_valid else 'PASS',
                   'front_horn_solid_index':1,'reference_solid_count':3,
                   'case_minimum_source_mm':low,'case_maximum_source_mm':high,
                   'horn_reference':{'outer_diameter_mm':19.2,'opposite_hole_spacing_mm':14.,'pilot_hole_diameter_mm':2.5,
                                     'source_axis_x_mm':-25.5,'source_axis_z_mm':0.,'source_front_face_y_mm':9.6},
                   'limitations':['Purchased reference envelopes, not a detailed repaired supplier model or printable servo parts.',
                     'Horn mounting dimensions come from supplier drawing/STEP. Spline profile and threads are omitted.',
                     'Physical connection uses the existing supplied metal horn.',
                     'Original STEP and unsuccessful repair/roundtrip diagnostics remain unchanged.',
                     'Reference bodies overlap internally; aggregate volume is not physical servo volume or a mass estimate.']})
    return Compound(label='ST3215_keepout_and_horn_mounting_reference',children=[case,horn,rear])
