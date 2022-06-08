#!/usr/bin/env python3

PKG = 'test_roslaunch'

import math
import copy
import unittest
import numpy as np

from grasplan.rqt_grasplan.grasps import Grasps
from geometry_msgs.msg import Pose

class TestGrasps(unittest.TestCase):

    def get_identity_grasp_msg(self):
        grasp = Pose()
        grasp.position.x = 0.0
        grasp.position.y = 0.0
        grasp.position.z = 0.0
        grasp.orientation.x = 0.0
        grasp.orientation.y = 0.0
        grasp.orientation.z = 0.0
        grasp.orientation.w = 1.0
        return copy.deepcopy(grasp)

    def pose_to_quaternion_list(self, pose):
        q_list = [pose.orientation.x,
                  pose.orientation.y,
                  pose.orientation.z,
                  pose.orientation.w]
        return q_list

    def get_grasps_object(self):
        g = Grasps()
        g.add_grasp(self.get_identity_grasp_msg())
        return copy.deepcopy(g)

    def test_grasp_size(self):
        g = self.get_grasps_object()
        self.assertEquals(g.size(), 1)

    def test_undo_redo(self):
        g = self.get_grasps_object()
        grasp = copy.deepcopy(g.get_grasp_by_index(0))
        g.undo()
        self.assertEquals(g.size(), 0)
        g.redo()
        self.assertEquals(grasp, g.get_grasp_by_index(0))
        self.assertEquals(g.size(), 1)

    def test_grasp_select(self):
        g = self.get_grasps_object()
        self.assertEquals(g.no_grasp_is_selected(), True)
        g.select_grasp(0)
        self.assertEquals(g.no_grasp_is_selected(), False)
        grasp = g.get_selected_grasp()
        self.assertEquals(grasp, self.get_identity_grasp_msg())

    def test_rotate_grasp_roll(self):
        g = self.get_grasps_object()
        grasp = g.rotate_grasp(g.get_grasp_by_index(0), roll=math.radians(90.0))
        q = self.pose_to_quaternion_list(grasp)
        # quaternion with a 90.0 degree roll rotation
        desired_q = [0.7071067811865475, 0.0, 0.0, 0.7071067811865476]
        self.assertEquals(np.allclose(desired_q, q), True)

    def test_rotate_grasp_pitch(self):
        g = self.get_grasps_object()
        grasp = g.rotate_grasp(g.get_grasp_by_index(0), pitch=math.radians(90.0))
        q = self.pose_to_quaternion_list(grasp)
        # quaternion with a 90.0 degree pitch rotation
        desired_q = [0.0, 0.7071067811865475, 0.0, 0.7071067811865476]
        self.assertEquals(np.allclose(desired_q, q), True)

    def test_rotate_grasp_yaw(self):
        g = self.get_grasps_object()
        grasp = g.rotate_grasp(g.get_grasp_by_index(0), yaw=math.radians(90.0))
        q = self.pose_to_quaternion_list(grasp)
        # quaternion with a 90.0 degree yaw rotation
        desired_q = [0.0, 0.0, 0.7071067811865475, 0.7071067811865476]
        self.assertEquals(np.allclose(desired_q, q), True)        

    def test_rotate_selected_grasps_replace_true(self):
        g = self.get_grasps_object()
        g.select_grasp(0)
        g.rotate_selected_grasps(roll=math.radians(90.0), replace=True)
        grasp = g.get_grasp_by_index(0)
        q = self.pose_to_quaternion_list(grasp)
        # quaternion with a 90.0 degree roll rotation
        desired_q = [0.7071067811865475, 0.0, 0.0, 0.7071067811865476]
        self.assertEquals(np.allclose(desired_q, q), True)

    def test_rotate_selected_grasps_replace_false(self):
        g = self.get_grasps_object()
        g.select_grasp(0)
        g.rotate_selected_grasps(roll=math.radians(90.0), replace=False)
        grasp = g.get_grasp_by_index(1)
        q = self.pose_to_quaternion_list(grasp)
        # quaternion with a 90.0 degree roll rotation
        desired_q = [0.7071067811865475, 0.0, 0.0, 0.7071067811865476]
        self.assertEquals(np.allclose(desired_q, q), True)

    def test_rotate_selected_grasps_replace_true_many_grasps(self):
        g = self.get_grasps_object()
        grasp = self.get_identity_grasp_msg()
        grasp.position.z = 0.05
        g.add_grasp(grasp)
        self.assertEquals(g.size(), 2)
        g.select_all_grasps()
        g.rotate_selected_grasps(yaw=math.radians(180.0), replace=True)
        grasp0 = g.get_grasp_by_index(0)
        grasp1 = g.get_grasp_by_index(1)
        q0 = self.pose_to_quaternion_list(grasp0)
        q1 = self.pose_to_quaternion_list(grasp1)
        desired_q = [0.0, 0.0, 1.0, 6.123233995736766e-17]
        self.assertEquals(np.allclose(desired_q, q0), True)
        self.assertEquals(np.allclose(desired_q, q1), True)

    def test_transform_selected_grasp_replace_true(self):
        g = self.get_grasps_object()
        g.select_grasp(0)
        linear = [0.05, 0.0, 0.0]
        g.transform_selected_grasps(linear=linear, replace=True)
        grasp = g.get_grasp_by_index(0)
        self.assertEquals(grasp.position.x, 0.05)

if __name__ == '__main__':
    import rostest
    rostest.rosrun(PKG, 'test_g', TestGrasps)
