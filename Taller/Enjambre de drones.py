import numpy as np, time
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
from gym_pybullet_drones.utils.enums import DroneModel, Physics
from consola import Console

N = 6
OFF = np.array([[(i % 3)*0.5, (i // 3)*0.5, 0] for i in range(N)])
PTS = {0: np.array([0, 0, 1.0]),    # A
       1: np.array([2, 0, 1.2]),    # B
       2: np.array([2, 2, 1.0])}    # C

con = Console("COM3")
init = OFF + np.array([0, 0, 0.1])
env = CtrlAviary(drone_model=DroneModel.CF2X, num_drones=N,
                 initial_xyzs=init, initial_rpys=np.zeros((N, 3)),
                 physics=Physics.PYB, pyb_freq=240, ctrl_freq=48, gui=True)
ctrl = [DSLPIDControl(drone_model=DroneModel.CF2X) for _ in range(N)]

goal = PTS[0].copy()
sp = goal.copy()
action = np.zeros((N, 4))
obs, *_ = env.step(action)
VMAX = 0.02                          # m por paso (~1 m/s)

while True:
    for i in range(3):
        if con.pressed(i): goal = PTS[i].copy()
    goal += np.array([con.ax[2], -con.ax[3], 0]) * 0.01
    d = goal - sp
    n = np.linalg.norm(d)
    if n > 1e-6: sp += d / n * min(VMAX, n)
    for j in range(N):
        action[j], _, _ = ctrl[j].computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP, state=obs[j],
            target_pos=sp + OFF[j], target_rpy=np.zeros(3))
    obs, *_ = env.step(action)
    time.sleep(env.CTRL_TIMESTEP)