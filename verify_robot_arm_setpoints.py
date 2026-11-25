import ast
import logging
from itertools import zip_longest

SYSTEM_INPUT_FILE = 'system_input_file.1630412935.txt'
SYSTEM_OUTPUT_FILE = 'system_ouput_file.1630412935.txt'

def is_xy_tuple(value):
    """Return True when value is a numeric 2D coordinate tuple."""
    return (
        isinstance(value, tuple)
        and len(value) == 2
        and all(isinstance(v, (int, float)) for v in value)
    )


def parse_points_block(lines):
    """Parse section lines into a flat list of (x, y) tuples."""
    points = []

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            continue
        if line in ('Points', 'Rectangle'):
            break

        try:
            parsed = ast.literal_eval(line)
        except (ValueError):
            points.append(line)
            continue

        if is_xy_tuple(parsed):
            x, y = map(float, parsed)
            points.append((x, y))
        elif isinstance(parsed, (list, tuple)):
            if len(parsed) == 0:
                points.append(parsed)
            for item in parsed:
                if is_xy_tuple(item):
                    x, y = map(float, item)
                    points.append((x, y))

    return points

def load_data_from_input_file():
    """Load input setpoints and rectangle vertices from the input file sections."""
    with open(SYSTEM_INPUT_FILE, 'r') as f:
        lines = f.readlines()

    points = []
    rectangle_vertices = []

    for idx, line in enumerate(lines):
        if line.strip() == 'Points':
            points = parse_points_block(lines[idx + 1:])
        elif line.strip() == 'Rectangle':
            rectangle_vertices = parse_points_block(lines[idx + 1:])

    return points, rectangle_vertices


def load_setpoints_from_system_output_file():
    """Load visited points emitted by the system output file."""
    with open(SYSTEM_OUTPUT_FILE, 'r') as f:
        lines = [line.strip() for line in f.readlines()]

    return parse_points_block(lines)


def compute_input_setpoints_partition(input_setpoints, rectangle_vertices):
    """Split input setpoints into points inside/outside rectangle bounds."""
    if len(rectangle_vertices) != 4:
        return [], []

    x_coords = [v[0] for v in rectangle_vertices]
    y_coords = [v[1] for v in rectangle_vertices]
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)

    visited = []
    not_visited = []
    for point in input_setpoints:
        x, y = point
        if min_x <= x <= max_x and min_y <= y <= max_y:
            visited.append(point)
        else:
            not_visited.append(point)

    return visited, not_visited

def write_test_results(expected_points, actual_points, row_result):
    """Write results with expected/actual columns and one overall PASS/FAIL value."""
    with open('test_results.txt', 'w') as results_file:
        results_file.write('Expected visited points\t\tActual visited points\t\tTest result (PASS / FAIL)\n')
        max_rows = max(len(expected_points), len(actual_points), 1)
        for idx in range(max_rows):
            expected_text = str(expected_points[idx]) if idx < len(expected_points) else ''
            actual_text = str(actual_points[idx]) if idx < len(actual_points) else ''
            result_text = str(row_result) if idx == 0 else ''
            results_file.write(f"{expected_text:<32} {actual_text:<32} {result_text}\n")


def run_verification():
    """Run all checks and return details for result writing."""
    input_setpoints, rectangle_vertices = load_data_from_input_file()
    system_setpoints = load_setpoints_from_system_output_file()
    expected_points_visited, points_not_visited = compute_input_setpoints_partition(input_setpoints, rectangle_vertices)

    req1 = (
        input_setpoints is not None
        and len(input_setpoints) > 0
        and all(is_xy_tuple(point) for point in input_setpoints)
    )

    req2 = (len(expected_points_visited) != 0 and len(points_not_visited) == 0)
    logging.error(f"REQ2: Not all setpoints provided are within the rectangle: {points_not_visited}")


    actual_system_visited = []
    system_not_visited_points = []

    for exp, act in zip_longest(expected_points_visited, system_setpoints, fillvalue=None):
        if exp == act:
            actual_system_visited.append(act)
        else:
            system_not_visited_points.append(act)

    req3 = len(system_not_visited_points) == 0 and len(actual_system_visited) != 0
    logging.error(f"REQ3: Not all system setpoints match expected visited points: {system_not_visited_points}")

    return {
        'expected_points': expected_points_visited,
        'actual_points': actual_system_visited,
        'req1': req1,
        'req2': req2,
        'req3': req3,
    }


if __name__ == '__main__':
    result = run_verification()
    overall_result = result['req1'] and result['req2'] and result['req3']

    write_test_results(
        result['expected_points'],
        result['actual_points'],
        'PASS' if overall_result else 'FAIL',
    )
