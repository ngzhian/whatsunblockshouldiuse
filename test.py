import random
import unittest

from server import (
    get_location_text,
)

class TestSequenceFunctions(unittest.TestCase):
    def setUp(self):
        self.f = open('testhtml')

    def test_get_location(self):
        location = get_location_text(
            '<b>The UV Index forecast for</b> <B><I>New York, NY</I></B> on <B>Saturday , March     07, 2015 is :&nbsp;</B>')
        self.assertEqual(location, 'New York, NY')

    def tearDown(self):
        self.f.close()

if __name__ == '__main__':
    unittest.main()
