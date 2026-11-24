import unittest

from mihoyo_captcha.vision import parse_cells


class ParseCellsTest(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(parse_cells('{"target": "喷泉", "cells": [5, 6, 8]}'), [5, 6, 8])

    def test_code_fence(self):
        content = '```json\n{"target": "鹿", "cells": [2, 5, 8]}\n```'
        self.assertEqual(parse_cells(content), [2, 5, 8])

    def test_string_cells(self):
        self.assertEqual(parse_cells('{"target": "x", "cells": ["1,3,5"]}'), [1, 3, 5])

    def test_filters_out_of_range_and_duplicates(self):
        self.assertEqual(parse_cells('{"target": "x", "cells": [1, 1, 0, 10, "2"]}'), [1, 2])

    def test_invalid_content(self):
        self.assertEqual(parse_cells("抱歉，我无法识别"), [])
        self.assertEqual(parse_cells(""), [])

    def test_bad_json(self):
        self.assertEqual(parse_cells('{"target": "x", "cells": [1,2'), [])


if __name__ == "__main__":
    unittest.main()
