import pybullet as p, pybullet_data, serial, time, math, os

PORT = "COM3"   # en Wokwi: "rfc2217://localhost:4000"
L1, L2 = 0.30, 0.30
Z_UP, Z_DOWN = 0.12, 0.0

urdf = f"""<?xml version="1.0"?>
<robot name="arm">
 <link name="base"><visual><geometry><cylinder length="0.05" radius="0.12"/></geometry>
  <material name="g"><color rgba="0.5 0.5 0.5 1"/></material></visual>
  <collision><geometry><cylinder length="0.05" radius="0.12"/></geometry></collision>
  <inertial><mass value="0"/><inertia ixx="1" iyy="1" izz="1" ixy="0" ixz="0" iyz="0"/></inertial></link>
 <link name="l1"><visual><origin xyz="{L1/2} 0 0"/><geometry><box size="{L1} 0.03 0.03"/></geometry>
  <material name="b"><color rgba="0.3 0.7 0.9 1"/></material></visual>
  <inertial><mass value="0.1"/><inertia ixx="0.01" iyy="0.01" izz="0.01" ixy="0" ixz="0" iyz="0"/></inertial></link>
 <link name="l2"><visual><origin xyz="{L2/2} 0 0"/><geometry><box size="{L2} 0.03 0.03"/></geometry>
  <material name="o"><color rgba="0.95 0.7 0.2 1"/></material></visual>
  <inertial><mass value="0.1"/><inertia ixx="0.01" iyy="0.01" izz="0.01" ixy="0" ixz="0" iyz="0"/></inertial></link>
 <link name="pen"><visual><origin xyz="0 0 -0.05"/><geometry><cylinder length="0.1" radius="0.01"/></geometry>
  <material name="r"><color rgba="1 0 0 1"/></material></visual>
  <inertial><mass value="0.05"/><inertia ixx="0.001" iyy="0.001" izz="0.001" ixy="0" ixz="0" iyz="0"/></inertial></link>
 <link name="tip"><inertial><mass value="0.001"/><inertia ixx="1e-6" iyy="1e-6" izz="1e-6" ixy="0" ixz="0" iyz="0"/></inertial></link>
 <joint name="j1" type="revolute"><parent link="base"/><child link="l1"/>
  <origin xyz="0 0 0.05"/><axis xyz="0 0 1"/><limit lower="-3.14" upper="3.14" effort="50" velocity="3"/></joint>
 <joint name="j2" type="revolute"><parent link="l1"/><child link="l2"/>
  <origin xyz="{L1} 0 0.03"/><axis xyz="0 0 1"/><limit lower="-3.0" upper="3.0" effort="50" velocity="3"/></joint>
 <joint name="j3" type="prismatic"><parent link="l2"/><child link="pen"/>
  <origin xyz="{L2} 0 0.03"/><axis xyz="0 0 1"/><limit lower="0" upper="0.15" effort="50" velocity="1"/></joint>
 <joint name="jt" type="fixed"><parent link="pen"/><child link="tip"/><origin xyz="0 0 -0.1"/></joint>
</robot>"""
open("arm.urdf", "w").write(urdf)

# Digitos como polilineas (x,y) en [0,1]x[0,1]; None = levantar lapiz
DIG = {
 '0': [[(.2,0),(.8,0),(.8,1),(.2,1),(.2,0)]],
 '1': [[(.3,.8),(.5,1),(.5,0)],[(.3,0),(.7,0)]],
 '2': [[(.2,1),(.8,1),(.8,.5),(.2,.5),(.2,0),(.8,0)]],
 '3': [[(.2,1),(.8,1),(.8,0),(.2,0)],[(.3,.5),(.8,.5)]],
 '4': [[(.2,1),(.2,.5),(.8,.5)],[(.7,1),(.7,0)]],
 '5': [[(.8,1),(.2,1),(.2,.5),(.8,.5),(.8,0),(.2,0)]],
 '6': [[(.8,1),(.2,1),(.2,0),(.8,0),(.8,.5),(.2,.5)]],
 '7': [[(.2,1),(.8,1),(.4,0)]],
 '8': [[(.2,0),(.8,0),(.8,1),(.2,1),(.2,0)],[(.2,.5),(.8,.5)]],
 '9': [[(.8,.5),(.2,.5),(.2,1),(.8,1),(.8,0),(.2,0)]],
 'A': [[(.2,0),(.5,1),(.8,0)],[(.3,.4),(.7,.4)]],
 'B': [[(.2,0),(.2,1),(.7,1),(.7,.5),(.2,.5)],[(.7,.5),(.8,.5),(.8,0),(.2,0)]],
 'C': [[(.8,1),(.2,1),(.2,0),(.8,0)]],
 'D': [[(.2,0),(.2,1),(.7,1),(.8,.8),(.8,.2),(.7,0),(.2,0)]],
 '*': [[(.5,.2),(.5,.8)],[(.25,.35),(.75,.65)],[(.25,.65),(.75,.35)]],
 '#': [[(.35,.1),(.35,.9)],[(.65,.1),(.65,.9)],[(.1,.35),(.9,.35)],[(.1,.65),(.9,.65)]],
}

p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0,0,-9.8)
p.loadURDF("plane.urdf")
arm = p.loadURDF("arm.urdf", useFixedBase=True)
TIP = 4  # link "tip"
# hoja
p.addUserDebugLine([0.15,-0.2,0.001],[0.15,-0.2,0.001],[1,1,1])

X0, Y0, W, H = 0.30, -0.10, 0.20, 0.25   # zona de dibujo

def ik(x, y, z):
    q = p.calculateInverseKinematics(arm, TIP, [x,y,z+0.0],
                                     maxNumIterations=100, residualThreshold=1e-5)
    return q

def move(x, y, z, steps=40):
    q = ik(x, y, 0.08 + z)   # base en z=0.05+0.03+0.03 aprox; z relativo
    for j in range(3):
        p.setJointMotorControl2(arm, j, p.POSITION_CONTROL, q[j], force=50)
    for _ in range(steps):
        p.stepSimulation(); time.sleep(1/240)

def tip_pos():
    return p.getLinkState(arm, TIP)[0]

def draw(ch):
    for stroke in DIG.get(ch, []):
        pts = [(X0 + u*W*0.0 + (1-v)*0 + 0, 0) for u,v in []]
        pts = [(X0 + v*H, Y0 + u*W) for (u,v) in stroke]
        move(*pts[0], Z_UP)
        move(*pts[0], Z_DOWN)
        prev = tip_pos()
        for (x,y) in pts[1:]:
            for t in range(1,11):
                a = pts[pts.index((x,y))-1]
                xi = a[0] + (x-a[0])*t/10; yi = a[1] + (y-a[1])*t/10
                move(xi, yi, Z_DOWN, steps=6)
                cur = tip_pos()
                p.addUserDebugLine(prev, cur, [0,0,0], 3, 0)
                prev = cur
        move(*pts[-1], Z_UP)
    move(0.35, 0, Z_UP)

ser = serial.serial_for_url(PORT, 115200, timeout=0.1)
print("Esperando teclas...")
while p.isConnected():
    line = ser.readline().decode(errors="ignore").strip()
    if line:
        print("Tecla:", line[0]); draw(line[0])
    p.stepSimulation()