import pybullet as p, pybullet_data, numpy as np, time
from consola import Console

con = Console("COM3")
p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.8)
p.loadURDF("plane.urdf")
bx = p.loadURDF("baxter/baxter.urdf", [0, 0, 0.9], useFixedBase=True)

names = {}
for j in range(p.getNumJoints(bx)):
    info = p.getJointInfo(bx, j)
    names[info[1].decode()] = j
    names[info[12].decode()] = j        # nombre de link (mismo indice)
movable = [j for j in range(p.getNumJoints(bx)) if p.getJointInfo(bx, j)[2] != p.JOINT_FIXED]

ARM = {s: [names[f"{s}_{n}"] for n in ("s0","s1","e0","e1","w0","w1","w2")]
       for s in ("left", "right")}
EE = {s: names.get(f"{s}_gripper", ARM[s][-1]) for s in ("left", "right")}

cube = p.createMultiBody(0.1,
    p.createCollisionShape(p.GEOM_BOX, halfExtents=[.03]*3),
    p.createVisualShape(p.GEOM_BOX, halfExtents=[.03]*3, rgbaColor=[0,1,0,1]),
    basePosition=[0.7, 0.3, 0.75])

side = "left"
target = {s: np.array(p.getLinkState(bx, EE[s])[0]) for s in ARM}
holding, cid = False, None

def ik_move(s):
    q = p.calculateInverseKinematics(bx, EE[s], target[s].tolist(),
                                     maxNumIterations=50)
    for j in ARM[s]:
        p.setJointMotorControl2(bx, j, p.POSITION_CONTROL,
                                q[movable.index(j)], force=200,
                                maxVelocity=1.0, positionGain=0.05)

while True:
    if con.pressed(0): side = "right" if side == "left" else "left"
    s = side
    target[s] += np.array([-con.ax[1], con.ax[0], -con.ax[3]]) * 0.004
    ik_move(s)
    if con.pressed(1):
        ee = np.array(p.getLinkState(bx, EE[s])[0])
        cp = np.array(p.getBasePositionAndOrientation(cube)[0])
        if not holding and np.linalg.norm(ee - cp) < 0.12:
            cid = p.createConstraint(bx, EE[s], cube, -1, p.JOINT_FIXED,
                                     [0,0,0], [0,0,0], [0,0,0.03])
            holding = True
        elif holding:
            p.removeConstraint(cid); holding = False
    p.stepSimulation()
    time.sleep(1/240)