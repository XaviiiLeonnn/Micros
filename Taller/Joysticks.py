import pybullet as p, pybullet_data, numpy as np, time
from consola import Console

con = Console("COM3")
p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.8)
p.loadURDF("plane.urdf")
at = p.loadURDF("atlas/atlas_v4_with_multisense.urdf", [0, 0, 1.0],
                useFixedBase=True)

J = {p.getJointInfo(at, i)[1].decode(): i for i in range(p.getNumJoints(at))}
GROUPS = [
  ("Brazos",  [["l_arm_shx", "l_arm_ely"], ["r_arm_shx", "r_arm_ely"]]),
  ("Muneca",  [["l_arm_uwy", "l_arm_mwx"], ["r_arm_uwy", "r_arm_mwx"]]),
  ("Torso",   [["back_bkz", "back_bky"],   ["back_bkx", "neck_ry"]]),
]
g = 0
q = {j: p.getJointState(at, j)[0] for j in J.values()}
vel = {j: 0.0 for j in J.values()}
KP, ACC, VMAX = 0.1, 0.1, 1.2

while True:
    if con.pressed(0): g = (g + 1) % len(GROUPS); print("Grupo:", GROUPS[g][0])
    pares = GROUPS[g][1]
    cmd = {}
    for k, par in enumerate(pares):
        ax, ay = con.ax[2*k], con.ax[2*k+1]
        for name, a in zip(par, (ax, ay)):
            if name in J: cmd[J[name]] = a * VMAX
    dt = 1/240
    for j in vel:
        v_des = cmd.get(j, 0.0)
        vel[j] += np.clip(v_des - vel[j], -ACC, ACC)   # rampa suave
        info = p.getJointInfo(at, j)
        lo, hi = info[8], info[9]
        q[j] = np.clip(q[j] + vel[j]*dt, lo, hi) if lo < hi else q[j] + vel[j]*dt
        if info[2] != p.JOINT_FIXED:
            p.setJointMotorControl2(at, j, p.POSITION_CONTROL, q[j],
                                    force=300, positionGain=KP)
    p.stepSimulation()
    time.sleep(dt)