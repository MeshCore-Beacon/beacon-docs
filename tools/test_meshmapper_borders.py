import unittest
from download_meshmapper_borders import select_border


def feature(code="YKF"):
    return {"type": "Feature", "properties": {"code": code}, "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}}


class BorderSelectionTest(unittest.TestCase):
    def test_exact_group_member_only(self):
        wanted = feature()
        self.assertEqual(select_border({"type": "FeatureCollection", "features": [feature("YOW"), wanted]}, "YKF"), wanted)
        with self.assertRaises(ValueError):
            select_border({"type": "FeatureCollection", "features": [wanted, wanted]}, "YKF")

    def test_null_is_not_a_synthetic_circle(self):
        value = feature(); value["geometry"] = None
        self.assertIsNone(select_border({"type": "FeatureCollection", "features": [value]}, "YKF"))

    def test_malformed_geometry_fails(self):
        for position in ([181, 0], [0, 91], [float("nan"), 0], [False, 0]):
            value = feature(); value["geometry"]["coordinates"][0][1] = position
            with self.assertRaises(ValueError):
                select_border({"type": "FeatureCollection", "features": [value]}, "YKF")


if __name__ == "__main__":
    unittest.main()
