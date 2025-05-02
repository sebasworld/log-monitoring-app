import pytest
import os
from datetime import datetime, date, time, timedelta
from pathlib import Path

import monitor_logs

# --- Fixtures ---

@pytest.fixture
def sample_csv_content_ok():
    """Provides content for a valid CSV log file."""
    return """2025-05-02 10:00:00,Job A, START,pid1
2025-05-02 10:04:00,Job B, START,pid2
2025-05-02 10:05:00,Job A, END,pid1
2025-05-02 10:11:00,Job C, START,pid3
2025-05-02 10:15:00,Job B, END,pid2
2025-05-02 10:30:00,Job C, END,pid3
"""

@pytest.fixture
def sample_csv_content_missing_end():
    """Provides content where pid2 is missing END."""
    return """2025-05-02 10:00:00,Job A, START,pid1
2025-05-02 10:04:00,Job B, START,pid2
2025-05-02 10:05:00,Job A, END,pid1
"""

@pytest.fixture
def sample_csv_content_duplicate_start():
    """Provides content where pid1 has duplicate START (latest should be used)."""
    return """2025-05-02 09:00:00,Job A Old, START,pid1
2025-05-02 10:00:00,Job A New, START,pid1
2025-05-02 10:05:00,Job A New, END,pid1
"""

# --- Tests for transform_csv_into_dictionary ---

def test_transform_csv_ok(tmp_path, sample_csv_content_ok):
    """Tests successful parsing of a valid CSV."""
    p = tmp_path / "test_ok.csv"
    p.write_text(sample_csv_content_ok, encoding='utf-8')
    expected_dict = {
        'pid1': {' DESCRIPTION': 'Job A', ' START': '2025-05-02 10:00:00', ' END': '2025-05-02 10:05:00'},
        'pid2': {' DESCRIPTION': 'Job B', ' START': '2025-05-02 10:04:00', ' END': '2025-05-02 10:15:00'},
        'pid3': {' DESCRIPTION': 'Job C', ' START': '2025-05-02 10:11:00', ' END': '2025-05-02 10:30:00'}
    }
    result = monitor_logs.transform_csv_into_dictionary(str(p))
    assert result == expected_dict

def test_transform_csv_file_not_found():
    """Tests behavior when the input file doesn't exist."""
    result = monitor_logs.transform_csv_into_dictionary("non_existent_file.csv")
    assert result is None

def test_transform_csv_empty_file(tmp_path):
    """Tests behavior with an empty CSV file."""
    p = tmp_path / "empty.csv"
    p.write_text("", encoding='utf-8')
    result = monitor_logs.transform_csv_into_dictionary(str(p))
    assert result == {}

def test_transform_csv_missing_end(tmp_path, sample_csv_content_missing_end):
    """Tests parsing when some jobs are missing END records."""
    p = tmp_path / "missing_end.csv"
    p.write_text(sample_csv_content_missing_end, encoding='utf-8')
    expected_dict = {
        'pid1': {' DESCRIPTION': 'Job A', ' START': '2025-05-02 10:00:00', ' END': '2025-05-02 10:05:00'},
        'pid2': {' DESCRIPTION': 'Job B', ' START': '2025-05-02 10:04:00'} # No END key
    }
    result = monitor_logs.transform_csv_into_dictionary(str(p))
    assert result == expected_dict

def test_transform_csv_duplicate_start(tmp_path, sample_csv_content_duplicate_start):
    """Tests that the latest START timestamp is kept when duplicates occur."""
    p = tmp_path / "duplicate_start.csv"
    p.write_text(sample_csv_content_duplicate_start, encoding='utf-8')
    expected_dict = {
        # Description from the first encounter, START/END from latest relevant row
        'pid1': {' DESCRIPTION': 'Job A Old', ' START': '2025-05-02 10:00:00', ' END': '2025-05-02 10:05:00'}
    }
    result = monitor_logs.transform_csv_into_dictionary(str(p))
    # Note: The DESCRIPTION key might need adjustment if the script logic changes
    # For now, it keeps the description from the *first* time the PID is seen.
    assert result == expected_dict
    assert result['pid1'][' DESCRIPTION'] == 'Job A Old' # Verify description comes from first hit
    assert result['pid1'] [' START'] == '2025-05-02 10:00:00' # Verify latest START


# --- Tests for timestamps_from_string_to_time ---

@pytest.mark.parametrize("time_str, expected_time", [
    ("10:05:30", time(10, 5, 30)),
    ("00:00:00", time(0, 0, 0)),
    ("23:59:59", time(23, 59, 59)),
])
def test_timestamps_conversion_ok(time_str, expected_time):
    """Tests successful conversion of H:M:S strings to time objects."""
    result = monitor_logs.timestamps_from_string_to_time(time_str)
    assert result == expected_time
    assert isinstance(result, time)

def test_timestamps_conversion_invalid_format():
    """Tests that incorrect format raises ValueError."""
    with pytest.raises(ValueError):
        monitor_logs.timestamps_from_string_to_time("10-05-30") # Incorrect format
    with pytest.raises(ValueError):
        monitor_logs.timestamps_from_string_to_time("25:00:00") # Invalid hour

# --- Tests for substract_times ---

@pytest.mark.parametrize("start_str, end_str, expected_delta_seconds", [
    ("10:00:00", "10:05:30", 330),      # Normal case
    ("23:58:00", "00:03:00", 300),      # Across midnight
    ("14:10:15", "14:10:15", 0),        # Same time
    ("11:00:00", "10:59:00", -60),      # End before start (negative delta)
])
def test_substract_times(start_str, end_str, expected_delta_seconds):
    """Tests time subtraction, including midnight wrap-around."""
    start_t = monitor_logs.timestamps_from_string_to_time(start_str)
    end_t = monitor_logs.timestamps_from_string_to_time(end_str)
    expected_delta = timedelta(seconds=expected_delta_seconds)
    result_delta = monitor_logs.substract_times(start_t, end_t)
    assert result_delta == expected_delta

# --- Tests for alert_if_thresholds_passed ---

@pytest.mark.parametrize("duration_minutes, expected_return", [
    (3, 0),                      # Under 5 min
    (4.99, 0),                   # Just under 5 min
    (5, 0),                      # Exactly 5 min (uses >) -> 0
    (5.1, 1),                    # Just over 5 min -> 1
    (7, 1),                      # Between 5 and 10 -> 1
    (9.99, 1),                   # Just under 10 min -> 1
    (10, 1),                     # Exactly 10 min (uses > 5 and not > 10) -> 1
    (10.1, 2),                   # Just over 10 min -> 2
    (20, 2),                     # Well over 10 min -> 2
    (-1, 0),                     # Negative duration -> 0 (or depends on desired handling)
])
def test_alert_thresholds(duration_minutes, expected_return):
    """Tests threshold checking logic."""
    duration = timedelta(minutes=duration_minutes)
    result = monitor_logs.alert_if_thresholds_passed(duration)
    assert result == expected_return

# --- Tests for prepare_and_write_output_to_file ---

# Helper to create job dictionary structure easily
def create_job_entry(desc, start_str, end_str):
    entry = {' DESCRIPTION': desc}
    if start_str:
        entry[' START'] = start_str
    if end_str:
        entry[' END'] = end_str
    return entry

def test_prepare_write_ok_under_5min(tmp_path, capsys):
    """Tests processing and output for a job under 5 minutes."""
    jobs_dict = {'pid1': create_job_entry('Job Fast', '10:00:00', '10:03:00')}
    output_file = tmp_path / "output_ok.out"
    monitor_logs.prepare_and_write_output_to_file(jobs_dict, str(output_file))

    # Check console output
    captured = capsys.readouterr()
    assert "PID: pid1" in captured.out
    assert "START Timestamp: 10:00:00" in captured.out
    assert "END Timestamp:10:03:00" in captured.out
    assert "Job lasting time: 0:03:00" in captured.out
    assert "JOB lasting time was acceptable!" in captured.out

    # Check file output (should be empty)
    assert output_file.read_text(encoding='utf-8') == ""

def test_prepare_write_warning_5_to_10min(tmp_path, capsys):
    """Tests processing and output for a job between 5 and 10 minutes (WARNING)."""
    jobs_dict = {'pid2': create_job_entry('Job Warn', '11:00:00', '11:07:30')}
    output_file = tmp_path / "output_warn.out"
    monitor_logs.prepare_and_write_output_to_file(jobs_dict, str(output_file))

    # Check console output
    captured = capsys.readouterr()
    assert "PID: pid2" in captured.out
    assert "Job lasting time: 0:07:30" in captured.out
    assert "WARNING - JOB 'Job Warn' with PID:pid2 LASTED FOR MORE THAN 5 MINUTES!" in captured.out

    # Check file output
    file_content = output_file.read_text(encoding='utf-8')
    assert "WARNING - JOB 'Job Warn' with PID:pid2 LASTED FOR MORE THAN 5 MINUTES! (0:07:30)" in file_content

def test_prepare_write_error_over_10min(tmp_path, capsys):
    """Tests processing and output for a job over 10 minutes (ERROR)."""
    jobs_dict = {'pid3': create_job_entry('Job Error', '12:00:00', '12:15:00')}
    output_file = tmp_path / "output_err.out"
    monitor_logs.prepare_and_write_output_to_file(jobs_dict, str(output_file))

    # Check console output
    captured = capsys.readouterr()
    assert "PID: pid3" in captured.out
    assert "Job lasting time: 0:15:00" in captured.out
    assert "ERROR - JOB 'Job Error' with PID:pid3 LASTED FOR MORE THAN 10 MINUTES!" in captured.out

    # Check file output
    file_content = output_file.read_text(encoding='utf-8')
    assert "ERROR - JOB 'Job Error' with PID:pid3 LASTED FOR MORE THAN 10 MINUTES! (0:15:00)" in file_content

def test_prepare_write_missing_end(tmp_path, capsys):
    """Tests processing and output for a job missing the END record."""
    jobs_dict = {'pid4': create_job_entry('Job Open', '13:00:00', None)} # END is missing
    output_file = tmp_path / "output_missing_end.out"
    monitor_logs.prepare_and_write_output_to_file(jobs_dict, str(output_file))

    # Check console output
    captured = capsys.readouterr()
    assert "PID: pid4" in captured.out
    assert "START Timestamp: 13:00:00" in captured.out
    assert "END Timestamp:Not Found" in captured.out # Uses .get default
    assert "This JOB didn't END!" in captured.out
    assert "Job lasting time:" not in captured.out # Shouldn't calculate duration

    # Check file output (should be empty)
    assert output_file.read_text(encoding='utf-8') == ""

def test_prepare_write_missing_start(tmp_path, capsys):
    """
    Tests processing when START is missing.
    Verifies that the function catches the internal ValueError
    and prints the corresponding error message (Option 2).
    """
    # Use create_job_entry with None for start_str to simulate missing key
    # The helper function now explicitly sets 'Not Found' if start_str is None
    jobs_dict = {'pid5': create_job_entry('Job Orphan End', None, '14:30:00')}
    output_file = tmp_path / "output_missing_start.out"

    # Call the function directly - expect it to catch the error internally
    monitor_logs.prepare_and_write_output_to_file(jobs_dict, str(output_file))

    # Check console output
    captured = capsys.readouterr()
    # Check initial prints still happen
    assert "PID: pid5" in captured.out
    assert "START Timestamp: Not Found" in captured.out # Checks the .get default worked
    assert "END Timestamp:14:30:00" in captured.out
    # Check that the SPECIFIC error message printed by the internal except block is present
    assert "An unexpected error occurred during processing: time data 'Not Found' does not match format '%H:%M:%S'" in captured.out
    # Check that duration calculation/alerting messages are NOT present
    assert "Job lasting time:" not in captured.out
    assert "acceptable!" not in captured.out
    assert "WARNING - JOB" not in captured.out
    assert "ERROR - JOB" not in captured.out


    # Check file output (should be empty because the error prevents duration checks)
    assert output_file.read_text(encoding='utf-8') == ""

def test_prepare_write_empty_dict(tmp_path, capsys):
    """Tests processing with an empty input dictionary."""
    jobs_dict = {}
    output_file = tmp_path / "output_empty.out"
    monitor_logs.prepare_and_write_output_to_file(jobs_dict, str(output_file))

    # Check console output (should be minimal)
    captured = capsys.readouterr()
    assert "PID:" not in captured.out # No jobs processed

    # Check file output (should be empty)
    assert output_file.read_text(encoding='utf-8') == ""