#!/usr/bin/python3

import rospy
import std_msgs
import geometry_msgs
from geometry_msgs.msg import PoseStamped, PoseArray
from visualization_msgs.msg import Marker
from grasplan.grasp_planner.handcoded_grasp_planner import HandcodedGraspPlanner

'''
Load grasp configurations from yaml file and display them on rviz.
'''

class GraspVisualiser:
    def __init__(self):
        # parameters
        self.object_name = rospy.get_param('object_name', 'multimeter')
        self.global_reference_frame = 'map'
        # Publishers
        self.marker_pub = rospy.Publisher('object_mesh', Marker, queue_size=1, latch=True)
        self.pose_array_pub = rospy.Publisher('~grasp_poses', PoseArray, queue_size=50, latch=True)
        # use helper function to convert gripper poses to pose array
        self.handcoded_grasp_planner_obj = HandcodedGraspPlanner(call_parent_constructor=False)
        # load gripper grasps
        self.grasp_poses = rospy.get_param('~handcoded_grasp_planner_transforms')
        rospy.sleep(0.5)
        rospy.loginfo('grasp visualiser node started')

    def make_mesh_marker_msg(self, mesh_path, position=[0,0,0], orientation=[0,0,0,1], mesh_scale=[1,1,1]):
        mesh_marker_msg = Marker()
        # mesh_marker_msg.lifetime = rospy.Duration(3.0)
        mesh_marker_msg.ns = 'object'
        mesh_marker_msg.header.frame_id = self.global_reference_frame
        mesh_marker_msg.type = Marker.MESH_RESOURCE
        mesh_marker_msg.pose.position.x = position[0]
        mesh_marker_msg.pose.position.y = position[1]
        mesh_marker_msg.pose.position.z = position[2]
        mesh_marker_msg.pose.orientation.x = orientation[0]
        mesh_marker_msg.pose.orientation.y = orientation[1]
        mesh_marker_msg.pose.orientation.z = orientation[2]
        mesh_marker_msg.pose.orientation.w = orientation[3]
        mesh_marker_msg.mesh_use_embedded_materials = True
        mesh_marker_msg.scale = geometry_msgs.msg.Vector3(mesh_scale[0], mesh_scale[1], mesh_scale[2])
        # set rgba to 0 to allow mesh_use_embedded_materials to work
        mesh_marker_msg.color = std_msgs.msg.ColorRGBA(0,0,0,0)
        mesh_marker_msg.mesh_resource = mesh_path
        return mesh_marker_msg

    def publish_grasps_as_pose_array(self):
        object_name = self.object_name
        object_pose = PoseStamped()
        object_pose.header.frame_id = 'map'
        object_pose.pose.position.x = 0.0
        object_pose.pose.position.y = 0.0
        object_pose.pose.position.z = 0.0
        object_pose.pose.orientation.x = 0.0
        object_pose.pose.orientation.y = 0.0
        object_pose.pose.orientation.z = 0.0
        object_pose.pose.orientation.w = 1.0
        grasp_type = '' # not implemented yet, so it can be any value
        pose_array_msg = self.handcoded_grasp_planner_obj.gen_end_effector_grasp_poses(object_name, object_pose, grasp_type)
        self.pose_array_pub.publish(pose_array_msg)

    def start_grasp_visualiser(self):
        mesh_path = 'package://mobipick_gazebo/meshes/multimeter.dae'
        marker_msg = self.make_mesh_marker_msg(mesh_path)
        rospy.loginfo(f'publishing mesh:{mesh_path}')
        self.marker_pub.publish(marker_msg)
        # visualise grasps
        self.publish_grasps_as_pose_array()
        rospy.spin()

if __name__ == '__main__':
    rospy.init_node('grasp_visualiser', anonymous=False)
    grasp_visualiser = GraspVisualiser()
    grasp_visualiser.start_grasp_visualiser()
