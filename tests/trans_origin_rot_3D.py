import numpy as np
from twor.utils.general import random_rotation_3D, ensure_vec
from twor.geom.transform_3d import Rotation3D, TransOriginRotation3D

ax, theta = random_rotation_3D()

P = np.random.rand(3) * 10
P = ensure_vec(P)

rot_A = Rotation3D(P, ax, theta)

M_A = rot_A.get_matrix()

transf_B = rot_A.to_trans_origin_rot()

assert isinstance(transf_B, TransOriginRotation3D)

M_B = transf_B.get_matrix()

assert np.allclose(M_A, M_B)

print(rot_A)


print(transf_B)