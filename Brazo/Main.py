import pybullet as p
import pybullet_data
import numpy as np
import time

# Configuración inicial
p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.loadURDF("plane.urdf")
robot = p.loadURDF("kuka_iiwa/model.urdf", [0, 0, 0], useFixedBase=True)

# Objetivo aleatorio
target_pos = np.random.uniform([-0.5, -0.5, 0.2], [0.5, 0.5, 0.5])

# Cinemática inversa
joint_indices = range(p.getNumJoints(robot))[1:7]  # 6 DOF
ik_solution = p.calculateInverseKinematics(
    robot,
    endEffectorLinkIndex=6,
    targetPosition=target_pos,
    maxNumIterations=100
)

# Aplicar ángulos a las articulaciones
for i, angle in zip(joint_indices, ik_solution):
    p.resetJointState(robot, i, angle)

# Simulación
for _ in range(300):
    p.stepSimulation()
    time.sleep(5/240)