# real_robot
Implementation on the real robot

# rpi_pkg - ROS2 Robot Bridge Package

Package ROS2 pour piloter un robot réel à base de **Raspberry Pi**, **Arduino** et **caméra USB**.  
Il fournit deux nœuds principaux : un pont série vers l'Arduino et un flux vidéo depuis la caméra.


## Matériel requis

| Composant | Rôle |
|-----------|------|
| Raspberry Pi | Ordinateur embarqué, fait tourner ROS2 |
| Arduino | Contrôleur moteur, reçoit les commandes via USB série |
| Caméra USB / Pi Cam | Capture vidéo, publie les images sur ROS2 |


## Nœuds

### `serial_node` - Pont série Arduino

Souscrit au topic `/cmd_vel` (messages `Twist`) et convertit les vitesses linéaire/angulaire en commandes moteur envoyées à l'Arduino via port série.

**Protocole envoyé à l'Arduino :**
```
L:<vitesse_gauche>,R:<vitesse_droite>\n
```
Les valeurs sont comprises entre **-255** et **255**.

**Paramètres ROS2 :**

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `serial_port` | `/dev/ttyACM0` | Port série USB de l'Arduino |
| `baud_rate` | `115200` | Vitesse de communication série |

**Topics :**

| Topic | Type | Direction |
|-------|------|-----------|
| `/cmd_vel` | `geometry_msgs/Twist` | Souscription |


### `camera_pi_node` — Nœud caméra

Capture les images depuis une caméra USB (via V4L2/OpenCV) et les publie sur `/image_raw`.

**Paramètres ROS2 :**

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `camera_device` | `/dev/video0` | Périphérique caméra |
| `frame_width` | `640` | Largeur de l'image en pixels |
| `frame_height` | `480` | Hauteur de l'image en pixels |

**Topics :**

| Topic | Type | Direction |
|-------|------|-----------|
| `/image_raw` | `sensor_msgs/Image` | Publication |


## Installation

### Prérequis

- ROS2 (Humble ou supérieur)
- Python 3
- Bibliothèques Python :

```bash
pip install pyserial opencv-python
sudo apt install ros-$ROS_DISTRO-cv-bridge
```

### Build du package

```bash
cd ~/ros2_ws
colcon build --packages-select rpi_pkg
source install/setup.bash
```


## Utilisation

### Lancer les deux nœuds via le launch file

```bash
# Les deux nœuds (comportement par défaut)
ros2 launch rpi_pkg robot.launch.py

# Sans caméra
ros2 launch rpi_pkg robot.launch.py enable_camera:=false

# Port série personnalisé
ros2 launch rpi_pkg robot.launch.py serial_port:=/dev/ttyUSB0

# Tous les arguments combinés
ros2 launch rpi_pkg robot.launch.py serial_port:=/dev/ttyUSB0 baud_rate:=9600 enable_camera:=false
```

### Lancer les nœuds séparément

```bash
# Nœud série
ros2 run rpi_pkg serial_node

# Nœud caméra
ros2 run rpi_pkg camera_node
```

### Arguments du launch file

| Argument | Défaut | Description |
|----------|--------|-------------|
| `enable_camera` | `true` | Active/désactive le nœud caméra |
| `serial_port` | `/dev/ttyACM0` | Port série de l'Arduino |
| `baud_rate` | `115200` | Baud rate de la liaison série |


## Tester le robot

Envoyer une commande de vitesse manuellement :

```bash
# Avancer
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5}, angular: {z: 0.0}}" --once

# Tourner à gauche
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.5}}" --once

# Visualiser le flux caméra
ros2 run rqt_image_view rqt_image_view /image_raw
```


## Dépannage

**Port série non trouvé**
```bash
ls /dev/ttyACM* /dev/ttyUSB*
# Ajouter l'utilisateur au groupe dialout si besoin
sudo usermod -aG dialout $USER
```

**Caméra non détectée**
```bash
ls /dev/video*
v4l2-ctl --list-devices
```

**Permission refusée sur le port série**
```bash
sudo chmod 666 /dev/ttyACM0
```
 
Licence : Apache-2.0