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

### Packages ROS2 complémentaires pour le lidar

Pour avoir toutes les fonctionnalités du dépôt, et en particulier utiliser le **lidar** et l’odométrie laser, il faut aussi cloner les packages suivants dans le workspace ROS2 :

- `rplidar_ros` : driver du lidar, publie `/scan`
- `rf2o_laser_odometry` : calcule `/odom` à partir du lidar

Exemple :

```bash
cd ~/ros2_ws/src
git clone https://github.com/Slamtec/rplidar_ros.git
git clone https://github.com/MAPIRlab/rf2o_laser_odometry.git
```

Ensuite, reconstruire le workspace :

```bash
cd ~/ros2_ws
colcon build
source install/setup.bash
```

Sans ces deux packages, le répertoire ne fournit pas toutes les fonctions liées au lidar, et le launch `robot.launch.py` ne pourra pas démarrer la partie RF2O.

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


## Lidar 2D (RPLidar) et odométrie

Le robot peut être équipé d’un **lidar 2D RPLidar** pour permettre :

* la perception de l’environnement (`/scan`)
* l’estimation du mouvement (odométrie lidar via RF2O)
* la cartographie (SLAM)

### Lancer le driver RPLidar

```bash
ros2 launch rplidar_ros view_rplidar_a1_launch.py
```

Ce nœud publie le topic :

| Topic   | Type                    | Description   |
| ------- | ----------------------- | ------------- |
| `/scan` | `sensor_msgs/LaserScan` | Données lidar |


### Odométrie lidar (RF2O)

Le launch principal `robot.launch.py` inclut **RF2O** qui permet d’estimer le mouvement du robot à partir du lidar.

Il publie :

* `/odom`
* la transform TF : `odom -> base_link`


### Cartographie (SLAM)

Pour générer une carte de l’environnement :

```bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=/home/user/your_dir/slam_params.yaml \
  use_sim_time:=false
```

⚠️ Remplacer le chemin par celui de votre fichier `slam_params.yaml`.


### Pipeline global

```text
/scan → RF2O → odom → slam_toolbox → map
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
